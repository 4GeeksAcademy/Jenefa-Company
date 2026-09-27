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
    """Discover protected tools through a resilient stateless HTTP tool wrapper."""
    from langchain_core.tools import Tool
    
    connections = mcp_connections()
    healthcore_config = connections.get("healthcore", {})
    url = healthcore_config.get("url")
    headers = healthcore_config.get("headers", {})

    if not url:
        raise ExternalToolError("mcp", "HEALTHCORE_MCP_URL is not configured")

    # Ensure trailing slash matching for the stateless Starlette mount route rules
    base_mcp_url = url if url.endswith("/") else f"{url}/"

    # 1. Fetch available tools list using a direct, stateless HTTP POST query
    async def fetch_tools_list() -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(
                    base_mcp_url,
                    headers=headers,
                    json={"jsonrpc": "2.0", "id": "list", "method": "tools/list", "params": {}}
                )
                if response.status_code == 401:
                    logger.warning("MCP client authorization rejected by server.")
                    return []
                response.raise_for_status()
                return response.json().get("result", {}).get("tools", [])
            except Exception as exc:
                logger.error(f"Stateless MCP discovery check failed: {exc}")
                return []

    mcp_tools_metadata = await fetch_tools_list()
    langchain_adapter_tools = []

    # 2. Build individual custom LangChain wrapper tools dynamically
    for tool_meta in mcp_tools_metadata:
        name = tool_meta.get("name")
        description = tool_meta.get("description", "")

        def make_call_fn(tool_name: str = name):
            async def call_mcp_tool(arguments: dict[str, Any]) -> str:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                    resp = await client.post(
                        base_mcp_url,
                        headers=headers,
                        json={
                            "jsonrpc": "2.0",
                            "id": f"call_{tool_name}",
                            "method": "tools/call",
                            "params": {"name": tool_name, "arguments": arguments}
                        }
                    )
                    resp.raise_for_status()
                    content = resp.json().get("result", {}).get("content", [{}])
                    if content and isinstance(content, list):
                        return str(content[0].get("text", ""))
                    return ""
            return call_mcp_tool

        # Construct standard LangChain wrapper objects
        langchain_adapter_tools.append(
            Tool(
                name=name,
                description=description,
                func=None,  # Handled as an async tool function hook
                coroutine=make_call_fn(name)
            )
        )

    return langchain_adapter_tools


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
