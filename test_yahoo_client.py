import pytest

from config import Settings
from yahoo_client import YahooFantasyClient


def test_access_token_is_required() -> None:
    with pytest.raises(ValueError, match="access token"):
        YahooFantasyClient(Settings(_env_file=None), access_token="")
