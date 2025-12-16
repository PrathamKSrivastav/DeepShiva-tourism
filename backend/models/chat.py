from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    persona: Optional[str] = None
    intent: Optional[str] = None

class ChatCreate(BaseModel):
    user_id: str
    persona: str
    message: ChatMessage

class Chat(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    persona: str
    messages: List[ChatMessage] = []
    context: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True

class ChatResponse(BaseModel):
    id: str
    user_id: str
    persona: str
    messages: List[ChatMessage]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
