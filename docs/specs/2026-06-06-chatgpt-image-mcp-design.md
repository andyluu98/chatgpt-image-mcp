# chatgpt-image-mcp — Design Spec

**Date:** 2026-06-06
**Status:** Approved (design), pending implementation plan
**Author:** Cole + Claude

---

## 1. Purpose

Standalone MCP server (Python) that lets an AI coding tool (Claude Code, Codex,
Antigravity) generate images via the reverse-engineered ChatGPT image backend and
assemble them into PowerPoint decks — **without** the chatgpt2api WebUI, account
pool, or Docker stack.

Core reverse-engineering (OAuth + image backend) is **extracted (vendored) from
chatgpt2api**, which is already proven working on this machine. New code is limited
to: a single-account token store, a thin MCP/CLI layer, and a PPT builder.

### Non-goals (v1)
- No WebUI, no multi-account pool, no Docker.
- No chat/text completion, no search, no PSD/editable-file generation.
- No image editing (`/v1/images/edits`) — generation only.

---

## 2. Risk & Legal Notice

- Reverse-engineers ChatGPT web backend → **account ban risk**, violates OpenAI ToS.
  README must carry the same disclaimer as chatgpt2api. Use throwaway accounts.
- chatgpt2api is **MIT licensed** (Copyright (c) 2026 kunkun) — vendoring is
  permitted. Keep the MIT copyright notice in vendored file headers and add a
  NOTICE/attribution in README.

---

## 3. Architecture

```
chatgpt-image-mcp/
├── README.md                  # install + auth + disclaimer
├── pyproject.toml             # deps: mcp, curl_cffi, pillow, python-pptx
├── .python-version
├── src/cgimg/
│   ├── __init__.py
│   ├── server.py              # MCP entry (FastMCP, stdio transport)
│   ├── cli.py                 # `cgimg login` / `gen` / `ppt`
│   ├── sizes.py               # aspect ratio → ChatGPT size mapping
│   ├── auth/
│   │   ├── oauth.py           # [VENDORED] OAuth PKCE flow, terminal variant
│   │   ├── pkce.py            # [VENDORED] from utils/pkce.py
│   │   ├── constants.py       # [VENDORED] client_id, redirect_uri, headers
│   │   └── tokens.py          # [NEW] single-account token store + refresh
│   ├── engine/
│   │   ├── image_api.py       # [VENDORED, TRIMMED] image-gen path only
│   │   ├── pow.py             # [VENDORED] from utils/pow.py
│   │   ├── turnstile.py       # [VENDORED] from utils/turnstile.py
│   │   ├── sentinel.py        # [VENDORED] from utils/sentinel.py
│   │   └── helper.py          # [VENDORED, TRIMMED] from utils/helper.py
│   └── ppt/
│       └── builder.py         # [NEW] python-pptx: images → pptx
└── tests/
```

**Module boundaries:**
- `auth/` owns getting and refreshing a valid `access_token`. Consumers call
  `tokens.get_access_token()` and never touch OAuth internals.
- `engine/` owns talking to the ChatGPT image backend. Input: prompt + size +
  access_token. Output: image bytes. Knows nothing about MCP or files.
- `ppt/` owns turning a list of image files into a .pptx. Pure local, no network.
- `server.py` / `cli.py` are thin orchestration layers over the three above.

---

## 4. MCP Tools (v1 scope)

| Tool | Input | Output |
|---|---|---|
| `login_status` | — | `{authed: bool, email, expires_at}` |
| `generate_image` | `prompt: str`, `aspect: str = "16:9"`, `n: int = 1`, `out_dir: str` | `{paths: [str]}` saved PNG files |
| `build_pptx` | `image_paths: [str]`, `out_path: str`, `aspect: str = "16:9"` | `{path: str}` |
| `generate_slide_deck` | `prompts: [str]`, `aspect: str = "16:9"`, `out_pptx: str` | gen N images → assemble pptx → `{path, image_paths}` |

`login` is a **CLI-only** command (`cgimg login`), not an MCP tool — it needs an
interactive browser + paste step that doesn't fit the MCP request/response model.

---

## 5. Aspect Ratio Mapping

Verified empirically against the running chatgpt2api on 2026-06-06.

| `aspect` value | sent `size` | ChatGPT returns |
|---|---|---|
| `16:9` | `1920x1080` | 1672×941 |
| `1:1` | `1024x1024` | 1024×1024 |
| `3:4` | `1024x1536` | 1086×1448 |
| `9:16` | `1080x1920` | 941×1672 |

- Raw `"WxH"` strings pass through unchanged.
- Unknown aspect → error with the list of valid values.
- ChatGPT normalizes to its own native dimensions; the **ratio** is honored, exact
  pixel size is not guaranteed.

---

## 6. Auth Flow

```
cgimg login
  1. print authorize_url, attempt to open default browser
  2. user logs into ChatGPT → lands on platform.openai.com "Oops" page
  3. user copies the full callback URL, pastes into terminal
  4. exchange code + PKCE verifier → {access_token, refresh_token, id_token}
  5. save to <config_dir>/cgimg/auth.json

generate_image (and any backend call)
  → check access_token expiry (decode id_token / track issued time)
  → if near expiry, refresh via refresh_token using OpenAI token endpoint
  → proceed with valid access_token
```

**Token storage:** `<config_dir>/cgimg/auth.json` where `<config_dir>` is
`%APPDATA%` on Windows / `~/.config` on Linux/macOS (use `platformdirs` or stdlib
equivalent). File permissions tightened where the OS allows.

---

## 7. Installation (clone-and-run)

```bash
git clone <repo> && cd chatgpt-image-mcp
uv sync                    # install deps
uv run cgimg login         # one-time OAuth
```

MCP registration (identical shape across Claude Code / Codex / Antigravity):
```json
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "uv",
      "args": ["run", "cgimg-mcp"],
      "cwd": "/absolute/path/to/chatgpt-image-mcp"
    }
  }
}
```
`cgimg-mcp` is a console-script entry point declared in `pyproject.toml` that runs
the FastMCP stdio server.

---

## 8. Error Handling

- **Not logged in** → tools return a clear "run `cgimg login` first" message.
- **Token refresh fails** → surface "re-login required", do not crash the server.
- **Content policy block** → propagate ChatGPT's moderation rejection as a tool error.
- **PoW / Turnstile failure** → distinct error so the user knows it's an
  anti-bot issue, not a prompt issue.
- **Image poll timeout** → return partial/timeout error with retry hint.
- Backend HTTP errors → wrapped, never leak raw tokens into logs.

---

## 9. Testing

- **Unit (offline):** `sizes.py` mapping, `ppt/builder.py` (build deck from local
  sample PNGs and assert slide count + dimensions), token expiry logic.
- **Integration (network, manual / gated):** full `generate_image` against a real
  logged-in account — gated behind an env flag so CI without auth skips it.
- **Smoke:** `cgimg login` round-trip documented as a manual test.

---

## 10. Implementation Risks (verify during build)

1. **PoW + Turnstile headless** — image generation requires solving a
   proof-of-work token and a Turnstile token. Must confirm the vendored
   `pow.py` / `turnstile.py` / `sentinel.py` work without a browser. If
   `turnstile.py` depends on an external solver service, that dependency must be
   surfaced and configured. **Highest-risk item.**
2. **Trimming `openai_backend_api.py` (2606 lines)** — chat/search/PSD/PPT logic
   is interleaved with image gen. Extracting only the image path without breaking
   shared helpers needs care. Fallback: vendor more of the file intact rather than
   over-trimming.
3. **`account_service.py` token refresh** — only the refresh-token keepalive slice
   is needed (not the 1677-line pool). Rewrite as a small single-account
   `tokens.py` rather than vendoring the whole service.
4. ~~License compatibility~~ — **RESOLVED**: chatgpt2api is MIT, vendoring OK.

---

## 11. Open Questions

- None blocking. License (Risk #4) resolved: MIT. PoW/Turnstile feasibility
  (Risk #1) to be validated in the first implementation phase before building
  further.
