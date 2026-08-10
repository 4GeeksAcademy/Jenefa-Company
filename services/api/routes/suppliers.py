"""Supplier directory endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from constants import VALID_CATEGORIES, VALID_COUNTRIES
from database import (
    create_supplier,
    delete_supplier,
    get_supplier,
    list_suppliers,
    update_rate,
    update_status,
)
from models import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdateRate,
    SupplierUpdateStatus,
)

router = APIRouter(tags=["suppliers"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/meta/categories")
def meta_categories() -> list[str]:
    return VALID_CATEGORIES


@router.get("/meta/countries")
def meta_countries() -> list[str]:
    return VALID_COUNTRIES


@router.get("/backoffice", response_class=HTMLResponse)
def backoffice(request: Request) -> HTMLResponse:
    """Lightweight Jinja backoffice served by the API."""
    return templates.TemplateResponse(
        request,
        "backoffice.html",
        {
            "categories": VALID_CATEGORIES,
            "countries": VALID_COUNTRIES,
        },
    )


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def post_supplier(body: SupplierCreate) -> dict:
    return create_supplier(body.model_dump())


@router.get("/suppliers", response_model=list[SupplierResponse])
def get_suppliers(
    country: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    product_category: Optional[str] = Query(
        default=None,
        description="Alias for category (supplier-specs compatibility).",
    ),
) -> list[dict]:
    if country is not None and country not in VALID_COUNTRIES:
        raise HTTPException(
            status_code=422,
            detail=f"country must be one of {VALID_COUNTRIES}",
        )
    filter_category = category or product_category
    if filter_category is not None and filter_category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"category must be one of {VALID_CATEGORIES}",
        )
    return list_suppliers(
        country=country,
        category=category,
        product_category=product_category,
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier_by_id(supplier_id: int) -> dict:
    row = get_supplier(supplier_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return row


@router.patch("/suppliers/{supplier_id}/rate", response_model=SupplierResponse)
def patch_supplier_rate(supplier_id: int, body: SupplierUpdateRate) -> dict:
    row = update_rate(supplier_id, body.monthly_rate)
    if row is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return row


@router.patch("/suppliers/{supplier_id}/status", response_model=SupplierResponse)
def patch_supplier_status(supplier_id: int, body: SupplierUpdateStatus) -> dict:
    row = update_status(supplier_id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return row


@router.delete("/suppliers/{supplier_id}", status_code=204)
def remove_supplier(supplier_id: int) -> None:
    """Hard-delete (specs). Prefer PATCH status=suspended for audit history."""
    if not delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
