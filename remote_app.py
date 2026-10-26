"""Compose a protected remote MCP ASGI application.

This module does not expose a listener. A separate, reviewed launcher must
obtain the MCP transport ASGI app and pass it to build_protected_app.
"""

import os
from collections.abc import Callable
from typing import Any

from oauth_asgi_gate import OAuthASGIGate
from oauth_verifier import OAuthVerifier
from remote_security import validate_remote_config


def build_protected_app(
    mcp_asgi_app: Callable[..., Any],
    environ: dict[str, str] | None = None,
) -> OAuthASGIGate:
    """Fail closed if OAuth or durable-token prerequisites are missing."""
    env = dict(os.environ if environ is None else environ)
    validate_remote_config(env)
    subject = env.get("MCP_ALLOWED_SUBJECT", "")
    jwks_url = env.get("MCP_OAUTH_JWKS_URL", "")
    if not subject:
        raise ValueError("Remote MCP requires an explicit allowed OAuth subject")
    verifier = OAuthVerifier(
        issuer=env["MCP_OAUTH_ISSUER"],
        audience=env["MCP_OAUTH_AUDIENCE"],
        jwks_url=jwks_url,
    )
    return OAuthASGIGate(mcp_asgi_app, verifier, subject)
