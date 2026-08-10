"""TinyDB storage connection and query helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from tinydb import Query, TinyDB
from tinydb.table import Document

DB_PATH = Path(__file__).resolve().parent / "db.json"

_db: TinyDB | None = None


def utc_now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 without microseconds or offset."""
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")


def get_db() -> TinyDB:
    global _db
    if _db is None:
        _db = TinyDB(DB_PATH)
    return _db


def close_db() -> None:
    global _db
    if _db is not None:
        _db.close()
        _db = None


def doc_to_supplier(doc: Document) -> dict[str, Any]:
    data = dict(doc)
    data["id"] = doc.doc_id
    return data


def list_suppliers(
    *,
    country: Optional[str] = None,
    category: Optional[str] = None,
    product_category: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return suppliers, optionally filtered by country and/or category."""
    table = get_db().table("suppliers")
    rows = [doc_to_supplier(doc) for doc in table.all()]

    filter_category = category or product_category
    if country:
        rows = [r for r in rows if r.get("country") == country]
    if filter_category:
        rows = [r for r in rows if filter_category in (r.get("categories") or [])]

    rows.sort(key=lambda r: r["id"])
    return rows


def get_supplier(supplier_id: int) -> Optional[dict[str, Any]]:
    table = get_db().table("suppliers")
    doc = table.get(doc_id=supplier_id)
    if doc is None:
        return None
    return doc_to_supplier(doc)


def create_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    table = get_db().table("suppliers")
    record = {**payload, "updated_at": utc_now_iso()}
    doc_id = table.insert(record)
    return get_supplier(doc_id)  # type: ignore[return-value]


def update_rate(supplier_id: int, monthly_rate: float) -> Optional[dict[str, Any]]:
    table = get_db().table("suppliers")
    if table.get(doc_id=supplier_id) is None:
        return None
    table.update(
        {"monthly_rate": monthly_rate, "updated_at": utc_now_iso()},
        doc_ids=[supplier_id],
    )
    return get_supplier(supplier_id)


def update_status(supplier_id: int, status: str) -> Optional[dict[str, Any]]:
    table = get_db().table("suppliers")
    if table.get(doc_id=supplier_id) is None:
        return None
    table.update({"status": status}, doc_ids=[supplier_id])
    return get_supplier(supplier_id)


def delete_supplier(supplier_id: int) -> bool:
    table = get_db().table("suppliers")
    if table.get(doc_id=supplier_id) is None:
        return False
    table.remove(doc_ids=[supplier_id])
    return True


def count_suppliers() -> int:
    return len(get_db().table("suppliers"))


def find_by_name(name: str) -> Optional[dict[str, Any]]:
    table = get_db().table("suppliers")
    Supplier = Query()
    doc = table.get(Supplier.name == name)
    if doc is None:
        return None
    return doc_to_supplier(doc)


def insert_seed_record(payload: dict[str, Any]) -> int:
    table = get_db().table("suppliers")
    record = {**payload, "updated_at": utc_now_iso()}
    return table.insert(record)
