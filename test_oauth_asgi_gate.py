"""Tests that every remote MCP HTTP request is authenticated."""

import asyncio

import pytest

from oauth_asgi_gate import OAuthASGIGate


class FakeVerifier:
    def verify(self, token):
        if token == "good":
            return {"sub": "my-user"}
        if token == "other":
            return {"sub": "someone-else"}
        raise ValueError("invalid")


async def request(headers=None, scope_type="http"):
    calls = []
    messages = []

    async def app(scope, receive, send):
        calls.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def send(message):
        messages.append(message)

    gate = OAuthASGIGate(app, FakeVerifier(), "my-user")
    await gate(
        {"type": scope_type, "headers": headers or [], "path": "/mcp"},
        lambda: None,
        send,
    )
    return calls, messages


@pytest.mark.parametrize(
    "headers,expected",
    [
        ([], 401),
        ([(b"authorization", b"Basic secret")], 401),
        ([(b"authorization", b"Bearer bad")], 401),
        ([(b"authorization", b"Bearer other")], 403),
        ([(b"authorization", b"Bearer good"), (b"authorization", b"Bearer good")], 401),
        ([(b"authorization", b"Bearer good")], 200),
    ],
)
def test_authentication_gate(headers, expected):
    calls, messages = asyncio.run(request(headers))
    assert messages[0]["status"] == expected
    assert bool(calls) is (expected == 200)


def test_websocket_rejected():
    calls, messages = asyncio.run(request(scope_type="websocket"))
    assert not calls
    assert messages[0]["status"] == 403


def test_explicit_subject_required():
    with pytest.raises(ValueError):
        OAuthASGIGate(lambda *args: None, FakeVerifier(), "")
