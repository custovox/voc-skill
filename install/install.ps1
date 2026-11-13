# voc-skill installer for Windows (PowerShell)
# Usage, from the downloaded folder:
#   powershell -ExecutionPolicy Bypass -File install\install.ps1
#
# What it does:
#   1. checks that "uv" is available (offers to install it otherwise);
#   2. copies the "voix-du-client" skill to ~/.claude/skills (Claude Code)
#      and ~/.agents/skills (Codex, Cursor);
#   3. registers the "voc" MCP server in Claude Code if the "claude" command exists,
#      and prints the configuration to paste for Codex and Cursor.

$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
$SkillSrc = Join-Path $Repo "skills\voix-du-client"

Write-Host "`n== voc-skill - installation ==`n" -ForegroundColor Cyan

# 1. uv (runs the Python MCP server and installs its dependencies automatically)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "'uv' is not installed. It is needed to run the MCP server."
    $answer = Read-Host "Install it now from https://astral.sh/uv ? [Y/n]"
    if ($answer -eq "" -or $answer -match "^[YyOo]") {
        powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    } else {
        Write-Host "Skipped. The skill will work without the MCP server (reduced mode)." -ForegroundColor Yellow
    }
}

# 2. Skill files
$Targets = @(
    (Join-Path $env:USERPROFILE ".claude\skills\voix-du-client"),
    (Join-Path $env:USERPROFILE ".agents\skills\voix-du-client")
)
foreach ($t in $Targets) {
    if (Test-Path $t) { Remove-Item -Recurse -Force $t }
    New-Item -ItemType Directory -Force (Split-Path -Parent $t) | Out-Null
    Copy-Item -Recurse $SkillSrc $t
    Write-Host "Skill copied to $t" -ForegroundColor Green
}

# 3. MCP server
$Cmd = "uv"
$McpArgs = @("--directory", $Repo, "run", "--quiet", "voc-mcp")
if (Get-Command claude -ErrorAction SilentlyContinue) {
    try { claude mcp remove --scope user voc *> $null } catch { }  # ignore "not found"
    claude mcp add --scope user voc -- $Cmd @McpArgs
    Write-Host "MCP server 'voc' registered in Claude Code (user scope)." -ForegroundColor Green
} else {
    Write-Host "Claude Code not found: skipping MCP registration." -ForegroundColor Yellow
}

$RepoJson = $Repo.Replace("\", "\\")
Write-Host @"

-- Codex: add to %USERPROFILE%\.codex\config.toml
[mcp_servers.voc]
command = "uv"
args = ["--directory", '$Repo', "run", "--quiet", "voc-mcp"]

-- Cursor: add to %USERPROFILE%\.cursor\mcp.json (inside "mcpServers")
"voc": { "command": "uv", "args": ["--directory", "$RepoJson", "run", "--quiet", "voc-mcp"] }

Done. Restart your agent, then try:
  "Analyse the customer reviews in examples\data with the voix-du-client skill"
"@
