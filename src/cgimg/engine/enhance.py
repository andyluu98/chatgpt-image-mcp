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

# Shared CONTENT rules for slide styles — balance completeness vs density:
# a finished, informative slide (each point gets a one-line description + a relevant
# supporting element), that intelligently completes sparse input, stays MEDIUM density
# (not a wall of text, not nearly-empty), and never fabricates fake stats.
_CONTENT_RULES = (
    "CONTENT (complete & balanced — this is critical):\n"
    "- Present the given content FULLY. For EACH main point, add a short one-line supporting "
    "description (~6-14 words) so the slide is informative and feels like a finished "
    "professional infographic, not a bare list.\n"
    "- Where it fits the topic, add ONE relevant supporting element to make the slide feel "
    "complete — e.g. a row of 4-6 application/benefit chips, or a small stat/dashboard card, "
    "or a short takeaway line.\n"
    "- If the user's input is SPARSE, intelligently COMPLETE it into a full, sensible slide on "
    "that topic (reasonable points + descriptions).\n"
    "- Aim for MEDIUM density: informative and complete, NOT a wall of tiny text and NOT "
    "nearly-empty. Typically 3-6 main items, each = icon + short label + one-line description. "
    "Keep all text clearly legible.\n"
    "- Do NOT fabricate precise statistics, fake numbers, brand names, or quotes; keep any "
    "additions general and accurate.\n"
    "- Preserve all user-given wording and language (Vietnamese with correct diacritics)."
)

# "slide" style — clean, editorial, light/airy (cream + one warm accent, one hero visual).
_SLIDE_SYSTEM = (
    "You are an expert presentation designer. Turn the user's slide content into ONE "
    "image-generation prompt describing a single CLEAN, EDITORIAL 16:9 presentation slide.\n"
    + _CONTENT_RULES + "\n"
    "VISUAL STYLE:\n"
    "- LIGHT & AIRY: white or soft cream background with a subtle accent-colored watercolor "
    "wash in the corners and faint minimal motifs. Not dark, no heavy gradients.\n"
    "- RESTRAINED COLOR: dark navy text; ONE warm accent color highlighting a single key phrase "
    "in the title and small accents. Avoid rainbow palettes.\n"
    "- Items as soft rounded cards with simple line icons; ONE soft glossy 3D hero illustration "
    "as a side/center anchor with a gentle glow.\n"
    "- FRAME: a small 'Slide' pill in a top corner and a slim one-line takeaway banner at the "
    "bottom (soft pill + small icon + one keyword in the accent color).\n"
    "- Strong visual hierarchy, balanced, sophisticated — a professionally designed deck.\n"
    "Output ONLY the final image-generation prompt — no preamble, no quotes, no explanation."
)

# "fintech" style — premium light-blue dashboard look (glassy cards, gradient circular
# icon badges, optional friendly 3D robot + chart widgets). Matches modern AI/finance decks.
_FINTECH_SYSTEM = (
    "You are an expert fintech presentation designer. Turn the user's slide content into ONE "
    "image-generation prompt describing a single premium 16:9 presentation slide.\n"
    + _CONTENT_RULES + "\n"
    "VISUAL STYLE:\n"
    "- BACKGROUND: light blue-to-white gradient, bright and airy, subtle glowing particles and "
    "fine tech lines; premium, clean.\n"
    "- CARDS: translucent GLASSMORPHISM rounded cards with soft shadows and a faint blue glow.\n"
    "- ICONS: each item icon sits in a CIRCULAR badge filled with a blue gradient, white icon "
    "inside.\n"
    "- COLOR: deep navy (#1a2b5e) headings, blue (#2d6fe8) accent on key phrases; high-contrast "
    "white text areas so text stays readable.\n"
    "- OPTIONAL (when it fits the topic): a small friendly 3D white-and-blue robot mascot on one "
    "side, and a floating glass dashboard with donut / line charts and stat cards. Any chart "
    "numbers are clearly illustrative, not real data.\n"
    "- FRAME: a slim rounded blue banner at the bottom with a shield icon and a one-line tagline.\n"
    "- 4K, modern, sophisticated like a tech product keynote.\n"
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
    "background with a subtle accent-color wash; dark navy text with ONE warm accent on a key "
    "title phrase; 3-6 items, each an icon + short label + a one-line description; one soft "
    "glossy 3D hero illustration; a small slide-number pill and a slim bottom takeaway banner; "
    "medium density (informative, not crowded, not empty); legible text in the request's "
    "language with correct diacritics. If input is sparse, complete it sensibly; do not invent fake stats."
)

_FINTECH_TEMPLATE = (
    "{p}. Render as ONE premium 16:9 fintech slide: light blue-to-white gradient background with "
    "subtle glow; translucent glassmorphism cards; circular blue-gradient icon badges; navy "
    "headings with blue accent on a key phrase; 3-6 items each with icon + short label + one-line "
    "description; optionally a friendly 3D blue-white robot and a glass dashboard with donut/line "
    "charts (illustrative numbers); a slim blue bottom banner with a shield icon and tagline; "
    "medium density, legible text in the request's language with correct diacritics. If input is "
    "sparse, complete it sensibly; do not invent fake statistics."
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


_SLIDE_STYLES = {"slide", "fintech"}


def _template_enhance(prompt: str, brand_clause: str = "", style: str = "auto") -> str:
    base = {"slide": _SLIDE_TEMPLATE, "fintech": _FINTECH_TEMPLATE}.get(style, _TEMPLATE)
    out = base.format(p=prompt.strip())
    if brand_clause:
        out = f"{out} {brand_clause}"
    return out


def enhance_prompt(prompt: str, *, text_model: str = "gpt-5",
                   brand_colors: list[str] | None = None,
                   reserve_corner: str | None = None,
                   style: str = "auto") -> str:
    """Return an expanded prompt. Never raises — falls back to template on any error.

    style="slide" (clean editorial) or "fintech" (light-blue dashboard) apply a slide
    design aesthetic and ALWAYS enhance (the >=280-char skip is bypassed) so even
    detailed slide content gets the designer treatment, with content completed to a
    balanced medium density. When brand_colors/reserve_corner are provided, brand
    instructions are appended and enhancement also always runs.
    """
    p = prompt.strip()
    brand_clause = _brand_clause(brand_colors, reserve_corner)
    has_brand = bool(brand_clause)
    is_slide = style in _SLIDE_STYLES

    # Skip only for the generic "auto" style with no brand context on long prompts.
    if not is_slide and not has_brand and len(p) >= _LONG_PROMPT_CHARS:
        return p
    try:
        # Local imports: keep the vendored engine import lazy + after env/sys.path setup.
        from cgimg.auth import tokens
        from services.openai_backend_api import OpenAIBackendAPI
        from services.protocol.conversation import ConversationRequest, stream_text_deltas
        backend = OpenAIBackendAPI(access_token=tokens.get_access_token())
        system = {"slide": _SLIDE_SYSTEM, "fintech": _FINTECH_SYSTEM}.get(style, _SYSTEM)
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
