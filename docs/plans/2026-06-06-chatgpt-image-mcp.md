# chatgpt-image-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Python MCP server that generates images via the reverse-engineered ChatGPT backend (vendored from chatgpt2api) and assembles them into PowerPoint decks, usable from Claude Code / Codex / Antigravity.

**Architecture:** Vendor the proven image-gen code from chatgpt2api mostly intact under a `_vendor/` package (added to sys.path so original `services.*` / `utils.*` imports resolve). Replace only the multi-account `account_service` with a single-account **shim** backed by a local `auth.json`. Thin new layers on top: terminal OAuth login, token refresh, aspect→size mapping, MCP tools, and a python-pptx deck builder.

**Tech Stack:** Python 3.12, `uv`, `mcp` (FastMCP), `curl_cffi`, `Pillow`, `pybase64`, `python-pptx`, `pytest`.

**Source repo to vendor from:** `F:\1111111. Chatgpt2api` (MIT licensed, (c) 2026 kunkun — keep notice).

**Spec:** `docs/specs/2026-06-06-chatgpt-image-mcp-design.md`

---

## Key facts from source analysis (do not re-discover)

- **Image-gen entry (low-level, no pool):** `services/protocol/conversation.py::stream_image_outputs(backend, request, index, total)` → `conversation_events()` → `backend.stream_conversation(...)`. The pool wrapper `stream_image_outputs_with_pool()` is what we BYPASS.
- **Backend client:** `services/openai_backend_api.py::OpenAIBackendAPI(access_token=...)`. Method `_start_image_generation()` (line ~910) does the real work.
- **`size` is embedded into the prompt** by `conversation.py::build_image_prompt(prompt, size, quality)` as a text hint. NOT a separate HTTP field.
- **PoW** (`utils/pow.py`, `utils/sentinel.py`): pure local SHA3 computation, no browser/network. Required for `/backend-api/sentinel/chat-requirements`.
- **Turnstile** (`utils/turnstile.py`): self-contained local solver, NOT required for image gen (only auth/register, conditional). Vendor it but it should not fire.
- **Token refresh:** `POST https://auth.openai.com/oauth/token`, form body `{grant_type: refresh_token, refresh_token, client_id: app_2SKx67EdpoN0G6j64rFvigXD}` → `{access_token, refresh_token, id_token}`.
- **OAuth login client_id / redirect:** `app_2SKx67EdpoN0G6j64rFvigXD`, redirect `https://platform.openai.com/auth/callback`, audience `https://api.openai.com/v1`, scope `openid profile email offline_access`.
- **account_service interface used by vendored code (the shim must provide):**
  `get_available_access_token()`, `get_account(token)`, `refresh_access_token(token, *, force, event)`, `mark_image_result(...)`, `remove_invalid_token(token)`. (Confirm exact call sites during Task 5.)

---

## File Structure

```
F:\chatgpt-image-mcp\
├── README.md
├── pyproject.toml
├── .python-version
├── .gitignore
├── NOTICE                       # MIT attribution to chatgpt2api/kunkun
├── docs/
│   ├── specs/2026-06-06-chatgpt-image-mcp-design.md   (exists)
│   └── plans/2026-06-06-chatgpt-image-mcp.md          (this file)
├── src/cgimg/
│   ├── __init__.py
│   ├── _vendor_path.py          # prepends _vendor/ to sys.path on import
│   ├── sizes.py                 # [NEW] aspect → size string
│   ├── server.py                # [NEW] FastMCP stdio server
│   ├── cli.py                   # [NEW] cgimg login / gen / ppt
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth_login.py       # [NEW] terminal OAuth (adapted from oauth_login_service)
│   │   └── tokens.py            # [NEW] auth.json store + refresh
│   ├── engine/
│   │   ├── __init__.py
│   │   └── generate.py          # [NEW] adapter: token → backend → stream_image_outputs
│   └── ppt/
│       ├── __init__.py
│       └── builder.py           # [NEW] images → pptx
├── src/cgimg/_vendor/           # [VENDORED] sys.path root; keeps services.*/utils.* names
│   ├── services/
│   │   ├── __init__.py
│   │   ├── account_service.py   # [NEW SHIM] single-account drop-in
│   │   ├── config.py            # vendored
│   │   ├── proxy_service.py     # vendored
│   │   ├── openai_backend_api.py# vendored
│   │   └── protocol/
│   │       ├── __init__.py
│   │       └── conversation.py  # vendored
│   └── utils/
│       ├── __init__.py
│       ├── pow.py sentinel.py turnstile.py helper.py image_tokens.py log.py pkce.py  # vendored
└── tests/
    ├── test_sizes.py
    ├── test_ppt_builder.py
    ├── test_tokens.py
    └── assets/   # sample PNGs for ppt tests
```

---

## Task 1: Repo scaffold + deps

**Files:**
- Create: `F:\chatgpt-image-mcp\pyproject.toml`, `.python-version`, `.gitignore`, `src/cgimg/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "cgimg"
version = "0.1.0"
description = "Standalone MCP server for ChatGPT image generation + PPT building"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.2.0",
    "curl_cffi>=0.7.0",
    "pillow>=10.0.0",
    "pybase64>=1.3.0",
    "python-pptx>=1.0.0",
]

[project.scripts]
cgimg = "cgimg.cli:main"
cgimg-mcp = "cgimg.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cgimg"]

[dependency-groups]
dev = ["pytest>=8.0"]
```

- [ ] **Step 2: Write .python-version**

```
3.12
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
.venv/
auth.json
out/
*.pptx
dist/
.pytest_cache/
```

- [ ] **Step 4: Create empty package files**

Create `src/cgimg/__init__.py` with `__version__ = "0.1.0"` and empty `tests/__init__.py`.

- [ ] **Step 5: Verify env builds**

Run: `cd /f/chatgpt-image-mcp && uv sync`
Expected: resolves and installs all deps without error.

- [ ] **Step 6: Commit**

```bash
cd /f/chatgpt-image-mcp && git init && git add -A
git commit -m "chore: scaffold cgimg repo with deps"
```

---

## Task 2: Vendor the engine + add sys.path shim loader

**Files:**
- Create: `src/cgimg/_vendor_path.py`, `src/cgimg/_vendor/**` (copied files), `NOTICE`

- [ ] **Step 1: Copy vendored files preserving package layout**

Run (Git Bash):
```bash
SRC="/f/1111111. Chatgpt2api"
DST="/f/chatgpt-image-mcp/src/cgimg/_vendor"
mkdir -p "$DST/services/protocol" "$DST/utils"
cp "$SRC/services/openai_backend_api.py" "$DST/services/"
cp "$SRC/services/config.py"             "$DST/services/"
cp "$SRC/services/proxy_service.py"      "$DST/services/"
cp "$SRC/services/protocol/conversation.py" "$DST/services/protocol/"
cp "$SRC/services/__init__.py"           "$DST/services/" 2>/dev/null || touch "$DST/services/__init__.py"
touch "$DST/services/protocol/__init__.py"
for f in pow.py sentinel.py turnstile.py helper.py image_tokens.py log.py pkce.py __init__.py; do
  cp "$SRC/utils/$f" "$DST/utils/" 2>/dev/null || touch "$DST/utils/$f"
done
touch "$DST/__init__.py"
```

- [ ] **Step 2: Write NOTICE attribution**

```
This project vendors code from chatgpt2api (https://github.com/basketikun/chatgpt2api)
Copyright (c) 2026 kunkun — MIT License.
Vendored files live under src/cgimg/_vendor/ and retain their original behavior.
```

- [ ] **Step 3: Write _vendor_path.py**

```python
"""Prepend the vendored package root to sys.path so the vendored chatgpt2api
code can keep its original absolute imports (`import services.*`, `import utils.*`).
Importing this module once (side effect) is enough."""
import sys
from pathlib import Path

_VENDOR_ROOT = str(Path(__file__).resolve().parent / "_vendor")
if _VENDOR_ROOT not in sys.path:
    sys.path.insert(0, _VENDOR_ROOT)
```

- [ ] **Step 4: Inventory vendored imports that reference dropped modules**

Run: `grep -rn "from services" "/f/chatgpt-image-mcp/src/cgimg/_vendor" | grep -v "account_service\|config\|proxy_service\|protocol"`
Expected: capture any import of a service module we did NOT vendor (e.g. `image_task_service`, `content_filter`). Record the list — these get stubbed or the referencing code path is image-irrelevant. Do the same for `from utils` referencing un-vendored utils.

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp
git add -A && git commit -m "feat: vendor chatgpt2api image-gen engine (MIT)"
```

---

## Task 3: Single-account shim for account_service

**Files:**
- Create: `src/cgimg/_vendor/services/account_service.py` (the shim, replaces original)
- Read for context: `F:\1111111. Chatgpt2api\services\account_service.py` (find exact method signatures called by `openai_backend_api.py` and `conversation.py`)

- [ ] **Step 1: Find every account_service call site in vendored code**

Run: `grep -rn "account_service\." "/f/chatgpt-image-mcp/src/cgimg/_vendor"`
Expected: a finite list of `account_service.<method>(...)` calls. The shim must implement exactly these. Likely set: `get_available_access_token`, `get_account`, `refresh_access_token`, `mark_image_result`, `remove_invalid_token`. Confirm and note any extras.

- [ ] **Step 2: Write the shim**

```python
"""Single-account drop-in replacing chatgpt2api's multi-account pool.
Backed by a token store provided at runtime via set_token_provider().
Only implements the methods the vendored engine actually calls."""
from __future__ import annotations
from typing import Any, Callable, Optional

_provider: Optional[Callable[[], str]] = None        # returns a fresh access_token
_refresher: Optional[Callable[[bool], str]] = None    # (force) -> new access_token


def set_token_provider(get_token: Callable[[], str], refresh: Callable[[bool], str]) -> None:
    global _provider, _refresher
    _provider = get_token
    _refresher = refresh


class _AccountService:
    def get_available_access_token(self) -> str:
        if _provider is None:
            raise RuntimeError("cgimg: not logged in. Run `cgimg login` first.")
        return _provider()

    def get_account(self, token: str) -> dict[str, Any]:
        return {"access_token": token}

    def refresh_access_token(self, access_token: str, *, force: bool = False,
                             event: str = "refresh") -> str:
        if _refresher is None:
            raise RuntimeError("cgimg: no refresher configured")
        return _refresher(force)

    def mark_image_result(self, *args: Any, **kwargs: Any) -> None:
        return None  # no-op: single account, no quota bookkeeping

    def remove_invalid_token(self, token: str, *args: Any, **kwargs: Any) -> None:
        return None  # no-op: surfaced as error to user instead

    def __getattr__(self, name: str):
        # Defensive: any unforeseen method becomes a no-op returning None,
        # so a missed call site degrades gracefully rather than crashing.
        def _noop(*a: Any, **k: Any):
            return None
        return _noop


account_service = _AccountService()
```

- [ ] **Step 3: Reconcile shim methods with Step 1 findings**

If Step 1 found methods not covered above (other than the `__getattr__` catch-all), add explicit implementations. Any method whose return value the engine USES (not just calls) must return something valid — verify each non-noop call site.

- [ ] **Step 4: Verify vendored engine imports cleanly**

```python
# tests/test_vendor_import.py
import cgimg._vendor_path  # noqa: F401  (side effect: sys.path)


def test_backend_api_imports():
    import importlib
    mod = importlib.import_module("services.openai_backend_api")
    assert hasattr(mod, "OpenAIBackendAPI")


def test_conversation_imports():
    import importlib
    mod = importlib.import_module("services.protocol.conversation")
    assert hasattr(mod, "stream_image_outputs")
```

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_vendor_import.py -v`
Expected: PASS. If ImportError on a dropped module, stub it under `_vendor/services/` as a minimal no-op module (image-irrelevant paths only) and re-run.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: single-account shim for vendored account_service"
```

---

## Task 4: Token store + refresh (auth/tokens.py)

**Files:**
- Create: `src/cgimg/auth/__init__.py`, `src/cgimg/auth/tokens.py`
- Test: `tests/test_tokens.py`

- [ ] **Step 1: Write failing test for store round-trip + path**

```python
# tests/test_tokens.py
import json
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
```

- [ ] **Step 2: Run, expect fail**

Run: `uv run pytest tests/test_tokens.py -v`
Expected: FAIL (module/attr missing).

- [ ] **Step 3: Implement tokens.py**

```python
"""Single-account token store + refresh against OpenAI's OAuth endpoint."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import cgimg._vendor_path  # noqa: F401
from curl_cffi import requests

_CLIENT_ID = "app_2SKx67EdpoN0G6j64rFvigXD"
_TOKEN_URL = "https://auth.openai.com/oauth/token"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")
# Refresh if the stored access_token is older than this (seconds). 12h < 24h keepalive.
_REFRESH_AFTER = 12 * 3600


def _config_dir() -> Path:
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    return Path(base) / "cgimg"


def _auth_path() -> Path:
    return _config_dir() / "auth.json"


def save(tok: dict[str, Any]) -> None:
    p = _auth_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tok = {**tok, "saved_at": time.time()}
    p.write_text(json.dumps(tok, indent=2), encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def load() -> Optional[dict[str, Any]]:
    p = _auth_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _refresh_request(refresh_token: str) -> dict[str, str]:
    resp = requests.post(
        _TOKEN_URL,
        headers={"Accept": "application/json",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": _UA},
        data={"grant_type": "refresh_token",
              "refresh_token": refresh_token,
              "client_id": _CLIENT_ID},
        timeout=60,
    )
    data = resp.json() if resp.text else {}
    if resp.status_code != 200 or not data.get("access_token"):
        raise RuntimeError(f"token refresh failed (HTTP {resp.status_code})")
    return data


def get_access_token(force: bool = False) -> str:
    """Return a valid access_token, refreshing if stale or forced.
    Raises RuntimeError if not logged in."""
    tok = load()
    if tok is None:
        raise RuntimeError("not logged in — run `cgimg login`")
    stale = (time.time() - tok.get("saved_at", 0)) > _REFRESH_AFTER
    if force or stale:
        if not tok.get("refresh_token"):
            raise RuntimeError("no refresh_token stored — run `cgimg login` again")
        new = _refresh_request(tok["refresh_token"])
        tok = {**tok, **new}
        save(tok)
    return tok["access_token"]


def login_status() -> dict[str, Any]:
    tok = load()
    if tok is None:
        return {"authed": False}
    return {"authed": True,
            "has_refresh": bool(tok.get("refresh_token")),
            "saved_at": tok.get("saved_at")}
```

- [ ] **Step 4: Run tests, expect pass**

Run: `uv run pytest tests/test_tokens.py -v`
Expected: PASS (network-free tests only).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: single-account token store + refresh"
```

---

## Task 5: Terminal OAuth login (auth/oauth_login.py + cli login)

**Files:**
- Create: `src/cgimg/auth/oauth_login.py`, `src/cgimg/cli.py`
- Read for context: `F:\1111111. Chatgpt2api\services\oauth_login_service.py` (the PKCE flow to adapt), `F:\1111111. Chatgpt2api\utils\pkce.py`

- [ ] **Step 1: Write oauth_login.py (adapted, terminal variant)**

Adapt `oauth_login_service.py` to a synchronous terminal flow (no session dict needed — one shot). Use vendored `utils.pkce.generate_pkce`.

```python
"""Terminal OAuth (PKCE) login against OpenAI. One-shot, no web session store."""
from __future__ import annotations
import secrets
import uuid
import webbrowser
from urllib.parse import parse_qs, urlencode, urlparse

import cgimg._vendor_path  # noqa: F401
from curl_cffi import requests
from utils.pkce import generate_pkce  # vendored

_AUTH_BASE = "https://auth.openai.com"
_PLATFORM = "https://platform.openai.com"
_CLIENT_ID = "app_2SKx67EdpoN0G6j64rFvigXD"
_REDIRECT = f"{_PLATFORM}/auth/callback"
_AUDIENCE = "https://api.openai.com/v1"
_AUTH0_CLIENT = "eyJuYW1lIjoiYXV0aDAtc3BhLWpzIiwidmVyc2lvbiI6IjEuMjEuMCJ9"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")


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


def interactive_login() -> dict[str, str]:
    url, verifier = build_authorize_url()
    print("\n1. Opening browser to log into ChatGPT...")
    print("   If it doesn't open, paste this URL manually:\n")
    print("   " + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print("2. After login you'll land on a platform.openai.com page (may say 'Oops').")
    print("   Copy the FULL URL from the address bar (it has ?code=...&state=...).\n")
    callback = input("3. Paste the callback URL here: ").strip()
    code = extract_code(callback)
    tokens = exchange_code(code, verifier)
    print("\n[OK] Login successful.")
    return tokens
```

- [ ] **Step 2: Write cli.py with `login` subcommand**

```python
"""cgimg CLI: login / gen / ppt."""
from __future__ import annotations
import argparse
import sys


def _cmd_login(args: argparse.Namespace) -> int:
    from cgimg.auth import oauth_login, tokens
    tok = oauth_login.interactive_login()
    tokens.save(tok)
    print(f"Saved to {tokens._auth_path()}")
    return 0


def _cmd_gen(args: argparse.Namespace) -> int:
    from cgimg.engine.generate import generate_image
    paths = generate_image(args.prompt, aspect=args.aspect, n=args.n, out_dir=args.out)
    for p in paths:
        print(p)
    return 0


def _cmd_ppt(args: argparse.Namespace) -> int:
    from cgimg.ppt.builder import build_pptx
    out = build_pptx(args.images, args.out, aspect=args.aspect)
    print(out)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cgimg")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login").set_defaults(func=_cmd_login)

    g = sub.add_parser("gen")
    g.add_argument("prompt")
    g.add_argument("--aspect", default="16:9")
    g.add_argument("--n", type=int, default=1)
    g.add_argument("--out", default="out")
    g.set_defaults(func=_cmd_gen)

    pp = sub.add_parser("ppt")
    pp.add_argument("images", nargs="+")
    pp.add_argument("--out", default="deck.pptx")
    pp.add_argument("--aspect", default="16:9")
    pp.set_defaults(func=_cmd_ppt)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Manual smoke test — login round-trip**

Run: `cd /f/chatgpt-image-mcp && uv run cgimg login`
Follow prompts (reuse the ChatGPT account already used this session). 
Expected: `auth.json` created at `%APPDATA%\cgimg\auth.json` containing access_token + refresh_token. Verify: `uv run python -c "from cgimg.auth import tokens; print(tokens.login_status())"` → `{'authed': True, ...}`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: terminal OAuth login + cli login command"
```

---

## Task 6: FEASIBILITY SPIKE — one image end-to-end (engine/generate.py)

> **This is the make-or-break task.** It proves the vendored engine + shim + tokens produce a real image headlessly. If PoW or the streaming path fails standalone, stop and diagnose before building further.

**Files:**
- Create: `src/cgimg/engine/__init__.py`, `src/cgimg/engine/generate.py`, `src/cgimg/sizes.py`
- Read for context: `F:\1111111. Chatgpt2api\services\protocol\conversation.py` (find exact signature of `stream_image_outputs` / the `ConversationRequest` dataclass / what `conversation_events` yields and how image bytes/urls are returned).

- [ ] **Step 1: Write sizes.py with TDD test first**

```python
# tests/test_sizes.py
import pytest
from cgimg.sizes import resolve_size


def test_known_aspects():
    assert resolve_size("16:9") == "1920x1080"
    assert resolve_size("1:1") == "1024x1024"
    assert resolve_size("3:4") == "1024x1536"
    assert resolve_size("9:16") == "1080x1920"


def test_raw_passthrough():
    assert resolve_size("1280x720") == "1280x720"


def test_unknown_raises():
    with pytest.raises(ValueError):
        resolve_size("banana")
```

Run: `uv run pytest tests/test_sizes.py -v` → FAIL.

- [ ] **Step 2: Implement sizes.py**

```python
"""Map a friendly aspect ratio to the size string ChatGPT honors.
ChatGPT normalizes to its own native dims; the RATIO is what matters."""
from __future__ import annotations
import re

_ASPECTS = {
    "16:9": "1920x1080",
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "9:16": "1080x1920",
}
_RAW = re.compile(r"^\d{2,5}x\d{2,5}$")


def resolve_size(aspect: str) -> str:
    a = aspect.strip().lower().replace(" ", "")
    if a in _ASPECTS:
        return _ASPECTS[a]
    if _RAW.match(a):
        return a
    raise ValueError(f"unknown aspect {aspect!r}; use one of {list(_ASPECTS)} or WxH")
```

Run: `uv run pytest tests/test_sizes.py -v` → PASS.

- [ ] **Step 3: Inspect the real conversation.py signatures**

Run: `grep -n "def stream_image_outputs\|class ConversationRequest\|def conversation_events\|def stream_image_outputs_with_pool" "/f/1111111. Chatgpt2api/services/protocol/conversation.py"`
Read those functions. Note: the exact fields of `ConversationRequest`, what `stream_image_outputs(backend, request, index, total)` returns/yields, and how a finished image is represented (b64 vs url, key names). The generate.py below assumes a helper — adjust to the real API.

- [ ] **Step 4: Write generate.py (adapter, bypass pool)**

```python
"""Adapter: take our single-account token, build the vendored backend, and
drive the low-level image-output stream (bypassing the multi-account pool)."""
from __future__ import annotations
import base64
import time
from pathlib import Path

import cgimg._vendor_path  # noqa: F401
from cgimg.sizes import resolve_size
from cgimg.auth import tokens
from services.account_service import set_token_provider  # our shim

# Wire the shim to our token store BEFORE the engine asks for a token.
set_token_provider(
    get_token=lambda: tokens.get_access_token(force=False),
    refresh=lambda force: tokens.get_access_token(force=True),
)

from services.openai_backend_api import OpenAIBackendAPI            # noqa: E402
from services.protocol import conversation as conv                  # noqa: E402


def _save_outputs(outputs, out_dir: Path, stem: str) -> list[str]:
    """Persist returned image outputs to PNG files. `outputs` shape comes from
    Step 3 inspection — handle both b64_json and url forms."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for i, item in enumerate(outputs, start=1):
        p = out_dir / f"{stem}-{i}.png"
        b64 = item.get("b64_json") if isinstance(item, dict) else None
        url = item.get("url") if isinstance(item, dict) else None
        if b64:
            p.write_bytes(base64.b64decode(b64))
        elif url:
            from curl_cffi import requests
            p.write_bytes(requests.get(url, timeout=120).content)
        else:
            raise RuntimeError(f"unrecognized output item: {item!r}")
        paths.append(str(p))
    return paths


def generate_image(prompt: str, aspect: str = "16:9", n: int = 1,
                   out_dir: str = "out") -> list[str]:
    size = resolve_size(aspect)
    token = tokens.get_access_token()
    backend = OpenAIBackendAPI(access_token=token)

    # Build the request object the vendored code expects (fields from Step 3).
    request = conv.ConversationRequest(prompt=prompt, model="gpt-image-2",
                                       size=size, quality="auto", n=n)
    # Drive the low-level stream. Real return shape confirmed in Step 3.
    outputs = conv.stream_image_outputs(backend, request, 0, n)
    stem = f"img-{int(time.time())}"
    return _save_outputs(list(outputs), Path(out_dir), stem)
```

> NOTE: `ConversationRequest` field names and `stream_image_outputs` return shape MUST be reconciled with Step 3. If the only clean entry is `stream_image_outputs_with_pool`, prefer calling the pool wrapper (the shim's `get_available_access_token` already returns our token) and drop the manual backend construction.

- [ ] **Step 5: Run the spike**

Run: `cd /f/chatgpt-image-mcp && uv run cgimg gen "a cute astronaut cat, simple" --aspect 16:9 --out out`
Expected: one PNG in `out/`, dimensions ~1672×941. Verify dims:
`uv run python -c "from PIL import Image; im=Image.open('out/'+__import__('os').listdir('out')[0]); print(im.size)"`

- [ ] **Step 6: If it fails — diagnose, do not paper over**

Common failure modes and where to look:
- `InvalidAccessTokenError` → token not wired; check `set_token_provider` ordering / shim.
- PoW/sentinel error → inspect `utils/pow.py` bootstrap; confirm `_bootstrap()` HTML parse succeeded (network ok, no proxy needed).
- ImportError of a dropped module → stub it under `_vendor/services/`.
- Empty outputs / poll timeout → confirm the return-shape assumptions from Step 3 are right.
Fix root cause, re-run Step 5 until a real image is produced.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: image generation engine (feasibility spike passing)"
```

---

## Task 7: PPT builder (ppt/builder.py)

**Files:**
- Create: `src/cgimg/ppt/__init__.py`, `src/cgimg/ppt/builder.py`
- Test: `tests/test_ppt_builder.py`, `tests/assets/` (generate 2 sample PNGs in the test)

- [ ] **Step 1: Write failing test**

```python
# tests/test_ppt_builder.py
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches
from cgimg.ppt.builder import build_pptx


def _sample_png(p: Path, w=1672, h=941):
    Image.new("RGB", (w, h), (26, 58, 140)).save(p)


def test_build_169_deck(tmp_path):
    imgs = []
    for i in range(2):
        ip = tmp_path / f"s{i}.png"
        _sample_png(ip)
        imgs.append(str(ip))
    out = tmp_path / "deck.pptx"
    result = build_pptx(imgs, str(out), aspect="16:9")
    assert Path(result).exists()
    prs = Presentation(result)
    assert len(prs.slides) == 2
    # 16:9 slide size
    assert round(prs.slide_width / Inches(1), 2) == 13.33
    assert round(prs.slide_height / Inches(1), 2) == 7.5
```

Run: `uv run pytest tests/test_ppt_builder.py -v` → FAIL.

- [ ] **Step 2: Implement builder.py**

```python
"""Assemble image files into a full-bleed PPTX. Image aspect should match the
slide aspect (16:9 → 1672x941 images) for edge-to-edge with no bars/crop."""
from __future__ import annotations
import os
from pptx import Presentation
from pptx.util import Inches

# Slide dimensions (inches) per aspect.
_SLIDE_DIMS = {
    "16:9": (13.333, 7.5),
    "1:1": (7.5, 7.5),
    "3:4": (7.5, 10.0),
    "9:16": (7.5, 13.333),
}


def build_pptx(image_paths: list[str], out_path: str, aspect: str = "16:9") -> str:
    if not image_paths:
        raise ValueError("no images provided")
    dims = _SLIDE_DIMS.get(aspect.strip().lower())
    if dims is None:
        raise ValueError(f"unsupported ppt aspect {aspect!r}; use {list(_SLIDE_DIMS)}")
    w_in, h_in = dims

    prs = Presentation()
    prs.slide_width = Inches(w_in)
    prs.slide_height = Inches(h_in)
    blank = prs.slide_layouts[6]

    for img in image_paths:
        if not os.path.exists(img):
            raise FileNotFoundError(img)
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(img, 0, 0, prs.slide_width, prs.slide_height)

    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    prs.save(out_path)
    return out_path
```

Run: `uv run pytest tests/test_ppt_builder.py -v` → PASS.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: pptx deck builder"
```

---

## Task 8: MCP server (server.py)

**Files:**
- Create: `src/cgimg/server.py`
- Read for context: FastMCP usage in the installed `mcp` package (`python -c "import mcp; print(mcp.__file__)"`); confirm `from mcp.server.fastmcp import FastMCP` and `mcp.run()` stdio API.

- [ ] **Step 1: Confirm FastMCP API**

Run: `uv run python -c "from mcp.server.fastmcp import FastMCP; print('ok')"`
Expected: `ok`. If import path differs, adjust below to the installed version's API.

- [ ] **Step 2: Write server.py**

```python
"""FastMCP stdio server exposing cgimg tools."""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chatgpt-image")


@mcp.tool()
def login_status() -> dict:
    """Check whether a ChatGPT account is logged in for image generation."""
    from cgimg.auth import tokens
    return tokens.login_status()


@mcp.tool()
def generate_image(prompt: str, aspect: str = "16:9", n: int = 1,
                   out_dir: str = "out") -> dict:
    """Generate image(s) from a text prompt at the given aspect ratio
    (16:9, 1:1, 3:4, 9:16, or WxH). Returns saved PNG file paths."""
    from cgimg.engine.generate import generate_image as _gen
    return {"paths": _gen(prompt, aspect=aspect, n=n, out_dir=out_dir)}


@mcp.tool()
def build_pptx(image_paths: list[str], out_path: str = "deck.pptx",
               aspect: str = "16:9") -> dict:
    """Assemble existing image files into a full-bleed PowerPoint deck."""
    from cgimg.ppt.builder import build_pptx as _build
    return {"path": _build(image_paths, out_path, aspect=aspect)}


@mcp.tool()
def generate_slide_deck(prompts: list[str], aspect: str = "16:9",
                        out_pptx: str = "deck.pptx", out_dir: str = "out") -> dict:
    """Generate one image per prompt then assemble them into a PPTX deck."""
    from cgimg.engine.generate import generate_image as _gen
    from cgimg.ppt.builder import build_pptx as _build
    images: list[str] = []
    for i, pr in enumerate(prompts, start=1):
        images.extend(_gen(pr, aspect=aspect, n=1, out_dir=out_dir))
    path = _build(images, out_pptx, aspect=aspect)
    return {"path": path, "image_paths": images}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke test server starts**

Run: `cd /f/chatgpt-image-mcp && timeout 5 uv run cgimg-mcp < /dev/null; echo "exit=$?"`
Expected: starts on stdio without import errors (will exit on closed stdin). No traceback.

- [ ] **Step 4: Register + verify in Claude Code**

Add to MCP config (document exact path in README):
```json
{ "mcpServers": { "chatgpt-image": {
  "command": "uv", "args": ["run","cgimg-mcp"],
  "cwd": "F:\\chatgpt-image-mcp" } } }
```
Verify the tools appear and `login_status` returns `{authed: true}`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: FastMCP server with 4 tools"
```

---

## Task 9: README + final polish

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Include: one-line description; the chatgpt2api disclaimer (ban risk, ToS, throwaway accounts); install (`git clone`, `uv sync`, `uv run cgimg login`); MCP registration JSON for Claude Code / Codex / Antigravity; tool reference table; aspect ratio table; CLI usage examples (`cgimg gen`, `cgimg ppt`); attribution to chatgpt2api (MIT); troubleshooting (not-logged-in, token expiry, PoW failures).

- [ ] **Step 2: Full test suite green**

Run: `cd /f/chatgpt-image-mcp && uv run pytest -v`
Expected: all offline tests PASS.

- [ ] **Step 3: End-to-end manual check**

Run: `uv run python -c "from cgimg.engine.generate import generate_image as g; from cgimg.ppt.builder import build_pptx as b; ps=[]; 
import itertools" ` — then via CLI: generate 2 images and build a deck; open the pptx and confirm full-bleed 16:9, no bars.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: README, disclaimer, install + usage"
```

---

## Self-Review (completed)

**Spec coverage:** login (T5) ✓, login_status (T8) ✓, generate_image + aspect (T6) ✓, build_pptx (T7) ✓, generate_slide_deck (T8) ✓, token store+refresh (T4) ✓, install story (T1,T9) ✓, vendoring + MIT notice (T2) ✓, risk #1 PoW/Turnstile validated (T6 spike) ✓.

**Placeholder scan:** generate.py (T6 Step 4) intentionally depends on Step 3 inspection of real `ConversationRequest`/`stream_image_outputs` shapes — flagged explicitly, not a hidden TODO. All other code blocks are complete.

**Type consistency:** `tokens.get_access_token(force)` used consistently in T4/T5/T6; `resolve_size` (T6) used in generate.py; `build_pptx(image_paths, out_path, aspect)` signature consistent across T7/T8; shim `set_token_provider(get_token, refresh)` matches the wiring in generate.py T6.

**Known soft spot:** Task 6 is a genuine spike — exact vendored API (ConversationRequest fields, output shape, whether to use pool wrapper vs manual backend) is confirmed at Step 3 by reading source, and the code adapts to findings. This is by design for vendored-code integration.
