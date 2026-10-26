"""Remote launcher cannot start without trusted HTTPS ingress and OAuth."""

import pytest

from start_remote_server import create_app


def test_launcher_requires_explicit_trusted_https_proxy():
    with pytest.raises(ValueError, match="trusted HTTPS reverse proxy"):
        create_app({})


def test_launcher_still_requires_oauth_and_persistent_tokens():
    with pytest.raises(ValueError, match="Remote MCP is disabled"):
        create_app({"MCP_TRUSTED_HTTPS_PROXY": "true"})
