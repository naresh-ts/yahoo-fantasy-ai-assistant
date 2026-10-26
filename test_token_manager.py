"""Tests for Yahoo OAuth token management."""

import asyncio
from unittest.mock import AsyncMock, patch

from config import Settings
from token_manager import YahooTokenManager


def test_access_token_is_cached():
    """Repeated requests should reuse a valid access token."""

    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token="test-refresh-token",
    )

    manager = YahooTokenManager(settings)

    response = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
    }

    async def run_test():
        with (
            patch(
                "token_manager.load_refresh_token",
                return_value=None,
            ),
            patch(
                "token_manager.refresh_oauth_tokens",
                new_callable=AsyncMock,
                return_value=response,
            ) as refresh,
        ):
            first = await manager.get_access_token()
            second = await manager.get_access_token()

            assert first == "test-access-token"
            assert second == "test-access-token"
            assert refresh.await_count == 1

    asyncio.run(run_test())


def test_replacement_refresh_token_is_saved():
    """Save a replacement refresh token after successful renewal."""

    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token="original-refresh-token",
    )

    manager = YahooTokenManager(settings)

    response = {
        "access_token": "new-access-token",
        "refresh_token": "replacement-refresh-token",
        "expires_in": 3600,
    }

    async def run_test():
        with (
            patch(
                "token_manager.load_refresh_token",
                return_value=None,
            ),
            patch(
                "token_manager.save_refresh_token",
            ) as save,
            patch(
                "token_manager.refresh_oauth_tokens",
                new_callable=AsyncMock,
                return_value=response,
            ),
        ):
            result = await manager.get_access_token()

            assert result == "new-access-token"
            save.assert_called_once_with("replacement-refresh-token")

    asyncio.run(run_test())


def test_expired_access_token_is_refreshed():
    """An expired cached token must trigger another renewal."""

    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token="test-refresh-token",
    )

    manager = YahooTokenManager(settings)

    responses = [
        {
            "access_token": "first-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
        },
        {
            "access_token": "second-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
        },
    ]

    async def run_test():
        with (
            patch("token_manager.load_refresh_token", return_value=None),
            patch(
                "token_manager.refresh_oauth_tokens",
                new_callable=AsyncMock,
                side_effect=responses,
            ) as refresh,
        ):
            first = await manager.get_access_token()

            # Simulate expiration without waiting.
            manager._expires_at = 0

            second = await manager.get_access_token()

            assert first == "first-access-token"
            assert second == "second-access-token"
            assert refresh.await_count == 2

    asyncio.run(run_test())


def test_concurrent_requests_share_token_refresh():
    """Simultaneous requests should trigger only one token refresh."""

    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-client",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token="test-refresh-token",
    )

    manager = YahooTokenManager(settings)

    response = {
        "access_token": "shared-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
    }

    async def run_test():
        with (
            patch("token_manager.load_refresh_token", return_value=None),
            patch(
                "token_manager.refresh_oauth_tokens",
                new_callable=AsyncMock,
                return_value=response,
            ) as refresh,
        ):
            results = await asyncio.gather(
                manager.get_access_token(),
                manager.get_access_token(),
                manager.get_access_token(),
            )

            assert results == ["shared-access-token"] * 3
            assert refresh.await_count == 1

    asyncio.run(run_test())
