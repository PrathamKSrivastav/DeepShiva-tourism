import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from tools.geocoding_tool import geocode_location

async def main():
    location = await geocode_location("dehradun")
    print("\nGEOCODING RESULT:\n", location)

asyncio.run(main())
