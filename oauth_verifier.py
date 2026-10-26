"""OAuth access-token verification primitives for a future protected MCP endpoint.

This does not install authentication middleware or enable remote hosting.
"""

from dataclasses import dataclass
from urllib.parse import urlparse

import jwt
from jwt import PyJWKClient


@dataclass(frozen=True)
class OAuthVerifier:
    issuer: str
    audience: str
    jwks_url: str

    def __post_init__(self) -> None:
        for name, value in (("issuer", self.issuer), ("jwks_url", self.jwks_url)):
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError(f"{name} must be an HTTPS URL without userinfo")
        if not self.audience:
            raise ValueError("OAuth audience is required")

    def verify(self, access_token: str) -> dict:
        """Validate a signed, unexpired RS256 JWT for this MCP resource.

        Rejects unsigned, symmetric, expired, wrong-issuer and wrong-audience
        tokens. JWKS is retrieved only from the configured trusted HTTPS URL.
        """
        if not access_token or len(access_token) > 16384:
            raise ValueError("Invalid access token length")
        jwks = PyJWKClient(self.jwks_url, timeout=5, lifespan=300)
        signing_key = jwks.get_signing_key_from_jwt(access_token)
        return jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=30,
        )
