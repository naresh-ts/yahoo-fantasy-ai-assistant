"""Test OAuth discovery is public but MCP requests remain authenticated."""

import asyncio

import httpx
from mcp.server import MCPServer

from remote_transport import build_remote_mcp_app


def test_discovery_public_and_mcp_private():
    asyncio.run(_check())


async def _check():
    env = {
        "MCP_REMOTE_ENABLED": "true",
        "MCP_AUTH_MODE": "oauth",
        "MCP_OAUTH_ISSUER": "https://login.example.com/",
        "MCP_OAUTH_AUDIENCE": "fantasy-mcp",
        "MCP_OAUTH_JWKS_URL": "https://login.example.com/keys",
        "MCP_PUBLIC_URL": "https://fantasy.example.com/mcp",
        "YAHOO_TOKEN_DIR": "/var/lib/yahoo-fantasy",
        "MCP_SINGLE_WORKER": "true",
        "MCP_ALLOWED_SUBJECT": "authorized-user",
    }
    app = build_remote_mcp_app(MCPServer("discovery test"), env)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="https://fantasy.example.com",
    ) as client:
        metadata = await client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code == 200
        assert metadata.json() == {
            "resource": "https://fantasy.example.com/mcp",
            "authorization_servers": ["https://login.example.com"],
            "bearer_methods_supported": ["header"],
        }
        assert metadata.headers["cache-control"] == "no-store"
        assert (await client.get("/mcp")).status_code == 401
        assert (await client.get("/.well-known/oauth-protected-resource")).status_code == 401
        assert (await client.post("/.well-known/oauth-protected-resource/mcp")).status_code == 401
