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
                   out_dir: str = "out", enhance: bool = True) -> dict:
    """Generate image(s) from a text prompt at the given aspect ratio
    (16:9, 1:1, 3:4, 9:16, or WxH). Returns saved PNG file paths.

    When enhance is True (default), the prompt is auto-expanded into a rich,
    detailed prompt via the same ChatGPT account's text path (mirrors the web
    UI) before drawing, producing far denser images. Set enhance=False to send
    the prompt verbatim."""
    from cgimg.engine.generate import generate_image as _gen
    return {"paths": _gen(prompt, aspect=aspect, n=n, out_dir=out_dir, enhance=enhance)}


@mcp.tool()
def build_pptx(image_paths: list[str], out_path: str = "deck.pptx",
               aspect: str = "16:9") -> dict:
    """Assemble existing image files into a full-bleed PowerPoint deck."""
    from cgimg.ppt.builder import build_pptx as _build
    return {"path": _build(image_paths, out_path, aspect=aspect)}


@mcp.tool()
def generate_slide_deck(prompts: list[str], aspect: str = "16:9",
                        out_pptx: str = "deck.pptx", out_dir: str = "out",
                        enhance: bool = True) -> dict:
    """Generate one image per prompt then assemble them into a PPTX deck.

    When enhance is True (default), each prompt is auto-expanded into a rich,
    detailed prompt via the ChatGPT text path (mirrors the web UI) before
    drawing. Set enhance=False to send prompts verbatim."""
    from cgimg.engine.generate import generate_image as _gen
    from cgimg.ppt.builder import build_pptx as _build
    images: list[str] = []
    for pr in prompts:
        images.extend(_gen(pr, aspect=aspect, n=1, out_dir=out_dir, enhance=enhance))
    path = _build(images, out_pptx, aspect=aspect)
    return {"path": path, "image_paths": images}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
