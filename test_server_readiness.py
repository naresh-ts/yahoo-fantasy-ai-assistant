"""Readiness checks accept an existing private refresh-token file."""

from unittest.mock import patch

from config import Settings
from server import _required_live_settings, project_status


def test_readiness_with_stored_refresh_token():
    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-id",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token=None,
        yahoo_league_id="560937",
        yahoo_team_name="Redzone naresh",
    )
    with (
        patch("server.get_settings", return_value=settings),
        patch("server.load_refresh_token", return_value="stored-token"),
    ):
        assert _required_live_settings() is settings
        status = project_status()
    assert status["status"] == "live_access_configured"
    assert status["refresh_token_configured"] is True


def test_readiness_fails_without_any_refresh_token():
    settings = Settings(
        _env_file=None,
        yahoo_client_id="test-id",
        yahoo_client_secret="test-secret",
        yahoo_refresh_token=None,
        yahoo_league_id="560937",
        yahoo_team_name="Redzone naresh",
    )
    with (
        patch("server.get_settings", return_value=settings),
        patch("server.load_refresh_token", return_value=None),
    ):
        status = project_status()
    assert status["status"] == "setup_incomplete"
