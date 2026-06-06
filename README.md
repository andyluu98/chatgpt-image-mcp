# cgimg — ChatGPT Image MCP Server

A standalone MCP server (and CLI) that generates images through the ChatGPT web backend and assembles them into full-bleed PowerPoint decks.

## ⚠️ Disclaimer

This project **reverse-engineers the ChatGPT web backend** for image generation. It is provided **for personal learning and research only**.

- **Not affiliated with, endorsed by, or sponsored by OpenAI.**
- Using it **violates OpenAI's Terms of Service**. Your account may be rate-limited or **permanently banned**.
- **Use a throwaway / secondary account — never your important one.**
- Provided **as-is, with no warranty**. You assume all risk.

If you are not comfortable with these terms, do not use this software.

## What it does

- Generates images from text prompts at a chosen aspect ratio (16:9, 1:1, 3:4, 9:16, or raw `WxH`).
- Builds full-bleed PowerPoint (`.pptx`) decks from a set of images.
- Works as an MCP server across **Claude Code, Codex, and Antigravity** over stdio.
- Single-account, fully local auth — your token never leaves your machine.

## Requirements

- **Python ≥ 3.12**
- [**uv**](https://docs.astral.sh/uv/) (package manager / runner)
- A **ChatGPT account** (use a secondary one — see disclaimer)

## Install

```bash
git clone <repo-url> && cd chatgpt-image-mcp
uv sync
uv run cgimg login
# A browser opens -> log into ChatGPT -> you land on a platform.openai.com page (it may say "Oops").
# Copy the FULL callback URL from the address bar, then run:
uv run cgimg login --callback "<paste the callback URL here>"
```

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
      "cwd": "F:\\chatgpt-image-mcp"
    }
  }
}
```

Replace `cwd` with the absolute path where you cloned the repo. For Claude Code you can instead run:

```bash
claude mcp add chatgpt-image -- uv run cgimg-mcp
```

## MCP tools

| Tool | Params | Description |
|------|--------|-------------|
| `login_status` | — | Check whether a ChatGPT account is logged in. |
| `generate_image` | `prompt`, `aspect="16:9"`, `n=1`, `out_dir="out"` | Generate `n` image(s) from a prompt. Returns saved PNG paths. |
| `build_pptx` | `image_paths`, `out_path="deck.pptx"`, `aspect="16:9"` | Assemble existing images into a full-bleed PPTX. |
| `generate_slide_deck` | `prompts`, `aspect="16:9"`, `out_pptx="deck.pptx"`, `out_dir="out"` | Generate one image per prompt, then assemble into a PPTX. |

## CLI usage

```bash
# 1. Log in (two-step, see Install above)
uv run cgimg login
uv run cgimg login --callback "<paste callback URL>"

# 2. Generate image(s)
uv run cgimg gen "a serene mountain lake at dawn" --aspect 16:9 --n 1 --out out

# 3. Build a deck from images
uv run cgimg ppt img1.png img2.png --out deck.pptx --aspect 16:9
```

## Aspect ratios

| Aspect | Size sent | ChatGPT returns |
|--------|-----------|-----------------|
| `16:9` | 1920x1080 | 1672x941 |
| `1:1`  | 1024x1024 | 1024x1024 |
| `3:4`  | 1024x1536 | 1086x1448 |
| `9:16` | 1080x1920 | 941x1672 |
| `WxH`  | as given  | normalized by ChatGPT |

ChatGPT honors the **ratio**, not exact pixels — it normalizes to its own native dimensions (so `16:9` yields `1672x941`, not exactly `1920x1080`). This is expected.

PPTX output is **full-bleed**: the image fills the slide edge to edge, so the image aspect should match the deck aspect to avoid cropping or letterboxing.

## How it works

- Vendors [chatgpt2api](https://github.com/basketikun/chatgpt2api)'s proven OAuth + image backend (under `src/cgimg/_vendor/`).
- Stores a single account token locally at `%APPDATA%\cgimg\auth.json` (Windows) or `~/.config/cgimg/auth.json` (Linux/macOS).
- Auto-refreshes the access token via the stored `refresh_token` when it expires.

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `not logged in` | Run `uv run cgimg login` (two steps). |
| Token expired / auth errors | Re-run the login flow. |
| Generation is slow (~30–90s) | Normal — it polls ChatGPT until the image is ready. |
| Prompt rejected / blocked | ChatGPT's content moderation refused it. Adjust the prompt. |
| Image dims aren't exactly what you asked | Expected — ChatGPT honors the ratio and normalizes to its native size. |

## Attribution & License

This project vendors code from [**chatgpt2api**](https://github.com/basketikun/chatgpt2api), Copyright (c) 2026 kunkun, MIT License. Vendored files live under `src/cgimg/_vendor/` and retain their original behavior. See [`NOTICE`](./NOTICE) for details.
