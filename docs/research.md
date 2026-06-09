# Research pillar

The research pillar turns a **topic** into a ranked **TrendBrief** you can write content from.
It scrapes platforms with free external CLIs, scores results by engagement, clusters
near-duplicate stories, and writes a markdown brief plus a structured dict.

```
topic ──► channels (scrape) ──► scoring (rank + cluster) ──► brief (TrendBrief)
```

## Channels (`research/channels.py`)

Each channel runs a free CLI as a subprocess and normalizes output to a **Finding**.
A channel that errors or whose CLI is missing returns `[]` — it never aborts the run.

| Channel | How | Status |
|---------|-----|--------|
| `youtube` | `yt-dlp "ytsearch{N}:{topic}" --dump-json --flat-playlist` | Solid (yt-dlp bundled) |
| `x` | `twitter-cli search` (also `twitter` / `bird`) if installed | Optional — empty if CLI absent |
| web (`read_url`) | vendored Agent-Reach `WebChannel` (Jina Reader) → clean markdown | Solid |

`doctor` (`research/doctor.py`) reports `{channel: "ok"|"missing"}`. It prefers Agent-Reach's
own `check_all`, falling back to a simple CLI-presence check. On a typical machine
`youtube`, `web` are ok. Facebook / TikTok are **not** implemented (free scraping too fragile).

### Finding shape

Every channel returns a list of these dicts:

```python
{
  "platform": str,        # "youtube" | "x" | ...
  "title": str,
  "url": str,
  "text": str,            # description / body
  "author": str,
  "engagement": {"views": int, "likes": int, "comments": int},
  "published_at": str | None,
}
```

> **yt-dlp flat-mode limitation:** `--flat-playlist` is fast but only reliably returns
> **views**; **likes/comments are usually absent** (0) in this mode. Scoring still works —
> views alone rank the list — but engagement is coarser than a full per-video fetch.

## Scoring & clustering (`research/scoring.py`)

- **Score** = `views×1 + likes×20 + comments×50` — comments/likes signal stronger intent
  than passive views, so they weigh more.
- **Rank** sorts findings by score, highest first.
- **Cluster** groups near-duplicate stories by title similarity (`difflib` ratio ≥ 0.80,
  punctuation/case-normalized). The highest-scoring member becomes the cluster **lead**;
  the rest are recorded as additional **sources** for that story.

## TrendBrief output (`research/brief.py`)

`build_brief(topic, findings, out_path)` writes markdown to `out_path` and returns:

```python
{
  "brief_path": "out/brief.md",
  "insights": [ {"title", "platform", "url", "sources": [...], "score"}, ... ],
  "by_platform": {"youtube": 10},   # finding counts per platform
}
```

The markdown has a title, a "N chủ đề nổi bật từ M nguồn" summary, one `##` section per
insight (platform · source count · link), and a per-platform footer.

## Example run

```bash
uv run cgimg research "chứng khoán việt nam" --platforms youtube --out out/brief.md
```

Prints the brief path then each ranked insight, and writes `out/brief.md`:

```markdown
# Trend Brief — chứng khoán việt nam

**10 chủ đề nổi bật** từ 10 nguồn.

## 1. Giải thích về chứng khoán cho người chưa biết gì trong 11 phút
- Nền tảng: youtube · 1 nguồn
- Link: https://www.youtube.com/watch?v=SqcSkX_2yg4

## 2. CHỨNG KHOÁN VIỆT NAM ĐÃ BỊ THAO TÚNG NHƯ THẾ NÀO? | Gerard Do | TIỀN TÀI
- Nền tảng: youtube · 1 nguồn
- Link: https://www.youtube.com/watch?v=xHeZxq6OJOg

...
---
**Theo nền tảng:** youtube: 10
```

## Feeds the Write pillar

The TrendBrief is the handoff point: ranked, deduplicated, real topics with source links.
The planned **write/publish** pillar consumes `insights` to draft content grounded in what's
actually trending, rather than inventing topics from scratch.

## Attribution

The web reader and `doctor` diagnostic come from **Agent-Reach**
(https://github.com/Panniantong/Agent-Reach), © 2025 Agent Eyes, MIT License,
vendored under `src/cgimg/research/agent_reach/`. See [`NOTICE`](../NOTICE).
