import os

import requests

GITHUB_API_BASE = "https://api.github.com"


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_github_repos(query: str, language: str | None = None, limit: int = 5) -> list[dict]:
    """Search GitHub repositories matching a query, optionally filtered by language."""
    search_query = query if not language else f"{query} language:{language}"
    response = requests.get(
        f"{GITHUB_API_BASE}/search/repositories",
        params={"q": search_query, "sort": "stars", "order": "desc", "per_page": limit},
        headers=_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        raise ValueError(f"GitHub search failed ({response.status_code}): {response.text}")

    items = response.json().get("items", [])
    return [
        {
            "full_name": item["full_name"],
            "description": item.get("description"),
            "stars": item["stargazers_count"],
            "language": item.get("language"),
            "url": item["html_url"],
        }
        for item in items
    ]


def get_github_repo(owner: str, repo: str) -> dict:
    """Get details about a specific GitHub repository (owner/repo)."""
    response = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=_headers(), timeout=10)
    if response.status_code == 404:
        raise ValueError(f"Repository '{owner}/{repo}' not found")
    if response.status_code != 200:
        raise ValueError(f"GitHub request failed ({response.status_code}): {response.text}")

    data = response.json()
    return {
        "full_name": data["full_name"],
        "description": data.get("description"),
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data.get("language"),
        "license": (data.get("license") or {}).get("name"),
        "url": data["html_url"],
    }
