#!/usr/bin/env bash
# cgimg one-click installer (macOS / Linux)
# Usage:  bash install.sh
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cyan()  { printf '\n=== %s ===\n' "$1"; }
ok()    { printf '[OK] %s\n' "$1"; }
warn()  { printf '[!] %s\n' "$1"; }

cat <<'EOF'
==============================================
  cgimg - ChatGPT Image MCP Server installer
==============================================
WARNING: reverse-engineers ChatGPT (violates OpenAI ToS, account-ban risk).
Use a secondary/throwaway account. Press Ctrl+C now to abort.
EOF
sleep 1

# 1. Ensure uv ---------------------------------------------------------------
cyan "1/4  Checking uv"
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 || { echo "uv installed but not on PATH. Open a new terminal and re-run."; exit 1; }
fi
ok "uv: $(uv --version)"

# 2. Dependencies ------------------------------------------------------------
cyan "2/4  Installing dependencies (uv sync)"
cd "$repo"
uv sync
ok "Dependencies installed."

# 3. Login (two-step OAuth, interactive) ------------------------------------
cyan "3/4  Login to ChatGPT"
authed="$(uv run python -c 'from cgimg.auth import tokens; print(tokens.login_status().get("authed"))' | tr -d '[:space:]')"
skip_login=""
if [ "$authed" = "True" ]; then
  warn "Already logged in."
  read -r -p "Re-login? (y/N) " relog
  [[ "$relog" =~ ^[Yy] ]] || skip_login=1
fi
if [ -z "$skip_login" ]; then
  echo "A browser will open. Log into ChatGPT, then you'll land on a"
  echo "platform.openai.com page (it may say 'Oops' - that's fine)."
  echo
  uv run cgimg login        # opens browser, prints URL, stashes PKCE verifier
  echo
  read -r -p "Paste the FULL callback URL from the address bar here: " cb
  [ -n "$cb" ] || { echo "No callback URL provided. Re-run the script."; exit 1; }
  uv run cgimg login --callback "$cb"
fi
authed="$(uv run python -c 'from cgimg.auth import tokens; print(tokens.login_status().get("authed"))' | tr -d '[:space:]')"
[ "$authed" = "True" ] || { echo "Login did not complete. Re-run the script."; exit 1; }
ok "Logged in."

# 4. MCP registration --------------------------------------------------------
cyan "4/4  Register MCP server"
cat <<EOF
MCP config for Claude Code / Codex / Antigravity:
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "uv",
      "args": ["run", "cgimg-mcp"],
      "cwd": "$repo"
    }
  }
}
EOF
read -r -p "Auto-register with Claude Code via 'claude mcp add'? (y/N) " addcc
if [[ "$addcc" =~ ^[Yy] ]]; then
  if claude mcp add chatgpt-image -- uv run cgimg-mcp; then
    ok "Registered with Claude Code. Restart Claude Code to load it."
  else
    warn "Could not run 'claude mcp add'. Add the JSON above to your MCP config manually."
  fi
else
  echo "Add the JSON above to your MCP client config manually."
fi

printf '\n[DONE] cgimg is ready.\n'
echo 'Try it:  uv run cgimg gen "ai agent" --aspect 1:1'
