import json

import pytest

from cgimg.auth import tokens


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(tokens, "_auth_path", lambda: tmp_path / "auth.json")
    tokens.save({"access_token": "a", "refresh_token": "r", "id_token": "i"})
    loaded = tokens.load()
    assert loaded["access_token"] == "a"
    assert loaded["refresh_token"] == "r"


def test_load_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(tokens, "_auth_path", lambda: tmp_path / "nope.json")
    assert tokens.load() is None


def test_get_access_token_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(tokens, "_auth_path", lambda: tmp_path / "none.json")
    with pytest.raises(RuntimeError, match="not logged in"):
        tokens.get_access_token()


def test_login_status_not_authed(tmp_path, monkeypatch):
    monkeypatch.setattr(tokens, "_auth_path", lambda: tmp_path / "none.json")
    assert tokens.login_status() == {"authed": False}
