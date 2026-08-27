"""Inventory ledger operations. Stock is always computed, never stored."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from .models import InboundEntry, MedicalSupply, OutboundExit
from .schemas import (
    LedgerCreate,
    LedgerRead,
    MedicalSupplyCreate,
    MedicalSupplyDetail,
    MedicalSupplyRead,
    MedicalSupplySummary,
    OrderRead,
    PartitionStock,
)


def actor_uuid(current_user: dict[str, Any]) -> str:
    value = current_user.get("user_uuid") or current_user.get("id")
    if not value or not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return value


def current_stock_for(supply: MedicalSupply, clinic_id: str) -> tuple[int, int, int]:
    inbound_total = sum(
        row.quantity for row in supply.inbound_entries if row.clinic_id == clinic_id
    )
    outbound_total = sum(
        row.quantity for row in supply.outbound_exits if row.clinic_id == clinic_id
    )
    return inbound_total, outbound_total, inbound_total - outbound_total


def _summary(supply: MedicalSupply) -> MedicalSupplySummary:
    assert supply.id is not None
    return MedicalSupplySummary(
        id=supply.id,
        name=supply.name,
        sku=supply.sku,
        clinic_id=supply.clinic_id,
        regulatory_tier=supply.regulatory_tier,
    )


def _read(supply: MedicalSupply) -> MedicalSupplyRead:
    _, _, stock = current_stock_for(supply, supply.clinic_id)
    return MedicalSupplyRead(**_summary(supply).model_dump(), current_stock=stock)


def _detail(supply: MedicalSupply) -> MedicalSupplyDetail:
    buckets: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    buckets[supply.clinic_id]
    for row in supply.inbound_entries:
        buckets[row.clinic_id][0] += row.quantity
    for row in supply.outbound_exits:
        buckets[row.clinic_id][1] += row.quantity
    partitions = [
        PartitionStock(
            clinic_id=clinic_id,
            inbound_total=inbound,
            outbound_total=outbound,
            current_stock=inbound - outbound,
        )
        for clinic_id, (inbound, outbound) in sorted(buckets.items())
    ]
    _, _, stock = current_stock_for(supply, supply.clinic_id)
    return MedicalSupplyDetail(
        **_summary(supply).model_dump(),
        current_stock=stock,
        partitions=partitions,
    )


def _load_supplies(session: Session) -> Sequence[MedicalSupply]:
    statement = select(MedicalSupply).options(
        selectinload(MedicalSupply.inbound_entries),
        selectinload(MedicalSupply.outbound_exits),
    )
    return session.exec(statement).all()


def _load_supply(session: Session, supply_id: int) -> MedicalSupply | None:
    statement = (
        select(MedicalSupply)
        .where(MedicalSupply.id == supply_id)
        .options(
            selectinload(MedicalSupply.inbound_entries),
            selectinload(MedicalSupply.outbound_exits),
        )
    )
    return session.exec(statement).first()


def list_supplies(session: Session) -> list[MedicalSupplyRead]:
    return [_read(supply) for supply in _load_supplies(session)]


def get_supply(session: Session, supply_id: int) -> MedicalSupplyDetail:
    supply = _load_supply(session, supply_id)
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    return _detail(supply)


def create_supply(session: Session, payload: MedicalSupplyCreate) -> MedicalSupplyRead:
    supply = MedicalSupply(
        name=payload.name.strip(),
        sku=payload.sku.strip(),
        clinic_id=payload.clinic_id.strip(),
        regulatory_tier=payload.regulatory_tier.strip(),
    )
    session.add(supply)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A supply with this SKU already exists",
        ) from exc
    session.refresh(supply)
    loaded = _load_supply(session, supply.id or 0)
    assert loaded is not None
    return _read(loaded)


def record_inbound(
    session: Session,
    payload: LedgerCreate,
    current_user: dict[str, Any],
) -> LedgerRead:
    supply = _load_supply(session, payload.medical_supply_id)
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    entry = InboundEntry(
        medical_supply_id=payload.medical_supply_id,
        quantity=payload.quantity,
        clinic_id=payload.clinic_id.strip(),
        user_uuid=actor_uuid(current_user),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    entry.medical_supply = supply
    return _ledger_read(entry)


def record_outbound(
    session: Session,
    payload: LedgerCreate,
    current_user: dict[str, Any],
) -> LedgerRead:
    statement = (
        select(MedicalSupply)
        .where(MedicalSupply.id == payload.medical_supply_id)
        .options(
            selectinload(MedicalSupply.inbound_entries),
            selectinload(MedicalSupply.outbound_exits),
        )
        .with_for_update()
    )
    supply = session.exec(statement).first()
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")

    clinic_id = payload.clinic_id.strip()
    _, _, available = current_stock_for(supply, clinic_id)
    if payload.quantity > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock in clinic partition {clinic_id}: "
                f"requested {payload.quantity}, available {available}."
            ),
        )

    exit_row = OutboundExit(
        medical_supply_id=payload.medical_supply_id,
        quantity=payload.quantity,
        clinic_id=clinic_id,
        user_uuid=actor_uuid(current_user),
    )
    session.add(exit_row)
    session.commit()
    session.refresh(exit_row)
    exit_row.medical_supply = supply
    return _ledger_read(exit_row)


def list_orders(session: Session) -> list[OrderRead]:
    inbound_rows = session.exec(
        select(InboundEntry).options(selectinload(InboundEntry.medical_supply))
    ).all()
    outbound_rows = session.exec(
        select(OutboundExit).options(selectinload(OutboundExit.medical_supply))
    ).all()
    orders: list[OrderRead] = [
        OrderRead(kind="inbound", **_ledger_read(row).model_dump()) for row in inbound_rows
    ]
    orders.extend(
        OrderRead(kind="outbound", **_ledger_read(row).model_dump()) for row in outbound_rows
    )
    orders.sort(key=lambda row: (row.created_at, row.kind, row.id), reverse=True)
    return orders


def _ledger_read(row: InboundEntry | OutboundExit) -> LedgerRead:
    supply = row.medical_supply
    if supply is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The request could not be completed. Please try again.",
        )
    assert row.id is not None
    return LedgerRead(
        id=row.id,
        medical_supply_id=row.medical_supply_id,
        quantity=row.quantity,
        clinic_id=row.clinic_id,
        created_at=row.created_at,
        user_uuid=row.user_uuid,
        medical_supply=_summary(supply),
    )
