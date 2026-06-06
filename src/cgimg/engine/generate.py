"""Drive the vendored ChatGPT image-gen engine with our single-account token.

Entry: generate_image(prompt, aspect, n, out_dir) -> list of saved PNG paths.
"""
from __future__ import annotations

import base64
import os
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
    stream_image_outputs_with_pool,
)


def generate_image(
    prompt: str,
    aspect: str = "16:9",
    n: int = 1,
    out_dir: str = "out",
) -> list[str]:
    """Generate n image(s) and save them as PNGs. Returns saved file paths."""
    size = resolve_size(aspect)
    request = ConversationRequest(
        model="gpt-image-2",
        prompt=prompt,
        size=size,
        n=n,
        quality="auto",
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
