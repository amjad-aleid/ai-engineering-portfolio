# MCP With FastMCP

## What is this?

The companion to [`mcp-from-scratch`](../mcp-from-scratch) — the **same two tools** (`get_weather`, `wikipedia_summary`), but built with the official [`mcp` Python SDK](https://github.com/modelcontextprotocol/python-sdk)'s **FastMCP** instead of a hand-rolled JSON-RPC layer.

Where `mcp-from-scratch` is ~250 lines spread across `jsonrpc.py`, `server.py`, and `tools/`, this is a single file under 100 lines. The tools and the public APIs they call (Open-Meteo, Wikipedia) are deliberately identical — the only variable is "SDK vs. no SDK", so the two projects can be compared directly.

FastMCP's `mcp.run()` handles everything `mcp-from-scratch` implemented by hand:

- The JSON-RPC 2.0 envelope and stdio transport
- The `initialize` handshake and capability negotiation
- `tools/list` — auto-generates JSON Schema **input and output** schemas from type hints, and the description from the docstring
- `tools/call` — dispatches to the decorated function, wraps results and exceptions automatically
- `ping` and other lifecycle methods

## Architecture

```
MCP host (e.g. Claude Desktop / Claude Code)
         │  spawns server.py as a subprocess
         ▼
   stdin / stdout (JSON-RPC 2.0, newline-delimited)
         │
         ▼
   FastMCP (mcp.run()) ── handles envelope, lifecycle, dispatch
         │
    ┌────┴─────┐
    ▼          ▼
get_weather  wikipedia_summary
(Open-Meteo) (Wikipedia REST API)
```

## Tooling decisions

### FastMCP (`mcp[cli]`)
The official SDK's high-level server framework. The `[cli]` extra adds the `mcp` command, which includes a built-in dev/test harness (`mcp dev`) — no separate Node/`npx` install needed.

### Open-Meteo / Wikipedia REST API
Same APIs as `mcp-from-scratch`, reused on purpose — both are free and require no API key or signup.

### `requests`
The only extra HTTP dependency. As with `mcp-from-scratch`, all protocol-level work is handled by the SDK; `requests` is used purely inside the two tool functions.

## Setup

**Requirements:** Python 3.10+

```bash
# 1. Enter the project
cd mcp-with-fastmcp

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the server

### MCP Inspector (recommended for development)

```bash
mcp dev server.py
```

This is the SDK's built-in dev tool — it starts the server and opens the Inspector UI, where you can send `initialize`, call `tools/list`, and call `tools/call` for either tool.

### Claude Desktop

```bash
mcp install server.py
```

This registers the server in Claude Desktop's config automatically. To do it manually (or for Claude Code), add to your MCP client config:

```json
{
  "mcpServers": {
    "mcp-with-fastmcp": {
      "command": "/absolute/path/to/mcp-with-fastmcp/.venv/bin/python",
      "args": ["/absolute/path/to/mcp-with-fastmcp/server.py"]
    }
  }
}
```

## Tools

| Tool | Input | Description |
|---|---|---|
| `get_weather` | `city` (string) | Current weather conditions, temperature, and wind speed for a city |
| `wikipedia_summary` | `topic` (string) | Short summary of a Wikipedia article for a topic |

## Comparing to `mcp-from-scratch`

| | `mcp-from-scratch` | `mcp-with-fastmcp` |
|---|---|---|
| Files | 6 (`jsonrpc.py`, `server.py`, `tools/*`) | 1 (`server.py`) |
| Protocol code | Hand-written JSON-RPC envelope + dispatch | `mcp.run()` |
| `tools/list` schema | Input schema only, written by hand | Input **and output** schema, generated from type hints |
| Error handling | Manual `isError`/error-code logic | Automatic — exceptions become `isError: true` results |
| Dev/test tool | `npx @modelcontextprotocol/inspector ...` | `mcp dev server.py` |
