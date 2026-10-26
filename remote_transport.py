"""Build a protected MCP Streamable HTTP ASGI app without starting a listener."""

from urllib.parse import urlparse

from mcp.server.transport_security import TransportSecuritySettings

from remote_app import build_protected_app
from remote_security import validate_remote_config


def build_remote_mcp_app(mcp_server, environ=None):
    """Wrap the real MCP transport with OAuth and strict Host/Origin checks.

    No public listener is created here. A separate reviewed deployment
    launcher and OAuth discovery are still required.
    """
    import os

    env = dict(os.environ if environ is None else environ)
    validate_remote_config(env)
    public_url = urlparse(env["MCP_PUBLIC_URL"])
    if not public_url.hostname or public_url.username or public_url.password:
        raise ValueError("Invalid public MCP URL")
    if public_url.path != "/mcp" or public_url.query or public_url.fragment:
        raise ValueError("Public MCP URL must end in /mcp without query or fragment")

    host = public_url.hostname
    allowed_origins = [
        origin.strip()
        for origin in env.get("MCP_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if any(
        urlparse(origin).scheme != "https"
        or not urlparse(origin).hostname
        or urlparse(origin).path not in ("", "/")
        or urlparse(origin).query
        or urlparse(origin).fragment
        for origin in allowed_origins
    ):
        raise ValueError("Allowed origins must be HTTPS origins only")

    transport = mcp_server.streamable_http_app(
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[host, f"{host}:*"],
            allowed_origins=allowed_origins,
        ),
    )
    return build_protected_app(transport, env)
