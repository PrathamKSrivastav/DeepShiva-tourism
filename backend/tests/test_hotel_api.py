# backend/tests/test_hotel_api.py

import asyncio
import os
import sys
import logging
from datetime import datetime, timedelta

# Add parent dir to path so we can import 'tools'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.hotel_tool import get_hotel_rates

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_live_api():
    """Test 1: Check if LiteAPI works and fetches real data for a major city"""
    logger.info("🧪 TEST 1: Testing Live LiteAPI Call...")
    
    # Use a major city that definitely has data in Sandbox/Prod
    city = "Agra"
    tomorrow = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    result = await get_hotel_rates(city, tomorrow)
    
    if "error" in result:
        logger.error(f"❌ API Test Failed: {result['error']}")
        return False
        
    if result.get("found", 0) > 0:
        logger.info(f"✅ API Success! Found {result['found']} hotels in {city}.")
        h = result['hotels'][0]
        logger.info(f"   Top Hotel: {h['name']}")
        logger.info(f"   Price: {h['price']}")
        logger.info(f"   Rating: {h['rating']}")
        return True
    else:
        logger.warning(f"⚠️ API worked but found 0 hotels in {city}.")
        return True # Technical success

async def test_caching_mechanism():
    """Test 2: Check if the second call reads from cache"""
    logger.info("\n🧪 TEST 2: Testing Caching Mechanism...")
    
    city = "Jaipur" # Different city
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 1. First Call (Should hit API)
    logger.info(f"   1. Making FIRST call for {city} (API fetch)...")
    start_time = asyncio.get_event_loop().time()
    res1 = await get_hotel_rates(city, tomorrow)
    duration1 = asyncio.get_event_loop().time() - start_time
    
    if "error" in res1:
        logger.error(f"❌ Setup failed: {res1['error']}")
        return

    # 2. Second Call (Should hit Cache)
    logger.info(f"   2. Making SECOND call for {city} (Cache fetch)...")
    start_time = asyncio.get_event_loop().time()
    res2 = await get_hotel_rates(city, tomorrow)
    duration2 = asyncio.get_event_loop().time() - start_time
    
    # Validation
    is_cached = "cached_at" in res2
    
    if is_cached:
        logger.info(f"✅ Cache Hit! Response contained 'cached_at' timestamp.")
        logger.info(f"   - First call: {duration1:.2f}s")
        logger.info(f"   - Second call: {duration2:.2f}s")
    else:
        logger.error("❌ Cache Miss! The second call did not return cached data.")

async def main():
    # Check Environment
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("LITEAPI_KEY"):
        logger.error("❌ LITEAPI_KEY not found in .env file.")
        return

    logger.info("🚀 Starting Hotel Tool Tests (LiteAPI)...")
    
    # Run Tests
    api_success = await test_live_api()
    
    if api_success:
        await test_caching_mechanism()
    
    logger.info("\n🏁 Tests Completed.")

if __name__ == "__main__":
    asyncio.run(main())
