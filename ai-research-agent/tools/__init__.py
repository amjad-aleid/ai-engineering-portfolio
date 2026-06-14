from . import github, securities

TOOLS = {
    "screen_securities": {
        "description": (
            "Screen stocks or ETFs by P/E ratio, dividend yield, expense ratio "
            "(ETFs only), and historical growth (trailing 5-year average annual "
            "return for ETFs, latest earnings/revenue growth for stocks). Returns "
            "a list of matching securities with their metrics."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_type": {
                    "type": "string",
                    "enum": ["stock", "etf"],
                    "description": "Whether to screen individual stocks or ETFs/funds.",
                },
                "sector": {
                    "type": "string",
                    "description": "Optional sector filter, e.g. 'Technology' or 'Healthcare' (stocks only).",
                },
                "max_pe": {
                    "type": "number",
                    "description": "Maximum price-to-earnings (P/E) ratio.",
                },
                "min_dividend_yield": {
                    "type": "number",
                    "description": "Minimum dividend yield, as a percentage (e.g. 2.0 for 2%).",
                },
                "max_expense_ratio": {
                    "type": "number",
                    "description": "Maximum expense ratio, as a percentage (ETFs only, e.g. 0.1 for 0.1%).",
                },
                "min_historical_growth": {
                    "type": "number",
                    "description": (
                        "Minimum historical growth, as a percentage: trailing 5-year "
                        "average annual return for ETFs, or latest earnings/revenue "
                        "growth rate for stocks."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-10, default 5).",
                },
            },
            "required": ["asset_type"],
        },
        "handler": securities.screen_securities,
    },
    "search_github_repos": {
        "description": "Search GitHub repositories by keyword, optionally filtered by programming language.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords."},
                "language": {
                    "type": "string",
                    "description": "Optional programming language filter, e.g. 'Python'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5).",
                },
            },
            "required": ["query"],
        },
        "handler": github.search_github_repos,
    },
    "get_github_repo": {
        "description": "Get details (stars, forks, open issues, license, etc.) for a specific GitHub repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner (user or organization)."},
                "repo": {"type": "string", "description": "Repository name."},
            },
            "required": ["owner", "repo"],
        },
        "handler": github.get_github_repo,
    },
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    for name, tool in TOOLS.items()
]
