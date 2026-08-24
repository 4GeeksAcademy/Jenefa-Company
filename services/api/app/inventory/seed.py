"""Baseline identity cache and relational catalog for tracking environments."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlmodel import Session, select

from ..auth import database as auth_db
from ..auth.security import hash_password
from .models import InboundEntry, MedicalSupply, OutboundExit

SEED_PASSWORD_DEFAULT = "ClinicSeedPass1"

SEED_OPERATORS = (
    {
        "user_uuid": "usr-hc-9901",
        "email": "marcus.reid@healthcore.example",
        "name": "Dr. Marcus Reid",
        "role": "manager",
    },
    {
        "user_uuid": "usr-hc-2544",
        "email": "austin.nurse@healthcore.example",
        "name": "Austin Clinic Floor Nurse",
        "role": "user",
    },
)

_seed_password_hash: str | None = None


def seed_identity_cache() -> None:
    """Insert TinyDB operators from the product context when missing."""
    hashed = _password_hash()
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for operator in SEED_OPERATORS:
        user_uuid = operator["user_uuid"]
        if auth_db.get_user_by_id(user_uuid) is not None:
            continue
        if auth_db.get_user_by_email(operator["email"]) is not None:
            continue
        auth_db.insert_user(
            {
                "id": user_uuid,
                "user_uuid": user_uuid,
                "email": operator["email"],
                "hashed_password": hashed,
                "is_active": True,
                "role": operator["role"],
                "created_at": created,
            }
        )
        auth_db.insert_profile(
            {
                "id": str(uuid4()),
                "user_id": user_uuid,
                "name": operator["name"],
                "phone": "",
                "address": "",
            }
        )


def seed_relational_catalog(session: Session) -> None:
    """Load MedicalSupply / ledger rows when the catalog is empty."""
    if session.exec(select(MedicalSupply).limit(1)).first() is not None:
        return

    session.add(
        MedicalSupply(
            id=10,
            name="Sterile Surgical Gloves",
            sku="HC-GLV-002",
            clinic_id="CLINIC-TX-01",
            regulatory_tier="Standard Clinical",
        )
    )
    session.add(
        MedicalSupply(
            id=20,
            name="Controlled Sedative Vial",
            sku="HC-SED-882",
            clinic_id="CLINIC-UK-02",
            regulatory_tier="High-Regulated (GDPR/HIPAA)",
        )
    )
    session.flush()

    session.add(
        InboundEntry(
            id=1,
            medical_supply_id=10,
            quantity=500,
            clinic_id="CLINIC-TX-01",
            created_at=datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
            user_uuid="usr-hc-9901",
        )
    )
    session.add(
        InboundEntry(
            id=2,
            medical_supply_id=20,
            quantity=50,
            clinic_id="CLINIC-UK-02",
            created_at=datetime(2026, 1, 11, 9, 0, tzinfo=timezone.utc),
            user_uuid="usr-hc-2544",
        )
    )
    session.add(
        InboundEntry(
            id=3,
            medical_supply_id=10,
            quantity=250,
            clinic_id="CLINIC-TX-01",
            created_at=datetime(2026, 1, 20, 9, 0, tzinfo=timezone.utc),
            user_uuid="usr-hc-2544",
        )
    )
    session.add(
        OutboundExit(
            id=1,
            medical_supply_id=10,
            quantity=300,
            clinic_id="CLINIC-TX-01",
            created_at=datetime(2026, 1, 22, 9, 0, tzinfo=timezone.utc),
            user_uuid="usr-hc-2544",
        )
    )
    session.add(
        OutboundExit(
            id=2,
            medical_supply_id=20,
            quantity=15,
            clinic_id="CLINIC-UK-02",
            created_at=datetime(2026, 1, 23, 9, 0, tzinfo=timezone.utc),
            user_uuid="usr-hc-9901",
        )
    )
    session.commit()
    _sync_postgres_sequences(session)


def _password_hash() -> str:
    global _seed_password_hash
    if _seed_password_hash is None:
        password = os.getenv("INVENTORY_SEED_PASSWORD") or SEED_PASSWORD_DEFAULT
        _seed_password_hash = hash_password(password)
    return _seed_password_hash


def _sync_postgres_sequences(session: Session) -> None:
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in ("medicalsupply", "inboundentry", "outboundexit"):
        session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            )
        )
    session.commit()
