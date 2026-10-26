"""Tests for private Yahoo token storage."""

import os

import pytest

import token_store


def test_save_and_load_refresh_token(tmp_path, monkeypatch):
    token_file = tmp_path / "private" / "refresh_token"

    monkeypatch.setattr(
        token_store, "TOKEN_DIRECTORY", token_file.parent
    )
    monkeypatch.setattr(
        token_store, "TOKEN_FILE", token_file
    )

    token_store.save_refresh_token("example-token")

    assert token_store.load_refresh_token() == "example-token"
    assert token_file.stat().st_mode & 0o777 == 0o600
    assert token_file.parent.stat().st_mode & 0o777 == 0o700


def test_replacement_token(tmp_path, monkeypatch):
    token_file = tmp_path / "private" / "refresh_token"

    monkeypatch.setattr(
        token_store, "TOKEN_DIRECTORY", token_file.parent
    )
    monkeypatch.setattr(
        token_store, "TOKEN_FILE", token_file
    )

    token_store.save_refresh_token("original-token")
    token_store.save_refresh_token("replacement-token")

    assert token_store.load_refresh_token() == "replacement-token"


def test_reject_insecure_permissions(tmp_path, monkeypatch):
    token_file = tmp_path / "refresh_token"

    monkeypatch.setattr(token_store, "TOKEN_FILE", token_file)

    token_file.write_text("example-token")
    os.chmod(token_file, 0o644)

    with pytest.raises(PermissionError):
        token_store.load_refresh_token()
