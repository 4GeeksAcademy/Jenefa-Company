"""NIST GOVERN/IDENTIFY registry endpoints for AI systems and tools."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.deps import get_current_user
from app.inventory.database import get_session

from .models import AISystem
from .schemas import AISystemCreate, AISystemRead

router = APIRouter(prefix="/governance/ai-systems", tags=["secure-ai"])


def _require_admin(current_user: dict[str, Any]) -> None:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required")


@router.get("", response_model=list[AISystemRead])
def list_ai_systems(
    _current_user: dict[str, Any] = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[AISystem]:
    return list(session.exec(select(AISystem).order_by(AISystem.system_key)))


@router.post("", response_model=AISystemRead, status_code=status.HTTP_201_CREATED)
def register_ai_system(
    payload: AISystemCreate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AISystem:
    _require_admin(current_user)
    system = AISystem(**payload.model_dump())
    session.add(system)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="system_key already registered") from exc
    session.refresh(system)
    return system


@router.post("/{system_key}/suspend", response_model=AISystemRead)
def suspend_ai_system(
    system_key: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AISystem:
    _require_admin(current_user)
    system = session.exec(select(AISystem).where(AISystem.system_key == system_key)).first()
    if system is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI system not found")
    system.status = "suspended"
    system.updated_at = datetime.now(timezone.utc)
    session.add(system)
    session.commit()
    session.refresh(system)
    return system