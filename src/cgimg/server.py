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
                   out_dir: str = "out", enhance: bool = True,
                   style: str = "auto") -> dict:
    """Generate image(s) from a text prompt at the given aspect ratio
    (16:9, 1:1, 3:4, 9:16, or WxH). Returns saved PNG file paths.

    When enhance is True (default), the prompt is auto-expanded via the ChatGPT
    text path before drawing. style='slide' = clean editorial slide (light cream,
    one accent, hero visual); style='fintech' = premium light-blue dashboard look
    (glass cards, blue icon badges, optional robot + charts). Both auto-complete
    content into a full, information-rich slide (label + 2-line description per
    point, sparse input expanded). style='auto' is the general default."""
    from cgimg.engine.generate import generate_image as _gen
    return {"paths": _gen(prompt, aspect=aspect, n=n, out_dir=out_dir,
                          enhance=enhance, style=style)}


@mcp.tool()
def build_pptx(image_paths: list[str], out_path: str = "deck.pptx",
               aspect: str = "16:9") -> dict:
    """Assemble existing image files into a full-bleed PowerPoint deck."""
    from cgimg.ppt.builder import build_pptx as _build
    return {"path": _build(image_paths, out_path, aspect=aspect)}


@mcp.tool()
def generate_slide_deck(prompts: list[str], aspect: str = "16:9",
                        out_pptx: str = "deck.pptx", out_dir: str = "out",
                        enhance: bool = True, style: str = "slide") -> dict:
    """Generate one image per prompt then assemble them into a PPTX deck.

    Each prompt should be the CONTENT of one slide. style='slide' (default here)
    applies a clean editorial presentation design (light, restrained accent, one
    hero visual, short labels, takeaway banner) — pass raw slide content and the
    enhancer designs it. Set enhance=False to send prompts verbatim."""
    from cgimg.engine.generate import generate_image as _gen
    from cgimg.ppt.builder import build_pptx as _build
    images: list[str] = []
    for pr in prompts:
        images.extend(_gen(pr, aspect=aspect, n=1, out_dir=out_dir,
                           enhance=enhance, style=style))
    path = _build(images, out_pptx, aspect=aspect)
    return {"path": path, "image_paths": images}


@mcp.tool()
def branded_deck(logo_path: str, prompts: list[str], aspect: str = "16:9",
                 out_pptx: str = "deck.pptx", out_dir: str = "out",
                 logo_position: str = "top-left", logo_scale: float = 0.15) -> dict:
    """Build a branded slide deck: auto-detect brand colors from the logo, generate
    slides in those colors, composite the original logo onto each slide, assemble PPTX."""
    from cgimg.branding.deck import branded_deck as _bd
    return _bd(logo_path, prompts, aspect=aspect, out_pptx=out_pptx, out_dir=out_dir,
               logo_position=logo_position, logo_scale=logo_scale)


@mcp.tool()
def styled_deck(ref_image: str, prompts: list[str], aspect: str = "16:9",
                out_pptx: str = "deck.pptx", out_dir: str = "out") -> dict:
    """Generate a deck matching a reference design image's style and colors (content not copied)."""
    from cgimg.branding.deck import styled_deck as _sd
    return _sd(ref_image, prompts, aspect=aspect, out_pptx=out_pptx, out_dir=out_dir)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
