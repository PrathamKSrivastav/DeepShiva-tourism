import httpx
from typing import Optional, Dict

INDIA_HUB_URL = "https://www.india-location-hub.in/api/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode_with_india_hub(query: str) -> Optional[Dict]:
    params = {"q": query, "limit": 1}
    headers = {"User-Agent": "DeepShiva/1.0"}

    async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
        response = await client.get(INDIA_HUB_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    # India Location Hub usually returns {"data": [...]}
    results = data.get("data") or data.get("results") or []
    if not results:
        return None

    r = results[0]

    # Robust lat/lon handling
    lat = r.get("latitude") or r.get("lat")
    lon = r.get("longitude") or r.get("lng")

    if not lat or not lon:
        return None

    return {
        "place_name": r.get("name") or query.title(),
        "latitude": float(lat),
        "longitude": float(lon),
        "city": r.get("district") or r.get("city"),
        "state": r.get("state"),
        "country": "India",
        "source": "india_location_hub"
    }


async def geocode_with_nominatim(query: str) -> Optional[Dict]:
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "in"
    }
    headers = {"User-Agent": "DeepShiva/1.0"}

    async with httpx.AsyncClient(timeout=6) as client:
        response = await client.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()

    # Nominatim returns a LIST
    if not results:
        return None

    r = results[0]

    lat = r.get("lat")
    lon = r.get("lon")

    if not lat or not lon:
        return None

    return {
        "place_name": r.get("display_name"),
        "latitude": float(lat),
        "longitude": float(lon),
        "city": None,
        "state": None,
        "country": "India",
        "source": "nominatim"
    }


async def geocode_location(query: str) -> Optional[Dict]:
    """
    Try India Location Hub first, then fallback to Nominatim.
    """
    result = await geocode_with_india_hub(query)
    if result:
        return result

    return await geocode_with_nominatim(query)
