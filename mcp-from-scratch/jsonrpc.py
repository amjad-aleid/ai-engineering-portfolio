"""JSON-RPC 2.0 message helpers.

This module knows nothing about MCP — it's the generic envelope that
any JSON-RPC 2.0 protocol (MCP included) is built on.
"""
import json

JSONRPC_VERSION = "2.0"

# Standard JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class JSONRPCError(Exception):
    """Raised by handlers to produce a JSON-RPC error response."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def parse_message(line: str) -> dict:
    """Decode and validate a single JSON-RPC message line."""
    try:
        message = json.loads(line)
    except json.JSONDecodeError as exc:
        raise JSONRPCError(PARSE_ERROR, f"Invalid JSON: {exc}") from exc

    if not isinstance(message, dict) or message.get("jsonrpc") != JSONRPC_VERSION:
        raise JSONRPCError(INVALID_REQUEST, "Missing or invalid 'jsonrpc' field")

    return message


def success_response(request_id, result: dict) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def error_response(request_id, code: int, message: str) -> dict:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }
