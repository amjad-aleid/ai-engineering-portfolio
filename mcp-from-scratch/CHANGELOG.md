# Changelog

All notable changes to MCP From Scratch are listed here, most recent first.

---

## [0.1.0] - 2026-06-13
### Added
- Initial project scaffold
- Hand-rolled JSON-RPC 2.0 layer (`jsonrpc.py`) — message parsing, success/error responses, standard error codes
- MCP server core (`server.py`) — stdio transport loop, `initialize` / `notifications/initialized` lifecycle, `tools/list`, `tools/call`, `ping`
- `get_weather` tool — Open-Meteo geocoding + forecast APIs, no API key required
- `wikipedia_summary` tool — Wikipedia REST API page summaries, no API key required
