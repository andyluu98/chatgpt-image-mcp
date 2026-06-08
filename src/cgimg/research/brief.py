"""Assemble scored/clustered findings into a TrendBrief (markdown + structured dict)."""
from __future__ import annotations
import os
from collections import Counter
from typing import Any
from cgimg.research.scoring import cluster, score_finding


def build_brief(topic: str, findings: list[dict[str, Any]], out_path: str) -> dict[str, Any]:
    clusters = cluster(findings)
    insights = []
    for c in clusters:
        lead = c["lead"]
        insights.append({
            "title": lead.get("title", ""),
            "platform": lead.get("platform", ""),
            "url": lead.get("url", ""),
            "sources": [m.get("url", "") for m in c["members"]],
            "score": score_finding(lead),
        })
    by_platform = dict(Counter(f.get("platform", "?") for f in findings))

    lines = [f"# Trend Brief — {topic}", ""]
    if not insights:
        lines.append("_Không tìm thấy kết quả._")
    else:
        lines.append(f"**{len(insights)} chủ đề nổi bật** từ {len(findings)} nguồn.")
        lines.append("")
        for i, ins in enumerate(insights, 1):
            lines.append(f"## {i}. {ins['title']}")
            lines.append(f"- Nền tảng: {ins['platform']} · {len(ins['sources'])} nguồn")
            lines.append(f"- Link: {ins['url']}")
            lines.append("")
        lines.append("---")
        lines.append("**Theo nền tảng:** " + ", ".join(f"{k}: {v}" for k, v in by_platform.items()))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    return {"brief_path": out_path, "insights": insights, "by_platform": by_platform}
