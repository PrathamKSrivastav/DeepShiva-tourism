from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from routers import chat, persona, mock_data, rag_admin, auth, audio, meditation, tts
import os
from utils.kokoro_service import KokoroTTSService
from dotenv import load_dotenv
from utils.database import connect_to_mongo, close_mongo_connection
from config import settings
import logging
from pathlib import Path

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

public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount("/images", StaticFiles(directory=str(public_dir / "images")), name="images")
    logger.info(f"✅ Static files mounted: {public_dir}")
else:
    logger.warning(f"⚠️ Public directory not found: {public_dir}")
    logger.info(
        "📁 Create backend/public/audio/ and backend/public/images/ directories"
    )

# ✅ Custom audio endpoint with proper CORS headers
@app.get("/audio/{file_path:path}")
async def get_audio(file_path: str):
    """Serve audio files with CORS headers"""
    audio_dir = public_dir / "audio"
    requested_file = audio_dir / file_path
    
    # Security: prevent path traversal
    try:
        requested_file = requested_file.resolve()
        audio_dir = audio_dir.resolve()
        if not str(requested_file).startswith(str(audio_dir)):
            logger.warning(f"🚫 Attempted path traversal: {file_path}")
            return {"error": "Invalid path"}
    except Exception as e:
        logger.error(f"❌ Path resolution error: {str(e)}")
        return {"error": "Invalid path"}
    
    if not requested_file.exists():
        logger.warning(f"⚠️ Audio file not found: {requested_file}")
        return {"error": "File not found"}
    
    logger.info(f"🎵 Serving audio: {file_path}")
    
    # ✅ Serve with proper headers
    return FileResponse(
        path=requested_file,
        media_type="audio/mpeg",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cross-Origin-Resource-Policy": "cross-origin",
        }
    )

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Deep Shiva Tourism API...")
    try:
        await connect_to_mongo()
        en = KokoroTTSService(lang_code="a")
        hi = KokoroTTSService(lang_code="h")
        en.synthesize("Ready", voice="af_heart", speed=1.0)
        hi.synthesize("तैयार", voice="hf_alpha", speed=1.0)
        logger.info("✅ Kokoro TTS prewarmed")
    except Exception as e:
        logger.warning(f"⚠️ Kokoro prewarm failed: {e}")
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
app.include_router(meditation.router, prefix="/api", tags=["meditation"])
app.include_router(tts.router, prefix="/api", tags=["tts"])

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
        "auth_endpoints": "/api/auth/*",
        "static_files": {
            "audio": "/audio/",
            "images": "/images/"
        }
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
        "version": settings.API_VERSION,
        "static_files": {
            "audio_path": "/audio/",
            "images_path": "/images/"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
