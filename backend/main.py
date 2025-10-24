from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, persona, mock_data, rag_admin
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Deep Shiva - RAG-Enhanced AI Tourism Chatbot",
    description="Multi-persona AI chatbot with RAG, Groq API + offline fallback for Uttarakhand tourism",
    version="3.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Added admin panel port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(persona.router, prefix="/api", tags=["personas"])
app.include_router(mock_data.router, prefix="/api/mock", tags=["mock-data"])
app.include_router(rag_admin.router, prefix="/api/rag", tags=["rag-admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Deep Shiva RAG-Enhanced AI",
        "version": "3.0.0",
        "features": [
            "RAG-Enhanced Responses", 
            "Groq API Integration", 
            "Offline Fallback", 
            "Multi-Persona Chat",
            "Content Management",
            "Admin Interface"
        ],
        "docs": "/docs",
        "admin_endpoints": "/api/rag/*"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Deep Shiva RAG-Enhanced API",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "rag_enabled": True,
        "version": "3.0.0"
    }
