"""Fail-closed ASGI bearer-token gate for future remote MCP hosting.

The gate protects *all* HTTP and WebSocket scopes. A future remote
launcher must wrap the MCP ASGI application with this middleware before
binding a public interface.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from jwt import PyJWTError

from oauth_verifier import OAuthVerifier


class OAuthASGIGate:
    def __init__(
        self,
        app: Callable[..., Awaitable[Any]],
        verifier: OAuthVerifier,
        allowed_subject: str,
        resource_metadata_url: str | None = None,
    ) -> None:
        if not allowed_subject:
            raise ValueError("An explicit allowed OAuth subject is required")
        self.app = app
        self.verifier = verifier
        self.allowed_subject = allowed_subject
        self.resource_metadata_url = resource_metadata_url

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return

        if scope["type"] != "http":
            raise ValueError("Unsupported ASGI scope type")

        headers = [
            value.decode("latin1")
            for key, value in scope.get("headers", [])
            if key.lower() == b"authorization"
        ]
        if len(headers) != 1:
            await self._reject(send, 401, self.resource_metadata_url)
            return

        scheme, separator, token = headers[0].partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip():
            await self._reject(send, 401)
            return

        if token != token.strip() or len(token) > 16384:
            await self._reject(send, 401)
            return

        try:
            claims = self.verifier.verify(token)
        except (PyJWTError, ValueError, OSError):
            await self._reject(send, 401)
            return

        if claims.get("sub") != self.allowed_subject:
            await self._reject(send, 403, self.resource_metadata_url)
            return

        await self.app(scope, receive, send)

    @staticmethod
    async def _reject(send: Callable, status: int, metadata_url: str | None = None) -> None:
        body = json.dumps({"error": "unauthorized" if status == 401 else "forbidden"}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"cache-control", b"no-store"),
        ]
        if status == 401 and metadata_url:
            headers.append(
                (b"www-authenticate", f'Bearer resource_metadata="{metadata_url}"'.encode("ascii"))
            )
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": body})
