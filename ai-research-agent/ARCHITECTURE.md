# AI Research Agent — System Architecture

## Overview

[`mcp-from-scratch`](../mcp-from-scratch/ARCHITECTURE.md) and [`mcp-with-fastmcp`](../mcp-with-fastmcp/ARCHITECTURE.md) are **servers**: they sit and wait for an MCP host (Claude Desktop, Claude Code, etc.) to call `initialize`, `tools/list`, and `tools/call` over stdio.

This project is the **host** side, built on [Groq's](https://groq.com/) free API (the same provider [`papermind`](../papermind) uses). There is no MCP transport here — `agent.py` calls `client.chat.completions.create(tools=TOOL_SCHEMAS, ...)` directly, and the "tools" are plain Python functions in `tools/`, described to the model via JSON Schema (OpenAI-style function definitions) in `tools/__init__.py`.

An **agent**, concretely, is:

```
model (Llama 3.3 70B via Groq) + tool definitions + a loop that runs until the model stops asking for tools
```

The model decides *whether* to call a tool, *which* tool, and *with what arguments* — `agent.py` doesn't hardcode any of that; it just executes whatever `tool_calls` the model returns and feeds the results back.

---

## Message Flow

### A query that needs one tool call

```
User                  agent.py                          Groq API
 │ "Find ETFs with      │                                    │
 │  expense ratio<0.1%"  │                                    │
 │ ─────────────────────>│                                    │
 │                       │ chat.completions.create(           │
 │                       │   tools=TOOL_SCHEMAS,              │
 │                       │   messages=[system, user]) ──────>│
 │                       │                                    │
 │                       │ <── message.tool_calls: ────────────│
 │                       │     [screen_securities(             │
 │                       │        asset_type="etf",            │
 │                       │        max_expense_ratio=0.1)]      │
 │                       │                                    │
 │                       │ append assistant msg                │
 │                       │ (with tool_calls)                   │
 │                       │                                    │
 │                       │ tools/securities.py                │
 │                       │   .screen_securities(...)          │
 │                       │   ──> Yahoo Finance (yfinance)     │
 │                       │   <── candidates + metrics         │
 │                       │                                    │
 │                       │ append {"role": "tool",            │
 │                       │   "tool_call_id": ...,             │
 │                       │   "content": "[...]"}              │
 │                       │                                    │
 │                       │ chat.completions.create(           │
 │                       │   tools=TOOL_SCHEMAS,              │
 │                       │   messages=[..., tool msg]) ──────>│
 │                       │                                    │
 │                       │ <── message.content: ───────────────│
 │                       │     "Here are three ETFs            │
 │                       │      under a 0.1% expense ratio…"  │
 │ <─────────────────────│  (no tool_calls, loop ends)         │
 │   final reply          │                                    │
```

### A query needing no tools

If the model's first response has no `tool_calls` (e.g. "What's an expense ratio?"), the loop exits immediately after one `chat.completions.create` call — no tool is invoked.

### A query needing multiple tool calls

The `while True` loop in `agent.py` handles this naturally: each iteration can return zero, one, or several entries in `message.tool_calls` (e.g. one `screen_securities` call and one `search_github_repos` call in the same turn). Each is executed and appended as its own `{"role": "tool", "tool_call_id": ..., "content": ...}` message, and the loop continues until the model responds with no tool calls.

---

## Component Map

| Component | Role |
|---|---|
| `agent.py` | CLI entry point. Holds the system prompt, the agentic `while` loop, and dispatches `tool_calls` to `TOOLS[name]["handler"]` |
| `tools/__init__.py` | `TOOLS` — registry mapping tool name → `{description, parameters, handler}`. `TOOL_SCHEMAS` — OpenAI-style `{"type": "function", "function": {...}}` definitions passed to `chat.completions.create(tools=...)` |
| `tools/securities.py` | `screen_securities()` — runs a `yfinance` screener query (`EquityQuery`/`ETFQuery`) for candidates, then fetches `Ticker(symbol).info` per candidate for P/E, dividend yield, expense ratio (ETFs), and historical growth; filters and returns matches. `compare_securities()` — given a list of symbols, fetches `.info` and 5yr price history per symbol to produce expense ratio, dividend yield, and 1/3/5-year total returns for side-by-side comparison |
| `tools/github.py` | `search_github_repos()`, `get_github_repo()` — thin wrappers over the GitHub REST API |

Tool errors (bad API key, symbol not found, rate limit) raise `ValueError` from the handler; `agent.py` catches this, serializes `{"error": "..."}` as the tool message content, and lets the model explain the failure to the user instead of the program crashing.

---

## Directory Structure

```
ai-research-agent/
├── agent.py             # entry point: system prompt, agentic loop, CLI
├── tools/
│   ├── __init__.py       # TOOLS registry + TOOL_SCHEMAS (OpenAI-style function defs)
│   ├── securities.py     # screen_securities, compare_securities (Yahoo Finance via yfinance, no key)
│   └── github.py         # search_github_repos, get_github_repo
├── requirements.txt      # groq, requests, python-dotenv, yfinance, pandas
├── .env.example          # GROQ_API_KEY, GITHUB_TOKEN
└── .gitignore
```
