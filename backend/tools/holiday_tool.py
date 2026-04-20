import os
import httpx
import logging
from datetime import datetime
from typing import Optional, List, Dict

from utils.database import get_database

logger = logging.getLogger(__name__)

API_KEY = os.getenv("CALLENDRIFIC_API_KEY")
COUNTRY = "IN"
CACHE_COLLECTION = "holiday_cache"


async def _read_from_cache(country: str, year: int) -> Optional[List[Dict]]:
    try:
        db = get_database()
        doc = await db[CACHE_COLLECTION].find_one({"_id": f"{country}_{year}"})
        if doc:
            return doc.get("holidays", [])
    except Exception as e:
        logger.warning(f"Holiday cache read error: {e}")
    return None


async def _save_to_cache(country: str, year: int, holidays: List[Dict]):
    try:
        db = get_database()
        await db[CACHE_COLLECTION].update_one(
            {"_id": f"{country}_{year}"},
            {"$set": {"holidays": holidays, "cached_at": datetime.utcnow()}},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"Holiday cache write error: {e}")


async def _fetch_year_data(year: int) -> List[Dict]:
    """
    Internal: Fetches full year data (1 API call per year) and caches it in MongoDB.
    """
    cached = await _read_from_cache(COUNTRY, year)
    if cached:
        return cached

    url = "https://calendarific.com/api/v2/holidays"
    params = {"api_key": API_KEY, "country": COUNTRY, "year": year}

    logger.info(f"Fetching holidays for {year} from Calendarific API...")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            holidays = data.get("response", {}).get("holidays", [])

            if holidays:
                await _save_to_cache(COUNTRY, year, holidays)
                return holidays
        except Exception as e:
            logger.error(f"Calendarific API Error: {e}")

    return []


async def get_holidays(
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = None,
) -> List[Dict]:
    """
    Main Tool: Returns holidays, optionally filtered by month or quarter.
    """
    if year is None:
        year = datetime.now().year

    all_holidays = await _fetch_year_data(year)

    if not all_holidays:
        return []

    filtered = []

    target_months = []
    if month:
        target_months = [month]
    elif quarter:
        start_m = (quarter - 1) * 3 + 1
        target_months = [start_m, start_m + 1, start_m + 2]

    if target_months:
        for h in all_holidays:
            try:
                h_month = int(h["date"]["datetime"]["month"])
                if h_month in target_months:
                    filtered.append(h)
            except:
                continue
        return filtered

    return all_holidays


async def get_next_holidays(limit: int = 3) -> List[Dict]:
    """
    Get the next N upcoming holidays from today's date.
    """
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    current_year = today.year

    holidays_this_year = await _fetch_year_data(current_year)
    holidays_next_year = await _fetch_year_data(current_year + 1)

    all_holidays = holidays_this_year + holidays_next_year

    upcoming = []
    for h in all_holidays:
        try:
            holiday_date = h.get("date", {}).get("iso", "9999-99-99")
            if holiday_date >= today_str:
                upcoming.append(h)
        except Exception as e:
            logger.warning(f"Error processing holiday: {e}")
            continue

    upcoming.sort(key=lambda x: x.get("date", {}).get("iso", "9999-99-99"))

    return upcoming[:limit]
