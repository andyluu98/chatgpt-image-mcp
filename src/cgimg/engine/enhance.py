"""Expand a short prompt into a rich, detailed image-generation prompt, using
the same ChatGPT account's text path (mirrors what the web UI does silently).
Falls back to a deterministic template wrapper if the text call fails."""
from __future__ import annotations

import os

# The vendored config.py instantiates a ConfigStore at IMPORT time and raises
# if no auth-key is set. Satisfy it before any vendored import (those imports
# are inside enhance_prompt, but enhance.py may be imported standalone).
os.environ.setdefault("CHATGPT2API_AUTH_KEY", "cgimg-local")
import cgimg._vendor_path  # noqa: F401  (side-effect: prepends _vendor to sys.path)

# Skip enhancement when the user already wrote a detailed prompt.
_LONG_PROMPT_CHARS = 280

_SYSTEM = (
    "You are a prompt engineer for an image-generation model. Rewrite the user's "
    "short request into ONE single, richly detailed image-generation prompt. "
    "If the request is a concept/topic, design a dense professional INFOGRAPHIC: a bold "
    "title, 4-6 labelled sections with icons, a step/flow diagram, a consistent modern "
    "color theme, clean layout. If it names a real scene, write a vivid photographic "
    "prompt instead. Preserve the user's language for any text that should appear in the "
    "image (e.g. keep Vietnamese text in Vietnamese, with correct diacritics). "
    "Output ONLY the final prompt text — no preamble, no quotes, no explanation."
)

_TEMPLATE = (
    "{p}. Render as a dense, professional infographic: bold title, 4-6 labelled "
    "sections with clean line icons, a horizontal process/flow diagram, consistent "
    "modern color theme, generous spacing, high-end corporate look. Keep any text in "
    "the same language as the request with correct diacritics. Crisp, detailed, no gibberish text."
)


def _brand_clause(brand_colors: list[str] | None, reserve_corner: str | None) -> str:
    """Build the extra instruction text appended for brand context (may be empty)."""
    parts: list[str] = []
    if brand_colors:
        parts.append(
            "Use EXACTLY this brand color palette and no other dominant colors: "
            f"{', '.join(brand_colors)}. Apply them to the background, accents, "
            "and typography."
        )
    if reserve_corner:
        parts.append(
            f"Leave the {reserve_corner} corner area visually clear/empty — a logo "
            "will be placed there. Do NOT draw any logo, wordmark, brand name, or "
            "company text yourself anywhere in the image."
        )
    return " ".join(parts)


def _template_enhance(prompt: str, brand_clause: str = "") -> str:
    out = _TEMPLATE.format(p=prompt.strip())
    if brand_clause:
        out = f"{out} {brand_clause}"
    return out


def enhance_prompt(prompt: str, *, text_model: str = "gpt-5",
                   brand_colors: list[str] | None = None,
                   reserve_corner: str | None = None) -> str:
    """Return an expanded prompt. Never raises — falls back to template on any error.

    When brand_colors and/or reserve_corner are provided, brand instructions are
    appended and enhancement ALWAYS runs (the >=280-char skip applies only when no
    brand context is requested, so the brand rules always take effect).
    """
    p = prompt.strip()
    brand_clause = _brand_clause(brand_colors, reserve_corner)
    has_brand = bool(brand_clause)

    # Skip only when there is no brand context and the prompt is already detailed.
    if not has_brand and len(p) >= _LONG_PROMPT_CHARS:
        return p
    try:
        # Local imports: keep the vendored engine import lazy + after env/sys.path setup.
        from cgimg.auth import tokens
        from services.openai_backend_api import OpenAIBackendAPI
        from services.protocol.conversation import ConversationRequest, stream_text_deltas
        backend = OpenAIBackendAPI(access_token=tokens.get_access_token())
        system = _SYSTEM if not brand_clause else f"{_SYSTEM} {brand_clause}"
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": p},
        ]
        req = ConversationRequest(model=text_model, messages=messages)
        out = "".join(stream_text_deltas(backend, req)).strip()
        # Guard against empty / junk / accidental refusal.
        if len(out) >= 40:
            return out
    except Exception:
        pass
    return _template_enhance(p, brand_clause)
