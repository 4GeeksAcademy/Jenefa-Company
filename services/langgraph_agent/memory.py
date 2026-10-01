"""Dedicated episodic memory storage and human-in-the-loop governance."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MEMORY_TTL_DAYS = 90
APPROVE = "APPROVE"
REJECT = "REJECT"
EDIT = "EDIT"
DISCARD_BY_DEFAULT = "DISCARD_BY_DEFAULT"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def message_hash(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MemoryProposal:
    proposal_id: str
    fact_to_remember: str
    justification: str
    originating_message_hash: str
    created_at: str
    expires_at: str


@dataclass(frozen=True)
class MemoryResolution:
    proposal_id: str
    classification: str
    final_stored_state: str | None


class AgentMemoryStore:
    """SQLite-backed ``*_agent_memory`` store; never touches knowledge indexes."""

    def __init__(self, database_path: str | Path = "data/agent_memory.db") -> None:
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_proposals (
                proposal_id TEXT PRIMARY KEY,
                fact_to_remember TEXT NOT NULL,
                justification TEXT NOT NULL,
                originating_message_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING'
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_pending_memory_proposal
                ON memory_proposals(status) WHERE status = 'PENDING';
            CREATE TABLE IF NOT EXISTS agent_memory (
                memory_id TEXT PRIMARY KEY,
                fact TEXT NOT NULL,
                source_proposal_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(source_proposal_id) REFERENCES memory_proposals(proposal_id)
            );
            CREATE TABLE IF NOT EXISTS memory_audit (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                proposal_id TEXT NOT NULL,
                fact_proposed TEXT NOT NULL,
                originating_message_hash TEXT NOT NULL,
                user_classification TEXT NOT NULL,
                final_stored_state TEXT,
                authorizing_user_metadata TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def pending(self) -> MemoryProposal | None:
        row = self._connection.execute(
            "SELECT * FROM memory_proposals WHERE status = 'PENDING' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return self._proposal_from_row(row) if row else None

    def propose(self, fact_to_remember: str, justification: str, originating_message: str) -> MemoryProposal:
        fact = " ".join(fact_to_remember.split()).strip()
        reason = " ".join(justification.split()).strip()
        if not fact or not reason:
            raise ValueError("fact_to_remember and justification are required")
        if self.pending() is not None:
            raise ValueError("a memory proposal is already pending")
        created = utc_now()
        expires = created + timedelta(days=MEMORY_TTL_DAYS)
        proposal = MemoryProposal(
            proposal_id=str(uuid.uuid4()),
            fact_to_remember=fact,
            justification=reason,
            originating_message_hash=message_hash(originating_message),
            created_at=created.isoformat(),
            expires_at=expires.isoformat(),
        )
        self._connection.execute(
            "INSERT INTO memory_proposals VALUES (?, ?, ?, ?, ?, ?, 'PENDING')",
            (proposal.proposal_id, proposal.fact_to_remember, proposal.justification,
             proposal.originating_message_hash, proposal.created_at, proposal.expires_at),
        )
        self._connection.commit()
        return proposal

    def resolve(
        self,
        response: str,
        *,
        authorizing_user_metadata: dict[str, Any] | None = None,
    ) -> MemoryResolution:
        proposal = self.pending()
        if proposal is None:
            raise ValueError("no memory proposal is pending")
        classification, edited_fact = classify_intent(response)
        final_fact = edited_fact if classification == EDIT else (
            proposal.fact_to_remember if classification == APPROVE else None
        )
        now = utc_now().isoformat()
        self._connection.execute(
            "UPDATE memory_proposals SET status = ? WHERE proposal_id = ?",
            (classification, proposal.proposal_id),
        )
        if final_fact is not None:
            self._connection.execute(
                "INSERT INTO agent_memory VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), final_fact, proposal.proposal_id, now, proposal.expires_at),
            )
        self._connection.execute(
            "INSERT INTO memory_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), now, proposal.proposal_id, proposal.fact_to_remember,
             proposal.originating_message_hash, classification, final_fact,
             json.dumps(authorizing_user_metadata or {}, sort_keys=True)),
        )
        self._connection.commit()
        return MemoryResolution(proposal.proposal_id, classification, final_fact)

    def purge_expired(self, now: datetime | None = None) -> int:
        cutoff = (now or utc_now()).isoformat()
        cursor = self._connection.execute("DELETE FROM agent_memory WHERE expires_at <= ?", (cutoff,))
        self._connection.commit()
        return cursor.rowcount

    def search(self, query: str) -> list[str]:
        self.purge_expired()
        terms = [term for term in re.findall(r"[a-z0-9_]+", query.lower()) if len(term) > 2]
        if not terms:
            return []
        rows = self._connection.execute(
            "SELECT fact FROM agent_memory WHERE expires_at > ? ORDER BY created_at DESC",
            (utc_now().isoformat(),),
        ).fetchall()
        return [row["fact"] for row in rows if any(term in row["fact"].lower() for term in terms)]

    def audit_entries(self) -> list[dict[str, Any]]:
        rows = self._connection.execute("SELECT * FROM memory_audit ORDER BY timestamp").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _proposal_from_row(row: sqlite3.Row) -> MemoryProposal:
        return MemoryProposal(
            proposal_id=row["proposal_id"],
            fact_to_remember=row["fact_to_remember"],
            justification=row["justification"],
            originating_message_hash=row["originating_message_hash"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )


def classify_intent(response: str) -> tuple[str, str | None]:
    """Classify complete response forms; ambiguous text is never approval."""
    normalized = " ".join(response.split()).strip()
    if re.fullmatch(r"(?:yes|approve|approved|confirm|remember this)", normalized, re.I):
        return APPROVE, None
    if re.fullmatch(r"(?:no|reject|拒否|do not remember|forget it)", normalized, re.I):
        return REJECT, None
    edit = re.fullmatch(r"edit\s*:\s*(.{3,})", normalized, re.I)
    if edit:
        return EDIT, edit.group(1).strip()
    return DISCARD_BY_DEFAULT, None