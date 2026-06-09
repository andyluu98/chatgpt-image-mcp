# social-content-studio

An MCP server (and CLI) for end-to-end social content. It is built as three pillars:

- **Visuals ✅** — generate images through the ChatGPT web backend and assemble them into full-bleed PowerPoint decks (brand-aware and reference-styled).
- **Research ✅** — give it a topic, it scrapes YouTube / X / the web, ranks what's trending, and writes a **TrendBrief** that feeds content writing.
- **Write / Publish 🚧 (planned)** — turn a brief into drafts and push them to platforms.

> The package and commands are still named `cgimg` (the original ChatGPT-image tool it grew from). The product as a whole is `social-content-studio`.

## ⚠️ Disclaimer

This project is provided **for personal learning and research only**. It has two independent risk surfaces:

**Visuals pillar — reverse-engineers the ChatGPT web backend:**
- **Not affiliated with, endorsed by, or sponsored by OpenAI.**
- Using it **violates OpenAI's Terms of Service**. Your account may be rate-limited or **permanently banned**.
- **Use a throwaway / secondary account — never your important one.**

**Research pillar — scrapes third-party platforms:**
- It drives free external CLIs (yt-dlp, etc.) and web readers to **scrape YouTube, X, and websites**. This may violate those platforms' Terms of Service and is subject to their rate limits and scraping defenses.
- Scrapers are fragile by nature — a platform change can break a channel at any time.
- Scrape only public data, respect robots/ToS, and use it responsibly.

Provided **as-is, with no warranty**. You assume all risk. If you are not comfortable with these terms, do not use this software.

## What it does

### Visuals pillar

- Generates images from text prompts at a chosen aspect ratio (16:9, 1:1, 3:4, 9:16, or raw `WxH`).
- **Auto-enhances** prompts via your ChatGPT account's text model before drawing (mirrors what the web UI does silently). Three slide styles: `auto`, `slide`, `fintech`.
- Builds full-bleed PowerPoint (`.pptx`) decks from a set of images.
- **Branded decks**: auto-detects brand colors from your logo, generates slides in those colors, and composites your logo onto every slide.
- **Styled decks**: matches the design style and palette of a reference image (without copying its text/content).
- Works as an MCP server across **Claude Code, Codex, and Antigravity** over stdio.
- Single-account, fully local auth — your token never leaves your machine.

### Research pillar

- Takes a **topic** → scrapes YouTube / X / the web → ranks results by engagement → writes a **TrendBrief** (markdown + structured insights) you can hand to content writing.
- Uses **free external CLIs** (yt-dlp bundled; others optional) — **no ChatGPT account or token needed** (unlike the visuals pillar).
- Reads any web page/article to clean text (`read_url`), and ships a `doctor` that tells you which channels work on your machine.

See [**Research pillar**](#research-pillar-1) below for tools, CLI, and caveats, plus [`docs/research.md`](./docs/research.md) for the full guide.

## Requirements

- **[uv](https://docs.astral.sh/uv/)** — handles Python and dependencies (you do **not** need to install Python separately; `uv` fetches Python 3.12 automatically).
- **git**
- A **ChatGPT account** (use a secondary one — see disclaimer)

Install `uv` (one time per machine):

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

### One-click installer (recommended)

After cloning, run the installer — it installs `uv` if missing, syncs deps, walks you through login, and registers the MCP server:

```bash
git clone https://github.com/andyluu98/awesome-chatgpt-mcp-image.git
cd awesome-chatgpt-mcp-image
```
```powershell
# Windows (PowerShell) — or right-click install.ps1 -> Run with PowerShell
powershell -ExecutionPolicy Bypass -File install.ps1
```
```bash
# macOS / Linux
bash install.sh
```

### Manual install

```bash
git clone https://github.com/andyluu98/awesome-chatgpt-mcp-image.git
cd awesome-chatgpt-mcp-image
uv sync
uv run cgimg login
# A browser opens -> log into ChatGPT -> you land on a platform.openai.com page (it may say "Oops").
# Copy the FULL callback URL from the address bar, then run:
uv run cgimg login --callback "<paste the callback URL here>"
```

> The repo is **private** — the cloning machine must be signed into a GitHub account with access (e.g. `gh auth login`, or git credentials for `andyluu98`).

### Why login is two steps

Login uses OAuth with PKCE. Step 1 builds the authorization URL and stashes a one-time secret (the PKCE *verifier*) on disk. Step 2 exchanges the code in the callback URL for tokens — and that exchange needs the **same verifier** that step 1 generated. Splitting it into two commands lets the verifier persist between building the URL and redeeming the code, instead of being lost when the browser hands control back to you.

## Register as an MCP server

The config is the **same shape for Claude Code, Codex, and Antigravity**:

```json
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "uv",
      "args": ["run", "cgimg-mcp"],
      "cwd": "<absolute path to the cloned repo>"
    }
  }
}
```

Replace `cwd` with the absolute path where you cloned the repo (e.g. `F:\\chatgpt-image-mcp` on Windows — note the doubled backslashes in JSON). For Claude Code you can instead run:

```bash
claude mcp add chatgpt-image -- uv run cgimg-mcp
```

## MCP tools

Nine tools are exposed by the server (`src/cgimg/server.py`) — six for visuals, three for research.

**Visuals:**

| Tool | Params | Returns | Description |
|------|--------|---------|-------------|
| `login_status` | — | `{authed, ...}` | Check whether a ChatGPT account is logged in. |
| `generate_image` | `prompt`, `aspect="16:9"`, `n=1`, `out_dir="out"`, `enhance=True`, `style="auto"` | `{paths}` | Generate `n` image(s) from a prompt. Returns saved PNG paths. |
| `build_pptx` | `image_paths`, `out_path="deck.pptx"`, `aspect="16:9"` | `{path}` | Assemble existing images into a full-bleed PPTX. |
| `generate_slide_deck` | `prompts`, `aspect="16:9"`, `out_pptx="deck.pptx"`, `out_dir="out"`, `enhance=True`, `style="slide"` | `{path, image_paths}` | Generate one image per prompt (one slide each), then assemble into a PPTX. |
| `branded_deck` | `logo_path`, `prompts`, `aspect="16:9"`, `out_pptx="deck.pptx"`, `out_dir="out"`, `logo_position="top-left"`, `logo_scale=0.15` | `{path, image_paths, brand_colors}` | Auto-detects brand colors from the logo, generates slides in those colors, and composites the **original logo** onto each slide. |
| `styled_deck` | `ref_image`, `prompts`, `aspect="16:9"`, `out_pptx="deck.pptx"`, `out_dir="out"` | `{path, image_paths, brand_colors}` | Matches a **reference image's** design style + colors (does **not** copy its text/content). |

For `generate_slide_deck` / `branded_deck` / `styled_deck`, each prompt is the **content of one slide** — pass raw slide content and the enhancer designs it.

## Slide styles

When `enhance=True`, the prompt is expanded by your ChatGPT account's text model before drawing. The `style` argument picks the design treatment:

| Style | Look | Enhancement |
|-------|------|-------------|
| `auto` | General — a dense infographic, or a photographic scene if the prompt names a real scene. | Skipped if the prompt is already long (≥280 chars). |
| `slide` | Clean editorial presentation slide: light cream background, ONE warm accent color, a soft 3D hero visual, slide-number pill, bottom takeaway banner. | **Always runs.** |
| `fintech` | Premium light-blue dashboard look: glassmorphism cards, circular blue-gradient icon badges, optional 3D robot + chart widgets, bottom blue banner. | **Always runs.** |

**Content completion (for `slide` / `fintech`):** these styles complete your content into a **full, information-rich slide** — every main point gets a bold label **plus** a 2-line supporting description, sparse input is intelligently expanded into a sensible slide, and the prompt explicitly demands that **all** text be rendered in full (never dropped or abbreviated). It stays legible (not a wall of tiny text) and never fabricates fake statistics. See [`docs/styles.md`](./docs/styles.md) for a full reference.

> `generate_image` and the CLI `gen` accept `style` values `auto`, `slide`, and `fintech`. `generate_slide_deck` defaults to `slide`.

## CLI usage

```bash
# 1. Log in (two-step, see Install above)
uv run cgimg login
uv run cgimg login --callback "<paste callback URL>"

# 2. Generate image(s)  (auto-enhance is ON by default; add --no-enhance to send the prompt as-is)
uv run cgimg gen "a serene mountain lake at dawn" --aspect 16:9 --n 1 --out out
uv run cgimg gen "AI agents for customer support" --style slide      # clean editorial slide
uv run cgimg gen "real-time fraud detection" --style fintech         # light-blue dashboard slide
uv run cgimg gen "ai agent" --aspect 1:1 --no-enhance                # send prompt verbatim

# 3. Build a deck from existing images
uv run cgimg ppt img1.png img2.png --out deck.pptx --aspect 16:9

# 4. Branded deck — slides in your brand colors with your logo composited on each
uv run cgimg branded logo.png \
  --prompts "What is RAG?" "RAG pipeline" "Benefits" \
  --out deck.pptx --position top-left --scale 0.15

# 5. Styled deck — match a reference image's design (its text/content is NOT copied)
uv run cgimg styled reference-slide.png \
  --prompts "Intro" "How it works" "Pricing" \
  --out deck.pptx
```

`branded` and `styled` also accept `--aspect` and `--out-dir` (default `out`). They print the deck path, the detected `brand_colors`, and each generated image path.

## Aspect ratios

| Aspect | Size sent | ChatGPT returns |
|--------|-----------|-----------------|
| `16:9` | 1920x1080 | ~1672x941 |
| `1:1`  | 1024x1024 | 1024x1024 |
| `3:4`  | 1024x1536 | ~1086x1448 |
| `9:16` | 1080x1920 | ~941x1672 |
| `WxH`  | as given  | normalized by ChatGPT |

ChatGPT honors the **ratio**, not exact pixels — it normalizes to its own native dimensions (so `16:9` yields roughly `1672x941`, not exactly `1920x1080`). This is expected.

PPTX output is **full-bleed**: the image fills the slide edge to edge, so the image aspect should match the deck aspect to avoid cropping or letterboxing.

## How it works

- Vendors [chatgpt2api](https://github.com/basketikun/chatgpt2api)'s proven OAuth + image backend (under `src/cgimg/_vendor/`).
- Stores a single account token locally at `%APPDATA%\cgimg\auth.json` (Windows) or `~/.config/cgimg/auth.json` (Linux/macOS). It is **never committed**.
- Auto-refreshes the access token via the stored `refresh_token` when it expires.

## Research pillar

The research pillar answers "what's trending on this topic?" so you have real, ranked material to write from. Flow:

```
topic ──► scrape youtube / x / web ──► score by engagement + cluster near-dup titles ──► TrendBrief (markdown + insights)
```

`channels.py` runs each platform's free CLI as a subprocess (`youtube` = yt-dlp; `x` = `twitter-cli` if installed), normalizes results to a common **Finding** shape, then `scoring.py` ranks by engagement and groups near-duplicate stories, and `brief.py` writes the **TrendBrief**. The brief is meant to feed the planned **write/publish** pillar.

### Research MCP tools

| Tool | Params | Returns | Description |
|------|--------|---------|-------------|
| `research_topic` | `topic`, `platforms=["youtube","x"]`, `limit=10`, `out_dir="out"` | `{brief_path, insights[], by_platform}` | Scrape the given platforms for the topic, rank + cluster, write `out_dir/brief.md`. `insights` = top stories (`title`, `platform`, `url`, `sources`, `score`); `by_platform` = per-platform finding counts. |
| `read_url` | `url` | `{title, text, meta}` | Extract a web page/article's title + main text (markdown) via Jina Reader. Returns empty text on failure (never raises). |
| `research_doctor` | — | `{channels}` | Report which research channels are usable on this machine (`{name: "ok"\|"missing"}`). |

### Research CLI

```bash
# Trend brief for a topic (YouTube only here — comma-separate to add more, e.g. youtube,x)
uv run cgimg research "chứng khoán việt nam" --platforms youtube --out out/brief.md

# Which channels work on this machine?
uv run cgimg doctor

# Read a web page/article to clean text
uv run cgimg read "https://example.com/some-article"
```

`research` prints the brief path then each ranked insight as `- [platform] <title>`. The full brief lands at `--out` (default `out/brief.md`).

### Dependencies & graceful degradation

Research calls **free external CLIs**, not a paid API:

- **yt-dlp** is bundled (a project dependency) — YouTube works out of the box.
- Other channels need their own tool installed (e.g. **`twitter-cli`** for X). If a tool is missing, that channel simply returns **no results** instead of crashing the run.
- Run **`uv run cgimg doctor`** to see what's available before relying on a channel.

### Platform reliability

| Platform | Status | Notes |
|----------|--------|-------|
| YouTube | ✅ Solid | via bundled yt-dlp |
| Web / `read_url` | ✅ Solid | via Jina Reader |
| X (Twitter) | ⚠️ Needs `twitter-cli` | degrades to empty if the CLI isn't installed |
| Facebook / TikTok | ❌ Not supported | free scraping is too fragile — future work |

> See the [Disclaimer](#️-disclaimer) — scraping these platforms carries ToS / rate-limit risk.

## Examples

Showcase slides generated by this server live in [`examples/sample-slides/`](./examples/sample-slides/) — a mix of `slide`/`fintech` styles, dense multi-task slides, custom layouts, and tables.

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `not logged in` | Run `uv run cgimg login` (two steps). |
| Token expired / auth errors | Re-run the login flow. |
| Generation is slow (~30–90s per image) | Normal — it polls ChatGPT until the image is ready. |
| Prompt rejected / blocked | ChatGPT's content moderation refused it. Adjust the prompt and retry — refusals are often transient (`styled_deck` auto-retries up to 3×). |
| Text in the image looks imperfect on a very dense slide | Image models can garble small text when a slide is packed. Reduce the content or split into more slides. |
| Image dims aren't exactly what you asked | Expected — ChatGPT honors the ratio and normalizes to its native size. |

## Attribution & License

This project vendors code from:

- [**chatgpt2api**](https://github.com/basketikun/chatgpt2api) — Copyright (c) 2026 kunkun, MIT License. Powers the visuals pillar's OAuth + image backend. Vendored under `src/cgimg/_vendor/`.
- [**Agent-Reach**](https://github.com/Panniantong/Agent-Reach) — Copyright (c) 2025 Agent Eyes, MIT License. Powers the research pillar's `read_url` (Jina Reader) and the `doctor` channel diagnostic. Vendored under `src/cgimg/research/agent_reach/`.

Vendored files retain their original behavior. See [`NOTICE`](./NOTICE) for details.
