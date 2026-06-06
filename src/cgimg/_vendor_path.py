"""Prepend the vendored package root to sys.path so the vendored chatgpt2api
code can keep its original absolute imports (`import services.*`, `import utils.*`).
Importing this module once (side effect) is enough."""
import sys
from pathlib import Path

_VENDOR_ROOT = str(Path(__file__).resolve().parent / "_vendor")
if _VENDOR_ROOT not in sys.path:
    sys.path.insert(0, _VENDOR_ROOT)
