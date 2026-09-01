from config import Settings


def test_credentials_are_optional_while_access_is_pending() -> None:
    settings = Settings(_env_file=None)

    assert settings.yahoo_credentials_configured is False


def test_credentials_can_be_marked_configured() -> None:
    settings = Settings(
        _env_file=None,
        yahoo_client_id="example-client-id",
        yahoo_client_secret="example-client-secret",
    )

    assert settings.yahoo_credentials_configured is True
