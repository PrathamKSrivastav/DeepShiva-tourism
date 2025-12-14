from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Persona(BaseModel):
    id: str
    name: str
    description: str
    tone: str
    avatar: str

@router.get("/personas")
async def get_personas():
    """
    Returns all available chatbot personas
    """
    personas = [
        {
            "id": "local_guide",
            "name": "Local Guide",
            "description": "Your friendly neighborhood expert with practical tips and insider knowledge",
            "tone": "Friendly, conversational, practical",
            "avatar": "LG"
        },
        {
            "id": "spiritual_teacher",
            "name": "Spiritual Teacher",
            "description": "Serene guide to the spiritual essence of India's sacred sites",
            "tone": "Serene, reflective, philosophical",
            "avatar": "OM"
        },
        {
            "id": "trek_companion",
            "name": "Trek Companion",
            "description": "Your adventurous buddy for mountain expeditions and safety guidance",
            "tone": "Adventurous, concise, safety-focused",
            "avatar": "TE"
        },
        {
            "id": "cultural_expert",
            "name": "Cultural Expert",
            "description": "Master storyteller of myths, legends, and cultural heritage",
            "tone": "Informative, mythological, storytelling",
            "avatar": "CE"
        }
    ]
    
    return {"personas": personas}
