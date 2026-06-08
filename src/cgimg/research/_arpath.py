"""Expose the vendored Agent-Reach package under its original top-level name
`agent_reach` (it uses absolute self-imports). Import for side effect.

Safe here: Agent-Reach namespaces everything under `agent_reach.*` (no bare
`utils`/`services`/`config`), so adding this dir to sys.path introduces no
collision with the other vendored package."""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent)  # .../cgimg/research/ contains agent_reach/
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
