from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from routers import (
    chat,
    persona,
    mock_data,
    rag_admin,
    auth,
    audio,
    meditation,
    tts,
    yoga,  # ← yoga router
)
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

# ============= SINGLETON PATTERN FOR VECTOR STORE =============
_vector_store_instance = None


def get_vector_store_manager():
    """
    Singleton pattern to ensure only ONE VectorStoreManager instance
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        from rag.vector_store import VectorStoreManager

        logger.info("🔧 Initializing VectorStoreManager (SINGLETON)")
        _vector_store_instance = VectorStoreManager(
            persist_directory="data/vector_db",
            embedding_model_name="all-MiniLM-L6-v2",
            qdrant_host=os.getenv("QDRANT_HOST"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            qdrant_dim=int(os.getenv("QDRANT_DIM", 384)),
        )

        if _vector_store_instance._cloud_available():
            logger.info("✅ Qdrant is reachable")
        else:
            logger.info("⚠️ Qdrant not reachable, falling back to Chroma")

    return _vector_store_instance


# Initialize once at module load
vector_store = get_vector_store_manager()

app = FastAPI(
    title="Deep Shiva - RAG-Enhanced AI Tourism Chatbot",
    description="Multi-persona AI chatbot with RAG, Groq API + Google OAuth authentication + Yoga Pose Detection",
    version=settings.API_VERSION,
)

# CORS middleware
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

public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount(
        "/images", StaticFiles(directory=str(public_dir / "images")), name="images"
    )
    logger.info(f"✅ Static files mounted: {public_dir}")
else:
    logger.warning(f"⚠️ Public directory not found: {public_dir}")
    logger.info(
        "📁 Create backend/public/audio/ and backend/public/images/ directories"
    )

# Note: yoga-static files are served via custom endpoint with CORS headers (see /yoga-static/{file_path:path} below)


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
        },
    )


# ✅ Custom yoga-static endpoint with proper CORS headers
@app.get("/yoga-static/{file_path:path}")
async def get_yoga_static(file_path: str):
    """Serve yoga static files (images) with CORS headers"""
    yoga_dir = public_dir
    requested_file = yoga_dir / file_path

    # Security: prevent path traversal
    try:
        requested_file = requested_file.resolve()
        yoga_dir = yoga_dir.resolve()
        if not str(requested_file).startswith(str(yoga_dir)):
            logger.warning(f"🚫 Attempted path traversal: {file_path}")
            return {"error": "Invalid path"}
    except Exception as e:
        logger.error(f"❌ Path resolution error: {str(e)}")
        return {"error": "Invalid path"}

    if not requested_file.exists():
        logger.warning(f"⚠️ Yoga static file not found: {requested_file}")
        return {"error": "File not found"}

    # Determine media type based on file extension
    ext = requested_file.suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    logger.info(f"🖼️ Serving yoga static: {file_path}")

    # ✅ Serve with proper headers
    return FileResponse(
        path=requested_file,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Cross-Origin-Resource-Policy": "cross-origin",
        },
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
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Startup warning: {e}")


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
app.include_router(yoga.router, prefix="/api/yoga", tags=["yoga"])  # ← ADD yoga router


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
            "Admin Interface",
            "Yoga Pose Detection",
        ],
        "docs": "/docs",
        "admin_endpoints": "/api/rag/*",
        "auth_endpoints": "/api/auth/*",
        "yoga_endpoints": "/api/yoga/*",
        "static_files": {
            "audio": "/audio/",
            "images": "/images/",
            "yoga_static": "/yoga-static/",
        },
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
        "yoga_enabled": True,
        "version": settings.API_VERSION,
        "static_files": {
            "audio_path": "/audio/",
            "images_path": "/images/",
            "yoga_static_path": "/yoga-static/",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
