"""Authorize Yahoo, verify league access, and optionally save secure Codespaces secrets."""

from __future__ import annotations

import asyncio
import base64
import getpass
import json
import os
import secrets
import subprocess
import time
import webbrowser
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from config import Settings
from yahoo_client import YahooFantasyClient

AUTHORIZATION_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
FANTASY_API_URL = (
    "https://fantasysports.yahooapis.com/fantasy/v2/"
    "users;use_login=1/games;game_codes=nfl/leagues?format=json"
)
LOCAL_REDIRECT_URI = "https://localhost:8080"
CALLBACK_PORT = 8080
CALLBACK_TIMEOUT_SECONDS = 180
TARGET_LEAGUE_ID = "560937"
TARGET_TEAM_NAME = "Redzone naresh"
GITHUB_REPOSITORY = "naresh-ts/yahoo-fantasy-ai-assistant"
SAVE_SECRETS_ENV = "YAHOO_SAVE_CODESPACES_SECRETS"


def extract_authorization_code(value: str) -> str:
    """Return an OAuth code pasted alone or inside a callback URL."""

    cleaned = value.strip()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        return cleaned

    parameters = parse_qs(urlparse(cleaned).query)
    return parameters.get("code", [""])[0]


def codespace_redirect_uri() -> str:
    """Return the private HTTPS forwarding URL for port 8080, if available."""

    name = os.environ.get("CODESPACE_NAME", "").strip()
    domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "").strip()
    if name and domain:
        return f"https://{name}-{CALLBACK_PORT}.{domain}"
    return ""


def contains_league_id(value: Any, league_id: str) -> bool:
    """Recursively find a league ID without printing private league data."""

    if isinstance(value, Mapping):
        if str(value.get("league_id", "")) == league_id:
            return True
        return any(contains_league_id(item, league_id) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(contains_league_id(item, league_id) for item in value)
    return False


def request_json(request: Request) -> dict[str, Any]:
    """Execute an HTTPS request and decode a JSON object."""

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 403:
            raise RuntimeError(
                "Yahoo returned HTTP 403. OAuth may have succeeded, but Fantasy API "
                "provisioning is not active yet."
            ) from exc
        raise RuntimeError(f"Yahoo returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not connect to Yahoo: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise TypeError("Yahoo returned an unexpected response.")
    return payload


def receive_codespace_callback(expected_state: str) -> str:
    """Receive one valid Yahoo callback through the Codespaces HTTPS proxy."""

    results: Queue[str] = Queue(maxsize=1)

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parameters = parse_qs(urlparse(self.path).query)
            state = parameters.get("state", [""])[0]
            code = parameters.get("code", [""])[0]
            error = parameters.get("error", [""])[0]

            if state != expected_state:
                self.send_response(400)
                body = b"Invalid OAuth state. You may close this page."
            elif error:
                self.send_response(400)
                body = b"Yahoo authorization was not approved. You may close this page."
                if results.empty():
                    results.put("")
            elif code:
                self.send_response(200)
                body = b"Yahoo authorization received. You may return to ChatGPT."
                if results.empty():
                    results.put(code)
            else:
                self.send_response(404)
                body = b"Waiting for Yahoo authorization."

            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("0.0.0.0", CALLBACK_PORT), CallbackHandler)
    server.timeout = 1
    deadline = time.monotonic() + CALLBACK_TIMEOUT_SECONDS
    try:
        while time.monotonic() < deadline:
            server.handle_request()
            try:
                return results.get_nowait()
            except Empty:
                continue
    finally:
        server.server_close()

    return ""


def set_codespaces_secret(name: str, value: str) -> None:
    """Store a value as a user Codespaces secret scoped to this repository."""

    subprocess.run(
        [
            "gh",
            "secret",
            "set",
            name,
            "--user",
            "--app",
            "codespaces",
            "--repos",
            GITHUB_REPOSITORY,
        ],
        input=value,
        text=True,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def save_codespaces_configuration(refresh_token: str) -> None:
    """Persist renewable access and non-secret league selection privately."""

    set_codespaces_secret("YAHOO_REFRESH_TOKEN", refresh_token)
    set_codespaces_secret("YAHOO_LEAGUE_ID", TARGET_LEAGUE_ID)
    set_codespaces_secret("YAHOO_TEAM_NAME", TARGET_TEAM_NAME)


async def retrieve_snapshot(access_token: str) -> dict[str, Any]:
    """Retrieve a small live roster/free-agent snapshot for verification."""

    settings = Settings(_env_file=None)
    async with YahooFantasyClient(settings, access_token) as client:
        return await client.get_team_snapshot(
            TARGET_LEAGUE_ID,
            TARGET_TEAM_NAME,
            free_agent_count=5,
        )


def print_snapshot_summary(snapshot: Mapping[str, Any]) -> None:
    """Print only the normalized fields needed to verify live retrieval."""

    team = snapshot["team"]
    roster = snapshot["roster"]
    available = snapshot["available_players"]
    print(f"Team verified: {team['name']} ({team['team_key']})")
    print(f"Roster retrieved: {len(roster)} players")
    for player in roster:
        position = player["selected_position"] or player["positions"]
        print(f"  {position}: {player['name']} ({player['nfl_team']})")
    print("Available-player samples retrieved:")
    for position, players in available.items():
        names = ", ".join(player["name"] for player in players)
        print(f"  {position}: {len(players)} players - {names}")


def main() -> int:
    """Authorize the account, verify live reads, and optionally save secrets."""

    print("Yahoo Fantasy API access test")
    print("Credentials and OAuth tokens are never printed or written to the repository.\n")

    client_id = os.environ.get("YAHOO_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YAHOO_CLIENT_SECRET", "").strip()

    if client_id and client_secret:
        print("Using Yahoo credentials from secure environment variables.")
    else:
        client_id = getpass.getpass("Paste the Yahoo Client ID (input hidden): ").strip()
        client_secret = getpass.getpass(
            "Paste the Yahoo Client Secret (input hidden): "
        ).strip()
    if not client_id or not client_secret:
        print("Client ID and Client Secret are required.")
        return 1

    redirect_uri = codespace_redirect_uri() or LOCAL_REDIRECT_URI
    state = secrets.token_urlsafe(32)
    authorization_query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "language": "en-us",
            "state": state,
        }
    )
    authorization_url = f"{AUTHORIZATION_URL}?{authorization_query}"

    print("\nOpening the private Yahoo authorization page in your browser.")
    if codespace_redirect_uri():
        with ThreadPoolExecutor(max_workers=1) as executor:
            callback_future = executor.submit(receive_codespace_callback, state)
            time.sleep(0.25)
            if not webbrowser.open(authorization_url):
                print("The Yahoo authorization page could not be opened automatically.")
                return 1
            print("Waiting for Yahoo's secure callback; no copying or pasting is needed.")
            authorization_code = callback_future.result()
    else:
        if not webbrowser.open(authorization_url):
            print("The Yahoo authorization page could not be opened automatically.")
            return 1
        print("\nApprove access. The localhost page may fail to load; that is expected.")
        callback_value = getpass.getpass(
            "Paste the full redirected URL or only its code value (input hidden): "
        )
        authorization_code = extract_authorization_code(callback_value)

    if not authorization_code:
        print("No valid authorization code was received.")
        return 1

    basic_credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode("ascii")
    token_body = urlencode(
        {
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": authorization_code,
        }
    ).encode("ascii")
    token_request = Request(
        TOKEN_URL,
        data=token_body,
        headers={
            "Authorization": f"Basic {basic_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        token_payload = request_json(token_request)
        access_token = str(token_payload.get("access_token", ""))
        refresh_token = str(token_payload.get("refresh_token", ""))
        if not access_token:
            raise RuntimeError("Yahoo did not return an access token.")

        fantasy_request = Request(
            FANTASY_API_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        fantasy_payload = request_json(fantasy_request)
    except RuntimeError as exc:
        print(f"\nAccess test failed: {exc}")
        return 1

    if not contains_league_id(fantasy_payload, TARGET_LEAGUE_ID):
        print(
            "\nFantasy API access is active, but league "
            f"{TARGET_LEAGUE_ID} was not found for the authorized Yahoo account."
        )
        return 1

    print(f"\nSuccess: league {TARGET_LEAGUE_ID} is visible.")
    try:
        snapshot = asyncio.run(retrieve_snapshot(access_token))
        print_snapshot_summary(snapshot)
    except Exception as exc:  # noqa: BLE001
        print(f"Live roster/free-agent verification failed: {type(exc).__name__}: {exc}")
        return 1

    if os.environ.get(SAVE_SECRETS_ENV) == "1":
        if not refresh_token:
            print("Yahoo did not return a refresh token; secure storage was skipped.")
            return 1
        try:
            save_codespaces_configuration(refresh_token)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Could not save the private Codespaces secrets: {type(exc).__name__}")
            return 1
        print("Private Codespaces secrets saved successfully.")
    else:
        print("Refresh token kept in memory only; secure storage was not requested.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
