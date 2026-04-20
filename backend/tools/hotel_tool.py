import aiohttp
import logging
import os
import hashlib
from datetime import datetime, timedelta

from utils.database import get_database

logger = logging.getLogger(__name__)

LITEAPI_HOST = "api.liteapi.travel"
CACHE_COLLECTION = "hotel_cache"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h

_ttl_index_ensured = False


async def _ensure_ttl_index():
    """Create the TTL index on hotel_cache once per process."""
    global _ttl_index_ensured
    if _ttl_index_ensured:
        return
    try:
        db = get_database()
        await db[CACHE_COLLECTION].create_index(
            "created_at", expireAfterSeconds=CACHE_TTL_SECONDS
        )
        _ttl_index_ensured = True
    except Exception as e:
        logger.warning(f"Could not ensure hotel_cache TTL index: {e}")


class HotelRateTool:
    def __init__(self):
        self.api_key = os.getenv("LITEAPI_KEY")
        self.base_url = f"https://{LITEAPI_HOST}/v3.0"

    def _get_cache_key(self, city: str, checkin_date: str) -> str:
        city_clean = city.strip().lower()
        date_clean = checkin_date.strip()
        raw_key = f"liteapi_{city_clean}_{date_clean}"
        return hashlib.md5(raw_key.encode()).hexdigest()

    async def _read_from_cache(self, cache_key: str) -> dict | None:
        try:
            db = get_database()
            doc = await db[CACHE_COLLECTION].find_one({"_id": cache_key})
            if doc:
                logger.info(f"Loaded hotel data from Mongo cache: {cache_key}")
                return doc.get("payload")
        except Exception as e:
            logger.warning(f"Hotel cache read error: {e}")
        return None

    async def _save_to_cache(self, cache_key: str, data: dict):
        try:
            db = get_database()
            await db[CACHE_COLLECTION].update_one(
                {"_id": cache_key},
                {"$set": {"payload": data, "created_at": datetime.utcnow()}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Hotel cache write error: {e}")

    async def search_hotels(self, city: str, checkin_date: str = None, checkout_date: str = None):
        """
        Search hotels in a city using LiteAPI v3.0
        Flow: Get Place ID -> Get Rates
        """
        if not self.api_key:
            return {"error": "LITEAPI_KEY missing in .env"}

        # Default Dates (Tomorrow -> Day After)
        if not checkin_date:
            checkin_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not checkout_date:
            dt_checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
            checkout_date = (dt_checkin + timedelta(days=1)).strftime("%Y-%m-%d")

        await _ensure_ttl_index()

        cache_key = self._get_cache_key(city, checkin_date)
        cached = await self._read_from_cache(cache_key)
        if cached:
            return cached

        logger.info(f"Fetching LiteAPI data for: {city}")

        async with aiohttp.ClientSession() as session:
            headers = {
                "X-API-Key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json"
            }

            # Step 1: Get Place ID (Autocomplete)
            place_id = None
            try:
                place_url = f"{self.base_url}/data/places"
                async with session.get(place_url, headers=headers, params={"textQuery": city}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        places = data.get("data", [])
                        if places:
                            place_id = places[0]['placeId']
                            logger.info(f"📍 Found Place ID: {place_id} ({places[0]['displayName']})")
                    else:
                        logger.error(f"Place Search Failed: {resp.status}")
                        return {"error": "Could not find city ID"}
            except Exception as e:
                return {"error": str(e)}

            if not place_id:
                return {"error": f"City '{city}' not found in LiteAPI database"}

            # Step 2: Get Rates by Place ID
            rates_url = f"{self.base_url}/hotels/rates"
            payload = {
                "placeId": place_id,
                "occupancies": [{"adults": 2}],
                "currency": "INR",
                "guestNationality": "IN",
                "checkin": checkin_date,
                "checkout": checkout_date,
                "maxRatesPerHotel": 1,
                "includeHotelData": True
            }

            try:
                async with session.post(rates_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        price_map = {item['hotelId']: item for item in data.get('data', [])}
                        meta_list = data.get('hotels', [])

                        final_hotels = []
                        for meta in meta_list:
                            h_id = meta.get('id')
                            price_info = price_map.get(h_id)

                            if price_info and price_info.get('roomTypes'):
                                try:
                                    rate_obj = price_info['roomTypes'][0]['rates'][0]['retailRate']['total'][0]
                                    final_hotels.append({
                                        "name": meta.get('name'),
                                        "price": f"{rate_obj['currency']} {rate_obj['amount']}",
                                        "rating": f"{meta.get('rating', 'N/A')}/10",
                                        "image": meta.get('main_photo'),
                                        "address": meta.get('address')
                                    })
                                except: continue

                        result = {
                            "found": len(final_hotels),
                            "city": city,
                            "dates": f"{checkin_date} to {checkout_date}",
                            "hotels": final_hotels[:5],
                            "cached_at": datetime.now().isoformat()
                        }

                        await self._save_to_cache(cache_key, result)
                        return result
                    else:
                        text = await resp.text()
                        logger.error(f"Rates Search Failed: {text}")
                        return {"error": "Failed to fetch hotel rates"}
            except Exception as e:
                logger.error(f"Exception: {e}")
                return {"error": str(e)}


async def get_hotel_rates(city: str, checkin_date: str = None):
    tool = HotelRateTool()
    return await tool.search_hotels(city, checkin_date)
