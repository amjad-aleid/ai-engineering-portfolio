# MCP With FastMCP — System Architecture

## Overview

Same roles and transport as [`mcp-from-scratch`](../mcp-from-scratch/ARCHITECTURE.md): a **host** (Claude Desktop / Claude Code) spawns this server as a subprocess and exchanges JSON-RPC 2.0 messages over `stdin`/`stdout`. The difference is *who implements the protocol layer*.

In `mcp-from-scratch`, `jsonrpc.py` + `server.py` implement that layer by hand. Here, `FastMCP` (from the official `mcp` SDK) implements it — `server.py` contains only the two `@mcp.tool()` functions and a single `mcp.run()` call.

---

## What FastMCP Generates For You

| Concern | `mcp-from-scratch` | `mcp-with-fastmcp` |
|---|---|---|
| JSON-RPC envelope (parsing, error codes, response shapes) | `jsonrpc.py` | `mcp.run()` |
| stdio read/write loop | hand-written `main()` | `mcp.run()` |
| `initialize` response | hand-written, `capabilities: {"tools": {}}` | automatic — also reports `prompts`, `resources`, `tools.listChanged`, `experimental` |
| `tools/list` | built from a manual `TOOLS` registry; input schema only | automatic — **input and output** JSON Schema derived from type hints, description from the docstring |
| `tools/call` dispatch | hand-written lookup + try/except | automatic, by function name |
| Tool errors | manual `{"isError": true, ...}` construction | automatic — exception message becomes `"Error executing tool {name}: {message}"`, `isError: true` |
| `ping` | hand-written, returns `{}` | built in |
| `serverInfo.version` | hardcoded `"0.1.0"` | the installed `mcp` SDK version |

---

## Message Flow

The wire-level exchange is the same shape as `mcp-from-scratch` — only the side generating the server's half changes.

### 1. Initialize handshake

```
Host                                    Server (FastMCP)
  │ --- initialize (id=1) -------------> │
  │ <--- result (id=1) ------------------ │
  │     protocolVersion, capabilities    │
  │     (richer: prompts/resources/tools)│
  │     serverInfo: {name, sdk version}  │
  │                                       │
  │ --- notifications/initialized -----> │
```

### 2. Discovering tools

```
Host                                    Server (FastMCP)
  │ --- tools/list (id=2) -------------> │
  │ <--- result (id=2) ------------------ │
  │     tools: [                         │
  │       { name, description,           │
  │         inputSchema,   ← from type hints
  │         outputSchema } ← from return type
  │     ]                                 │
```

### 3. Calling a tool

```
Host                                    Server (FastMCP)
  │ --- tools/call (id=3) -------------> │
  │     { name: "get_weather",          │  ── HTTP ──> Open-Meteo
  │       arguments: { city: "Tokyo" } } │  <── JSON ──
  │ <--- result (id=3) ------------------ │
  │     { content: [{type: "text", ...}],│
  │       structuredContent: {result:..}│  ← extra vs. mcp-from-scratch
  │       isError: false }               │
```

If `get_weather`/`wikipedia_summary` raise (e.g. unknown city), FastMCP
still returns a JSON-RPC **result** with `isError: true` and the
exception message — same `isError` convention as `mcp-from-scratch`,
just generated automatically instead of caught by hand.

---

## Directory Structure

```
mcp-with-fastmcp/
├── server.py           # FastMCP app + both tools — the entire implementation
├── requirements.txt    # mcp[cli], requests
└── .gitignore
```

Compare to `mcp-from-scratch/`'s six files (`jsonrpc.py`, `server.py`,
`tools/__init__.py`, `tools/weather.py`, `tools/wikipedia.py`) — the
file-per-concern split made there largely collapses because FastMCP
*is* that split, already written.
