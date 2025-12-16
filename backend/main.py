from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, persona, mock_data, rag_admin, auth, audio
import os
from dotenv import load_dotenv
from utils.database import connect_to_mongo, close_mongo_connection
from config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

os.environ["ANONYMIZED_TELEMETRY"] = "False"

app = FastAPI(
    title="Deep Shiva - RAG-Enhanced AI Tourism Chatbot",
    description="Multi-persona AI chatbot with RAG, Groq API + Google OAuth authentication",
    version=settings.API_VERSION
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        settings.FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Deep Shiva Tourism API...")
    try:
        await connect_to_mongo()
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Deep Shiva Tourism API...")
    await close_mongo_connection()
    logger.info("✅ Cleanup completed")

# Register routers
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(persona.router, prefix="/api", tags=["personas"])
app.include_router(mock_data.router, prefix="/api/mock", tags=["mock-data"])
app.include_router(rag_admin.router, prefix="/api/rag", tags=["rag-admin"])
app.include_router(audio.router, prefix="/api", tags=["audio"]) 

@app.get("/")
async def root():
    return {
        "message": "Welcome to Deep Shiva RAG-Enhanced AI",
        "version": settings.API_VERSION,
        "features": [
            "RAG-Enhanced Responses",
            "Groq API Integration",
            "Google OAuth Authentication",
            "User Chat History",
            "Offline Fallback",
            "Multi-Persona Chat",
            "Content Management",
            "Admin Interface"
        ],
        "docs": "/docs",
        "admin_endpoints": "/api/rag/*",
        "auth_endpoints": "/api/auth/*"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Deep Shiva RAG-Enhanced API",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "mongodb_configured": bool(settings.MONGODB_URI),
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID),
        "rag_enabled": True,
        "version": settings.API_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
