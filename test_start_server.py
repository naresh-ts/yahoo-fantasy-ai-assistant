"""Security regression tests for the local-only MCP launcher."""

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


LAUNCHER = str(Path(__file__).with_name("start_server.py"))


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.10"])
def test_launcher_rejects_public_bindings(host):
    fake_mcp = Mock()
    with (
        patch.dict(sys.modules, {"server": SimpleNamespace(mcp=fake_mcp)}),
        patch.dict("os.environ", {"MCP_HOST": host, "PORT": "8000"}),
        pytest.raises(SystemExit, match="Refusing non-loopback binding"),
    ):
        runpy.run_path(LAUNCHER, run_name="__main__")
    fake_mcp.run.assert_not_called()


def test_launcher_starts_on_loopback():
    fake_mcp = Mock()
    with (
        patch.dict(sys.modules, {"server": SimpleNamespace(mcp=fake_mcp)}),
        patch.dict("os.environ", {"MCP_HOST": "127.0.0.1", "PORT": "8123"}),
    ):
        runpy.run_path(LAUNCHER, run_name="__main__")
    fake_mcp.run.assert_called_once_with(
        transport="streamable-http",
        host="127.0.0.1",
        port=8123,
        streamable_http_path="/mcp",
    )
