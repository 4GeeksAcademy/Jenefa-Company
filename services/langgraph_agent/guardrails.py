"""Programmatic security, retrieval, and output boundaries for the agent."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable

from .graph import HONEST_REFUSAL, AgentState, generate_answer, invoke_agent, retrieve

logger = logging.getLogger(__name__)

SECURITY = "SECURITY"
CONTENT = "CONTENT"
STRUCTURAL = "STRUCTURAL"

_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+of\s+)?your\s+previous\s+instructions", re.I),
    re.compile(r"you\s+are\s+now\s+an\s+assistant\s+with\s+no\s+rules", re.I),
    re.compile(r"forget\s+that\s+you\s+work\s+for\s+the\s+company", re.I),
    re.compile(r"(?:system|developer)\s+override|jailbreak|bypass\s+(?:your\s+)?rules", re.I),
)
_PERSONAL_PATTERNS = (
    re.compile(r"\b(?:love|romantic)\s+poem\b", re.I),
    re.compile(r"\b(?:university|college)\s+homework\b", re.I),
    re.compile(r"\b(?:write|compose)\s+(?:an?\s+)?(?:essay|poem)\b", re.I),
    re.compile(r"\b(?:act|be)\s+as\s+(?:my\s+)?therapist\b", re.I),
    re.compile(r"\bsource\s+code\b", re.I),
)
_CASUAL_PATTERNS = (
    re.compile(r"\bwhat\s+time\s+is\s+it\b", re.I),
    re.compile(r"\b(?:weather|trivia|capital|population)\b", re.I),
)
_LEAK_PATTERNS = (
    re.compile(r"(?:system|developer)\s+prompt", re.I),
    re.compile(r"administrative\s+keys?|internal\s+instructions?", re.I),
    re.compile(r"\b(?:patient_id|ssn|social\s+security\s+number)\b", re.I),
    re.compile(r"ignore\s+(?:all\s+of\s+)?your\s+previous\s+instructions", re.I),
)

_counts: Counter[str] = Counter()
_counts_lock = Lock()


def _record(category: str, text: str, reason: str) -> None:
    snippet = " ".join(text.split())[:240]
    with _counts_lock:
        _counts[category] += 1
    logger.warning(
        "guardrail_trigger category=%s reason=%s input_snippet=%r",
        category,
        reason,
        snippet,
    )


def guardrail_summary() -> dict[str, Any]:
    with _counts_lock:
        counts = dict(_counts)
    return {
        "total": sum(counts.values()),
        "categories": {
            SECURITY: counts.get(SECURITY, 0),
            CONTENT: counts.get(CONTENT, 0),
            STRUCTURAL: counts.get(STRUCTURAL, 0),
        },
    }


def _guardrail_state(question: str, answer: str, error: str | None = None) -> AgentState:
    return {
        "question": question,
        "retrieved_context": [],
        "answer": answer,
        "error": error,
        "route": "guardrail",
        "live_context": [],
        "contacted_sources": [],
        "memory_context": [],
        "memory_proposal": None,
    }


def _casual_answer(question: str) -> str:
    if re.search(r"what\s+time\s+is\s+it\s+in\s+tokyo", question, re.I):
        now = datetime.now(timezone.utc)
        tokyo_hour = (now.hour + 9) % 24
        return f"Tokyo uses Japan Standard Time (UTC+9); it is currently {tokyo_hour:02d}:00 there. For HealthCore help, ask about our clinics, operations, or compliance."
    return "I can answer brief general questions. For HealthCore help, ask about our clinics, operations, or compliance."


def isolate_untrusted_text(value: Any, *, source: str) -> str:
    """Serialize dynamic data as data, with explicit boundaries for the generator."""
    text = str(value).replace("\x00", "")
    return f"[UNTRUSTED_{source.upper()}_DATA]\n{text}\n[/UNTRUSTED_{source.upper()}_DATA]"


def validate_output(answer: Any) -> str:
    if not isinstance(answer, str) or not answer.strip():
        _record(STRUCTURAL, str(answer), "missing_or_non_text_answer")
        return HONEST_REFUSAL
    if any(pattern.search(answer) for pattern in _LEAK_PATTERNS):
        _record(CONTENT, answer, "restricted_content_or_instruction_leak")
        return HONEST_REFUSAL
    return answer


def guarded_invoke_agent(
    question: str,
    *,
    config: dict[str, Any] | None = None,
    retriever: Callable[..., list[dict[str, Any]]] | None = None,
    generator: Callable[[str, list[dict[str, Any]]], str] | None = None,
) -> AgentState:
    """Apply input, retrieval, and output controls around the existing graph."""
    normalized = (question or "").strip()
    if not normalized:
        _record(STRUCTURAL, normalized, "question_required")
        return _guardrail_state(normalized, HONEST_REFUSAL, "question is required")
    if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
        _record(SECURITY, normalized, "prompt_injection")
        return _guardrail_state(normalized, "I can't change my HealthCore instructions or security boundaries.")
    if any(pattern.search(normalized) for pattern in _PERSONAL_PATTERNS):
        _record(SECURITY, normalized, "personal_task_out_of_scope")
        return _guardrail_state(normalized, "I can only help with HealthCore business operations, clinical workflows, billing, and compliance.")
    if any(pattern.search(normalized) for pattern in _CASUAL_PATTERNS):
        _record(CONTENT, normalized, "casual_redirect")
        return _guardrail_state(normalized, _casual_answer(normalized))

    base_retriever = retriever or retrieve

    def isolated_retriever(request: str) -> list[dict[str, Any]]:
        chunks = base_retriever(request)
        isolated: list[dict[str, Any]] = []
        for chunk in chunks:
            if not isinstance(chunk, dict) or "text" not in chunk:
                _record(STRUCTURAL, str(chunk), "malformed_retrieval_payload")
                continue
            isolated.append({"text": isolate_untrusted_text(chunk["text"], source="retrieved")})
        return isolated

    state = invoke_agent(
        normalized,
        config=config,
        retriever=isolated_retriever,
        generator=generator or generate_answer,
    )
    state["answer"] = validate_output(state.get("answer"))
    return state