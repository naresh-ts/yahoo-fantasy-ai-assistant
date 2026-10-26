"""Opt-in remote MCP launcher; refuses unsafe configuration before listening.

Requires a trusted HTTPS reverse proxy, persistent private Yahoo token
storage, and a compatible OAuth authorization server. Do not expose
this directly to the internet without TLS termination and rate limits.
"""

import os

import uvicorn

from remote_transport import build_remote_mcp_app
from server import mcp


def create_app(environ=None):
    """Build the fully protected MCP ASGI app, or fail before binding."""
    env = dict(os.environ if environ is None else environ)
    if env.get("MCP_TRUSTED_HTTPS_PROXY") != "true":
        raise ValueError("A trusted HTTPS reverse proxy is required")
    return build_remote_mcp_app(mcp, env)


def main():
    app = create_app()
    host = os.environ.get("MCP_BIND_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise SystemExit("Remote launcher binds only to loopback behind a trusted HTTPS proxy")
    port = int(os.environ.get("PORT", "8000"))
    if not 1 <= port <= 65535:
        raise SystemExit("Invalid PORT")
    uvicorn.run(app, host=host, port=port, workers=1, proxy_headers=False)


if __name__ == "__main__":
    main()
