# AI Research Agent

## What is this?

The third project in this portfolio's progression. [`mcp-from-scratch`](../mcp-from-scratch) and [`mcp-with-fastmcp`](../mcp-with-fastmcp) built MCP **servers** — passive tool providers that any MCP host can connect to. This project is the **host** side: an actual **AI agent**, built on Groq's free API (same provider as [`papermind`](../papermind)).

An agent = a model + a set of tools + a loop where the model decides, on its own, when and how to call those tools and how to use the results. This agent has two tool groups:

- **`screen_securities`** — screens stocks or ETFs by P/E ratio, dividend yield, expense ratio (ETFs), and historical growth, via [Yahoo Finance](https://finance.yahoo.com/) (`yfinance`) — no API key required
- **`compare_securities`** — fetches expense ratio, dividend yield, and 1/3/5-year price performance for a list of specific symbols, for side-by-side comparison
- **`search_github_repos`** / **`get_github_repo`** — searches and inspects GitHub repositories via the GitHub REST API

You chat with it on the command line; it decides which tool(s) to call (if any) and reasons over the results to answer you.

## Architecture

```
User (CLI)
   │
   ▼
agent.py ── chat.completions.create(tools=TOOL_SCHEMAS) ──> Groq (llama-3.3-70b-versatile)
   │                                                              │
   │ <── tool_calls: screen_securities(...) ──────────────────────┤
   │ <── tool_calls: compare_securities(...) ───────────────────────┤
   │ <── tool_calls: search_github_repos(...) ─────────────────────┘
   ▼
tools/securities.py ──> Yahoo Finance (yfinance, no key)
tools/github.py     ──> GitHub REST API
   │
   └── tool result message(s) ──> Groq ──> final text reply
```

The loop in `agent.py` repeats "call the model → run any requested tools → send results back" until the model responds without requesting another tool call.

## Tooling decisions

### Groq SDK + manual agentic loop
[`papermind`](../papermind) already uses Groq's free API (Llama 3.3 70B Versatile), which has a generous free tier and supports OpenAI-style tool calling — so this agent uses it too, avoiding per-token Anthropic API charges. The agentic loop is written explicitly rather than via a framework helper — consistent with the "from scratch" approach of `mcp-from-scratch`, it makes the agent's core mechanic (call model → execute tool → feed result back → repeat) visible.

### Yahoo Finance (`yfinance`)
Unlike Financial Modeling Prep and Alpha Vantage, `yfinance` needs **no API key or signup at all** and still provides everything `screen_securities` needs: a real market screener (`yf.screen()` with `EquityQuery`/`ETFQuery`), per-symbol P/E and dividend yield, and (for ETFs) net expense ratio and 5-year average return.

`screen_securities` first runs a screener query to find a candidate pool (filtering on exchange/market cap/sector for stocks, or region/expense-ratio for ETFs), then fetches `yf.Ticker(symbol).info` per candidate to apply the remaining filters and pull the final metrics. Keep `limit` modest (default 5, max 10) since each candidate is a separate lookup. Data quality varies by symbol — some ETFs report a `0.0` expense ratio when Yahoo simply doesn't have that field populated.

`compare_securities` skips the screener entirely — given a list of symbols, it fetches `.info` plus 5 years of price history per symbol, and computes 1/3/5-year total returns from the actual close prices (works the same way for stocks and ETFs, unlike the asset-type-dependent "historical growth" in `screen_securities`).

### GitHub REST API
Free and unauthenticated for light use (60 requests/hour). Set `GITHUB_TOKEN` in `.env` to use an authenticated token instead (5000 requests/hour) — optional.

### `python-dotenv`
Loads `GROQ_API_KEY` and `GITHUB_TOKEN` from a local `.env` file, if one exists. `load_dotenv()` never overrides variables already set in your shell — so if you export these in `~/.zshrc` (or similar), no `.env` file is needed at all.

## Setup

**Requirements:** Python 3.10+

```bash
# 1. Enter the project
cd ai-research-agent

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
```

Either export these in your shell profile (e.g. `~/.zshrc`):
```bash
export GROQ_API_KEY="..."   # free key from console.groq.com (same key works for papermind)
export GITHUB_TOKEN="..."   # optional, raises the GitHub rate limit
```

...or copy `.env.example` to `.env` and fill in the same values. `screen_securities` needs **no API key at all** — it runs entirely on `yfinance`.

## Running

```bash
python agent.py
```

Example prompts:
- "Find dividend-paying stocks in the technology sector with a P/E under 25"
- "Find ETFs with an expense ratio under 0.1% and a dividend yield over 2%"
- "Compare AAPL, MSFT, and GOOGL on dividend yield and historical performance"
- "Compare SPY, QQQ, and VOO on expense ratio and 5-year returns"
- "Search GitHub for popular Python MCP server repositories"

Each tool call the agent makes is printed (`[tool] name(args)`) before its result is fed back to the model, so you can see the agentic loop happening.

## Tools

| Tool | Input | Description |
|---|---|---|
| `screen_securities` | `asset_type` ("stock"/"etf"), `sector?`, `max_pe?`, `min_dividend_yield?`, `max_expense_ratio?`, `min_historical_growth?`, `limit?` | Screens stocks/ETFs by P/E, dividend yield, expense ratio, and historical growth |
| `compare_securities` | `symbols` (list of tickers) | Compares specific symbols on expense ratio, dividend yield, and 1/3/5-year price performance |
| `search_github_repos` | `query`, `language?`, `limit?` | Searches GitHub repositories by keyword |
| `get_github_repo` | `owner`, `repo` | Gets stars, forks, issues, license, etc. for a repository |
