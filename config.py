"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the read-only connector."""

    yahoo_client_id: str | None = None
    yahoo_client_secret: SecretStr | None = None
    yahoo_redirect_uri: HttpUrl | None = None
    yahoo_league_key: str | None = None
    yahoo_api_base_url: str = "https://fantasysports.yahooapis.com/fantasy/v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def yahoo_credentials_configured(self) -> bool:
        """Return whether the Yahoo OAuth application credentials are present."""

        return bool(self.yahoo_client_id and self.yahoo_client_secret)


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
