"""Non-PHI baseline AI systems from the SecureAI product context."""

from sqlmodel import Session, select
from sqlalchemy.engine import Engine

from .models import AISystem


BASELINE_SYSTEMS = (
    {
        "system_key": "classification-agent",
        "name": "Classification Agent",
        "architecture_type": "autonomous-core / inbound-intent-router",
        "data_traversal_surface": "user messages, email, phone transcripts, webhooks",
        "provider": "OpenAI API / Anthropic Claude",
        "owner": "Dr. Marcus Reid",
        "risk_tier": "high",
        "jurisdiction": "cross-border",
    },
    {
        "system_key": "response-agent",
        "name": "Response Agent",
        "architecture_type": "RAG-augmented documentation and messaging",
        "data_traversal_surface": "EHR contexts, billing rules, memory vectors",
        "provider": "Anthropic Claude API",
        "owner": "Priya Nair",
        "risk_tier": "critical",
        "jurisdiction": "cross-border",
    },
    {
        "system_key": "escalation-workflow-engine",
        "name": "Escalation Workflow Engine",
        "architecture_type": "state machine / approval loops",
        "data_traversal_surface": "appointment diaries, messaging gateways",
        "provider": "Twilio SMS API / regional telecoms",
        "owner": "Tom Callahan",
        "risk_tier": "high",
        "jurisdiction": "cross-border",
    },
    {
        "system_key": "semantic-memory-module",
        "name": "Semantic Memory Module",
        "architecture_type": "vector database storage and recall",
        "data_traversal_surface": "clinical notes, compliance guidelines",
        "provider": "Pinecone / Qdrant Cloud",
        "owner": "James Osei",
        "risk_tier": "high",
        "jurisdiction": "cross-border",
    },
    {
        "system_key": "mcp-tool-gateway",
        "name": "MCP Tool Gateway",
        "architecture_type": "Model Context Protocol infrastructure hub",
        "data_traversal_surface": "US/UK EHRs, billing databases, legacy spreadsheets",
        "provider": "internal APIs / legacy systems",
        "owner": "James Osei",
        "risk_tier": "critical",
        "jurisdiction": "cross-border",
    },
)


def seed_baseline_systems(engine: Engine) -> None:
    with Session(engine) as session:
        existing = {row.system_key for row in session.exec(select(AISystem))}
        for values in BASELINE_SYSTEMS:
            if values["system_key"] not in existing:
                session.add(AISystem(**values))
        session.commit()