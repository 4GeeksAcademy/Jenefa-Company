"""OAuth-protected HealthCore MCP server.

The server exposes operational capabilities only through FastMCP's streamable
HTTP transport. OAuth verification is deliberately provided by ``mcpauth``;
FastMCP's auth providers are not used.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

import httpx
from fastmcp import FastMCP
from mcpauth import AuthInfo, MCPAuth
from mcpauth.config import AuthServerConfig, AuthServerType, AuthorizationServerMetadata
from pydantic import BaseModel, ConfigDict, Field
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

logger = logging.getLogger(__name__)

JURISDICTIONS = {"US", "UK"}
INCIDENT_SCOPES = ["incidents:read"]
INCIDENT_WRITE_SCOPES = ["incidents:write"]
INVENTORY_SCOPES = ["inventory:read"]


class MCPValidationError(ValueError):
    """A controlled 400 error for invalid or unsafe tool input."""


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    jurisdiction: Literal["US", "UK"]
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class IncidentQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str | None = Field(default=None, min_length=1)
    status: str | None = None
    jurisdiction: Literal["US", "UK"] | None = None


class IncidentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["open", "in_progress", "resolved", "closed"]
    jurisdiction: Literal["US", "UK"]


class InventoryQuery(BaseModel):
    """Read-only inventory filters; mutation-shaped fields are rejected."""
    model_config = ConfigDict(extra="allow")
    product_id: str | None = None
    sku: str | None = None
    name: str | None = None
    jurisdiction: Literal["US", "UK"] | None = None


class IncidentClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("HEALTHCORE_INCIDENTS_BASE_URL", "http://localhost:8000").rstrip("/")
        self.timeout = httpx.Timeout(float(os.getenv("MCP_UPSTREAM_TIMEOUT", "4")))

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, f"{self.base_url}{path}", **kwargs)
            response.raise_for_status()
            return response.json()


class InventoryClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("HEALTHCORE_INVENTORY_BASE_URL", "http://localhost:8000").rstrip("/")
        self.timeout = httpx.Timeout(float(os.getenv("MCP_UPSTREAM_TIMEOUT", "4")))

    def request(self, params: dict[str, Any]) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/inventory/products", params=params)
            response.raise_for_status()
            return response.json()


def _auth() -> AuthInfo:
    info = auth.auth_info
    if info is None:
        raise PermissionError("Unauthenticated")
    return info


def _require(scopes: list[str], jurisdiction: str | None = None) -> AuthInfo:
    info = _auth()
    granted = set(info.scopes)
    if not set(scopes).issubset(granted):
        raise PermissionError(f"Insufficient scope; required: {' '.join(scopes)}")
    token_jurisdiction = info.claims.get("jurisdiction")
    if jurisdiction and token_jurisdiction != jurisdiction:
        raise MCPValidationError("Token jurisdiction does not match requested jurisdiction")
    return info


def _safe_require(scopes: list[str], jurisdiction: str | None, tool_name: str) -> AuthInfo:
    """Audit auth failures while preserving mcpauth's explicit HTTP errors."""
    try:
        return _require(scopes, jurisdiction)
    except PermissionError:
        _audit_failure(tool_name, "Access Denied")
        raise
    except MCPValidationError:
        info = auth.auth_info
        if info:
            _audit(info, tool_name, "Parameter Validation Error")
        else:
            _audit_failure(tool_name, "Parameter Validation Error")
        raise


def _audit_failure(tool_name: str, result: str) -> None:
    """Record failures where no authenticated identity is available."""
    logger.info(json.dumps({"client_id": None, "tool_name": tool_name, "execution_result": result}, sort_keys=True))


def _audit(info: AuthInfo, tool_name: str, result: str) -> None:
    logger.info(json.dumps({"client_id": info.client_id or info.subject, "tool_name": tool_name, "execution_result": result}, sort_keys=True))


mcp = FastMCP("HealthCore Digital MCP", instructions="OAuth-protected incident and inventory operations")


@mcp.tool
async def list_incidents(query: IncidentQuery) -> Any:
    """Read incident tickets, filtered by ticket ID, status, and jurisdiction."""
    info = _safe_require(INCIDENT_SCOPES, query.jurisdiction, "list_incidents")
    try:
        params = query.model_dump(exclude_none=True)
        result = IncidentClient().request("GET", "/api/incidents", params=params)
        _audit(info, "list_incidents", "Success")
        return result
    except MCPValidationError:
        _audit(info, "list_incidents", "Parameter Validation Error")
        raise
    except Exception:
        _audit(info, "list_incidents", "Access Denied")
        raise


@mcp.tool
async def create_incident(incident: Incident) -> Any:
    """Create a ticket in the caller's jurisdiction."""
    info = _safe_require(INCIDENT_WRITE_SCOPES, incident.jurisdiction, "create_incident")
    try:
        result = IncidentClient().request("POST", "/api/incidents", json=incident.model_dump())
        _audit(info, "create_incident", "Success")
        return result
    except Exception:
        _audit(info, "create_incident", "Access Denied")
        raise


@mcp.tool
async def update_incident_status(ticket_id: str, update: IncidentStatusUpdate) -> Any:
    """Transition an incident using only PATCH /api/incidents/{id}/status."""
    if not ticket_id.strip():
        raise MCPValidationError("ticket_id is required")
    info = _safe_require(INCIDENT_WRITE_SCOPES, update.jurisdiction, "update_incident_status")
    try:
        result = IncidentClient().request("PATCH", f"/api/incidents/{ticket_id}/status", json=update.model_dump())
        _audit(info, "update_incident_status", "Success")
        return result
    except Exception:
        _audit(info, "update_incident_status", "Access Denied")
        raise


@mcp.tool
async def query_inventory(query: InventoryQuery) -> Any:
    """Read clinical inventory; all mutation-shaped fields are rejected."""
    mutation_fields = {"quantity", "current_stock", "operation", "method", "action", "write", "delete"}
    attempted = mutation_fields.intersection(query.model_extra or {})
    if attempted:
        info = auth.auth_info
        if info:
            _audit(info, "query_inventory", "Parameter Validation Error")
        else:
            _audit_failure("query_inventory", "Parameter Validation Error")
        raise MCPValidationError("Inventory is read-only; write operations are not permitted")
    info = _safe_require(INVENTORY_SCOPES, query.jurisdiction, "query_inventory")
    try:
        result = InventoryClient().request(query.model_dump(exclude_none=True))
        _audit(info, "query_inventory", "Success")
        return result
    except Exception:
        _audit(info, "query_inventory", "Access Denied")
        raise


def _build_auth() -> MCPAuth:
    issuer = os.environ["MCP_OAUTH_ISSUER"]
    metadata = AuthorizationServerMetadata(
        issuer=issuer,
        authorization_endpoint=os.environ.get("MCP_OAUTH_AUTHORIZATION_ENDPOINT", f"{issuer}/authorize"),
        token_endpoint=os.environ.get("MCP_OAUTH_TOKEN_ENDPOINT", f"{issuer}/token"),
        jwks_uri=os.environ.get("MCP_OAUTH_JWKS_URI"),
        response_types_supported=["code"],
        grant_types_supported=["authorization_code", "client_credentials"],
        code_challenge_methods_supported=["S256"],
        scope_supported=INCIDENT_SCOPES + INCIDENT_WRITE_SCOPES + INVENTORY_SCOPES,
    )
    return MCPAuth(AuthServerConfig(metadata=metadata, type=AuthServerType.OAUTH))


# Constructed at import time so FastAPI/uvicorn can mount this module predictably.
auth = _build_auth()


def create_app() -> Any:
    """Return a Starlette app with public OAuth metadata and protected MCP."""
    auth_middleware = [
        Middleware(
            auth.bearer_auth_middleware(
                "jwt",
                audience=os.getenv("MCP_OAUTH_AUDIENCE"),
                show_error_details=False,
            )
        )
    ]
    return Starlette(
        routes=[
            auth.metadata_route(),
            Mount(
                "/mcp",
                app=mcp.http_app(transport="streamable-http", stateless_http=True),
                middleware=auth_middleware,
            ),
        ]
    )


app = create_app()
