"""Clinic supply routes under `/inventory`. All handlers require TinyDB auth."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..auth.deps import get_current_user
from .database import get_session
from .schemas import (
    LedgerCreate,
    LedgerRead,
    MedicalSupplyCreate,
    MedicalSupplyDetail,
    MedicalSupplyRead,
    OrderRead,
)
from . import service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/products", response_model=list[MedicalSupplyRead])
def list_products(
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[MedicalSupplyRead]:
    _ = current_user
    return service.list_supplies(session)


@router.post("/products", response_model=MedicalSupplyRead, status_code=201)
def create_product(
    payload: MedicalSupplyCreate,
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MedicalSupplyRead:
    _ = current_user
    return service.create_supply(session, payload)


@router.get("/products/{supply_id}", response_model=MedicalSupplyDetail)
def get_product(
    supply_id: int,
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MedicalSupplyDetail:
    _ = current_user
    return service.get_supply(session, supply_id)


@router.post("/orders/inbound", response_model=LedgerRead, status_code=201)
def create_inbound(
    payload: LedgerCreate,
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> LedgerRead:
    return service.record_inbound(session, payload, current_user)


@router.post("/orders/outbound", response_model=LedgerRead, status_code=201)
def create_outbound(
    payload: LedgerCreate,
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> LedgerRead:
    return service.record_outbound(session, payload, current_user)


@router.get("/orders", response_model=list[OrderRead])
def list_orders(
    session: Session = Depends(get_session),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[OrderRead]:
    _ = current_user
    return service.list_orders(session)
