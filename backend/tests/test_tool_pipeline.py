import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.intents import extract_location
from tools.geocoding_tool import geocode_location
from tools.weather_tool import get_weather

async def main():
    query = "what is the temperature and weather in dehradun today?"

    location_query = extract_location(query)
    print("STEP 1 - Extracted location:", location_query)

    if not location_query:
        print("❌ Location extraction failed")
        return

    location_data = await geocode_location(location_query)
    print("STEP 2 - Geocoding result:", location_data)

    if not location_data:
        print("❌ Geocoding failed")
        return

    weather = await get_weather(
        latitude=location_data["latitude"],
        longitude=location_data["longitude"]
    )
    print("STEP 3 - Weather result:", weather)

asyncio.run(main())
