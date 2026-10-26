"""RFC 9728 protected-resource discovery for MCP OAuth clients.

Only the exact metadata endpoint is public; all other requests are passed
through the existing OAuth gate.
"""

import json
from urllib.parse import urlparse


class OAuthResourceDiscovery:
    def __init__(self, protected_app, resource_url: str, issuer: str):
        resource = urlparse(resource_url)
        authorization_server = urlparse(issuer)
        if (
            resource.scheme != "https"
            or not resource.hostname
            or resource.username
            or resource.password
            or resource.path != "/mcp"
            or resource.query
            or resource.fragment
        ):
            raise ValueError("Resource must be a public HTTPS /mcp URL")
        if (
            authorization_server.scheme != "https"
            or not authorization_server.hostname
            or authorization_server.username
            or authorization_server.password
            or authorization_server.query
            or authorization_server.fragment
        ):
            raise ValueError("Authorization server must use HTTPS")
        self.app = protected_app
        self.resource_url = resource_url
        self.issuer = issuer.rstrip("/")
        self.metadata_path = "/.well-known/oauth-protected-resource/mcp"

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] == "http"
            and scope.get("path") == self.metadata_path
            and scope.get("method") in ("GET", "HEAD")
        ):
            body = json.dumps(
                {
                    "resource": self.resource_url,
                    "authorization_servers": [self.issuer],
                    "bearer_methods_supported": ["header"],
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"cache-control", b"no-store"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": body if scope["method"] == "GET" else b"",
                }
            )
            return
        await self.app(scope, receive, send)
