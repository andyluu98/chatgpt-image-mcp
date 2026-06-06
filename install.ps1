# cgimg one-click installer (Windows / PowerShell)
# Usage: right-click -> "Run with PowerShell", or:  powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot

function Section($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Ok($msg)      { Write-Host "[OK] $msg"      -ForegroundColor Green }
function Warn($msg)    { Write-Host "[!] $msg"       -ForegroundColor Yellow }

Write-Host @"
==============================================
  cgimg - ChatGPT Image MCP Server installer
==============================================
WARNING: reverse-engineers ChatGPT (violates OpenAI ToS, account-ban risk).
Use a secondary/throwaway account. Press Ctrl+C now to abort.
"@ -ForegroundColor Magenta
Start-Sleep -Seconds 1

# 1. Ensure uv is installed -------------------------------------------------
Section "1/4  Checking uv"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Warn "uv not found. Installing..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    # Make uv available in THIS session (installer puts it under ~\.local\bin).
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv installed but not on PATH. Open a NEW terminal and re-run this script."
    }
}
Ok "uv: $(uv --version)"

# 2. Install dependencies ---------------------------------------------------
Section "2/4  Installing dependencies (uv sync)"
Push-Location $repo
uv sync
Ok "Dependencies installed."

# 3. Login to ChatGPT (two-step OAuth, interactive) -------------------------
Section "3/4  Login to ChatGPT"
$status = (uv run python -c "from cgimg.auth import tokens; print(tokens.login_status().get('authed'))").Trim()
if ($status -eq "True") {
    Warn "Already logged in."
    $relog = Read-Host "Re-login? (y/N)"
    if ($relog -notmatch '^[Yy]') { $skipLogin = $true }
}
if (-not $skipLogin) {
    Write-Host "A browser will open. Log into ChatGPT, then you'll land on a" -ForegroundColor White
    Write-Host "platform.openai.com page (it may say 'Oops' - that's fine)." -ForegroundColor White
    Write-Host ""
    uv run cgimg login    # opens browser, prints URL, stashes PKCE verifier
    Write-Host ""
    $cb = Read-Host "Paste the FULL callback URL from the address bar here"
    if ([string]::IsNullOrWhiteSpace($cb)) { throw "No callback URL provided. Re-run the script." }
    uv run cgimg login --callback "$cb"
}
$status = (uv run python -c "from cgimg.auth import tokens; print(tokens.login_status().get('authed'))").Trim()
if ($status -ne "True") { throw "Login did not complete. Re-run the script." }
Ok "Logged in."

# 4. Register as an MCP server ----------------------------------------------
Section "4/4  Register MCP server"
$cwdJson = $repo -replace '\\', '\\'
$config = @"
{
  "mcpServers": {
    "chatgpt-image": {
      "command": "uv",
      "args": ["run", "cgimg-mcp"],
      "cwd": "$cwdJson"
    }
  }
}
"@
Write-Host "MCP config for Claude Code / Codex / Antigravity:" -ForegroundColor White
Write-Host $config -ForegroundColor Gray

$addCC = Read-Host "`nAuto-register with Claude Code via 'claude mcp add'? (y/N)"
if ($addCC -match '^[Yy]') {
    try {
        claude mcp add chatgpt-image -- uv run cgimg-mcp
        Ok "Registered with Claude Code. Restart Claude Code to load it."
    } catch {
        Warn "Could not run 'claude mcp add'. Add the JSON above to your MCP config manually."
    }
} else {
    Write-Host "Add the JSON above to your MCP client config manually." -ForegroundColor White
}

Pop-Location
Write-Host "`n[DONE] cgimg is ready." -ForegroundColor Green
Write-Host "Try it:  uv run cgimg gen `"ai agent`" --aspect 1:1" -ForegroundColor White
