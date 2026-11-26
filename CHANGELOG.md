# Changelog

Format inspired by [Keep a Changelog](https://keepachangelog.com/); versions follow [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-11-26

### Changed

- The MCP server is now declared in `.claude-plugin/plugin.json` instead of a root `.mcp.json`, so opening the cloned repository in Claude Code no longer shows a "Missing environment variables: CLAUDE_PLUGIN_ROOT" warning.
- README: first-start note and troubleshooting for a server that fails on first launch (Reconnect, pre-install with `uv sync`) and for persistent `UV_SYSTEM_CERTS` settings.

## [0.1.0] - 2026-11-13

### Added

- `voix-du-client` skill (Agent Skills format): 7-step method, analysis grid, weak signals, frequency × intensity prioritisation, report template, JSON schema.
- `voc-mcp` MCP server (FastMCP): `load_feedback`, `anonymize`, `stats`, `sample`, `export_report`, optional `transcribe` (FunASR, French and English).
- Rule-based pseudonymisation (French and English formats), on by default.
- Claude Code plugin and marketplace manifests; installers for Windows, macOS and Linux (Claude Code, Codex, Cursor).
- Fictional demo data (200 reviews, 5 call transcripts) and the resulting report.
- Tests (pytest) and CI on Windows, macOS and Linux.
