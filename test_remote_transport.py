"""Tests for real MCP transport composition and host restrictions."""

import pytest

from oauth_asgi_gate import OAuthASGIGate
from remote_transport import build_remote_mcp_app


def env():
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


class FakeMCP:
    def __init__(self):
        self.kwargs = None
        self.app = object()

    def streamable_http_app(self, **kwargs):
        self.kwargs = kwargs
        return self.app


def test_real_transport_is_wrapped_with_oauth():
    mcp = FakeMCP()
    app = build_remote_mcp_app(mcp, env())
    assert isinstance(app, OAuthASGIGate)
    assert app.app is mcp.app
    assert mcp.kwargs["streamable_http_path"] == "/mcp"
    security = mcp.kwargs["transport_security"]
    assert security.enable_dns_rebinding_protection
    assert security.allowed_hosts == ["fantasy.example.com", "fantasy.example.com:*"]
    assert security.allowed_origins == ["https://chatgpt.com"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("MCP_PUBLIC_URL", "https://fantasy.example.com/not-mcp"),
        ("MCP_PUBLIC_URL", "https://fantasy.example.com/mcp?unsafe=1"),
        ("MCP_PUBLIC_URL", "https://user@fantasy.example.com/mcp"),
        ("MCP_ALLOWED_ORIGINS", "http://chatgpt.com"),
        ("MCP_ALLOWED_ORIGINS", "https://chatgpt.com/evil"),
        ("MCP_AUTH_MODE", "none"),
    ],
)
def test_invalid_remote_transport_configuration_fails(key, value):
    config = env()
    config[key] = value
    with pytest.raises(ValueError):
        build_remote_mcp_app(FakeMCP(), config)
