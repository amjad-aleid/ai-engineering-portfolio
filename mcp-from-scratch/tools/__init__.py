"""Tool registry: maps tool names to their MCP definitions and Python handlers."""
from .weather import get_weather
from .wikipedia import wikipedia_summary

TOOLS = {
    "get_weather": {
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'London' or 'Tokyo'",
                }
            },
            "required": ["city"],
        },
        "handler": get_weather,
    },
    "wikipedia_summary": {
        "description": "Get a short summary of a Wikipedia article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic or article title, e.g. 'Alan Turing'",
                }
            },
            "required": ["topic"],
        },
        "handler": wikipedia_summary,
    },
}
