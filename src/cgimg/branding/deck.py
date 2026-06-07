"""Orchestrate a branded slide deck: detect brand colors from a logo, generate
slides in those colors, composite the original logo onto each, assemble a PPTX.

Reuses the existing engine (generate_image, enhance_prompt) and ppt builder —
this module only wires them together.
"""
from __future__ import annotations

import os
import sys

from cgimg.branding.colors import extract_brand_colors
from cgimg.branding.composite import overlay_logo
from cgimg.engine.enhance import enhance_prompt
from cgimg.engine.generate import generate_image
from cgimg.ppt.builder import build_pptx


def branded_deck(logo_path: str, prompts: list[str], aspect: str = "16:9",
                 out_pptx: str = "deck.pptx", out_dir: str = "out",
                 logo_position: str = "top-left", logo_scale: float = 0.15) -> dict:
    """Build a branded deck and return its path, slide images, and brand colors."""
    if not prompts:
        raise ValueError("no prompts provided")

    colors = extract_brand_colors(logo_path)
    os.makedirs(out_dir, exist_ok=True)

    composited: list[str] = []
    total = len(prompts)
    for i, prompt in enumerate(prompts):
        print(f"[branded_deck] slide {i + 1}/{total}", file=sys.stderr)
        # Inject brand context, then generate verbatim (already enhanced).
        enhanced = enhance_prompt(prompt, brand_colors=colors, reserve_corner=logo_position)
        imgs = generate_image(enhanced, aspect=aspect, n=1, out_dir=out_dir, enhance=False)
        out_png = os.path.join(out_dir, f"branded-{i}.png")
        overlay_logo(imgs[0], logo_path, out_png,
                     position=logo_position, scale=logo_scale)
        composited.append(out_png)

    deck = build_pptx(composited, out_pptx, aspect=aspect)
    return {"path": deck, "image_paths": composited, "brand_colors": colors}


def styled_deck(ref_image: str, prompts: list[str], aspect: str = "16:9",
                out_pptx: str = "deck.pptx", out_dir: str = "out") -> dict:
    """Generate a slide deck whose design MATCHES a reference image (style + colors).

    - extract brand colors from ref_image
    - for each prompt: enhance (style='slide' + brand_colors) then generate with the
      ref_image attached as a STYLE reference (content NOT copied)
    - assemble PPTX. Returns {path, image_paths, brand_colors}.

    A failing slide is retried up to 3 times (ChatGPT sometimes throws a transient
    content-policy/timeout error that clears on re-run). On final failure the slide
    is skipped rather than aborting the whole deck.
    """
    if not prompts:
        raise ValueError("no prompts provided")

    colors = extract_brand_colors(ref_image)
    os.makedirs(out_dir, exist_ok=True)

    images: list[str] = []
    skipped: list[int] = []
    total = len(prompts)
    for i, prompt in enumerate(prompts):
        print(f"[styled_deck] slide {i + 1}/{total}", file=sys.stderr)
        enhanced = enhance_prompt(prompt, style="slide", brand_colors=colors)
        img: str | None = None
        for attempt in range(1, 4):
            try:
                imgs = generate_image(enhanced, aspect=aspect, n=1, out_dir=out_dir,
                                      enhance=False, ref_image=ref_image)
                img = imgs[0]
                break
            except Exception as exc:  # transient policy/timeout — retry then skip
                print(f"[styled_deck] slide {i + 1} attempt {attempt} failed: {exc}",
                      file=sys.stderr)
        if img:
            images.append(img)
        else:
            skipped.append(i + 1)
            print(f"[styled_deck] slide {i + 1} skipped after 3 attempts",
                  file=sys.stderr)

    if not images:
        raise RuntimeError("no slides could be generated")
    if skipped:
        print(f"[styled_deck] skipped slides: {skipped}", file=sys.stderr)

    deck = build_pptx(images, out_pptx, aspect=aspect)
    return {"path": deck, "image_paths": images, "brand_colors": colors}
