#!/usr/bin/env bash
# One-shot setup for the aso-store-screenshots skill (macOS).
# Installs Pillow, @houtini/gemini-mcp, registers the MCP server with
# Claude Code, and checks the SF Pro font + GEMINI_API_KEY.
# Safe to re-run — every step is idempotent.

set -u
ok()   { printf "\033[32m✓ %s\033[0m\n" "$1"; }
warn() { printf "\033[33m! %s\033[0m\n" "$1"; }
fail() { printf "\033[31m✗ %s\033[0m\n" "$1"; }

echo "── aso-store-screenshots setup ──────────────────────────"

# 1. Python + Pillow ─────────────────────────────────────────
if ! command -v python3 >/dev/null; then
  fail "python3 not found — install Xcode Command Line Tools: xcode-select --install"
  exit 1
fi
if python3 -c "import PIL" 2>/dev/null; then
  ok "Pillow already installed ($(python3 -c 'import PIL; print(PIL.__version__)'))"
else
  echo "Installing Pillow…"
  python3 -m pip install Pillow 2>/dev/null \
    || python3 -m pip install --user Pillow 2>/dev/null \
    || python3 -m pip install --break-system-packages Pillow \
    || { fail "Pillow install failed — run manually: python3 -m pip install Pillow"; exit 1; }
  ok "Pillow installed"
fi

# 2. Headline font ───────────────────────────────────────────
if [ -f "/Library/Fonts/SF-Pro-Display-Black.otf" ]; then
  ok "SF Pro Display Black found"
else
  warn "SF Pro Display Black missing (scripts fall back to a lesser font)."
  warn "Get it: https://developer.apple.com/fonts/ → download 'SF Pro' → run the .pkg"
  warn "Expected at: /Library/Fonts/SF-Pro-Display-Black.otf"
fi

# 3. gemini-mcp (AI enhancement) ─────────────────────────────
if ! command -v npm >/dev/null; then
  fail "npm not found — install Node.js first: https://nodejs.org (or: brew install node)"
  exit 1
fi
if npm ls -g @houtini/gemini-mcp >/dev/null 2>&1; then
  ok "@houtini/gemini-mcp already installed globally"
else
  echo "Installing @houtini/gemini-mcp globally…"
  npm install -g @houtini/gemini-mcp || { fail "npm install failed"; exit 1; }
  ok "@houtini/gemini-mcp installed"
fi

# 4. GEMINI_API_KEY ──────────────────────────────────────────
KEY_SET=0
if [ -n "${GEMINI_API_KEY:-}" ]; then
  KEY_SET=1
  ok "GEMINI_API_KEY is set in this shell"
else
  warn "GEMINI_API_KEY not set. Get a key at https://aistudio.google.com/apikey then add to ~/.zshrc:"
  warn '  export GEMINI_API_KEY="your-key-here"'
fi

# 5. Register MCP server with Claude Code ────────────────────
if ! command -v claude >/dev/null; then
  fail "claude CLI not found in PATH — is Claude Code installed?"
  exit 1
fi
if claude mcp list 2>/dev/null | grep -q "gemini-mcp"; then
  ok "gemini-mcp already registered with Claude Code"
elif [ "$KEY_SET" = "1" ]; then
  claude mcp add gemini-mcp -s user -e GEMINI_API_KEY="$GEMINI_API_KEY" -- npx -y @houtini/gemini-mcp \
    && ok "gemini-mcp registered with Claude Code (user scope)" \
    || fail "claude mcp add failed — run manually: claude mcp add gemini-mcp -s user -e GEMINI_API_KEY=\$GEMINI_API_KEY -- npx -y @houtini/gemini-mcp"
else
  warn "Skipping MCP registration until GEMINI_API_KEY is set. Then run:"
  warn '  claude mcp add gemini-mcp -s user -e GEMINI_API_KEY="$GEMINI_API_KEY" -- npx -y @houtini/gemini-mcp'
fi

# 6. Skill presence ──────────────────────────────────────────
if [ -f "$HOME/.claude/skills/aso-store-screenshots/SKILL.md" ]; then
  ok "Skill installed at ~/.claude/skills/aso-store-screenshots"
else
  warn "Skill not found at ~/.claude/skills/aso-store-screenshots — copy it there:"
  warn "  cp -R $(cd "$(dirname "$0")" && pwd) ~/.claude/skills/aso-store-screenshots"
fi

echo "─────────────────────────────────────────────────────────"
echo "Done. Open a NEW Claude Code session, run /doctor to confirm the"
echo "skill is discovered (not context-stripped), then /aso-store-screenshots."
