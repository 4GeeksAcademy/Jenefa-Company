"""Validated contracts for the AI governance registry."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RiskTier = Literal["low", "medium", "high", "critical"]
Jurisdiction = Literal["US", "UK", "cross-border"]
SystemStatus = Literal["sandbox", "pending_review", "approved", "suspended"]


class AISystemCreate(BaseModel):
    system_key: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,79}$")
    name: str = Field(min_length=1, max_length=120)
    architecture_type: str = Field(min_length=1, max_length=120)
    data_traversal_surface: str = Field(min_length=1, max_length=500)
    provider: str = Field(min_length=1, max_length=160)
    owner: str = Field(min_length=1, max_length=120)
    risk_tier: RiskTier
    jurisdiction: Jurisdiction
    status: SystemStatus = "sandbox"


class AISystemRead(AISystemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime