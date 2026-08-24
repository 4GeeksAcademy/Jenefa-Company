"""Presentation schemas for inventory endpoints. Never serialize table models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field
from sqlmodel import SQLModel


class MedicalSupplyCreate(SQLModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    clinic_id: str = Field(min_length=1)
    regulatory_tier: str = Field(min_length=1)


class MedicalSupplySummary(SQLModel):
    id: int
    name: str
    sku: str
    clinic_id: str
    regulatory_tier: str


class PartitionStock(SQLModel):
    clinic_id: str
    inbound_total: int
    outbound_total: int
    current_stock: int


class MedicalSupplyRead(MedicalSupplySummary):
    current_stock: int


class MedicalSupplyDetail(MedicalSupplyRead):
    partitions: list[PartitionStock]


class LedgerCreate(SQLModel):
    medical_supply_id: int
    quantity: int = Field(gt=0)
    clinic_id: str = Field(min_length=1)


class LedgerRead(SQLModel):
    id: int
    medical_supply_id: int
    quantity: int
    clinic_id: str
    created_at: datetime
    user_uuid: str
    medical_supply: MedicalSupplySummary


class OrderRead(LedgerRead):
    kind: Literal["inbound", "outbound"]
