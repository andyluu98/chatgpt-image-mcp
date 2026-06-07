# cgimg — ChatGPT Image MCP Server

A standalone MCP server (and CLI) that generates images through the ChatGPT web backend, then assembles them into full-bleed PowerPoint decks — including brand-aware and reference-styled decks.

## ⚠️ Disclaimer

This project **reverse-engineers the ChatGPT web backend** for image generation. It is provided **for personal learning and research only**.

- **Not affiliated with, endorsed by, or sponsored by OpenAI.**
- Using it **violates OpenAI's Terms of Service**. Your account may be rate-limited or **permanently banned**.
- **Use a throwaway / secondary account — never your important one.**
- Provided **as-is, with no warranty**. You assume all risk.

If you are not comfortable with these terms, do not use this software.

## What it does

- Generates images from text prompts at a chosen aspect ratio (16:9, 1:1, 3:4, 9:16, or raw `WxH`).
- **Auto-enhances** prompts via your ChatGPT account's text model before drawing (mirrors what the web UI does silently). Three slide styles: `auto`, `slide`, `fintech`.
- Builds full-bleed PowerPoint (`.pptx`) decks from a set of images.
- **Branded decks**: auto-detects brand colors from your logo, generates slides in those colors, and composites your logo onto every slide.
- **Styled decks**: matches the design style and palette of a reference image (without copying its text/content).
- Works as an MCP server across **Claude Code, Codex, and Antigravity** over stdio.
- Single-account, fully local auth — your token never leaves your machine.

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

Six tools are exposed by the server (`src/cgimg/server.py`):

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

This project vendors code from [**chatgpt2api**](https://github.com/basketikun/chatgpt2api), Copyright (c) 2026 kunkun, MIT License. Vendored files live under `src/cgimg/_vendor/` and retain their original behavior. See [`NOTICE`](./NOTICE) for details.
