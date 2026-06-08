"""Score findings by engagement and cluster near-duplicate stories."""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Any

_SIM_THRESHOLD = 0.80  # title similarity to treat two findings as the same story


def score_finding(f: dict[str, Any]) -> float:
    e = f.get("engagement") or {}
    views = float(e.get("views") or 0)
    likes = float(e.get("likes") or 0)
    comments = float(e.get("comments") or 0)
    # comments/likes signal stronger intent than passive views
    return views * 1.0 + likes * 20.0 + comments * 50.0


def rank(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(findings, key=score_finding, reverse=True)


def _norm_title(t: str) -> str:
    return re.sub(r"[^\w\s]", "", (t or "").lower()).strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_title(a), _norm_title(b)).ratio()


def cluster(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group near-duplicate findings by title similarity.
    Returns clusters: {lead: <highest-engagement finding>, members: [...]}.
    Strongest finding is processed first so it becomes the lead.
    """
    clusters: list[dict[str, Any]] = []
    for f in rank(findings):
        placed = False
        for c in clusters:
            if _similar(f.get("title", ""), c["lead"].get("title", "")) >= _SIM_THRESHOLD:
                c["members"].append(f)
                placed = True
                break
        if not placed:
            clusters.append({"lead": f, "members": [f]})
    return clusters
