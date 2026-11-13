# Changelog

Format inspired by [Keep a Changelog](https://keepachangelog.com/); versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-13

### Added

- `voix-du-client` skill (Agent Skills format): 7-step method, analysis grid, weak signals, frequency × intensity prioritisation, report template, JSON schema.
- `voc-mcp` MCP server (FastMCP): `load_feedback`, `anonymize`, `stats`, `sample`, `export_report`, optional `transcribe` (FunASR, French and English).
- Rule-based pseudonymisation (French and English formats), on by default.
- Claude Code plugin and marketplace manifests; installers for Windows, macOS and Linux (Claude Code, Codex, Cursor).
- Fictional demo data (200 reviews, 5 call transcripts) and the resulting report.
- Tests (pytest) and CI on Windows, macOS and Linux.
