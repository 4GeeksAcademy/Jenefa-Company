"""Pydantic v2 models for the supplier directory API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from constants import (
    CURRENCY_BY_COUNTRY,
    VALID_CATEGORIES,
    VALID_COMPLIANCE,
    VALID_COUNTRIES,
    VALID_STATUSES,
)


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1)
    country: str
    categories: list[str] = Field(..., min_length=1)
    monthly_rate: float = Field(..., gt=0.0)
    currency: str
    status: str
    compliance_agreement: Optional[str] = None
    contract_renewal_date: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        if value not in VALID_COUNTRIES:
            raise ValueError(f"country must be one of {VALID_COUNTRIES}")
        return value

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("contact_email must be a valid email address")
        return value

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("categories must contain at least one entry")
        invalid = [c for c in value if c not in VALID_CATEGORIES]
        if invalid:
            raise ValueError(
                f"invalid categories: {invalid}; allowed: {VALID_CATEGORIES}"
            )
        # Preserve order, drop accidental duplicates.
        seen: set[str] = set()
        unique: list[str] = []
        for item in value:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return value

    @field_validator("compliance_agreement")
    @classmethod
    def validate_compliance(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in VALID_COMPLIANCE:
            raise ValueError(f"compliance_agreement must be one of {VALID_COMPLIANCE}")
        return value

    @field_validator("contract_renewal_date")
    @classmethod
    def validate_renewal_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        # YYYY-MM-DD
        parts = value.split("-")
        if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
            raise ValueError("contract_renewal_date must use YYYY-MM-DD")
        if not all(p.isdigit() for p in parts):
            raise ValueError("contract_renewal_date must use YYYY-MM-DD")
        return value

    @model_validator(mode="after")
    def validate_currency_matches_country(self) -> SupplierBase:
        expected = CURRENCY_BY_COUNTRY[self.country]
        if self.currency != expected:
            raise ValueError(
                f"currency for country {self.country} must be {expected}, got {self.currency}"
            )
        return self


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdateStatus(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return value


class SupplierUpdateRate(BaseModel):
    monthly_rate: float = Field(..., gt=0.0)


class SupplierResponse(SupplierBase):
    id: int
    updated_at: str
