# backend/main.py

import os
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import chat, persona, mock_data, rag_admin, auth
from config import settings
from utils.database import init_database
from utils.mongo_watcher import MongoWatcher

# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# ENV
# -------------------------------------------------------------------

load_dotenv()

# -------------------------------------------------------------------
# APP
# -------------------------------------------------------------------

app = FastAPI(
    title="Deep Shiva - RAG-Enhanced AI Tourism Chatbot",
    description="Offline-first RAG + Local LLM + MongoDB resilience",
    version=settings.API_VERSION
)

# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# STARTUP
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """
    Offline-first startup.
    MongoDB failure does NOT prevent boot.
    """
    logger.info("🚀 Starting Deep Shiva Tourism API...")

    # 1️⃣ Attempt MongoDB connection (non-fatal)
    init_database()

    # 2️⃣ Start watcher to reattach MongoDB when it comes back
    watcher = MongoWatcher(
        uri=settings.MONGODB_URI,
        db_name="deepshiva_tourism"
    )

    asyncio.create_task(watcher.wait_until_available())

    logger.info("✅ Startup sequence complete")

# -------------------------------------------------------------------
# ROUTERS
# -------------------------------------------------------------------

app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(persona.router, prefix="/api", tags=["personas"])
app.include_router(mock_data.router, prefix="/api/mock", tags=["mock-data"])
app.include_router(rag_admin.router, prefix="/api/rag", tags=["rag-admin"])

# -------------------------------------------------------------------
# ROOT
# -------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "Deep Shiva Tourism API",
        "mode": "offline-first",
        "docs": "/docs",
        "features": [
            "Local GGUF LLM",
            "Offline MongoDB Shim",
            "Online MongoDB Hot-Swap",
            "RAG Retrieval",
            "Persona Routing",
        ],
    }

# -------------------------------------------------------------------
# HEALTH
# -------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mongodb_uri_set": bool(settings.MONGODB_URI),
        "groq_key_present": bool(os.getenv("GROQ_API_KEY")),
        "version": settings.API_VERSION,
    }

# -------------------------------------------------------------------
# DEV ENTRY
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
