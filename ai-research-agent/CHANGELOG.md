# Changelog

All notable changes to AI Research Agent are listed here, most recent first.

---

## [0.3.0] - 2026-06-15
### Added
- `calculate_returns` tool — dynamic investment calculator: given a list of symbols, a dollar amount, and one or more year periods, computes total return %, gain/loss, and ending portfolio value per symbol per period using live Yahoo Finance price history

## [0.2.0] - 2026-06-15
### Added
- `compare_securities` tool — fetches live expense ratio, dividend yield, and 1/3/5-year price returns for a list of specified symbols, enabling side-by-side comparison without relying on model training data

---

## [0.1.0] - 2026-06-14
### Added
- Initial project scaffold
- `agent.py` — manual agentic loop against Groq's `llama-3.3-70b-versatile` (free tier, same provider as `papermind`), plus a CLI chat interface
- `tools/securities.py` — `screen_securities`, screening stocks and ETFs by P/E ratio, dividend yield, expense ratio (ETFs), and historical growth, via Yahoo Finance (`yfinance`) — no API key required
- `tools/github.py` — `search_github_repos` and `get_github_repo`, via the GitHub REST API
- `tools/__init__.py` — tool registry and OpenAI-style tool-schema definitions for Groq's function-calling API
