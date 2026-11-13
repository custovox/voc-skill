#!/usr/bin/env bash
# voc-skill installer for macOS and Linux
# Usage, from the downloaded folder:   bash install/install.sh
#
# What it does:
#   1. checks that "uv" is available (offers to install it otherwise);
#   2. copies the "voix-du-client" skill to ~/.claude/skills (Claude Code)
#      and ~/.agents/skills (Codex, Cursor);
#   3. registers the "voc" MCP server in Claude Code if the "claude" command exists,
#      and prints the configuration to paste for Codex and Cursor.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$REPO/skills/voix-du-client"

printf "\n== voc-skill - installation ==\n\n"

# 1. uv (runs the Python MCP server and installs its dependencies automatically)
if ! command -v uv >/dev/null 2>&1; then
  echo "'uv' is not installed. It is needed to run the MCP server."
  read -r -p "Install it now from https://astral.sh/uv ? [Y/n] " answer
  if [[ -z "${answer}" || "${answer}" =~ ^[YyOo] ]]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "Skipped. The skill will work without the MCP server (reduced mode)."
  fi
fi

# 2. Skill files
for target in "$HOME/.claude/skills/voix-du-client" "$HOME/.agents/skills/voix-du-client"; do
  rm -rf "$target"
  mkdir -p "$(dirname "$target")"
  cp -R "$SKILL_SRC" "$target"
  echo "Skill copied to $target"
done

# 3. MCP server
if command -v claude >/dev/null 2>&1; then
  claude mcp remove --scope user voc >/dev/null 2>&1 || true
  claude mcp add --scope user voc -- uv --directory "$REPO" run --quiet voc-mcp
  echo "MCP server 'voc' registered in Claude Code (user scope)."
else
  echo "Claude Code not found: skipping MCP registration."
fi

cat <<EOF

-- Codex: add to ~/.codex/config.toml
[mcp_servers.voc]
command = "uv"
args = ["--directory", "$REPO", "run", "--quiet", "voc-mcp"]

-- Cursor: add to ~/.cursor/mcp.json (inside "mcpServers")
"voc": { "command": "uv", "args": ["--directory", "$REPO", "run", "--quiet", "voc-mcp"] }

Done. Restart your agent, then try:
  "Analyse the customer reviews in examples/data with the voix-du-client skill"
EOF
