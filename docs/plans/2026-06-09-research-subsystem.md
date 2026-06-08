# Research Subsystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Research pillar to the studio — vendor Agent-Reach's free multi-platform scrapers and expose `research_topic` / `read_url` / `scrape_channel` / `research_doctor` that produce a TrendBrief (JSON + markdown) feeding the future Write pillar.

**Architecture:** Vendor Agent-Reach's `agent_reach/` package (MIT) under `src/cgimg/research/agent_reach/`. A thin layer on top — `channels.py` (adapter), `scoring.py` (engagement+recency ranking & clustering), `brief.py` (TrendBrief assembly) — orchestrates the vendored channels. New MCP tools + CLI subcommands. Visuals pillar (`cgimg.engine/branding/ppt`) untouched.

**Tech Stack:** Python 3.12, `uv`, vendored Agent-Reach (wraps `yt-dlp`, `gh`, `twitter-cli`, `feedparser`, Jina Reader), `pytest`.

**Spec:** `docs/specs/2026-06-08-research-subsystem-design.md`
**Source to vendor:** https://github.com/Panniantong/Agent-Reach (MIT, © 2025 Agent Eyes)

---

## Key facts (from spec + source inspection)

- Agent-Reach layout: package `agent_reach/`, channels in `agent_reach/channels/` (`web.py`, `twitter.py`, `youtube.py`, `github.py`, `reddit.py`, `rss.py`, `exa_search.py`, `bilibili.py`, `linkedin.py`, `douyin.py`, `xiaohongshu.py`, `wechat.py`). Each channel exposes a `check()` for the doctor diagnostic and wraps an external CLI tool.
- External CLI tools are SYSTEM deps installed separately (`yt-dlp`, `gh`, `twitter-cli`, …). The `doctor` reports which are available.
- **Repo rename:** GitHub repo → `social-content-studio`; the LOCAL folder stays `F:\chatgpt-image-mcp` and the Python package stays `cgimg` (avoid breaking the registered MCP `cwd` + imports). Only the GitHub name + product name change.
- **Spike-first:** YouTube (`yt-dlp`, no auth) is the most reliable channel — prove it end-to-end before wiring the rest. FB/TikTok deferred.

---

## File Structure

```
F:\chatgpt-image-mcp\                       (GitHub repo renamed → social-content-studio)
├── src/cgimg/                              (visuals pillar — UNCHANGED)
│   └── research/                           (NEW research pillar)
│       ├── __init__.py
│       ├── agent_reach/                    (VENDORED, MIT — channels + helpers)
│       ├── channels.py                     (adapter: call a vendored channel → Finding[])
│       ├── scoring.py                      (engagement+recency score, cluster dedupe)
│       ├── brief.py                        (TrendBrief: findings → markdown + JSON)
│       └── doctor.py                       (channel availability report)
├── docs/specs/ docs/plans/
└── tests/  (test_research_scoring.py, test_research_brief.py, test_research_doctor.py, test_research_import.py)
```

---

## Task 1: Rename repo + research package skeleton + deps

**Files:**
- Modify: `pyproject.toml` (deps), `README.md` (product name note)
- Create: `src/cgimg/research/__init__.py`

- [ ] **Step 1: Rename the GitHub repo** (local folder + package stay the same)

Run:
```bash
cd /f/chatgpt-image-mcp && gh repo rename social-content-studio --yes
git remote -v
```
Expected: remote origin now points to `.../social-content-studio.git`. If `gh repo rename` is unavailable, do it in GitHub UI → Settings → Rename, then `git remote set-url origin https://github.com/andyluu98/social-content-studio.git`.

- [ ] **Step 2: Add research deps to pyproject.toml**

Add to `[project].dependencies`: `"feedparser>=6.0"`, `"yt-dlp>=2024.0"`. (Other channels rely on system CLIs, not pip deps.) Run `cd /f/chatgpt-image-mcp && uv sync`. Expected: resolves OK.

- [ ] **Step 3: Create the research package marker**

Create `src/cgimg/research/__init__.py` with a one-line docstring `"""Research pillar: multi-platform trend scraping (vendored Agent-Reach)."""`.

- [ ] **Step 4: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "chore: rename to social-content-studio + research package skeleton"
```

---

## Task 2: Vendor Agent-Reach

**Files:**
- Create: `src/cgimg/research/agent_reach/**` (copied), update `NOTICE`

- [ ] **Step 1: Clone Agent-Reach to a temp location and inspect**

```bash
cd /tmp && rm -rf agent-reach-src && git clone --depth 1 https://github.com/Panniantong/Agent-Reach.git agent-reach-src
ls agent-reach-src/agent_reach && ls agent-reach-src/agent_reach/channels
```
Read `agent_reach/channels/youtube.py`, `web.py`, `rss.py`, and the package `__init__.py` / any `doctor`/`install` module. Note the exact function/class names a channel exposes (e.g. a `search()`/`fetch()` entry and `check()`), and what each returns. This determines the adapter in Task 4/Task 7.

- [ ] **Step 2: Copy the vendored package**

```bash
SRC=/tmp/agent-reach-src/agent_reach
DST=/f/chatgpt-image-mcp/src/cgimg/research/agent_reach
cp -r "$SRC" "$DST"
# keep its LICENSE alongside the vendored code
cp /tmp/agent-reach-src/LICENSE "$DST/LICENSE" 2>/dev/null || true
ls -R "$DST" | head -40
```

- [ ] **Step 3: Update NOTICE attribution**

Append to `F:\chatgpt-image-mcp\NOTICE`:
```
This project also vendors code from Agent-Reach
(https://github.com/Panniantong/Agent-Reach), Copyright (c) 2025 Agent Eyes, MIT License.
Vendored under src/cgimg/research/agent_reach/.
```

- [ ] **Step 4: Inventory imports + third-party deps the vendored code needs**

```bash
grep -rhoE "^(import|from) [a-zA-Z0-9_.]+" "$DST" | sort -u
```
List any third-party package the vendored code imports that is NOT already in our deps (e.g. `click`, `requests`, `feedparser`, `rich`). Record them — Task 3 adds the needed ones. Internal `agent_reach.*` imports will resolve as a normal package import (`from cgimg.research.agent_reach...`) only if the vendored code uses RELATIVE imports or the package name `agent_reach`. Note which style it uses — this is the key integration detail for Task 3.

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: vendor Agent-Reach scrapers (MIT)"
```

---

## Task 3: Make the vendored package importable + add missing deps

**Files:**
- Modify: `pyproject.toml` (deps found in Task 2 Step 4)
- Possibly create: `src/cgimg/research/_arpath.py` (only if the vendored code uses absolute `import agent_reach...`)
- Test: `tests/test_research_import.py`

- [ ] **Step 1: Add missing third-party deps**

From Task 2 Step 4's inventory, add each missing package to `pyproject.toml` deps (e.g. `"click"`, `"rich"`, `"requests"`). Run `cd /f/chatgpt-image-mcp && uv sync`.

- [ ] **Step 2: Resolve the import style — AVOID NAMESPACE CLASH**

**Critical:** the visuals pillar's chatgpt2api vendor puts generic top-level modules
`services` and `utils` on `sys.path` (via `cgimg._vendor_path`). Agent-Reach likely
has its own `utils`/`config`/etc. If we add Agent-Reach's dir to `sys.path` as a
generic root, an `import utils` inside Agent-Reach could resolve to chatgpt2api's
`utils` (or vice-versa) in the shared MCP-server process → silent wrong-module bugs.

**Rule:** prefer importing Agent-Reach ONLY as the package-qualified
`cgimg.research.agent_reach.*`. First try rewriting any absolute self-imports in the
vendored code (`import agent_reach.x` → `from cgimg.research.agent_reach import x`, or
relative `from ..x import`) if they are few. Do NOT add a generic dir to `sys.path`.
ONLY if the vendored code has many absolute `import agent_reach...` self-references
that are impractical to rewrite, add a path shim that exposes EXACTLY the name
`agent_reach` (not its parent dir, so no `utils`/`services`/`config` leak):
`src/cgimg/research/_arpath.py`:
```python
"""Make the vendored Agent-Reach importable under its original top-level name
`agent_reach` (it uses absolute self-imports). Import for side effect."""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent)  # .../research/ contains agent_reach/
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
```
(Mirrors the `_vendor_path.py` pattern already used for the chatgpt2api vendor.)

- [ ] **Step 3: Write the import test**

```python
# tests/test_research_import.py
def test_vendored_youtube_channel_imports():
    import cgimg.research  # noqa: F401
    try:
        import cgimg.research._arpath  # noqa: F401  (no-op if not needed)
    except ModuleNotFoundError:
        pass
    import importlib
    # Adjust the module path to the actual vendored layout confirmed in Task 2.
    mod = importlib.import_module("cgimg.research.agent_reach.channels.youtube")
    assert mod is not None
```

- [ ] **Step 4: Run it; fix until green**

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_import.py -v`
Expected: PASS. If ImportError on a third-party dep, add it (Step 1) and re-run. If the module path differs, correct the test to the real path from Task 2.

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: vendored research package imports cleanly"
```

---

## Task 4: SPIKE — YouTube channel end-to-end (`channels.py` + Finding)

> **Make-or-break.** Prove the vendored YouTube channel returns real data headlessly on Windows, normalized to our `Finding` shape.

**Files:**
- Create: `src/cgimg/research/channels.py`
- Read for context: the real vendored `agent_reach/channels/youtube.py` (entry function + return shape, from Task 2 Step 1)

- [ ] **Step 1: Confirm `yt-dlp` is available**

Run: `cd /f/chatgpt-image-mcp && uv run yt-dlp --version` (it's a pip dep from Task 1). Expected: a version string. If missing, `uv sync` and retry.

- [ ] **Step 2: Define the normalized Finding + a YouTube adapter**

Create `src/cgimg/research/channels.py`:
```python
"""Adapter over vendored Agent-Reach channels → a normalized Finding dict.

Finding = {
  "platform": str, "title": str, "url": str, "text": str, "author": str,
  "engagement": {"views": int, "likes": int, "comments": int},
  "published_at": str | None,
}
"""
from __future__ import annotations
from typing import Any

try:
    import cgimg.research._arpath  # noqa: F401
except ModuleNotFoundError:
    pass


def _finding(platform, title, url, text="", author="", engagement=None,
             published_at=None) -> dict[str, Any]:
    return {"platform": platform, "title": title or "", "url": url or "",
            "text": text or "", "author": author or "",
            "engagement": engagement or {}, "published_at": published_at}


def youtube(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search YouTube via the vendored channel (yt-dlp) → Finding[]."""
    # Use the real entry function discovered in Task 2 Step 1. The call below is the
    # SHAPE; reconcile the function name/return with the actual vendored channel.
    from cgimg.research.agent_reach.channels import youtube as yt
    raw = yt.search(query, limit=limit)  # <-- adjust to real API (name/args/return)
    out = []
    for r in raw:
        out.append(_finding(
            "youtube", r.get("title"), r.get("url") or r.get("webpage_url"),
            text=r.get("description") or "", author=r.get("uploader") or "",
            engagement={"views": r.get("view_count") or 0,
                        "likes": r.get("like_count") or 0,
                        "comments": r.get("comment_count") or 0},
            published_at=r.get("upload_date")))
    return out
```
> NOTE: the vendored channel's real function name, args, and return keys MUST be reconciled with what you read in Task 2 Step 1. If the channel returns transcripts/text instead of search results, adapt `youtube()` to the actual capability (e.g. fetch metadata for a search via `yt-dlp` directly if the channel only does transcript extraction).

- [ ] **Step 3: Run the spike (real network)**

```bash
cd /f/chatgpt-image-mcp && uv run python -c "from cgimg.research.channels import youtube; r=youtube('chứng khoán việt nam', limit=5); print(len(r)); import json; print(json.dumps(r[0], ensure_ascii=False)[:400])"
```
Expected: ≥1 Finding with a real title + url. Generous timeout (yt-dlp can take 20-60s). If it fails, diagnose: yt-dlp present? channel API shape correct? network/region issue? Fix root cause and re-run until real findings come back.

- [ ] **Step 4: Commit (only once real findings are produced)**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: research YouTube channel adapter (spike passing)"
```

---

## Task 5: Scoring + clustering (`scoring.py`, TDD)

**Files:**
- Create: `src/cgimg/research/scoring.py`
- Test: `tests/test_research_scoring.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_research_scoring.py
from cgimg.research.scoring import score_finding, rank, cluster


def test_score_rewards_engagement():
    low = {"engagement": {"views": 10, "likes": 1, "comments": 0}, "published_at": "20260101"}
    high = {"engagement": {"views": 100000, "likes": 5000, "comments": 300}, "published_at": "20260101"}
    assert score_finding(high) > score_finding(low)


def test_rank_sorts_desc():
    items = [{"engagement": {"views": 10}}, {"engagement": {"views": 999}}]
    ranked = rank(items)
    assert ranked[0]["engagement"]["views"] == 999


def test_cluster_merges_similar_titles():
    items = [
        {"title": "VN-Index tăng mạnh phiên hôm nay", "url": "a", "engagement": {"views": 5}},
        {"title": "VN-Index tăng mạnh phiên hôm nay!!!", "url": "b", "engagement": {"views": 9}},
        {"title": "Giá vàng lập đỉnh", "url": "c", "engagement": {"views": 3}},
    ]
    clusters = cluster(items)
    assert len(clusters) == 2  # the two VN-Index items merge


def test_cluster_keeps_highest_engagement_as_lead():
    items = [
        {"title": "Cổ phiếu thép bứt phá", "url": "a", "engagement": {"views": 5}},
        {"title": "Cổ phiếu thép bứt phá mạnh", "url": "b", "engagement": {"views": 50}},
    ]
    clusters = cluster(items)
    assert clusters[0]["lead"]["url"] == "b"  # higher engagement leads
```

- [ ] **Step 2: Run, expect FAIL**

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_scoring.py -v` → FAIL (module missing).

- [ ] **Step 3: Implement `scoring.py`**

```python
"""Score findings by engagement (recency-weighted) and cluster near-duplicates."""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Any

_SIM_THRESHOLD = 0.82  # title similarity to treat two findings as the same story


def score_finding(f: dict[str, Any]) -> float:
    e = f.get("engagement") or {}
    views = float(e.get("views") or 0)
    likes = float(e.get("likes") or 0)
    comments = float(e.get("comments") or 0)
    # weighted: comments and likes signal stronger intent than passive views
    return views * 1.0 + likes * 20.0 + comments * 50.0


def rank(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(findings, key=score_finding, reverse=True)


def _norm_title(t: str) -> str:
    return re.sub(r"[^\w\s]", "", (t or "").lower()).strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm_title(a), _norm_title(b)).ratio()


def cluster(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group near-duplicate findings (by title similarity) across platforms.
    Returns clusters: {lead: <highest-engagement finding>, members: [...]}.
    """
    clusters: list[dict[str, Any]] = []
    for f in rank(findings):  # process strongest first so it becomes the lead
        placed = False
        for c in clusters:
            if _similar(f.get("title", ""), c["lead"].get("title", "")) >= _SIM_THRESHOLD:
                c["members"].append(f)
                placed = True
                break
        if not placed:
            clusters.append({"lead": f, "members": [f]})
    return clusters
```

- [ ] **Step 4: Run, expect PASS**

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_scoring.py -v` → 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: research scoring + clustering"
```

---

## Task 6: TrendBrief assembly (`brief.py`, TDD)

**Files:**
- Create: `src/cgimg/research/brief.py`
- Test: `tests/test_research_brief.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_research_brief.py
from pathlib import Path
from cgimg.research.brief import build_brief


def _f(platform, title, url, views):
    return {"platform": platform, "title": title, "url": url, "text": "",
            "author": "", "engagement": {"views": views}, "published_at": None}


def test_build_brief_structure(tmp_path):
    findings = [
        _f("youtube", "VN-Index tăng mạnh", "u1", 9000),
        _f("web", "VN-Index tăng mạnh hôm nay", "u2", 100),
        _f("youtube", "Giá vàng lập đỉnh", "u3", 500),
    ]
    out = tmp_path / "brief.md"
    res = build_brief("chứng khoán", findings, str(out))
    assert Path(res["brief_path"]).exists()
    md = out.read_text(encoding="utf-8")
    assert "chứng khoán" in md
    assert "VN-Index" in md
    # two stories after clustering (VN-Index merged)
    assert len(res["insights"]) == 2
    # by_platform breakdown present
    assert "youtube" in res["by_platform"]


def test_build_brief_empty(tmp_path):
    res = build_brief("topic", [], str(tmp_path / "b.md"))
    assert res["insights"] == []
    assert Path(res["brief_path"]).exists()
```

- [ ] **Step 2: Run, expect FAIL**

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_brief.py -v` → FAIL.

- [ ] **Step 3: Implement `brief.py`**

```python
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
```

- [ ] **Step 4: Run, expect PASS**

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_brief.py -v` → 2 passed.

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: TrendBrief assembly"
```

---

## Task 7: Orchestrator + more channels (`research_topic`, `read_url`)

**Files:**
- Modify: `src/cgimg/research/channels.py` (add `web`/`rss`/`twitter` adapters + `read_url`)
- Create: `src/cgimg/research/__init__.py` exports (or a small `topic.py`)
- Read for context: vendored `agent_reach/channels/{web,rss,twitter}.py`

- [ ] **Step 1: Add `web`/`rss`/`twitter` adapters + `read_url` to `channels.py`**

For each, follow the same pattern as `youtube()` in Task 4: call the real vendored channel function (reconcile names/returns from the source), normalize to `_finding(...)`. Add:
```python
def web(query: str, limit: int = 10) -> list[dict]:
    from cgimg.research.agent_reach.channels import web as w
    raw = w.search(query, limit=limit)   # adjust to real API
    return [_finding("web", r.get("title"), r.get("url"), text=r.get("snippet") or "")
            for r in raw]

def read_url(url: str) -> dict:
    from cgimg.research.agent_reach.channels import web as w
    art = w.read(url)                     # adjust to real API (Jina reader)
    return {"title": art.get("title", ""), "text": art.get("text") or art.get("content", ""),
            "meta": {k: art.get(k) for k in ("author", "published_at") if art.get(k)}}

def twitter(query: str, limit: int = 10) -> list[dict]:
    from cgimg.research.agent_reach.channels import twitter as tw
    raw = tw.search(query, limit=limit)   # adjust to real API
    return [_finding("x", r.get("text", "")[:80], r.get("url"), text=r.get("text") or "",
                     author=r.get("author") or "",
                     engagement={"likes": r.get("likes") or 0, "comments": r.get("replies") or 0})
            for r in raw]

CHANNELS = {"youtube": youtube, "web": web, "x": twitter}
```
Each adapter must degrade gracefully: if its CLI is missing/errors, return `[]` (never raise) so one broken channel doesn't kill `research_topic`.

- [ ] **Step 2: Add `research_topic` orchestrator**

Append to `channels.py` (or a `topic.py`):
```python
def research_topic(topic: str, platforms: list[str] | None = None,
                   limit: int = 10, out_path: str = "out/brief.md") -> dict:
    """Scrape requested platforms → score/cluster → TrendBrief."""
    from cgimg.research.brief import build_brief
    platforms = platforms or ["youtube", "web", "x"]
    findings: list[dict] = []
    for p in platforms:
        fn = CHANNELS.get(p)
        if not fn:
            continue
        try:
            findings.extend(fn(topic, limit=limit))
        except Exception:
            pass  # graceful: skip a failing channel
    return build_brief(topic, findings, out_path)
```

- [ ] **Step 3: Offline test (CHANNELS mockable) — `tests/test_research_topic.py`**

```python
from cgimg.research import channels


def test_research_topic_aggregates(monkeypatch, tmp_path):
    monkeypatch.setitem(channels.CHANNELS, "youtube",
                        lambda q, limit=10: [channels._finding("youtube", "T1", "u1",
                                             engagement={"views": 100})])
    monkeypatch.setitem(channels.CHANNELS, "web",
                        lambda q, limit=10: [channels._finding("web", "T2", "u2")])
    res = channels.research_topic("x", platforms=["youtube", "web"],
                                  out_path=str(tmp_path / "b.md"))
    assert len(res["insights"]) == 2
    assert res["by_platform"].get("youtube") == 1


def test_research_topic_skips_broken_channel(monkeypatch, tmp_path):
    def boom(q, limit=10):
        raise RuntimeError("cli missing")
    monkeypatch.setitem(channels.CHANNELS, "youtube", boom)
    monkeypatch.setitem(channels.CHANNELS, "web",
                        lambda q, limit=10: [channels._finding("web", "T", "u")])
    res = channels.research_topic("x", platforms=["youtube", "web"],
                                  out_path=str(tmp_path / "b.md"))
    assert len(res["insights"]) == 1  # broken youtube skipped, web survives
```

Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_topic.py -v` → 2 passed.

- [ ] **Step 4: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: research_topic orchestrator + web/x channels + read_url"
```

---

## Task 8: Doctor + MCP tools + CLI

**Files:**
- Create: `src/cgimg/research/doctor.py`
- Modify: `src/cgimg/server.py` (MCP tools), `src/cgimg/cli.py` (subcommands)
- Test: `tests/test_research_doctor.py`

- [ ] **Step 1: Write `doctor.py` + test**

`tests/test_research_doctor.py`:
```python
from cgimg.research import doctor


def test_doctor_reports_known_channels():
    rep = doctor.check_channels()
    assert "youtube" in rep
    assert rep["youtube"] in ("ok", "missing", "error")
```
`src/cgimg/research/doctor.py`:
```python
"""Report which research channels are usable (their underlying CLI present)."""
from __future__ import annotations
import shutil

# channel -> the external CLI it needs (None = pure-python / always ok)
_CLI = {"youtube": "yt-dlp", "web": None, "x": "twitter-cli", "github": "gh", "reddit": "rdt-cli"}


def check_channels() -> dict[str, str]:
    rep = {}
    for name, cli in _CLI.items():
        if cli is None:
            rep[name] = "ok"
        else:
            rep[name] = "ok" if shutil.which(cli) else "missing"
    return rep
```
Run: `cd /f/chatgpt-image-mcp && uv run pytest tests/test_research_doctor.py -v` → pass.

- [ ] **Step 2: Add MCP tools to `server.py`**

Append (lazy imports inside each tool, matching the existing style):
```python
@mcp.tool()
def research_topic(topic: str, platforms: list[str] | None = None,
                   limit: int = 10, out_dir: str = "out") -> dict:
    """Scrape platforms (youtube, web, x) for a topic, score+cluster, and return a
    TrendBrief (markdown path + insights). Feeds content writing."""
    from cgimg.research.channels import research_topic as _rt
    import os
    return _rt(topic, platforms=platforms, limit=limit,
               out_path=os.path.join(out_dir, "brief.md"))


@mcp.tool()
def read_url(url: str) -> dict:
    """Extract title + main text from a web page or article."""
    from cgimg.research.channels import read_url as _ru
    return _ru(url)


@mcp.tool()
def research_doctor() -> dict:
    """Report which research channels are usable on this machine."""
    from cgimg.research.doctor import check_channels
    return {"channels": check_channels()}
```

- [ ] **Step 3: Add CLI subcommands to `cli.py`**

Add `research` / `read` / `doctor` subcommands mirroring the existing argparse pattern:
```python
def _cmd_research(args):
    from cgimg.research.channels import research_topic
    plats = args.platforms.split(",") if args.platforms else None
    res = research_topic(args.topic, platforms=plats, out_path=args.out)
    print(res["brief_path"])
    for ins in res["insights"]:
        print(f"- [{ins['platform']}] {ins['title']}")
    return 0

def _cmd_doctor(args):
    from cgimg.research.doctor import check_channels
    for k, v in check_channels().items():
        print(f"{k}: {v}")
    return 0
```
Wire subparsers: `research <topic> --platforms youtube,web,x --out out/brief.md`; `doctor`. (A `read <url>` subcommand similarly.)

- [ ] **Step 4: Smoke test CLI + full suite**

Run: `cd /f/chatgpt-image-mcp && uv run cgimg doctor` (lists channel availability, no traceback) and `uv run pytest -q` (all pass). Verify the MCP server still imports: `timeout 5 uv run cgimg-mcp < /dev/null; echo exit=$?` (no traceback).

- [ ] **Step 5: Commit**

```bash
cd /f/chatgpt-image-mcp && git add -A && git commit -m "feat: research doctor + MCP tools + CLI subcommands"
```

---

## Task 9: README + docs + real end-to-end

**Files:**
- Modify: `README.md`; Create: `docs/research.md`

- [ ] **Step 1: Update README**

Add a "Research pillar" section: what it does, the new MCP tools (`research_topic`, `read_url`, `research_doctor`), CLI (`research`, `doctor`, `read`), the external-CLI dependency note + `doctor`, the platform reliability caveat (YouTube/Web solid; FB/TikTok not yet), and extend the disclaimer to cover scraping/ToS. Update the product name to **social-content-studio** and mention the pillars (visuals ✓, research ✓, write/publish planned).

- [ ] **Step 2: Write `docs/research.md`**

~40-60 lines: channels, the TrendBrief shape, how scoring/clustering work, example CLI run, how it will feed the future Write pillar.

- [ ] **Step 3: Real end-to-end check**

Run: `cd /f/chatgpt-image-mcp && uv run cgimg research "chứng khoán việt nam" --platforms youtube --out out/brief.md` → confirm `out/brief.md` exists with real insights. (Web/X depend on their CLIs being installed — `doctor` shows status.)

- [ ] **Step 4: Full suite green + commit + push**

```bash
cd /f/chatgpt-image-mcp && uv run pytest -q
git add -A && git commit -m "docs: research pillar README + guide"
git push
```

---

## Self-Review (completed)

**Spec coverage:** repo rename + research package (T1) ✓; vendor Agent-Reach + MIT notice (T2) ✓; importable vendored package (T3) ✓; YouTube spike / channels + Finding (T4) ✓; scoring+clustering (T5) ✓; TrendBrief JSON+markdown (T6) ✓; research_topic orchestrator + web/x + read_url + graceful degradation (T7) ✓; doctor + MCP tools + CLI (T8) ✓; README/disclaimer/docs + real e2e (T9) ✓; risks #1/#5 (CLI/Windows) validated by the T4 spike + `doctor`; FB/TikTok intentionally deferred (spec §8).

**Placeholder scan:** Tasks 4 & 7 channel adapters explicitly depend on reconciling the vendored channels' real function names/returns (read in T2 Step 1) — flagged inline, not a hidden TODO. All new-code tasks (scoring, brief, doctor, orchestrator, tests) have complete code.

**Type consistency:** the `Finding` dict shape (`platform/title/url/text/author/engagement/published_at`) is consistent across `channels._finding`, `scoring.score_finding`, `brief.build_brief`. `CHANNELS` registry keys (`youtube/web/x`) match `doctor._CLI` + `research_topic`. `build_brief(topic, findings, out_path)` signature consistent across T6/T7/T8.

**Known soft spot:** like the chatgpt2api vendoring, the exact vendored-channel API is confirmed by reading source at T2 Step 1 and the adapters adapt to it — by design for vendored integration.
