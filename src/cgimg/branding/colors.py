"""Extract dominant brand colors from a logo PNG.

Strategy: open + downscale for speed, drop transparent / near-white / near-black
pixels (usually background or outline, not brand color), quantize the rest and
count frequency. Return the top hex strings ordered by prominence.
"""
from __future__ import annotations

from collections import Counter

from PIL import Image

# Pixels with alpha below this are treated as (near-)transparent and ignored.
_ALPHA_MIN = 128
# Channels above this on every component => near-white (background/paper).
_WHITE_MAX = 240
# Channels below this on every component => near-black (outline/text).
_BLACK_MIN = 15
# Quantization step: round each channel to the nearest multiple of this. Groups
# slightly-different shades together so the same brand color counts as one.
_QUANT = 16
# Downscale longest side to this for speed; color stats are unaffected.
_THUMB = 128


def _quantize(value: int) -> int:
    """Snap a 0-255 channel to the nearest _QUANT multiple, clamped to 255."""
    return min(255, round(value / _QUANT) * _QUANT)


def _is_white(r: int, g: int, b: int) -> bool:
    return r > _WHITE_MAX and g > _WHITE_MAX and b > _WHITE_MAX


def _is_black(r: int, g: int, b: int) -> bool:
    return r < _BLACK_MIN and g < _BLACK_MIN and b < _BLACK_MIN


def _to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def extract_brand_colors(logo_path: str, max_colors: int = 4) -> list[str]:
    """Return up to `max_colors` dominant brand colors as hex strings.

    Ordered by prominence (most frequent first). Raises FileNotFoundError if the
    file cannot be opened; never raises on a normal-but-unusual image.
    """
    try:
        img = Image.open(logo_path)
        img = img.convert("RGBA")
    except FileNotFoundError:
        raise
    except Exception as exc:  # unreadable / corrupt file
        raise FileNotFoundError(f"cannot read logo image {logo_path!r}: {exc}") from exc

    # Downscale in place; keeps aspect ratio. Fast color survey, same hues.
    img.thumbnail((_THUMB, _THUMB))

    counts: Counter[tuple[int, int, int]] = Counter()
    # Fallback bucket: kept only if the filtered survey finds nothing usable.
    relaxed: Counter[tuple[int, int, int]] = Counter()

    for r, g, b, a in img.getdata():
        if a < _ALPHA_MIN:
            continue  # transparent: ignore entirely
        q = (_quantize(r), _quantize(g), _quantize(b))
        relaxed[q] += 1
        if _is_white(r, g, b) or _is_black(r, g, b):
            continue  # background / outline: skip for the primary survey
        counts[q] += 1

    # If filtering removed everything (e.g. a pure black-on-transparent logo),
    # relax and keep the blacks/whites so we always return at least one color.
    survey = counts if counts else relaxed
    top = survey.most_common(max_colors)
    return [_to_hex(rgb) for rgb, _ in top]
