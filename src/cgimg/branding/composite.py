"""Overlay the original logo onto a base image, pixel-perfect with transparency.

The logo is only resized (aspect preserved) and alpha-composited into a corner;
its pixels are never recolored, so the brand mark stays exact.
"""
from __future__ import annotations

from PIL import Image

_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


def _paste_xy(position: str, base_w: int, base_h: int,
              logo_w: int, logo_h: int, pad: int) -> tuple[int, int]:
    """Top-left paste coordinate for the logo in the requested corner."""
    if position == "top-left":
        return pad, pad
    if position == "top-right":
        return base_w - logo_w - pad, pad
    if position == "bottom-left":
        return pad, base_h - logo_h - pad
    # bottom-right
    return base_w - logo_w - pad, base_h - logo_h - pad


def overlay_logo(base_path: str, logo_path: str, out_path: str,
                 position: str = "top-left", scale: float = 0.15,
                 margin: float = 0.03) -> str:
    """Composite `logo_path` onto `base_path` in a corner; save PNG to out_path.

    - logo WIDTH becomes scale * base_width (aspect ratio preserved)
    - margin * base_width padding from the edges
    - logo alpha used as the paste mask so transparency is respected
    Returns out_path. Raises ValueError on an unknown position.
    """
    if position not in _POSITIONS:
        raise ValueError(f"unknown position {position!r}; use {sorted(_POSITIONS)}")

    base = Image.open(base_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    base_w, base_h = base.size

    # Resize logo to target width, keeping its aspect ratio.
    target_w = max(1, int(round(scale * base_w)))
    ratio = target_w / logo.width
    target_h = max(1, int(round(logo.height * ratio)))
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    pad = int(round(margin * base_w))
    x, y = _paste_xy(position, base_w, base_h, target_w, target_h, pad)

    # Alpha-composite: paste the logo using its own alpha channel as the mask.
    base.paste(logo, (x, y), logo)

    # Convert back to RGB so PPT does not choke on an alpha channel.
    base.convert("RGB").save(out_path, "PNG")
    return out_path
