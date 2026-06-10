"""Drive the vendored ChatGPT image-gen engine with our single-account token.

Entry: generate_image(prompt, aspect, n, out_dir) -> list of saved PNG paths.
"""
from __future__ import annotations

import base64
import os
import sys
import time

# The vendored config.py instantiates a ConfigStore at IMPORT time and raises
# ValueError if no auth-key is set. Satisfy it BEFORE importing any engine
# module. This key is unrelated to our OAuth token.
os.environ.setdefault("CHATGPT2API_AUTH_KEY", "cgimg-local")

# Make the vendored `services.*` / `utils.*` packages importable.
import cgimg._vendor_path  # noqa: F401  (side-effect: prepends _vendor to sys.path)

from cgimg.auth import tokens
from cgimg.sizes import resolve_size

# Wire our token store into the vendored single-account shim BEFORE the engine
# asks for a token. The shim's get_available_access_token() returns get_token().
from services.account_service import set_token_provider  # noqa: E402

set_token_provider(
    get_token=lambda: tokens.get_access_token(False),
    refresh=lambda force: tokens.get_access_token(True),
)

from services.protocol.conversation import (  # noqa: E402
    ConversationRequest,
    encode_images,
    stream_image_outputs_with_pool,
)

from cgimg.engine.enhance import enhance_prompt  # noqa: E402

# Instruction appended when a reference image is attached. Two modes:
#   "style" — borrow the LOOK only, never copy the reference's text/content
#             (used by styled_deck).
#   "logo"  — the reference IS a real brand asset (logo); place it into the
#             image exactly as given, do not redraw or invent a different one.
_REF_STYLE_SUFFIX = (
    " QUAN TRỌNG: Ảnh đính kèm CHỈ là tham chiếu PHONG CÁCH THIẾT KẾ "
    "(bảng màu, bố cục, kiểu chữ, không khí, hoạ tiết trang trí). TUYỆT ĐỐI "
    "KHÔNG sao chép chữ, tiêu đề, hay nội dung cụ thể trong ảnh tham chiếu. "
    "Hãy tạo slide MỚI với nội dung đã cho ở trên, mang phong cách giống ảnh "
    "tham chiếu. (IMPORTANT: the attached image is a DESIGN-STYLE reference "
    "ONLY — palette, layout, typography, mood, decorative motifs. Do NOT copy "
    "any text, titles, or specific content from it; create a NEW slide with "
    "the content above, styled like the reference.)"
)
_REF_LOGO_SUFFIX = (
    " QUAN TRỌNG: Ảnh đính kèm là LOGO thương hiệu THẬT. Hãy đưa CHÍNH XÁC logo "
    "này vào ảnh — giữ nguyên chữ, màu sắc, hình dạng và tỉ lệ của logo; TUYỆT "
    "ĐỐI không vẽ lại, không đổi font, không bịa logo khác. Đặt logo gọn gàng, "
    "cân đối, không che nội dung chính. (IMPORTANT: the attached image is the "
    "REAL brand logo — incorporate it into the composition EXACTLY as given, "
    "preserving its exact text, colors, shape and proportions; do NOT redraw, "
    "restyle, or invent a different logo.)"
)


def _ref_suffix(ref_mode: str) -> str:
    """Pick the reference-image instruction for the given mode."""
    return _REF_LOGO_SUFFIX if ref_mode in ("logo", "asset") else _REF_STYLE_SUFFIX


def generate_image(
    prompt: str,
    aspect: str = "16:9",
    n: int = 1,
    out_dir: str = "out",
    enhance: bool = True,
    style: str = "auto",
    ref_image: str | None = None,
    ref_mode: str = "style",
) -> list[str]:
    """Generate n image(s) and save them as PNGs. Returns saved file paths.

    When enhance is True (default), the prompt is first expanded via the ChatGPT
    text path (mirrors the web UI). style="slide" applies a clean editorial
    presentation-slide aesthetic (light, restrained, one hero, short labels) —
    best for slide content.

    When ref_image is a path, the engine attaches it so the model SEES it:
      ref_mode="style" (default) — match the reference's DESIGN STYLE only
        (palette, layout, typography, mood); its text/content is NOT copied.
      ref_mode="logo" (alias "asset") — the reference IS a real logo/brand asset;
        the model places it into the image exactly as given (no redraw/invent).
    """
    size = resolve_size(aspect)
    if enhance:
        prompt = enhance_prompt(prompt, style=style)
        print(f"[enhance] prompt expanded to {len(prompt)} chars", file=sys.stderr)

    encoded: list[str] | None = None
    if ref_image:
        prompt = prompt + _ref_suffix(ref_mode)
        ext = os.path.splitext(ref_image)[1].lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        with open(ref_image, "rb") as f:
            data = f.read()
        encoded = encode_images([(data, mime, os.path.basename(ref_image))])

    request = ConversationRequest(
        model="gpt-image-2",
        prompt=prompt,
        size=size,
        n=n,
        quality="auto",
        images=encoded,
        # response_format defaults to "b64_json" -> result dicts carry b64_json.
    )

    os.makedirs(out_dir, exist_ok=True)
    saved: list[str] = []
    message = ""

    # The pool wrapper calls account_service.get_available_access_token()
    # internally (our shim -> our token), so no manual backend construction.
    for output in stream_image_outputs_with_pool(request):
        if output.kind == "message":
            message = output.text or message
        elif output.kind == "result":
            for item in output.data:
                b64 = str(item.get("b64_json") or "").strip()
                if not b64:
                    continue
                path = os.path.join(
                    out_dir, f"img-{int(time.time() * 1000)}-{len(saved)}.png"
                )
                with open(path, "wb") as f:
                    f.write(base64.b64decode(b64))
                saved.append(path)

    if not saved:
        raise RuntimeError(
            f"image generation produced no images. Engine said: {message or '(no message)'}"
        )
    return saved
