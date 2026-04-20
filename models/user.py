from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None

class User(BaseModel):
    id: str = Field(alias="_id")
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    role: str = "user"  # "user" or "admin"
    created_at: datetime
    last_login: datetime
    
    class Config:
        populate_by_name = True

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str
    created_at: datetime
    last_login: datetime
