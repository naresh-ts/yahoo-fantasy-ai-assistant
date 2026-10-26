"""Fail closed when attempting an unsafe remote MCP deployment.

This is a deployment guard, not an authentication implementation.
"""

import os


def validate_deployment_environment() -> None:
    """Reject remote binding until the authenticated hosting layer exists."""
    host = os.getenv("MCP_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError(
            "Remote MCP hosting is not configured. Do not bind to a public "
            "interface without HTTPS, authenticated client access, and "
            "persistent secure Yahoo refresh-token storage."
        )


if __name__ == "__main__":
    validate_deployment_environment()
    print("Local-only MCP configuration verified.")
