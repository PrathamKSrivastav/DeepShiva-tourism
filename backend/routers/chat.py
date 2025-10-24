from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging
from utils.groq_service import GroqService
from utils.intents import classify_intent
from utils.persona_templates import generate_response as generate_local_response
from utils.connection_checker import check_internet_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    persona: str = "local_guide"
    context: Optional[dict] = None
    force_offline: Optional[bool] = False
    use_rag: Optional[bool] = True  # New: Enable/disable RAG

class ChatResponse(BaseModel):
    response: str
    persona: str
    intent: str
    suggestions: list[str]
    response_source: str  # "groq_with_rag", "groq", "local_template", "error_fallback"
    response_time_ms: int
    is_offline_mode: bool
    rag_info: Optional[Dict[str, Any]] = None  # New: RAG information

# Initialize Groq service with RAG
groq_service = GroqService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Enhanced hybrid chat endpoint: Groq API with RAG primary, local template fallback
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Classify user intent (always local)
        intent = classify_intent(request.message)
        
        # Check if we should force offline mode (for testing)
        if request.force_offline:
            logger.info("Forced offline mode requested")
            return await _generate_local_response(request, intent, start_time, forced=True)
        
        # Check internet connectivity and API availability
        is_online = await check_internet_connection()
        if not is_online:
            logger.info("No internet connection - using offline mode")
            return await _generate_local_response(request, intent, start_time)
        
        # Try Groq API with RAG enhancement
        try:
            response_text, suggestions = await groq_service.generate_persona_response(
                message=request.message,
                persona=request.persona,
                intent=intent,
                context=request.context or {}
            )
            
            end_time = asyncio.get_event_loop().time()
            response_time = int((end_time - start_time) * 1000)
            
            # Get RAG information for response
            rag_info = None
            if request.use_rag and hasattr(groq_service, 'persona_rag') and groq_service.persona_rag:
                try:
                    rag_status = await groq_service.get_rag_status()
                    if rag_status.get("rag_enabled", False):
                        rag_info = {
                            "rag_used": True,
                            "total_documents": rag_status.get("total_documents", 0),
                            "collections_used": list(rag_status.get("collections", {}).keys()),
                            "rag_status": "active"
                        }
                except Exception as e:
                    logger.warning(f"Error getting RAG info: {str(e)}")
                    rag_info = {"rag_used": False, "error": str(e)}
            
            response_source = "groq_with_rag" if (rag_info and rag_info.get("rag_used")) else "groq"
            
            return ChatResponse(
                response=response_text,
                persona=request.persona,
                intent=intent,
                suggestions=suggestions,
                response_source=response_source,
                response_time_ms=response_time,
                is_offline_mode=False,
                rag_info=rag_info
            )
            
        except Exception as groq_error:
            logger.warning(f"Groq API failed: {str(groq_error)[:100]}... - Falling back to local templates")
            return await _generate_local_response(request, intent, start_time, api_error=True)
    
    except Exception as e:
        logger.error(f"Critical error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")

async def _generate_local_response(
    request: ChatRequest, 
    intent: str, 
    start_time: float, 
    forced: bool = False,
    api_error: bool = False
) -> ChatResponse:
    """Generate response using local template system"""
    
    try:
        # Generate local response
        response_text = generate_local_response(
            message=request.message,
            persona=request.persona,
            intent=intent,
            context=request.context or {}
        )
        
        # Add offline mode indicator to response
        if not forced and not api_error:
            response_text += "\n\n🔸 *Currently in offline mode - providing cached information*"
        elif api_error:
            response_text += "\n\n🔸 *AI service temporarily unavailable - providing local knowledge*"
        
        # Generate suggestions (local)
        suggestions = get_local_suggestions(intent, request.persona)
        
        end_time = asyncio.get_event_loop().time()
        response_time = int((end_time - start_time) * 1000)
        
        source = "local_template" if not api_error else "error_fallback"
        
        return ChatResponse(
            response=response_text,
            persona=request.persona,
            intent=intent,
            suggestions=suggestions,
            response_source=source,
            response_time_ms=response_time,
            is_offline_mode=True,
            rag_info={"rag_used": False, "reason": "offline_mode"}
        )
        
    except Exception as e:
        logger.error(f"Local response generation failed: {str(e)}")
        # Emergency fallback
        end_time = asyncio.get_event_loop().time()
        response_time = int((end_time - start_time) * 1000)
        
        return ChatResponse(
            response="I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment. 🙏",
            persona=request.persona,
            intent=intent,
            suggestions=["Try asking again", "Check connection", "Contact support"],
            response_source="emergency_fallback",
            response_time_ms=response_time,
            is_offline_mode=True,
            rag_info={"rag_used": False, "reason": "system_error"}
        )

def get_local_suggestions(intent: str, persona: str) -> list[str]:
    """Generate contextual suggestions for local responses"""
    base_suggestions = {
        "weather": [
            "What's the best time to visit?",
            "Tell me about monsoon season",
            "Current crowd levels?"
        ],
        "itinerary": [
            "How many days do I need for Char Dham?",
            "What are the distances between temples?",
            "Best route planning tips"
        ],
        "spiritual": [
            "Tell me temple legends",
            "Significance of Kedarnath",
            "Best time for darshan"
        ],
        "trekking": [
            "Valley of Flowers difficulty",
            "Essential trekking gear",
            "Safety precautions"
        ],
        "emergency": [
            "Altitude sickness precautions",
            "Nearest medical facilities", 
            "Emergency evacuation procedures"
        ],
        "festival": [
            "When is Ganga Dussehra?",
            "What festivals happen in summer?",
            "Cultural events in Rishikesh"
        ],
        "crowd": [
            "Peak season timing",
            "Off-season advantages", 
            "How to avoid crowds"
        ],
        "accommodation": [
            "Where to stay in Kedarnath?",
            "Budget accommodation options",
            "Booking recommendations"
        ],
        "food": [
            "Local Uttarakhand cuisine",
            "Vegetarian options",
            "Food safety tips"
        ],
        "general": [
            "Plan my Uttarakhand trip",
            "Best spiritual destinations",
            "Adventure activities available"
        ]
    }
    
    return base_suggestions.get(intent, base_suggestions["general"])

@router.get("/connection-status")
async def connection_status():
    """Check API and internet connectivity status with RAG info"""
    internet_status = await check_internet_connection()
    groq_status = await groq_service.health_check()
    
    # Get RAG status
    rag_status = {"rag_enabled": False}
    if hasattr(groq_service, 'get_rag_status'):
        try:
            rag_status = await groq_service.get_rag_status()
        except Exception as e:
            logger.error(f"Error getting RAG status: {str(e)}")
    
    return {
        "internet_connected": internet_status,
        "groq_api_available": groq_status,
        "rag_enabled": rag_status.get("rag_enabled", False),
        "rag_total_documents": rag_status.get("total_documents", 0),
        "recommended_mode": "online" if (internet_status and groq_status) else "offline"
    }

@router.post("/test-offline")
async def test_offline_mode(request: ChatRequest):
    """Test endpoint to force offline mode for development"""
    request.force_offline = True
    return await chat(request)

@router.post("/test-rag")
async def test_rag_query(query: str, persona: str = "local_guide"):
    """Test RAG functionality directly"""
    try:
        if not hasattr(groq_service, 'persona_rag') or not groq_service.persona_rag:
            return {"error": "RAG not initialized"}
        
        from utils.intents import classify_intent
        intent = classify_intent(query)
        
        rag_context = await groq_service.persona_rag.enhance_query_with_rag(
            query=query,
            persona=persona,
            intent=intent
        )
        
        return {
            "query": query,
            "persona": persona,
            "intent": intent,
            "rag_context": rag_context
        }
        
    except Exception as e:
        logger.error(f"Error testing RAG: {str(e)}")
        return {"error": str(e)}
