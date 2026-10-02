"""Persistent, non-PHI registry for HealthCore AI systems."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AISystem(SQLModel, table=True):
    __tablename__ = "ai_system_registry"
    id: int | None = Field(default=None, primary_key=True)
    system_key: str = Field(unique=True, index=True, max_length=80)
    name: str = Field(max_length=120)
    architecture_type: str = Field(max_length=120)
    data_traversal_surface: str = Field(max_length=500)
    provider: str = Field(max_length=160)
    owner: str = Field(max_length=120)
    risk_tier: str = Field(index=True, max_length=20)
    jurisdiction: str = Field(index=True, max_length=20)
    status: str = Field(default="sandbox", index=True, max_length=20)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)