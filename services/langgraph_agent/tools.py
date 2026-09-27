"""Read-only clients for live HealthCore operational services."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 4.0


def mcp_connections() -> dict[str, dict[str, str]]:
    """Return the authenticated MCP connection used by LangChain adapters."""
    url = os.getenv("HEALTHCORE_MCP_URL")
    if not url:
        raise ExternalToolError("mcp", "HEALTHCORE_MCP_URL is not configured")
    token = os.getenv("HEALTHCORE_SERVICE_TOKEN") or os.getenv("HEALTHCORE_API_KEY")
    if not token:
        raise ExternalToolError("mcp", "HEALTHCORE_SERVICE_TOKEN is not configured")
    return {
        "healthcore": {
            "transport": "http",
            "url": url.rstrip("/"),
            "headers": {"Authorization": f"Bearer {token}"},
        }
    }


async def get_mcp_tools() -> list[Any]:
    """Discover protected tools through langchain-mcp-adapters."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(mcp_connections())
    return await client.get_tools(server_name="healthcore")


class IncidentLookup(BaseModel):
    """Optional incident identifier and filters sent to the incident service."""

    ticket_id: str | None = Field(default=None, min_length=1)
    status: str | None = None
    category: str | None = None


class InventoryLookup(BaseModel):
    """Optional product filters sent to the inventory service."""

    product_id: str | None = None
    sku: str | None = None
    name: str | None = None


class ExternalToolError(RuntimeError):
    """A safe, non-domain error raised when a live lookup cannot be confirmed."""

    def __init__(self, tool: str, reason: str) -> None:
        super().__init__(reason)
        self.tool = tool
        self.reason = reason


def _client() -> httpx.Client:
    token = os.getenv("HEALTHCORE_SERVICE_TOKEN") or os.getenv("HEALTHCORE_API_KEY")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS, headers=headers)


def _base_url(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ExternalToolError(name, f"{name} is not configured")
    return value.rstrip("/")


def _get_json(tool: str, url: str, params: dict[str, str]) -> Any:
    # Log only the tool and endpoint: query values may contain operational or PHI.
    logger.info("healthcore_external_lookup tool=%s endpoint=%s", tool, url)
    try:
        with _client() as client:
            response = client.get(url, params=params)
            if response.status_code == 404:
                raise ExternalToolError(tool, "resource not found")
            response.raise_for_status()
            return response.json()
    except ExternalToolError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("healthcore_external_lookup_failed tool=%s error=%s", tool, type(exc).__name__)
        raise ExternalToolError(tool, "live service request failed") from exc


def lookup_incident(payload: IncidentLookup) -> Any:
    """Read incident data only; never creates, updates, or deletes tickets."""
    base = _base_url("HEALTHCORE_INCIDENTS_BASE_URL")
    if payload.ticket_id:
        url = f"{base}/api/incidents/{payload.ticket_id}"
        params: dict[str, str] = {}
    else:
        url = f"{base}/api/incidents"
        params = payload.model_dump(exclude_none=True)
    return _get_json("incident", url, params)


def lookup_inventory(payload: InventoryLookup) -> Any:
    """Read cross-border stock data only; never mutates inventory."""
    base = _base_url("HEALTHCORE_INVENTORY_BASE_URL")
    return _get_json(
        "inventory",
        f"{base}/inventory/products",
        payload.model_dump(exclude_none=True),
    )


def format_tool_context(tool: str, result: Any) -> str:
    """Keep live payloads available to the answer generator without inventing fields."""
    return f"Live {tool} service response (verified at request time): {result!r}"
