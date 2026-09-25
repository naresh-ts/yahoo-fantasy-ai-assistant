import asyncio

import httpx
import pytest

from config import Settings
from yahoo_client import YahooFantasyClient, extract_leagues, extract_players, extract_teams


def test_access_token_is_required() -> None:
    with pytest.raises(ValueError, match="access token"):
        YahooFantasyClient(Settings(_env_file=None), access_token="")


def test_normalizers_handle_yahoo_numbered_records() -> None:
    payload = {
        "fantasy_content": {
            "league": [
                {"league_key": "461.l.560937"},
                {"league_id": "560937"},
                {"name": "Test League"},
                {"season": "2026"},
            ],
            "teams": {
                "0": {
                    "team": [
                        {"team_key": "461.l.560937.t.1"},
                        {"team_id": "1"},
                        {"name": "Redzone naresh"},
                        {"is_owned_by_current_login": 1},
                    ]
                }
            },
            "players": {
                "0": {
                    "player": [
                        [
                            {"player_key": "461.p.123"},
                            {"player_id": "123"},
                            {"name": {"full": "Example Player"}},
                            {"editorial_team_abbr": "BUF"},
                            {"display_position": "QB"},
                        ],
                        [{"selected_position": {"position": "QB"}}],
                    ]
                }
            },
        }
    }
    assert extract_leagues(payload)[0]["league_id"] == "560937"
    assert extract_teams(payload)[0]["is_owned_by_current_login"] is True
    assert extract_players(payload)[0] == {
        "player_key": "461.p.123",
        "player_id": "123",
        "name": "Example Player",
        "nfl_team": "BUF",
        "positions": "QB",
        "selected_position": "QB",
        "status": "",
        "ownership": "",
    }


def test_available_players_builds_read_only_filtered_request() -> None:
    requested: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(200, json={"fantasy_content": {"players": {"count": 0}}})

    async def run() -> None:
        client = YahooFantasyClient(
            Settings(_env_file=None),
            "test-token",
            transport=httpx.MockTransport(handler),
        )
        try:
            assert await client.get_available_players(
                "461.l.560937", position="wr", start=25, count=10
            ) == []
        finally:
            await client.close()

    asyncio.run(run())
    request = requested[0]
    assert request.method == "GET"
    assert request.url.path.endswith(
        "/league/461.l.560937/players;status=A;position=WR;start=25;count=10"
    )
    assert request.url.params["format"] == "json"
    assert request.headers["Authorization"] == "Bearer test-token"
