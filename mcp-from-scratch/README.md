# MCP From Scratch

## What is this?

A minimal [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, implemented directly on top of JSON-RPC 2.0 — **no `mcp` SDK**. The goal is to understand exactly what an SDK like `FastMCP` does under the hood: framing messages over stdio, handling the `initialize` handshake, and dispatching `tools/list` / `tools/call`.

It exposes two tools backed by free, key-free public APIs:

- **`get_weather`** — current weather for a city, via [Open-Meteo](https://open-meteo.com)
- **`wikipedia_summary`** — short summary of a topic, via the [Wikipedia REST API](https://www.mediawiki.org/wiki/API:REST_API)

## Architecture

```
MCP host (e.g. Claude Desktop / Claude Code)
         │  spawns server.py as a subprocess
         ▼
   stdin / stdout (JSON-RPC 2.0, newline-delimited)
         │
         ▼
   server.py ── dispatches by "method"
         │
    ┌────┴─────┬──────────────┬────────┐
    ▼          ▼              ▼        ▼
initialize  tools/list   tools/call   ping
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              get_weather       wikipedia_summary
              (Open-Meteo)      (Wikipedia REST API)
```

## Tooling decisions

### No SDK
The official `mcp` SDK (`FastMCP`) reduces a server like this to a handful of decorators. Implementing the JSON-RPC envelope and lifecycle by hand is the entire point of this project — it's how the SDK's abstractions actually work underneath.

### Open-Meteo
A weather API that requires no signup or API key. A two-step call — geocode the city name to coordinates, then fetch the current weather for those coordinates — both endpoints are free and unauthenticated.

### Wikipedia REST API
Returns a clean, pre-written summary for almost any topic with a single unauthenticated GET request. Ideal for a "no setup" second tool.

### `requests`
The only third-party dependency. Used purely for the HTTP calls inside the two tools — the MCP/JSON-RPC layer itself uses only the standard library.

## Setup

**Requirements:** Python 3.10+

```bash
# 1. Enter the project
cd mcp-from-scratch

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the server

The server speaks JSON-RPC over stdio — it's not meant to be run directly and typed into. Use one of:

### MCP Inspector (recommended for development)

```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```

This opens a web UI where you can send `initialize`, call `tools/list`, and call `tools/call` for either tool and see the raw JSON-RPC exchange.

### Claude Desktop / Claude Code

Add to your MCP client config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-from-scratch": {
      "command": "/absolute/path/to/mcp-from-scratch/.venv/bin/python",
      "args": ["/absolute/path/to/mcp-from-scratch/server.py"]
    }
  }
}
```

## Tools

| Tool | Input | Description |
|---|---|---|
| `get_weather` | `city` (string) | Current weather conditions, temperature, and wind speed for a city |
| `wikipedia_summary` | `topic` (string) | Short summary of a Wikipedia article for a topic |
