import aiohttp
import logging
import os
import json
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Constants
LITEAPI_HOST = "api.liteapi.travel"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "hotel_cache")

class HotelRateTool:
    def __init__(self):
        self.api_key = os.getenv("LITEAPI_KEY")
        self.base_url = f"https://{LITEAPI_HOST}/v3.0"
        
        # Create cache directory
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _get_cache_key(self, city: str, checkin_date: str) -> str:
        """Create a unique filename"""
        # 🟢 FIX: Normalize inputs (lowercase, strip spaces)
        city_clean = city.strip().lower()
        date_clean = checkin_date.strip()
        
        raw_key = f"liteapi_{city_clean}_{date_clean}"
        hash_key = hashlib.md5(raw_key.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_key}.json")

    def _read_from_cache(self, cache_file: str) -> dict:
        """Read from cache if valid (24h)"""
        if not os.path.exists(cache_file): return None
        try:
            file_time = os.path.getmtime(cache_file)
            age_hours = (datetime.now().timestamp() - file_time) / 3600
            if age_hours > 24: return None
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded hotel data from cache: {cache_file}")
                return data
        except: return None

    def _save_to_cache(self, cache_file: str, data: dict):
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Cache write error: {e}")

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

        # 1. Check Cache
        cache_file = self._get_cache_key(city, checkin_date)
        cached = self._read_from_cache(cache_file)
        if cached: return cached

        logger.info(f"🏨 Fetching LiteAPI data for: {city}")

        async with aiohttp.ClientSession() as session:
            headers = {
                "X-API-Key": self.api_key, 
                "accept": "application/json",
                "content-type": "application/json"
            }

            # Step 1: Get Place ID (Autocomplete)
            # GET https://api.liteapi.travel/v3.0/data/places?textQuery={city}
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
                        logger.error(f"❌ Place Search Failed: {resp.status}")
                        return {"error": "Could not find city ID"}
            except Exception as e:
                return {"error": str(e)}

            if not place_id:
                return {"error": f"City '{city}' not found in LiteAPI database"}

            # Step 2: Get Rates by Place ID
            # POST https://api.liteapi.travel/v3.0/hotels/rates
            rates_url = f"{self.base_url}/hotels/rates"
            payload = {
                "placeId": place_id,
                "occupancies": [{"adults": 2}],
                "currency": "INR",
                "guestNationality": "IN",
                "checkin": checkin_date,
                "checkout": checkout_date,
                "maxRatesPerHotel": 1,
                "includeHotelData": True # Critical to get names/images
            }

            try:
                async with session.post(rates_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Process Data
                        # 'data': Rates/Prices
                        # 'hotels': Metadata (Names, Images)
                        
                        price_map = {item['hotelId']: item for item in data.get('data', [])}
                        meta_list = data.get('hotels', [])
                        
                        final_hotels = []
                        for meta in meta_list:
                            h_id = meta.get('id')
                            price_info = price_map.get(h_id)
                            
                            if price_info and price_info.get('roomTypes'):
                                try:
                                    # Extract cheapest rate
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
                            "hotels": final_hotels[:5], # Return top 5
                            "cached_at": datetime.now().isoformat()
                        }
                        
                        self._save_to_cache(cache_file, result)
                        return result
                    else:
                        text = await resp.text()
                        logger.error(f"❌ Rates Search Failed: {text}")
                        return {"error": "Failed to fetch hotel rates"}
            except Exception as e:
                logger.error(f"❌ Exception: {e}")
                return {"error": str(e)}

async def get_hotel_rates(city: str, checkin_date: str = None):
    tool = HotelRateTool()
    return await tool.search_hotels(city, checkin_date)
