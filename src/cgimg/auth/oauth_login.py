"""Terminal OAuth (PKCE) login against OpenAI, two-step (non-blocking).

Step 1 (build_and_stash): create authorize URL + persist the PKCE verifier.
Step 2 (complete): read the stashed verifier, exchange the code for tokens.
"""
from __future__ import annotations
import json
import secrets
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import cgimg._vendor_path  # noqa: F401
from curl_cffi import requests
from utils.pkce import generate_pkce  # vendored

from cgimg.auth import tokens as _tokens

_AUTH_BASE = "https://auth.openai.com"
_PLATFORM = "https://platform.openai.com"
_CLIENT_ID = "app_2SKx67EdpoN0G6j64rFvigXD"
_REDIRECT = f"{_PLATFORM}/auth/callback"
_AUDIENCE = "https://api.openai.com/v1"
_AUTH0_CLIENT = "eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")


def _pending_path() -> Path:
    return _tokens._config_dir() / "login_pending.json"


def build_authorize_url(email_hint: str = "") -> tuple[str, str]:
    """Return (authorize_url, code_verifier)."""
    verifier, challenge = generate_pkce()
    params = {
        "issuer": _AUTH_BASE, "client_id": _CLIENT_ID, "audience": _AUDIENCE,
        "redirect_uri": _REDIRECT, "device_id": str(uuid.uuid4()),
        "screen_hint": "login_or_signup", "max_age": "0",
        "scope": "openid profile email offline_access",
        "response_type": "code", "response_mode": "query",
        "state": secrets.token_urlsafe(16), "nonce": secrets.token_urlsafe(32),
        "code_challenge": challenge, "code_challenge_method": "S256",
        "auth0Client": _AUTH0_CLIENT,
    }
    if email_hint.strip():
        params["login_hint"] = email_hint.strip()
    return f"{_AUTH_BASE}/api/accounts/authorize?{urlencode(params)}", verifier


def extract_code(callback: str) -> str:
    raw = callback.strip()
    if raw.startswith("http"):
        code = (parse_qs(urlparse(raw).query).get("code") or [""])[0].strip()
        if not code:
            raise RuntimeError("callback URL has no ?code= param")
        return code
    return raw  # user pasted bare code


def exchange_code(code: str, verifier: str) -> dict[str, str]:
    resp = requests.post(
        f"{_AUTH_BASE}/api/accounts/oauth/token",
        headers={"Content-Type": "application/json", "User-Agent": _UA,
                 "origin": _PLATFORM, "referer": f"{_PLATFORM}/"},
        json={"client_id": _CLIENT_ID, "code_verifier": verifier,
              "grant_type": "authorization_code", "code": code,
              "redirect_uri": _REDIRECT},
        timeout=60,
    )
    data = resp.json() if resp.text else {}
    if resp.status_code != 200 or not data.get("access_token"):
        detail = data.get("error_description") or data.get("error") or resp.text[:200]
        raise RuntimeError(f"token exchange failed (HTTP {resp.status_code}): {detail}")
    if not data.get("refresh_token"):
        raise RuntimeError("no refresh_token returned (scope missing offline_access?)")
    return {"access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "id_token": data.get("id_token", "")}


def build_and_stash(email_hint: str = "") -> str:
    """Step 1: build authorize URL, persist verifier, open browser. Returns the URL."""
    url, verifier = build_authorize_url(email_hint)
    p = _pending_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"code_verifier": verifier}), encoding="utf-8")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    return url


def complete(callback: str) -> dict[str, str]:
    """Step 2: read stashed verifier, exchange code, save tokens. Returns the tokens."""
    p = _pending_path()
    if not p.exists():
        raise RuntimeError("no pending login — run `cgimg login` first")
    verifier = json.loads(p.read_text(encoding="utf-8")).get("code_verifier", "")
    if not verifier:
        raise RuntimeError("pending login is corrupt — run `cgimg login` again")
    code = extract_code(callback)
    toks = exchange_code(code, verifier)
    _tokens.save(toks)
    try:
        p.unlink()
    except OSError:
        pass
    return toks
