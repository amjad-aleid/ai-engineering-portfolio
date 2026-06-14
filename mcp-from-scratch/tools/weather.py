"""get_weather tool — Open-Meteo geocoding + forecast APIs (no API key required)."""
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

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


def get_weather(city: str) -> str:
    geo_resp = requests.get(
        GEOCODING_URL, params={"name": city, "count": 1}, timeout=10
    )
    geo_resp.raise_for_status()
    results = geo_resp.json().get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{city}'")

    location = results[0]
    latitude, longitude = location["latitude"], location["longitude"]
    name, country = location["name"], location.get("country", "")

    forecast_resp = requests.get(
        FORECAST_URL,
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
