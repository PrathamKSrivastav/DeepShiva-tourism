import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from tools.weather_tool import get_weather

async def main():
    weather = await get_weather(
        latitude=30.3165,
        longitude=78.0322
    )
    print("\nWEATHER RESULT:\n", weather)

asyncio.run(main())
