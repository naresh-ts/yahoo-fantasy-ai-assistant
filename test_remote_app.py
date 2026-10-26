"""Test remote app composition requires all OAuth security settings."""

import pytest

from oauth_asgi_gate import OAuthASGIGate
from remote_app import build_protected_app


def valid_env():
    return {
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


def test_protected_app_factory():
    app = object()
    gate = build_protected_app(app, valid_env())
    assert isinstance(gate, OAuthASGIGate)
    assert gate.app is app
    assert gate.allowed_subject == "authorized-user"


@pytest.mark.parametrize(
    "key,value",
    [
        ("MCP_REMOTE_ENABLED", "false"),
        ("MCP_AUTH_MODE", "none"),
        ("MCP_OAUTH_ISSUER", "http://login.example.com"),
        ("MCP_OAUTH_JWKS_URL", "http://login.example.com/keys"),
        ("MCP_OAUTH_AUDIENCE", ""),
        ("MCP_ALLOWED_SUBJECT", ""),
        ("MCP_PUBLIC_URL", "http://fantasy.example.com/mcp"),
        ("YAHOO_TOKEN_DIR", ""),
        ("MCP_SINGLE_WORKER", "false"),
    ],
)
def test_factory_rejects_unsafe_config(key, value):
    env = valid_env()
    env[key] = value
    with pytest.raises(ValueError):
        build_protected_app(object(), env)
