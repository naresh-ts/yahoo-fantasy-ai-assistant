"""Small asynchronous client for Yahoo Fantasy's read-only API."""

from typing import Any, Self

import httpx

from config import Settings


class YahooFantasyClient:
    """Call Yahoo Fantasy endpoints using an OAuth access token.

    OAuth authorization and refresh-token storage will be added after Yahoo
    provisions the application's API credentials.
    """

    def __init__(self, settings: Settings, access_token: str) -> None:
        if not access_token:
            raise ValueError("A Yahoo OAuth access token is required")

        self._base_url = settings.yahoo_api_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=httpx.Timeout(20.0),
        )

    async def get(self, resource_path: str, **params: str | int) -> dict[str, Any]:
        """Retrieve one Yahoo Fantasy resource as JSON."""

        normalized_path = resource_path.lstrip("/")
        query = {"format": "json", **params}
        response = await self._client.get(f"{self._base_url}/{normalized_path}", params=query)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
