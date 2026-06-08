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


CHANNELS = {"youtube": youtube}
