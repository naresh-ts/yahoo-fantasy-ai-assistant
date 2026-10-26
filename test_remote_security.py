"""Regression tests for secure remote-hosting prerequisites."""

import pytest

from remote_security import validate_remote_config


def valid_environment():
    return {
        "MCP_REMOTE_ENABLED": "true",
        "MCP_AUTH_MODE": "oauth",
        "MCP_OAUTH_ISSUER": "https://login.example.com/",
        "MCP_OAUTH_AUDIENCE": "yahoo-fantasy-mcp",
        "MCP_PUBLIC_URL": "https://fantasy.example.com/mcp",
        "YAHOO_TOKEN_DIR": "/var/lib/yahoo-fantasy",
        "MCP_SINGLE_WORKER": "true",
    }


def test_valid_remote_configuration():
    validate_remote_config(valid_environment())


@pytest.mark.parametrize(
    "key,value",
    [
        ("MCP_REMOTE_ENABLED", "false"),
        ("MCP_AUTH_MODE", "none"),
        ("MCP_OAUTH_ISSUER", "http://insecure.example.com"),
        ("MCP_OAUTH_AUDIENCE", ""),
        ("MCP_PUBLIC_URL", "http://fantasy.example.com/mcp"),
        ("YAHOO_TOKEN_DIR", "relative/path"),
        ("MCP_SINGLE_WORKER", "false"),
    ],
)
def test_remote_configuration_fails_closed(key, value):
    env = valid_environment()
    env[key] = value
    with pytest.raises(ValueError):
        validate_remote_config(env)


def test_empty_environment_fails_closed():
    with pytest.raises(ValueError):
        validate_remote_config({})
