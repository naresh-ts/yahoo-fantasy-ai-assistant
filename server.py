"""MCP entry point for the Yahoo Fantasy AI Assistant."""

from typing import Any

from mcp.server import MCPServer

from config import get_settings

mcp = MCPServer("Yahoo Fantasy AI Assistant")


@mcp.tool()
def project_status() -> dict[str, Any]:
    """Report connector readiness without exposing any secret values."""

    settings = get_settings()
    return {
        "status": "awaiting_yahoo_api_credentials"
        if not settings.yahoo_credentials_configured
        else "credentials_configured",
        "read_only": True,
        "credentials_configured": settings.yahoo_credentials_configured,
        "league_key_configured": bool(settings.yahoo_league_key),
        "planned_tools": [
            "get_league_settings",
            "get_my_roster",
            "get_all_rosters",
            "get_available_players",
            "get_matchups",
            "get_standings",
            "get_transactions",
        ],
    }
