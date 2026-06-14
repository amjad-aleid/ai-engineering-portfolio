"""MCP server built with the official `mcp` SDK's FastMCP.

Same two tools as the `mcp-from-scratch` project — get_weather and
wikipedia_summary — reimplemented here to show what FastMCP's decorators
replace: the JSON-RPC envelope, the initialize handshake, and the
tools/list / tools/call dispatch are all handled by `mcp.run()`.
"""
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-with-fastmcp")

# WMO weather interpretation codes, as used by Open-Meteo.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_resp.raise_for_status()
    results = geo_resp.json().get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{city}'")

    location = results[0]
    latitude, longitude = location["latitude"], location["longitude"]
    name, country = location["name"], location.get("country", "")

    forecast_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": latitude, "longitude": longitude, "current_weather": True},
        timeout=10,
    )
    forecast_resp.raise_for_status()
    current = forecast_resp.json()["current_weather"]

    code = current["weathercode"]
    description = WEATHER_CODES.get(code, f"Weather code {code}")
    return (
        f"Weather in {name}, {country}: {description}, "
        f"{current['temperature']}°C, wind {current['windspeed']} km/h"
    )


@mcp.tool()
def wikipedia_summary(topic: str) -> str:
    """Get a short summary of a Wikipedia article."""
    from urllib.parse import quote

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic.replace(' ', '_'))}"
    resp = requests.get(
        url,
        headers={"User-Agent": "mcp-with-fastmcp/0.1 (educational MCP server)"},
        timeout=10,
    )

    if resp.status_code == 404:
        raise ValueError(f"No Wikipedia article found for '{topic}'")
    resp.raise_for_status()

    data = resp.json()
    return f"{data['title']}: {data['extract']}"


if __name__ == "__main__":
    mcp.run()
