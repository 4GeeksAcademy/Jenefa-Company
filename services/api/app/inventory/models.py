"""SQLModel table definitions for the HealthCore Clinic Supply Network.

Stock quantities are never stored on `MedicalSupply`. Balances are derived from
inbound and outbound ledger rows only.
"""

from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MedicalSupply(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(unique=True, index=True)
    clinic_id: str = Field(index=True)
    regulatory_tier: str

    inbound_entries: list["InboundEntry"] = Relationship(back_populates="medical_supply")
    outbound_exits: list["OutboundExit"] = Relationship(back_populates="medical_supply")


class InboundEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    medical_supply_id: int = Field(foreign_key="medicalsupply.id", index=True)
    quantity: int
    clinic_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utc_now)
    user_uuid: str

    medical_supply: MedicalSupply | None = Relationship(back_populates="inbound_entries")


class OutboundExit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    medical_supply_id: int = Field(foreign_key="medicalsupply.id", index=True)
    quantity: int
    clinic_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utc_now)
    user_uuid: str

    medical_supply: MedicalSupply | None = Relationship(back_populates="outbound_exits")
