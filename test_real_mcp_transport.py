"""Integration smoke test using the installed MCP SDK, not a mock."""

from mcp.server import MCPServer

from oauth_asgi_gate import OAuthASGIGate
from remote_transport import build_remote_mcp_app


def test_real_mcp_sdk_transport_construction():
    settings = {
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
    mcp = MCPServer("Integration Smoke Test")
    app = build_remote_mcp_app(mcp, settings)
    assert isinstance(app, OAuthASGIGate)
    assert callable(app.app)
