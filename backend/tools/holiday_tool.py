# tools/holiday_tool.py
import os
import json
import httpx
from datetime import datetime
from typing import Optional, List, Dict

# --- CONFIGURATION ---
API_KEY = os.getenv("CALLENDRIFIC_API_KEY") 
COUNTRY = "IN"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def _fetch_year_data(year: int) -> List[Dict]:
    """
    Internal: Fetches full year data (1 API call per year) and caches it.
    """
    cache_file = os.path.join(CACHE_DIR, f"holidays_{COUNTRY}_{year}.json")

    # 1. Check Cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")

    # 2. Fetch from API
    url = "https://calendarific.com/api/v2/holidays"
    params = {"api_key": API_KEY, "country": COUNTRY, "year": year}
    
    print(f"🌏 Fetching holidays for {year} from Calendarific API...")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            holidays = data.get("response", {}).get("holidays", [])
            
            if holidays:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(holidays, f, indent=4)
                return holidays
        except Exception as e:
            print(f"❌ API Error: {e}")
    
    return []

async def get_holidays(year: Optional[int] = None, month: Optional[int] = None, quarter: Optional[int] = None) -> List[Dict]:
    """
    Main Tool: Returns holidays, optionally filtered by month or quarter.
    """
    if year is None:
        year = datetime.now().year

    # Always fetch the full year (efficient caching)
    all_holidays = await _fetch_year_data(year)
    
    if not all_holidays:
        return []

    filtered = []
    
    # Define Month Ranges
    target_months = []
    if month:
        target_months = [month]
    elif quarter:
        # Q1: 1-3, Q2: 4-6, Q3: 7-9, Q4: 10-12
        start_m = (quarter - 1) * 3 + 1
        target_months = [start_m, start_m + 1, start_m + 2]
    
    # Filter Logic
    if target_months:
        for h in all_holidays:
            try:
                # Calendarific date is YYYY-MM-DD
                h_month = int(h["date"]["datetime"]["month"])
                if h_month in target_months:
                    filtered.append(h)
            except:
                continue
        return filtered

    return all_holidays
