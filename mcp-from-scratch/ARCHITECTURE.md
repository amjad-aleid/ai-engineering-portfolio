# MCP From Scratch — System Architecture

## Overview

MCP defines three roles:

- **Host** — the AI application (Claude Desktop, Claude Code, etc.). Runs the LLM and decides when to call a tool.
- **Client** — built into the host, manages the connection to a server.
- **Server** — this project. Exposes tools; has no LLM and no "intelligence" of its own.

The host launches this server as a subprocess and communicates over its `stdin`/`stdout` using JSON-RPC 2.0 messages, one per line (the **stdio transport**). `stderr` is free for logging.

---

## Message Flow

### 1. Initialize handshake (once, at startup)

```
Host                                    Server
  │ --- initialize (id=1) -------------> │
  │     protocolVersion, capabilities    │
  │                                       │
  │ <--- result (id=1) ------------------ │
  │     protocolVersion, capabilities,   │
  │     serverInfo                       │
  │                                       │
  │ --- notifications/initialized -----> │
  │     (no id — no response sent)       │
```

### 2. Discovering tools

```
Host                                    Server
  │ --- tools/list (id=2) -------------> │
  │                                       │
  │ <--- result (id=2) ------------------ │
  │     { tools: [ {name, description,  │
  │                  inputSchema}, ... ] } │
```

### 3. Calling a tool

```
Host                                    Server
  │ --- tools/call (id=3) -------------> │
  │     { name: "get_weather",          │  ── HTTP ──> Open-Meteo
  │       arguments: { city: "Tokyo" } } │  <── JSON ──
  │                                       │
  │ <--- result (id=3) ------------------ │
  │     { content: [{type: "text",      │
  │                   text: "..."}],     │
  │       isError: false }               │
```

If the handler raises (e.g. unknown city), the server still returns a normal JSON-RPC **result** — but with `isError: true` and the error message as the content, so the model sees it and can react.

A malformed request or unknown method returns a JSON-RPC **error** object instead (`-32700` / `-32601` / etc.) — that's a protocol-level problem, not a tool-level one.

---

## Component Map

```
┌──────────────────────────────────────────────────────┐
│ Host (Claude Desktop / Claude Code)                   │
└────────────────────────┬─────────────────────────────┘
                          │ stdio (JSON-RPC 2.0)
┌────────────────────────▼─────────────────────────────┐
│ server.py                                             │
│  - stdio read/write loop                              │
│  - method dispatch table                              │
│  - initialize / tools/list / tools/call / ping        │
└──────┬─────────────────────────────────┬─────────────┘
       │                                 │
       ▼                                 ▼
┌────────────────┐               ┌──────────────────────┐
│ jsonrpc.py      │               │ tools/                │
│ - parse_message │               │ - registry (__init__) │
│ - responses     │               │ - get_weather         │
│ - error codes   │               │ - wikipedia_summary    │
└────────────────┘               └───────────┬───────────┘
                                              │
                                  ┌───────────┴───────────┐
                                  ▼                       ▼
                           Open-Meteo API           Wikipedia REST API
```

---

## Directory Structure

```
mcp-from-scratch/
├── server.py           # stdio loop + MCP method dispatch (entry point)
├── jsonrpc.py           # JSON-RPC 2.0 envelope + standard error codes
├── tools/
│   ├── __init__.py       # tool registry: name -> description, schema, handler
│   ├── weather.py         # get_weather (Open-Meteo)
│   └── wikipedia.py        # wikipedia_summary (Wikipedia REST API)
├── requirements.txt
└── .gitignore
```
