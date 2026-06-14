"""MCP server entry point: stdio transport + protocol dispatch.

No SDK — this implements the JSON-RPC 2.0 envelope and the slice of the
MCP spec needed to serve tools: the `initialize` lifecycle handshake,
`tools/list`, `tools/call`, and `ping`.
"""
import json
import sys

from jsonrpc import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    JSONRPCError,
    error_response,
    parse_message,
    success_response,
)
from tools import TOOLS

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "mcp-from-scratch", "version": "0.1.0"}

# Notifications (no "id") that we recognize but don't need to act on.
NOTIFICATION_METHODS = {"notifications/initialized"}


def log(message: str) -> None:
    """Diagnostics go to stderr — stdout is reserved for protocol messages."""
    print(message, file=sys.stderr, flush=True)


def handle_initialize(params: dict) -> dict:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": SERVER_INFO,
    }


def handle_tools_list(params: dict) -> dict:
    return {
        "tools": [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["input_schema"],
            }
            for name, tool in TOOLS.items()
        ]
    }


def handle_tools_call(params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments", {}) or {}

    tool = TOOLS.get(name)
    if tool is None:
        raise JSONRPCError(INVALID_PARAMS, f"Unknown tool: {name}")

    try:
        text = tool["handler"](**arguments)
        return {"content": [{"type": "text", "text": text}], "isError": False}
    except Exception as exc:
        # Tool-level failure (bad input, upstream API error, etc.) — report
        # it to the model as a result, not as a protocol-level error.
        return {"content": [{"type": "text", "text": str(exc)}], "isError": True}


def handle_ping(params: dict) -> dict:
    return {}


REQUEST_HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "ping": handle_ping,
}


def handle_message(line: str) -> dict | None:
    """Process one JSON-RPC message line, returning a response dict or None."""
    try:
        message = parse_message(line)
    except JSONRPCError as exc:
        return error_response(None, exc.code, exc.message)

    method = message.get("method")
    params = message.get("params", {}) or {}
    is_notification = "id" not in message

    if is_notification:
        if method not in NOTIFICATION_METHODS:
            log(f"Ignoring unknown notification: {method}")
        return None

    request_id = message["id"]
    handler = REQUEST_HANDLERS.get(method)
    if handler is None:
        return error_response(request_id, METHOD_NOT_FOUND, f"Unknown method: {method}")

    try:
        result = handler(params)
        return success_response(request_id, result)
    except JSONRPCError as exc:
        return error_response(request_id, exc.code, exc.message)
    except Exception as exc:
        return error_response(request_id, INTERNAL_ERROR, str(exc))


def main() -> None:
    log("mcp-from-scratch server starting (stdio transport)")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        response = handle_message(line)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
