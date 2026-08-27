"""Per-request SQLModel sessions for the inventory ledger. No global Session."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from fastapi import Depends, Request
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from . import models as _models  # noqa: F401 — register table metadata

DEFAULT_SQLITE = Path(__file__).resolve().parents[2] / "data" / "inventory.db"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(ENV_PATH)


def inventory_database_url() -> str:
    explicit = (
        os.getenv("DB_URL")
        or os.getenv("INVENTORY_DATABASE_URL")
        or os.getenv("SUPABASE_DB_URL")
        or os.getenv("DATABASE_URL")
        or ""
    ).strip()
    if explicit:
        return _normalize_url(explicit)
    DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
    return _normalize_url(f"sqlite:///{DEFAULT_SQLITE}")


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def create_inventory_engine(url: str | None = None) -> Engine:
    resolved = url or inventory_database_url()
    connect_args: dict[str, object] = {}
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if resolved.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if resolved in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(resolved, connect_args=connect_args, **kwargs)
    if resolved.startswith("sqlite"):
        listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_inventory_schema(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_inventory_engine(request: Request) -> Engine:
    engine = getattr(request.app.state, "inventory_engine", None)
    if engine is None:
        raise RuntimeError("Inventory database is not initialized")
    return engine


def get_session(engine: Engine = Depends(get_inventory_engine)) -> Iterator[Session]:
    with Session(engine) as session:
        yield session
