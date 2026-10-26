"""Asynchronous, read-only client for Yahoo Fantasy Sports."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Self

import httpx

from config import Settings

TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"


def _walk(value: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            yield from _walk(child)


def _first(value: Any, key: str) -> Any:
    for item in _walk(value):
        if key in item:
            found = item[key]
            if isinstance(found, (str, int, float, bool)) or found is None:
                return found
    return None


def _entities(payload: Any, entity: str, identifier: str) -> list[Any]:
    """Return unique Yahoo entities from its numbered/list-heavy JSON format."""

    found: list[Any] = []
    seen: set[str] = set()
    for item in _walk(payload):
        if entity not in item:
            continue
        raw = item[entity]
        identity = _first(raw, identifier)
        if identity is None or str(identity) in seen:
            continue
        seen.add(str(identity))
        found.append(raw)
    return found


def _nested_first(value: Any, container: str, key: str) -> Any:
    for item in _walk(value):
        if container in item:
            found = _first(item[container], key)
            if found is not None:
                return found
    return None


def extract_leagues(payload: Any) -> list[dict[str, Any]]:
    """Normalize league records returned by Yahoo."""

    return [
        {
            "league_key": str(_first(raw, "league_key") or ""),
            "league_id": str(_first(raw, "league_id") or ""),
            "name": str(_first(raw, "name") or ""),
            "season": str(_first(raw, "season") or ""),
        }
        for raw in _entities(payload, "league", "league_key")
    ]


def extract_teams(payload: Any) -> list[dict[str, Any]]:
    """Normalize fantasy-team records returned by Yahoo."""

    return [
        {
            "team_key": str(_first(raw, "team_key") or ""),
            "team_id": str(_first(raw, "team_id") or ""),
            "name": str(_first(raw, "name") or ""),
            "is_owned_by_current_login": bool(
                int(_first(raw, "is_owned_by_current_login") or 0)
            ),
        }
        for raw in _entities(payload, "team", "team_key")
    ]


def extract_players(payload: Any) -> list[dict[str, Any]]:
    """Normalize roster or available-player records returned by Yahoo."""

    players: list[dict[str, Any]] = []
    for raw in _entities(payload, "player", "player_key"):
        players.append(
            {
                "player_key": str(_first(raw, "player_key") or ""),
                "player_id": str(_first(raw, "player_id") or ""),
                "name": str(_nested_first(raw, "name", "full") or ""),
                "nfl_team": str(_first(raw, "editorial_team_abbr") or ""),
                "positions": str(_first(raw, "display_position") or ""),
                "selected_position": str(
                    _nested_first(raw, "selected_position", "position") or ""
                ),
                "status": str(_first(raw, "status") or ""),
                "ownership": str(
                    _nested_first(raw, "ownership", "ownership_type") or ""
                ),
            }
        )
    return players


async def refresh_access_token(settings: Settings, refresh_token: str) -> str:
    """Exchange a Yahoo refresh token for a short-lived access token."""

    if not settings.yahoo_client_id or not settings.yahoo_client_secret:
        raise ValueError("Yahoo client credentials are required")
    if not refresh_token:
        raise ValueError("A Yahoo refresh token is required")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            TOKEN_URL,
            auth=(settings.yahoo_client_id, settings.yahoo_client_secret.get_secret_value()),
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        response.raise_for_status()
        token = str(response.json().get("access_token", ""))
    if not token:
        raise RuntimeError("Yahoo did not return an access token")
    return token


class YahooFantasyClient:
    """Call Yahoo Fantasy endpoints using an OAuth access token."""

    def __init__(
        self,
        settings: Settings,
        access_token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not access_token:
            raise ValueError("A Yahoo OAuth access token is required")

        self._base_url = settings.yahoo_api_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=httpx.Timeout(20.0),
            transport=transport,
        )

    async def get(self, resource_path: str, **params: str | int) -> dict[str, Any]:
        """Retrieve one Yahoo Fantasy resource as JSON."""

        normalized_path = resource_path.lstrip("/")
        query = {"format": "json", **params}
        response = await self._client.get(f"{self._base_url}/{normalized_path}", params=query)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("Yahoo returned an unexpected response")
        return payload

    async def resolve_league(self, league_id: str) -> dict[str, Any]:
        payload = await self.get("users;use_login=1/games;game_codes=nfl/leagues")
        for league in extract_leagues(payload):
            if league["league_id"] == str(league_id):
                return league
        raise LookupError(f"Yahoo league {league_id} was not found")

    async def resolve_team(self, league_key: str, team_name: str = "") -> dict[str, Any]:
        payload = await self.get(f"league/{league_key}/teams")
        teams = extract_teams(payload)
        wanted = team_name.casefold().strip()
        for team in teams:
            if team["is_owned_by_current_login"]:
                return team
        for team in teams:
            if wanted and team["name"].casefold().strip() == wanted:
                return team
        raise LookupError(f"Yahoo team {team_name or 'owned by the current user'} was not found")

    async def get_roster(self, team_key: str, week: int | None = None) -> list[dict[str, Any]]:
        resource = f"team/{team_key}/roster"
        if week is not None:
            resource += f";week={week}"
        return extract_players(await self.get(resource))

    async def get_available_players(
        self,
        league_key: str,
        *,
        position: str | None = None,
        start: int = 0,
        count: int = 25,
    ) -> list[dict[str, Any]]:
        filters = ["status=A", f"start={start}", f"count={count}"]
        if position:
            filters.insert(1, f"position={position.upper()}")
        resource = f"league/{league_key}/players;" + ";".join(filters)
        return extract_players(await self.get(resource))

    async def get_team_snapshot(
        self,
        league_id: str,
        team_name: str,
        *,
        free_agent_positions: Sequence[str] = ("QB", "RB", "WR", "TE", "K", "DEF"),
        free_agent_count: int = 25,
    ) -> dict[str, Any]:
        league = await self.resolve_league(league_id)
        team = await self.resolve_team(league["league_key"], team_name)
        available = {
            position: await self.get_available_players(
                league["league_key"], position=position, count=free_agent_count
            )
            for position in free_agent_positions
        }
        return {
            "league": league,
            "team": team,
            "roster": await self.get_roster(team["team_key"]),
            "available_players": available,
        }

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()


async def refresh_oauth_tokens(
    settings: Settings, refresh_token: str
) -> dict[str, Any]:
    """Refresh Yahoo OAuth credentials and preserve replacement tokens."""

    if not settings.yahoo_client_id or not settings.yahoo_client_secret:
        raise ValueError("Yahoo client credentials are required")
    if not refresh_token:
        raise ValueError("A Yahoo refresh token is required")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            TOKEN_URL,
            auth=(
                settings.yahoo_client_id,
                settings.yahoo_client_secret.get_secret_value(),
            ),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        payload = response.json()

    access_token = payload.get("access_token")
    if not access_token:
        raise RuntimeError("Yahoo did not return an access token")

    return {
        "access_token": access_token,
        "refresh_token": payload.get("refresh_token") or refresh_token,
        "expires_in": payload.get("expires_in", 3600),
    }
