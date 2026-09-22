from oauth_access_test import contains_league_id, extract_authorization_code


def test_extract_authorization_code_from_value() -> None:
    assert extract_authorization_code("abc123") == "abc123"


def test_extract_authorization_code_from_callback_url() -> None:
    callback = "https://localhost:8080/?code=abc%2B123&state=test"
    assert extract_authorization_code(callback) == "abc+123"


def test_contains_nested_league_id() -> None:
    payload = {"fantasy_content": {"users": [{"league_id": "560937"}]}}
    assert contains_league_id(payload, "560937")


def test_does_not_match_another_league() -> None:
    payload = {"fantasy_content": {"users": [{"league_id": "111111"}]}}
    assert not contains_league_id(payload, "560937")
