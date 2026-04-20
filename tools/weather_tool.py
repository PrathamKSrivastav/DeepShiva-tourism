import httpx
from typing import Dict, Optional

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(latitude: float, longitude: float) -> Optional[Dict]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max"
        ],
        "forecast_days": 7,
        "timezone": "auto"
    }

    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    if "daily" not in data:
        return None

    return {
        "source": "open_meteo",
        "timezone": data.get("timezone"),
        "dates": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "precipitation": data["daily"]["precipitation_sum"],
        "wind_speed": data["daily"]["windspeed_10m_max"],
    }
