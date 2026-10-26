"""Tests for Yahoo OAuth token renewal."""

import asyncio

import httpx

from config import Settings
from yahoo_client import refresh_access_token, refresh_oauth_tokens


def test_refresh_returns_access_token() -> None:
    """Verify that refreshing returns a usable access token."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(
            200,
            json={
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
    )

    async def run_test() -> None:
        original_client = httpx.AsyncClient

        def mock_client(*args, **kwargs):
            kwargs["transport"] = transport
            return original_client(*args, **kwargs)

        from unittest.mock import patch

        with patch("yahoo_client.httpx.AsyncClient", side_effect=mock_client):
            result = await refresh_access_token(
                settings, "old-refresh-token"
            )

        assert result == "new-access-token"

    asyncio.run(run_test())


def test_refresh_preserves_replacement_token() -> None:
    """A replacement refresh token must not be discarded."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": "new-access-token",
                "refresh_token": "replacement-refresh-token",
                "expires_in": 3600,
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
    )

    async def run_test() -> None:
        from unittest.mock import patch

        original_client = httpx.AsyncClient

        def mock_client(*args, **kwargs):
            kwargs["transport"] = transport
            return original_client(*args, **kwargs)

        with patch("yahoo_client.httpx.AsyncClient", side_effect=mock_client):
            result = await refresh_oauth_tokens(
                settings, "old-refresh-token"
            )

        assert result["access_token"] == "new-access-token"
        assert result["refresh_token"] == "replacement-refresh-token"

    asyncio.run(run_test())
