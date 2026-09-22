"""Interactively verify Yahoo OAuth and Fantasy Sports API access.

This script keeps credentials and OAuth tokens in memory only. It is intended to
be run from a private local terminal or GitHub Codespace.
"""

from __future__ import annotations

import base64
import getpass
import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

AUTHORIZATION_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
FANTASY_API_URL = (
    "https://fantasysports.yahooapis.com/fantasy/v2/"
    "users;use_login=1/games;game_codes=nfl/leagues?format=json"
)
REDIRECT_URI = "https://localhost:8080"
TARGET_LEAGUE_ID = "560937"


def extract_authorization_code(value: str) -> str:
    """Return an OAuth code pasted alone or inside a callback URL."""

    cleaned = value.strip()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        return cleaned

    parameters = parse_qs(urlparse(cleaned).query)
    return parameters.get("code", [""])[0]


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


def main() -> int:
    """Authorize the account and verify access to the user's fantasy league."""

    print("Yahoo Fantasy API access test")
    print("Credentials and tokens are kept in memory and are not saved.\n")

    client_id = getpass.getpass("Paste the Yahoo Client ID (input hidden): ").strip()
    client_secret = getpass.getpass("Paste the Yahoo Client Secret (input hidden): ").strip()
    if not client_id or not client_secret:
        print("Client ID and Client Secret are required.")
        return 1

    authorization_query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "language": "en-us",
        }
    )
    print("\nOpen this private authorization link in your browser:")
    print(f"{AUTHORIZATION_URL}?{authorization_query}")
    print("\nApprove access. The localhost page may fail to load; that is expected.")
    callback_value = getpass.getpass(
        "Paste the full redirected URL or only its code value (input hidden): "
    )
    authorization_code = extract_authorization_code(callback_value)
    if not authorization_code:
        print("No authorization code was found.")
        return 1

    basic_credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode("ascii")
    token_body = urlencode(
        {
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
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

    if contains_league_id(fantasy_payload, TARGET_LEAGUE_ID):
        print(f"\nSuccess: Fantasy API access is active and league {TARGET_LEAGUE_ID} is visible.")
    else:
        print(
            "\nSuccess: Fantasy API access is active, but league "
            f"{TARGET_LEAGUE_ID} was not found for the authorized Yahoo account."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
