"""wikipedia_summary tool — Wikipedia REST API page summaries (no API key required)."""
from urllib.parse import quote

import requests

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

# Wikimedia's API etiquette guidelines ask clients to identify themselves.
HEADERS = {"User-Agent": "mcp-from-scratch/0.1 (educational MCP server)"}


def wikipedia_summary(topic: str) -> str:
    url = SUMMARY_URL.format(quote(topic.replace(" ", "_")))
    resp = requests.get(url, headers=HEADERS, timeout=10)

    if resp.status_code == 404:
        raise ValueError(f"No Wikipedia article found for '{topic}'")
    resp.raise_for_status()

    data = resp.json()
    return f"{data['title']}: {data['extract']}"
