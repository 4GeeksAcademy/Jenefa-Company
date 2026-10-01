from datetime import datetime, timedelta, timezone

import pytest

from services.langgraph_agent.graph import invoke_agent
from services.langgraph_agent.memory import (
    APPROVE,
    DISCARD_BY_DEFAULT,
    EDIT,
    AgentMemoryStore,
)


def test_approved_memory_is_audited_and_available_to_new_session(tmp_path):
    store = AgentMemoryStore(tmp_path / "agent-memory.db")
    try:
        proposal = store.propose(
            "Use Texas commercial rule TX-17 for this payer",
            "The billing team explicitly confirmed this recurring exception.",
            "Apply TX-17 for this payer going forward.",
        )
        resolution = store.resolve("approve", authorizing_user_metadata={"role": "billing"})

        assert resolution.classification == APPROVE
        assert resolution.final_stored_state == proposal.fact_to_remember
        assert store.search("Texas payer") == [proposal.fact_to_remember]

        state = invoke_agent(
            "What Texas payer rule should I use?",
            memory_store=store,
            retriever=lambda question: [],
            generator=lambda question, context: context[0]["text"],
        )
        assert state["answer"] == proposal.fact_to_remember
        assert store.audit_entries()[0]["final_stored_state"] == proposal.fact_to_remember
    finally:
        store.close()


def test_ambiguous_resolution_discards_without_writing_memory(tmp_path):
    store = AgentMemoryStore(tmp_path / "agent-memory.db")
    try:
        store.propose("Prefer the London morning slot", "Repeated scheduling preference", "Use mornings")
        result = store.resolve("Can you also tell me the staffing hours?")
        assert result.classification == DISCARD_BY_DEFAULT
        assert result.final_stored_state is None
        assert store.search("London morning") == []
        assert store.audit_entries()[0]["user_classification"] == DISCARD_BY_DEFAULT
    finally:
        store.close()


def test_edit_resolution_and_single_pending_rule(tmp_path):
    store = AgentMemoryStore(tmp_path / "agent-memory.db")
    try:
        store.propose("Use the old wording", "Operator correction", "Correction")
        with pytest.raises(ValueError, match="already pending"):
            store.propose("Another fact", "Another reason", "Another message")
        result = store.resolve("edit: Use the approved wording")
        assert result.classification == EDIT
        assert store.search("approved wording") == ["Use the approved wording"]
    finally:
        store.close()


def test_expired_memory_is_purged(tmp_path):
    store = AgentMemoryStore(tmp_path / "agent-memory.db")
    try:
        proposal = store.propose("Temporary clinic workaround", "Quarterly exception", "Remember this")
        store.resolve("yes")
        expired_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        store._connection.execute(
            "UPDATE agent_memory SET expires_at = ?", (expired_at,)
        )
        store._connection.commit()
        assert store.search("clinic workaround") == []
    finally:
        store.close()