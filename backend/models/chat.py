from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    role: str                  # "user" | "assistant"
    content: str
    timestamp: datetime
    persona: Optional[str] = None
    intent: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: str
    persona: Optional[str] = None
    message: str
    use_rag: bool = True
    force_offline: bool = False
    history: List[Dict[str, str]] = []
    context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    response: str
    persona: Optional[str]
    intent: str
    response_source: str        # "groq" | "local"
    is_offline_mode: bool
    rag_used: bool
    sources: List[Dict[str, Any]] = []
