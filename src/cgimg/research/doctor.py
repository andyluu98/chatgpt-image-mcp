"""Report which research channels are usable on this machine.
Prefers Agent-Reach's own diagnostic; falls back to a simple CLI-presence check."""
from __future__ import annotations
import shutil

# Fallback map: channel -> external CLI it needs (None = pure-python, always ok).
_FALLBACK_CLI = {"youtube": "yt-dlp", "web": None, "x": "twitter", "github": "gh", "reddit": "rdt"}


def check_channels() -> dict[str, str]:
    """Return {channel: 'ok'|'missing'} . Tries Agent-Reach check_all first."""
    try:
        import cgimg.research._arpath  # noqa: F401
        from agent_reach.config import Config
        from agent_reach.doctor import check_all
        raw = check_all(Config())  # check_all(config: Config) -> {name: {status,...}}
        rep = {}
        for name, info in (raw or {}).items():
            status = info.get("status") if isinstance(info, dict) else str(info)
            rep[name] = "ok" if status in ("ok", "warn") else "missing"
        if rep:
            return rep
    except Exception:
        pass
    # fallback
    return {name: ("ok" if (cli is None or shutil.which(cli)) else "missing")
            for name, cli in _FALLBACK_CLI.items()}
