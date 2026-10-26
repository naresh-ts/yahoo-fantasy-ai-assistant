"""Manage Yahoo OAuth tokens across MCP requests."""

import asyncio
import time

from config import Settings
from token_store import load_refresh_token, save_refresh_token
from yahoo_client import refresh_oauth_tokens


class YahooTokenManager:
    """Cache access tokens and preserve refreshed credentials."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token = None
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Return a valid cached or newly refreshed access token."""

        async with self._lock:
            if self._access_token and time.monotonic() < self._expires_at:
                return self._access_token

            refresh_token = load_refresh_token()

            if not refresh_token:
                if not self.settings.yahoo_refresh_token:
                    raise RuntimeError("Yahoo refresh token is missing")
                refresh_token = (
                    self.settings.yahoo_refresh_token.get_secret_value()
                )

            result = await refresh_oauth_tokens(
                self.settings, refresh_token
            )

            access_token = result["access_token"]
            replacement = result["refresh_token"]

            # Persist replacement credentials before caching access.
            if replacement != refresh_token:
                save_refresh_token(replacement)

            expires_in = max(0, int(result["expires_in"]))
            self._access_token = access_token
            self._expires_at = (
                time.monotonic() + max(0, expires_in - 120)
            )

            return access_token
