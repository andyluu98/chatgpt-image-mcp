"""Adapters that scrape a platform and normalize results to a Finding dict.

Finding = {
  "platform": str, "title": str, "url": str, "text": str, "author": str,
  "engagement": {"views": int, "likes": int, "comments": int},
  "published_at": str | None,
}
Scraping calls external CLIs (yt-dlp, ...) as subprocesses — same tools Agent-Reach
installs/diagnoses; we invoke them directly.
"""
from __future__ import annotations
import json
import subprocess
from typing import Any


def _finding(platform: str, title: str, url: str, text: str = "", author: str = "",
             engagement: dict | None = None, published_at: str | None = None) -> dict[str, Any]:
    return {"platform": platform, "title": title or "", "url": url or "",
            "text": text or "", "author": author or "",
            "engagement": engagement or {}, "published_at": published_at}


def youtube(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search YouTube via yt-dlp (subprocess) → Finding[]. Returns [] on failure."""
    try:
        proc = subprocess.run(
            ["yt-dlp", f"ytsearch{int(limit)}:{query}", "--dump-json",
             "--flat-playlist", "--no-warnings"],
            capture_output=True, text=True, timeout=120, encoding="utf-8",
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = v.get("url") or v.get("webpage_url") or (
            f"https://youtube.com/watch?v={v['id']}" if v.get("id") else "")
        out.append(_finding(
            "youtube", v.get("title"), url,
            text=v.get("description") or "",
            author=v.get("uploader") or v.get("channel") or "",
            engagement={"views": int(v.get("view_count") or 0),
                        "likes": int(v.get("like_count") or 0),
                        "comments": int(v.get("comment_count") or 0)},
            published_at=v.get("upload_date")))
    return out


def twitter(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search X/Twitter via the `twitter-cli` tool if installed → Finding[].
    Returns [] if the CLI is missing or errors (graceful)."""
    import shutil
    cli = shutil.which("twitter") or shutil.which("twitter-cli") or shutil.which("bird")
    if not cli:
        return []
    try:
        proc = subprocess.run([cli, "search", query, "--limit", str(int(limit))],
                              capture_output=True, text=True, timeout=90, encoding="utf-8")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            t = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.append(_finding("x", (t.get("text") or "")[:80], t.get("url") or "",
                            text=t.get("text") or "", author=t.get("author") or t.get("username") or "",
                            engagement={"likes": int(t.get("likes") or t.get("favorite_count") or 0),
                                        "comments": int(t.get("replies") or t.get("reply_count") or 0)}))
    return out


def read_url(url: str) -> dict[str, Any]:
    """Read a web page/article via the vendored Agent-Reach WebChannel (Jina Reader).
    Returns {title, text, meta}. Never raises — returns empty text on failure."""
    import cgimg.research._arpath  # noqa: F401
    try:
        from agent_reach.channels.web import WebChannel
        md = WebChannel().read(url) or ""
    except Exception:
        return {"title": "", "text": "", "meta": {"url": url, "error": "read_failed"}}
    # Jina markdown often starts with "Title: ..." — extract a title heuristically.
    title = ""
    for line in md.splitlines():
        s = line.strip()
        if s.lower().startswith("title:"):
            title = s.split(":", 1)[1].strip()
            break
        if s.startswith("# "):
            title = s[2:].strip()
            break
    return {"title": title, "text": md, "meta": {"url": url}}


def research_topic(topic: str, platforms: list[str] | None = None,
                   limit: int = 10, out_path: str = "out/brief.md") -> dict[str, Any]:
    """Scrape requested platforms → score/cluster → TrendBrief.
    A channel that errors is skipped (never aborts the whole run)."""
    from cgimg.research.brief import build_brief
    platforms = platforms or ["youtube", "x"]
    findings: list[dict[str, Any]] = []
    for p in platforms:
        fn = CHANNELS.get(p)
        if not fn:
            continue
        try:
            findings.extend(fn(topic, limit=limit))
        except Exception:
            pass  # graceful: skip a failing channel
    return build_brief(topic, findings, out_path)


CHANNELS = {"youtube": youtube, "x": twitter}
