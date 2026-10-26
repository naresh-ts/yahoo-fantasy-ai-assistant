"""Tests for league scoring and matchup Yahoo API reads."""

import asyncio

import httpx
import pytest

from config import Settings
from yahoo_client import YahooFantasyClient


def test_league_settings_and_scoreboard_urls():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"fantasy_content": {"ok": True}})

    async def run():
        settings = Settings(_env_file=None)
        async with YahooFantasyClient(
            settings, "fake-token", transport=httpx.MockTransport(handler)
        ) as client:
            settings_data = await client.get_league_settings("461.l.560937")
            scoreboard_data = await client.get_league_scoreboard("461.l.560937", week=8)
        assert "fantasy_content" in settings_data
        assert "fantasy_content" in scoreboard_data

    asyncio.run(run())
    assert requests[0].url.path.endswith("/league/461.l.560937/settings")
    assert requests[1].url.path.endswith("/league/461.l.560937/scoreboard;week=8")
    assert all(req.url.params["format"] == "json" for req in requests)


def test_invalid_week_is_rejected():
    async def run():
        settings = Settings(_env_file=None)
        async with YahooFantasyClient(settings, "fake-token") as client:
            with pytest.raises(ValueError, match="Week"):
                await client.get_league_scoreboard("461.l.560937", week=99)

    asyncio.run(run())
