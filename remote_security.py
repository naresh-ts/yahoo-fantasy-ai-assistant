"""Fail-closed deployment checks before any remote MCP exposure.

This module does not enable remote serving. It documents and enforces the
security prerequisites for a future authenticated launcher.
"""

import os
from pathlib import Path


def validate_remote_config(environ: dict[str, str] | None = None) -> None:
    """Reject unsafe remote hosting settings before binding a public port."""
    env = os.environ if environ is None else environ
    if env.get("MCP_REMOTE_ENABLED") != "true":
        raise ValueError("Remote MCP is disabled by default")

    if env.get("MCP_AUTH_MODE") != "oauth":
        raise ValueError("Remote MCP requires OAuth authentication")

    issuer = env.get("MCP_OAUTH_ISSUER", "")
    audience = env.get("MCP_OAUTH_AUDIENCE", "")
    if not issuer.startswith("https://") or not audience:
        raise ValueError("Remote MCP requires an HTTPS OAuth issuer and audience")

    if env.get("MCP_PUBLIC_URL", "").startswith("https://") is False:
        raise ValueError("Remote MCP requires an HTTPS public URL")

    directory = env.get("YAHOO_TOKEN_DIR")
    if not directory or not Path(directory).is_absolute():
        raise ValueError("Remote MCP requires an absolute persistent token directory")

    if env.get("MCP_SINGLE_WORKER") != "true":
        raise ValueError("Remote MCP must run as a single worker until token locking exists")
