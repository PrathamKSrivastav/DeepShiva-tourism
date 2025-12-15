from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)
        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as e:
        logger.error(f"❌ Could not connect to MongoDB: {str(e)}")
        raise e

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("🔌 Closed MongoDB connection")

def get_database():
    """Get database instance"""
    # FIX: Add validation
    if db.client is None:
        logger.error("❌ Database client is None - connection not initialized!")
        raise RuntimeError("Database connection not initialized. Call connect_to_mongo() first.")
    
    return db.client[settings.DATABASE_NAME]
