"""MCP entry point for the read-only Yahoo Fantasy AI Assistant."""

from typing import Any

from mcp.server import MCPServer

from config import Settings, get_settings
from token_manager import YahooTokenManager
from token_store import load_refresh_token
from yahoo_client import YahooFantasyClient

mcp = MCPServer("Yahoo Fantasy AI Assistant")


def _required_live_settings() -> Settings:
    settings = get_settings()
    if not (
        settings.yahoo_credentials_configured
        and settings.yahoo_league_id
        and settings.yahoo_team_name
        and (settings.yahoo_refresh_token or load_refresh_token())
    ):
        raise RuntimeError(
            "Yahoo live access requires client credentials, refresh token, league ID, "
            "and team name."
        )
    return settings


_token_manager: YahooTokenManager | None = None


async def _authorized_client(settings: Settings) -> YahooFantasyClient:
    global _token_manager

    if _token_manager is None:
        _token_manager = YahooTokenManager(settings)

    access_token = await _token_manager.get_access_token()
    return YahooFantasyClient(settings, access_token)


async def _resolve_team(
    client: YahooFantasyClient, settings: Settings
) -> tuple[dict[str, Any], dict[str, Any]]:
    assert settings.yahoo_league_id is not None
    assert settings.yahoo_team_name is not None
    league = await client.resolve_league(settings.yahoo_league_id)
    team = await client.resolve_team(league["league_key"], settings.yahoo_team_name)
    return league, team


@mcp.tool()
def project_status() -> dict[str, Any]:
    """Report connector readiness without exposing secret values."""

    settings = get_settings()
    refresh_token_configured = bool(
        settings.yahoo_refresh_token or load_refresh_token()
    )
    live_access_configured = bool(
        settings.yahoo_credentials_configured
        and refresh_token_configured
        and settings.yahoo_league_id
        and settings.yahoo_team_name
    )
    return {
        "status": (
            "live_access_configured"
            if live_access_configured
            else "setup_incomplete"
        ),
        "read_only": True,
        "credentials_configured": settings.yahoo_credentials_configured,
        "refresh_token_configured": refresh_token_configured,
        "league_configured": bool(settings.yahoo_league_id),
        "team_configured": bool(settings.yahoo_team_name),
        "available_tools": [
            "get_my_roster",
            "get_available_players",
            "get_team_snapshot",
        ],
    }


@mcp.tool()
async def get_my_roster() -> dict[str, Any]:
    """Return the authorized user's current Yahoo fantasy roster."""

    settings = _required_live_settings()
    async with await _authorized_client(settings) as client:
        league, team = await _resolve_team(client, settings)
        roster = await client.get_roster(team["team_key"])
    return {"league": league, "team": team, "roster": roster}


@mcp.tool()
async def get_available_players(
    position: str = "", start: int = 0, count: int = 25
) -> dict[str, Any]:
    """Return available Yahoo players, optionally filtered by position."""

    settings = _required_live_settings()
    safe_start = max(0, start)
    safe_count = min(max(1, count), 100)
    async with await _authorized_client(settings) as client:
        league, _ = await _resolve_team(client, settings)
        players = await client.get_available_players(
            league["league_key"],
            position=position or None,
            start=safe_start,
            count=safe_count,
        )
    return {
        "league": league,
        "position": position.upper() or "ALL",
        "start": safe_start,
        "count": len(players),
        "players": players,
    }


@mcp.tool()
async def get_team_snapshot(free_agent_count: int = 25) -> dict[str, Any]:
    """Return the current roster and available players for core positions."""

    settings = _required_live_settings()
    assert settings.yahoo_league_id is not None
    assert settings.yahoo_team_name is not None
    async with await _authorized_client(settings) as client:
        return await client.get_team_snapshot(
            settings.yahoo_league_id,
            settings.yahoo_team_name,
            free_agent_count=min(max(1, free_agent_count), 50),
        )
