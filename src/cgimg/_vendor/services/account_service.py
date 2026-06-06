"""Single-account drop-in replacing chatgpt2api's multi-account pool.
Backed by a token provider wired at runtime via set_token_provider().
Only implements the methods the vendored engine actually calls.

Call sites covered (grep of src/cgimg/_vendor):
  IMAGE PATH (must work — return value consumed):
    - conversation.py:1246 get_available_access_token(plan_type=, source_type=, plan_types=)
        -> returns the single token string. Accepts/ignores the pool-selection
           kwargs since we have exactly one account.
    - conversation.py:1257 / openai_backend_api.py:161,544,749 get_account(token)
        -> code does `... or {}` then `.get("email"/"source_type"/"type")`,
           so we return a dict with the token; missing keys resolve to "".
    - openai_backend_api.py:750 _decode_jwt_payload(token)
        -> code does `.get(...)` on the result, so it MUST be a dict. We decode
           the JWT body best-effort; on any failure return {} (the engine guards
           every access with .get / isinstance, so {} is safe).
  TEXT PATH (not image-gen; only hit if text streaming is used):
    - conversation.py:675 get_text_access_token() / :706 (attempted_tokens)
        -> returns the single token string.
    - conversation.py:696 mark_text_used(token) -> no-op (return unused).
  SIDE-EFFECT ONLY (return value never consumed -> no-op None is safe):
    - mark_image_result(token, bool)            conversation.py:1289..1392
    - refresh_access_token(token, force=, event=) conversation.py:701,1402 /
                                                   openai_backend_api refresh
    - remove_invalid_token(token, reason)       conversation.py:705,1406
  Any other attribute -> catch-all no-op (covers pool/registration helpers
  that are off the image-generation path).
"""
from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Callable, Optional

_provider: Optional[Callable[[], str]] = None
_refresher: Optional[Callable[[bool], str]] = None


def set_token_provider(get_token: Callable[[], str], refresh: Callable[[bool], str]) -> None:
    global _provider, _refresher
    _provider = get_token
    _refresher = refresh


def _current_token() -> str:
    if _provider is None:
        raise RuntimeError("cgimg: not logged in. Run `cgimg login` first.")
    return _provider()


class _AccountService:
    # --- image path: token selection ----------------------------------------
    def get_available_access_token(self, *args: Any, **kwargs: Any) -> str:
        # Pool-selection kwargs (plan_type, source_type, plan_types) are ignored:
        # cgimg has a single account, so there is nothing to select among.
        return _current_token()

    # --- text path: token selection ------------------------------------------
    def get_text_access_token(self, *args: Any, **kwargs: Any) -> str:
        return _current_token()

    # --- account lookup (return value consumed via .get) ---------------------
    def get_account(self, token: str) -> dict[str, Any]:
        # Engine reads optional keys (email/source_type/type) defensively with
        # .get(); a minimal dict is enough.
        return {"access_token": token}

    def _decode_jwt_payload(self, token: str) -> dict[str, Any]:
        # Must return a dict — engine calls .get(...) on the result. Best-effort
        # base64url decode of the JWT payload segment; {} on any failure.
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}
            payload_b64 = parts[1]
            padding = "=" * (-len(payload_b64) % 4)
            decoded = base64.urlsafe_b64decode(payload_b64 + padding)
            data = json.loads(decoded)
            return data if isinstance(data, dict) else {}
        except (ValueError, binascii.Error, json.JSONDecodeError):
            return {}

    # --- token refresh (return value not consumed by engine) -----------------
    def refresh_access_token(self, access_token: str, *, force: bool = False,
                             event: str = "refresh") -> str:
        if _refresher is None:
            raise RuntimeError("cgimg: no refresher configured")
        return _refresher(force)

    # --- pure side-effect calls (return value never used) --------------------
    def mark_image_result(self, *args: Any, **kwargs: Any) -> None:
        return None

    def mark_text_used(self, *args: Any, **kwargs: Any) -> None:
        return None

    def remove_invalid_token(self, token: str, *args: Any, **kwargs: Any) -> None:
        return None

    # --- catch-all for off-path pool/registration helpers --------------------
    def __getattr__(self, name: str):
        def _noop(*a: Any, **k: Any):
            return None
        return _noop


account_service = _AccountService()
