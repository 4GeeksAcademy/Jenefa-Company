"""Clinic inventory: ledger stock math, auth, and overdraft guardrails."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.inventory.models import MedicalSupply
from app.inventory.seed import SEED_OPERATORS, SEED_PASSWORD_DEFAULT


@pytest.fixture()
def inventory_client(
    auth_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    db_file = tmp_path / "inventory.db"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
    from app.main import app

    with TestClient(app) as client:
        yield client


def _auth_header(client: TestClient) -> dict[str, str]:
    operator = SEED_OPERATORS[0]
    response = client.post(
        "/auth/login",
        json={"email": operator["email"], "password": SEED_PASSWORD_DEFAULT},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_products_require_authentication(inventory_client: TestClient) -> None:
    response = inventory_client.get("/inventory/products")
    assert response.status_code == 401


def test_seed_catalog_stock_aggregations(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    response = inventory_client.get("/inventory/products", headers=headers)
    assert response.status_code == 200
    rows = {item["id"]: item for item in response.json()}

    gloves = rows[10]
    assert gloves["name"] == "Sterile Surgical Gloves"
    assert gloves["sku"] == "HC-GLV-002"
    assert gloves["clinic_id"] == "CLINIC-TX-01"
    assert gloves["current_stock"] == 450
    assert "stock" not in gloves

    vial = rows[20]
    assert vial["name"] == "Controlled Sedative Vial"
    assert vial["sku"] == "HC-SED-882"
    assert vial["clinic_id"] == "CLINIC-UK-02"
    assert vial["current_stock"] == 35


def test_product_detail_includes_partition_quantities(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    response = inventory_client.get("/inventory/products/10", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["current_stock"] == 450
    partitions = {row["clinic_id"]: row for row in body["partitions"]}
    assert partitions["CLINIC-TX-01"]["inbound_total"] == 750
    assert partitions["CLINIC-TX-01"]["outbound_total"] == 300
    assert partitions["CLINIC-TX-01"]["current_stock"] == 450


def test_create_product_starts_at_zero_stock(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    response = inventory_client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "N95 Respirator Mask",
            "sku": "HC-MSK-100",
            "clinic_id": "CLINIC-TX-01",
            "regulatory_tier": "Standard Clinical",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["current_stock"] == 0
    assert "stock" not in MedicalSupply.model_fields


def test_inbound_records_tinydb_user_uuid(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    response = inventory_client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={"medical_supply_id": 10, "quantity": 10, "clinic_id": "CLINIC-TX-01"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user_uuid"] == SEED_OPERATORS[0]["user_uuid"]
    assert body["medical_supply"]["sku"] == "HC-GLV-002"

    listed = inventory_client.get("/inventory/products/10", headers=headers)
    assert listed.json()["current_stock"] == 460


def test_outbound_overdraft_rejected_before_write(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    before = inventory_client.get("/inventory/orders", headers=headers)
    assert before.status_code == 200
    prior_count = len(before.json())

    response = inventory_client.post(
        "/inventory/orders/outbound",
        headers=headers,
        json={"medical_supply_id": 10, "quantity": 451, "clinic_id": "CLINIC-TX-01"},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "451" in str(detail)
    assert "450" in str(detail)

    after = inventory_client.get("/inventory/orders", headers=headers)
    assert len(after.json()) == prior_count
    stock = inventory_client.get("/inventory/products/10", headers=headers)
    assert stock.json()["current_stock"] == 450


def test_valid_outbound_decrements_computed_stock(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    response = inventory_client.post(
        "/inventory/orders/outbound",
        headers=headers,
        json={"medical_supply_id": 20, "quantity": 5, "clinic_id": "CLINIC-UK-02"},
    )
    assert response.status_code == 201, response.text
    stock = inventory_client.get("/inventory/products/20", headers=headers)
    assert stock.json()["current_stock"] == 30


def test_orders_preload_related_supplies(inventory_client: TestClient) -> None:
    headers = _auth_header(inventory_client)
    engine = inventory_client.app.state.inventory_engine
    queries: list[str] = []

    def _on_execute(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:  # noqa: ANN001
        queries.append(str(statement))

    event.listen(engine, "before_cursor_execute", _on_execute)
    try:
        response = inventory_client.get("/inventory/orders", headers=headers)
    finally:
        event.remove(engine, "before_cursor_execute", _on_execute)

    assert response.status_code == 200
    rows = response.json()
    assert {row["kind"] for row in rows} == {"inbound", "outbound"}
    assert all("medical_supply" in row and row["medical_supply"]["sku"] for row in rows)
    select_count = sum(1 for sql in queries if sql.strip().lower().startswith("select"))
    assert select_count <= 6
