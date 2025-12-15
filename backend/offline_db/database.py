import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from offline_db.database import OfflineDatabase

logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017"
_DB_NAME = "deepshiva_tourism"

DB_MODE = "offline"
DB_CLIENT = None
OFFLINE_DB = None


def init_database():
    global DB_CLIENT, DB_MODE, OFFLINE_DB

    try:
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=3000
        )
        client.admin.command("ping")

        DB_CLIENT = client[_DB_NAME]
        DB_MODE = "online"

        logger.info("🟢 MongoDB connected")

    except ServerSelectionTimeoutError:
        DB_CLIENT = None
        DB_MODE = "offline"

        OFFLINE_DB = OfflineDatabase(
            base_path="backend/data/offline_db",
            name=_DB_NAME
        )

        logger.warning("🔴 MongoDB unavailable — offline DB active")


def get_database():
    if DB_MODE == "online" and DB_CLIENT:
        return DB_CLIENT
    return OFFLINE_DB
