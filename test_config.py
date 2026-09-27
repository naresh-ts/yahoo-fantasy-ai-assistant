from config import Settings


def test_credentials_are_optional_while_access_is_pending() -> None:
    settings = Settings(
        _env_file=None,
        yahoo_client_id=None,
        yahoo_client_secret=None,
        yahoo_refresh_token=None,
        yahoo_league_id=None,
        yahoo_team_name=None,
    )

    assert settings.yahoo_credentials_configured is False
    assert settings.yahoo_live_access_configured is False


def test_live_access_can_be_marked_configured() -> None:
    settings = Settings(
        _env_file=None,
        yahoo_client_id="example-client-id",
        yahoo_client_secret="example-client-secret",
        yahoo_refresh_token="example-refresh-token",
        yahoo_league_id="example-league-id",
        yahoo_team_name="Example Team",
    )

    assert settings.yahoo_credentials_configured is True
    assert settings.yahoo_live_access_configured is True
