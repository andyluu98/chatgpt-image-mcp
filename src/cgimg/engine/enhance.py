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

# "slide" style — encodes a clean, editorial, "just enough" presentation-slide
# aesthetic (light/airy, restrained accent, one hero visual, short labels, fixed
# header/footer frame). Mirrors a professionally designed Figma/Canva deck rather
# than a cluttered AI infographic.
_SLIDE_SYSTEM = (
    "You are an expert presentation designer. Turn the user's slide content into ONE "
    "image-generation prompt describing a single CLEAN, EDITORIAL 16:9 presentation slide. "
    "Follow these design rules strictly:\n"
    "- LIGHT & AIRY: white or soft cream background with a very subtle accent-colored "
    "watercolor wash in one or two corners and faint minimal motifs. NOT dark, no heavy "
    "gradients, never crowded.\n"
    "- RESTRAINED COLOR: dark navy as the default text color; ONE warm accent color used "
    "sparingly — to highlight just ONE key phrase in the title and for small accents. Avoid "
    "saturated rainbow palettes. At most one soft secondary tint for a hero object.\n"
    "- TITLE: large and clear, with only ONE key phrase colored in the accent; one short "
    "subtitle below with a small colored tick/bar.\n"
    "- CONTENT: organize into AT MOST 4-6 concise items, or two balanced groups/columns. "
    "Each item = a simple line icon + a SHORT label (2-6 words). NEVER dense paragraphs, "
    "never 10+ item grids, never tiny text. If the source has many points, GROUP or condense.\n"
    "- ONE HERO VISUAL: a single soft glossy 3D illustration (e.g. a crystal, brain, network "
    "node, or a relevant object) as a central or side anchor, with a gentle glow — subtle, "
    "not overpowering. Use it to fill space elegantly instead of extra cards.\n"
    "- FRAME: a small 'Slide' label/pill in a top corner and a slim one-line takeaway banner "
    "(soft pill + small icon + one short insight, one keyword in the accent color) at the bottom.\n"
    "- GENEROUS WHITESPACE, strong visual hierarchy, balanced, sophisticated, modern — looks "
    "like a professionally designed deck, NOT an AI-cluttered infographic.\n"
    "- FIDELITY: keep the user's exact wording, labels, and language (Vietnamese with correct "
    "diacritics). Do NOT invent filler sections, fake statistics, or extra cards beyond the "
    "given content.\n"
    "Output ONLY the final image-generation prompt — no preamble, no quotes, no explanation."
)

_TEMPLATE = (
    "{p}. Render as a dense, professional infographic: bold title, 4-6 labelled "
    "sections with clean line icons, a horizontal process/flow diagram, consistent "
    "modern color theme, generous spacing, high-end corporate look. Keep any text in "
    "the same language as the request with correct diacritics. Crisp, detailed, no gibberish text."
)

_SLIDE_TEMPLATE = (
    "{p}. Render as ONE clean, editorial 16:9 presentation slide: light cream/white "
    "background with a subtle accent-color wash in the corners; dark navy text with ONE "
    "warm accent color highlighting a single key phrase in the title; at most 4-6 concise "
    "items each with a simple line icon and a short 2-6 word label (no dense paragraphs, no "
    "tiny text); one soft glossy 3D hero illustration as the anchor; a small slide-number "
    "pill in a top corner and a slim one-line takeaway banner at the bottom; generous "
    "whitespace, strong hierarchy, sophisticated and uncluttered. Keep all text in the "
    "request's language with correct diacritics; do not invent extra content."
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


def _template_enhance(prompt: str, brand_clause: str = "", style: str = "auto") -> str:
    base = _SLIDE_TEMPLATE if style == "slide" else _TEMPLATE
    out = base.format(p=prompt.strip())
    if brand_clause:
        out = f"{out} {brand_clause}"
    return out


def enhance_prompt(prompt: str, *, text_model: str = "gpt-5",
                   brand_colors: list[str] | None = None,
                   reserve_corner: str | None = None,
                   style: str = "auto") -> str:
    """Return an expanded prompt. Never raises — falls back to template on any error.

    style="slide" applies a clean editorial presentation-slide aesthetic and ALWAYS
    enhances (the >=280-char skip is bypassed) so even detailed slide content gets the
    designer treatment. When brand_colors/reserve_corner are provided, brand
    instructions are appended and enhancement also always runs.
    """
    p = prompt.strip()
    brand_clause = _brand_clause(brand_colors, reserve_corner)
    has_brand = bool(brand_clause)
    is_slide = style == "slide"

    # Skip only for the generic "auto" style with no brand context on long prompts.
    if not is_slide and not has_brand and len(p) >= _LONG_PROMPT_CHARS:
        return p
    try:
        # Local imports: keep the vendored engine import lazy + after env/sys.path setup.
        from cgimg.auth import tokens
        from services.openai_backend_api import OpenAIBackendAPI
        from services.protocol.conversation import ConversationRequest, stream_text_deltas
        backend = OpenAIBackendAPI(access_token=tokens.get_access_token())
        system = _SLIDE_SYSTEM if is_slide else _SYSTEM
        if brand_clause:
            system = f"{system} {brand_clause}"
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
    return _template_enhance(p, brand_clause, style)
