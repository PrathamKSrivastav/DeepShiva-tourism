import asyncio
import logging
from utils.database import connect_to_mongo, close_mongo_connection
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    try:
        print(f"📋 Testing MongoDB connection...")
        print(f"📋 MongoDB URI: {settings.MONGODB_URI[:30]}...")
        print(f"📋 Database Name: {settings.DATABASE_NAME}")
        
        await connect_to_mongo()
        print("✅ Connection successful!")
        
        await close_mongo_connection()
        print("✅ Disconnection successful!")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())

