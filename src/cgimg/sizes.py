"""Map a friendly aspect ratio to the size string ChatGPT honors.
ChatGPT normalizes to its own native dims; the RATIO is what matters."""
from __future__ import annotations
import re

_ASPECTS = {
    "16:9": "1920x1080",
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "9:16": "1080x1920",
}
_RAW = re.compile(r"^\d{2,5}x\d{2,5}$")


def resolve_size(aspect: str) -> str:
    a = aspect.strip().lower().replace(" ", "")
    if a in _ASPECTS:
        return _ASPECTS[a]
    if _RAW.match(a):
        return a
    raise ValueError(f"unknown aspect {aspect!r}; use one of {list(_ASPECTS)} or WxH")
