import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime
from bson import ObjectId


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

async def save_to_session(
    user_id,
    persona,
    user_message,
    bot_response,
    intent,
    session_id=None
):
    """
    Save a user + assistant message pair into a chat session.
    Creates a new session if session_id is None.
    """
    db = get_database()
    if db is None:
        return None, False

    message_pair = [
        {
            "role": "user",
            "content": user_message,
            "intent": intent,
            "timestamp": datetime.utcnow()
        },
        {
            "role": "assistant",
            "content": bot_response,
            "timestamp": datetime.utcnow()
        }
    ]

    # Create new session
    if not session_id:
        session_doc = {
            "user_id": user_id,
            "persona": persona,
            "title": user_message[:50],
            "messages": message_pair,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.chats.insert_one(session_doc)
        return str(result.inserted_id), True

    # Update existing session
    await db.chats.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": {"$each": message_pair}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    return session_id, True