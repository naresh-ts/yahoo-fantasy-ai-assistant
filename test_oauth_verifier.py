"""Security regression tests for OAuth JWT verification."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from oauth_verifier import OAuthVerifier

ISSUER = "https://login.example.com/"
AUDIENCE = "yahoo-fantasy-mcp"
JWKS = "https://login.example.com/.well-known/jwks.json"


def verifier():
    return OAuthVerifier(ISSUER, AUDIENCE, JWKS)


def test_configuration_requires_https():
    with pytest.raises(ValueError):
        OAuthVerifier(ISSUER, AUDIENCE, "http://login.example.com/keys")
    with pytest.raises(ValueError):
        OAuthVerifier("http://login.example.com", AUDIENCE, JWKS)
    with pytest.raises(ValueError):
        OAuthVerifier(ISSUER, "", JWKS)


def test_signed_token_and_rejections():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "authorized-user",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }

    class FakeJWKClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_signing_key_from_jwt(self, token):
            return type("Key", (), {"key": key.public_key()})()

    with patch("oauth_verifier.PyJWKClient", FakeJWKClient):
        valid = jwt.encode(claims, key, algorithm="RS256")
        assert verifier().verify(valid)["sub"] == "authorized-user"

        for altered in (
            {**claims, "aud": "different-resource"},
            {**claims, "iss": "https://attacker.example.com/"},
            {**claims, "exp": now - timedelta(minutes=5)},
            {k: v for k, v in claims.items() if k != "sub"},
        ):
            with pytest.raises(jwt.PyJWTError):
                verifier().verify(jwt.encode(altered, key, algorithm="RS256"))

        with pytest.raises(jwt.PyJWTError):
            verifier().verify(jwt.encode(claims, "attacker-secret", algorithm="HS256"))


def test_reject_empty_or_oversized_token():
    with pytest.raises(ValueError):
        verifier().verify("")
    with pytest.raises(ValueError):
        verifier().verify("a" * 16385)
