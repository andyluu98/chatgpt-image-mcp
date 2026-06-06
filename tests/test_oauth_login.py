from cgimg.auth import oauth_login
import pytest


def test_build_authorize_url_has_required_params():
    url, verifier = oauth_login.build_authorize_url()
    assert url.startswith("https://auth.openai.com/api/accounts/authorize?")
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    assert "scope=openid+profile+email+offline_access" in url
    assert len(verifier) > 20


def test_extract_code_from_url():
    cb = "https://platform.openai.com/auth/callback?code=ac_ABC123&state=xyz"
    assert oauth_login.extract_code(cb) == "ac_ABC123"


def test_extract_code_bare():
    assert oauth_login.extract_code("ac_RAW") == "ac_RAW"


def test_extract_code_missing_raises():
    with pytest.raises(RuntimeError, match="no \\?code="):
        oauth_login.extract_code("https://platform.openai.com/auth/callback?state=xyz")


def test_cli_login_step1_prints_url(capsys, tmp_path, monkeypatch):
    from cgimg.auth import tokens
    monkeypatch.setattr(tokens, "_config_dir", lambda: tmp_path)
    monkeypatch.setattr("webbrowser.open", lambda *a, **k: False)
    from cgimg import cli
    rc = cli.main(["login"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "auth.openai.com/api/accounts/authorize" in out
    assert (tmp_path / "login_pending.json").exists()
