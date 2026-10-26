"""Exercise the real MCP transport behind the OAuth gate via ASGI requests."""

import httpx
import pytest
from mcp.server import MCPServer

from remote_transport import build_remote_mcp_app


def settings():
    return {
        "MCP_REMOTE_ENABLED": "true",
        "MCP_AUTH_MODE": "oauth",
        "MCP_OAUTH_ISSUER": "https://login.example.com/",
        "MCP_OAUTH_AUDIENCE": "fantasy-mcp",
        "MCP_OAUTH_JWKS_URL": "https://login.example.com/keys",
        "MCP_PUBLIC_URL": "https://fantasy.example.com/mcp",
        "MCP_ALLOWED_ORIGINS": "https://chatgpt.com",
        "YAHOO_TOKEN_DIR": "/var/lib/yahoo-fantasy",
        "MCP_SINGLE_WORKER": "true",
        "MCP_ALLOWED_SUBJECT": "authorized-user",
    }


@pytest.mark.asyncio
async def test_real_transport_rejects_missing_or_invalid_authorization():
    app = build_remote_mcp_app(MCPServer("auth integration"), settings())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://fantasy.example.com"
    ) as client:
        for headers in (
            {},
            {"Authorization": "Basic abc"},
            {"Authorization": "Bearer not-a-jwt"},
        ):
            response = await client.post(
                "/mcp",
                headers=headers,
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            )
            assert response.status_code == 401
            assert response.headers["cache-control"] == "no-store"
