"""Start the Yahoo Fantasy MCP server on a local-only HTTP listener.

Do not expose this endpoint publicly until authentication is configured.
"""

import os

from server import mcp


if __name__ == "__main__":
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit(
            "Refusing non-loopback binding: configure authenticated access first."
        )

    port = int(os.environ.get("PORT", "8000"))
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path="/mcp",
    )
