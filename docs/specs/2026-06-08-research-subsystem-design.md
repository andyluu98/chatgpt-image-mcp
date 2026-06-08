# Social Content Studio — Research Subsystem Design Spec

**Date:** 2026-06-08
**Status:** Approved (design), pending implementation plan
**Author:** Cole + Claude
**Repo:** evolves `chatgpt-image-mcp` → **`social-content-studio`**

---

## 1. Context & Big Picture

The existing `cgimg` repo (image generation, logo compositing, deck building, MCP
server) becomes the **visuals** pillar of a larger **Social Content Studio**: a
pipeline of `research → write → visuals → publish`. This spec covers ONLY the first
new sub-project: **Research** (trend discovery / scraping). Other pillars are future
specs.

**Decisions already made:**
- **Publish** (future): reuse the already-connected `aitoearn` / `social-content`
  MCP servers — do NOT rebuild publishing.
- **Build location:** extend the current repo; rename to `social-content-studio`.
- **Research scrape mechanism:** **vendor Agent-Reach** (MIT, Python — verify license
  in phase 1).
- **Research purpose:** discover trends → produce a structured brief that feeds the
  future Write pillar.
- **Platforms:** YouTube, Web/news, X/Twitter + Threads (reliable); Facebook + TikTok
  (fragile — second wave).

---

## 2. Non-goals (this spec)
- No Write, Publish, or Orchestration pillars yet (future specs).
- No rebuild of publishing (use existing MCPs later).
- No paid scraping API (ScrapeCreators etc.) — free CLI tools only.

---

## 3. Repo Evolution

```
social-content-studio/                 (renamed from chatgpt-image-mcp)
├── src/cgimg/                          (KEEP — visuals pillar, unchanged)
│   ├── engine/ auth/ branding/ ppt/ _vendor/ server.py cli.py ...
│   └── research/                       (NEW — research pillar)
│       ├── __init__.py
│       ├── agent_reach/                (VENDORED Agent-Reach channels, MIT)
│       ├── channels.py                 (thin adapter over vendored channels)
│       ├── scoring.py                  (engagement scoring + clustering)
│       ├── brief.py                    (TrendBrief assembly: JSON + markdown)
│       └── doctor.py                   (channel health check + install helper)
├── docs/specs/ docs/plans/ ...
└── tests/
```

Visuals (`cgimg.engine`, `branding`, `ppt`) stay untouched. Research is an additive
package. MCP server + CLI gain new tools/subcommands.

> Note: the Python package stays `cgimg` internally to avoid a churny import rename;
> only the GitHub repo + product name change to `social-content-studio`. (A later
> spec may rename the package once the studio shape is stable.)

---

## 4. Vendoring Agent-Reach

- Source: https://github.com/Panniantong/Agent-Reach (Python, modular channels).
- **License: MIT** (Copyright (c) 2025 Agent Eyes) — vendoring permitted. Keep the
  MIT notice in vendored files + add attribution to NOTICE.
- Vendor the channel modules + the CLI-wrapper utilities under
  `src/cgimg/research/agent_reach/`.
- Agent-Reach wraps these external CLI tools (system deps, installed separately):
  `yt-dlp` (YouTube), `gh` (GitHub), `twitter-cli`/`rdt-cli` (X/Reddit),
  `feedparser` + Jina Reader (web/RSS), `xhs-cli` (XHS), etc.
- Provide `studio doctor` (which channels work) and `studio install` (install CLI
  deps) — adapted from Agent-Reach's `doctor` / `install`.

---

## 5. Research Flow

```
research_topic(topic, platforms, timeframe="30d")
  → for each requested platform: call the vendored Agent-Reach channel
      (search/read posts, transcripts, articles)
  → normalize results to a common Finding shape
  → score by engagement (upvotes/likes/views/comments, recency-weighted)
  → cluster near-duplicate findings across platforms into consolidated items
  → assemble a TrendBrief: ranked insights + sources + a markdown summary
  → return {brief_markdown, findings: [...], by_platform: {...}}
```

**Finding shape (normalized):**
`{platform, title, url, text, author, engagement: {likes, comments, views, ...},
published_at, score}`

**TrendBrief output:** structured JSON + a human-readable markdown brief (dark,
shareable — last30days style). This brief is the handoff artifact to the future
Write pillar.

---

## 6. Tools Exposed

**MCP tools** (added to `server.py`):
| Tool | Params | Returns |
|---|---|---|
| `research_topic` | `topic`, `platforms=[...]`, `timeframe="30d"`, `out_dir` | `{brief_path, findings, by_platform}` |
| `read_url` | `url` | `{title, text, meta}` (Jina/feedparser extraction) |
| `scrape_channel` | `platform`, `query`, `limit=20` | `{findings: [...]}` |
| `research_doctor` | — | `{channels: {name: ok|missing|error}}` |

**CLI subcommands** (added to `cli.py`):
- `studio research "<topic>" --platforms youtube,web,x --out brief.md`
- `studio read "<url>"`
- `studio doctor`
- `studio install`

(The existing `cgimg` CLI/`cgimg-mcp` entry points remain; a `studio` alias may be
added for the broader product.)

---

## 7. Feasibility Spike (phase 1, make-or-break)

Before building the full multi-platform layer, prove ONE reliable channel end-to-end:
**YouTube via `yt-dlp`** (most stable, no auth, free). `research_topic("...",
platforms=["youtube"])` must return a real brief from real YouTube data on this
machine. If the vendored Agent-Reach + yt-dlp pipeline works headless on Windows, the
architecture is viable; then add Web/RSS, X/Twitter, and finally FB/TikTok.

---

## 8. Risks (flagged)

1. **External CLI auth/setup** — each channel needs its own tool installed + (often)
   login/cookies. Windows setup may be painful. Mitigated by `doctor`/`install`.
   **Highest-friction item.**
2. **Facebook + TikTok free-scraping is fragile** — no robust free CLI; breaks when
   platforms change. Deferred to a second wave after the stable channels work.
3. ~~License~~ — **RESOLVED**: Agent-Reach is MIT, vendoring OK.
4. **ToS / legal** — scraping carries account-ban / legal risk, same class as the
   reverse-engineering in the visuals pillar. README disclaimer extended.
5. **Windows compatibility** — Agent-Reach is Linux-leaning; some CLI tools may need
   WSL or Windows-specific install. Verify in the spike.

---

## 9. Testing
- **Unit (offline):** `scoring.py` (engagement + recency ranking), clustering
  (dedupe near-identical findings), `brief.py` (markdown assembly from sample
  findings).
- **Integration (gated, network):** YouTube channel returns real findings for a known
  query — gated behind an env flag so CI without tools skips it.
- **Smoke:** `studio doctor` reports channel availability.

---

## 10. Open Questions
- None blocking. License (Risk #3) resolved: MIT. Windows CLI feasibility
  (Risks #1, #5) validated in phase 1 (spike) before building the full channel set.
