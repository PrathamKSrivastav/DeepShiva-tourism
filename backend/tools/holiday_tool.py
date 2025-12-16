# tools/holiday_tool.py

import os
import json
import httpx
from datetime import datetime
from typing import Optional, List, Dict

# --- CONFIGURATION ---
# Replace with your actual key or load from os.getenv("CALENDARIFIC_API_KEY")
API_KEY = os.getenv("CALLENDRIFIC_API_KEY")
COUNTRY = "IN"
CACHE_DIR = "cache"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

async def get_indian_holidays(year: Optional[int] = None) -> List[Dict]:
    """
    Fetches Indian holidays for a given year.
    Uses local file caching to minimize API calls (1 call per year).
    """
    if year is None:
        year = datetime.now().year

    cache_file = os.path.join(CACHE_DIR, f"holidays_{COUNTRY}_{year}.json")

    # 1. Check Cache First (Zero Latency)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                print(f"✅ Loading holidays for {year} from cache.")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}. Fetching fresh data.")

    # 2. Fetch from API if cache missing
    url = "https://calendarific.com/api/v2/holidays"
    params = {
        "api_key": API_KEY,
        "country": COUNTRY,
        "year": year
    }

    print(f"🌏 Fetching holidays for {year} from Calendarific API...")
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Calendarific returns data under data['response']['holidays']
            holidays = data.get("response", {}).get("holidays", [])
            
            if holidays:
                # Save to cache
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(holidays, f, indent=4)
                print(f"✅ Saved {len(holidays)} holidays to cache.")
                
            return holidays
            
        except httpx.HTTPStatusError as e:
            print(f"❌ API Error: {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return []

async def get_upcoming_holiday(days_limit: int = 30) -> str:
    """
    Helper for the agent to quickly find the next holiday.
    Returns a human-readable string summary.
    """
    today = datetime.now().date()
    current_year = today.year
    
    holidays = await get_indian_holidays(current_year)
    
    upcoming = []
    for h in holidays:
        # Calendarific dates are in ISO format YYYY-MM-DD
        h_date_str = h["date"]["iso"]
        h_date = datetime.fromisoformat(h_date_str).date()
        
        if h_date >= today:
            delta = (h_date - today).days
            if delta <= days_limit:
                upcoming.append(f"- {h['name']} on {h_date_str} ({h.get('description', '')[:50]}...)")
    
    if not upcoming:
        return "No major holidays found in the next 30 days."
    
    return "Upcoming Holidays:\n" + "\n".join(upcoming[:3])
