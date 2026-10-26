"""Remote deployment preflight rejects unauthenticated public binding."""

from unittest.mock import patch

import pytest

from deployment_preflight import validate_deployment_environment


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "10.0.0.2"])
def test_public_binding_is_rejected(host):
    with (
        patch.dict("os.environ", {"MCP_HOST": host}),
        pytest.raises(RuntimeError, match="Remote MCP hosting is not configured"),
    ):
        validate_deployment_environment()


def test_loopback_is_allowed():
    with patch.dict("os.environ", {"MCP_HOST": "127.0.0.1"}):
        validate_deployment_environment()
