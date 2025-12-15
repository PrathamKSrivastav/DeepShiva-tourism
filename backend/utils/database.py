import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# ======================
# DB CONSTANTS (FIRST)
# ======================

MONGO_URI = "mongodb://localhost:27017"
_DB_NAME = "deepshiva_tourism"

DB_MODE = "offline"   # "online" | "offline"
DB_CLIENT = None      # pymongo database handle OR None


# ======================
# INITIALIZER
# ======================

def init_database():
    """
    Attempts MongoDB connection.
    Fails gracefully into offline mode.
    """
    global DB_CLIENT, DB_MODE

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=3000
        )
        client.admin.command("ping")

        DB_CLIENT = client[_DB_NAME]
        DB_MODE = "online"

        logger.info("🟢 Connected to MongoDB")

    except ServerSelectionTimeoutError:
        DB_CLIENT = None
        DB_MODE = "offline"

        logger.warning("🔴 MongoDB unavailable — offline DB active")

    return DB_CLIENT


# ======================
# ACCESSOR
# ======================

def get_database():
    """
    Unified DB accessor.
    Online → MongoDB
    Offline → handled upstream by offline DB shim
    """
    return DB_CLIENT
