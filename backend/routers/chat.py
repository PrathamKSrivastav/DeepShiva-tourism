from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime
from utils.groq_service import GroqService
from utils.intents import classify_intent
from utils.persona_templates import generate_response as generate_local_response
from utils.connection_checker import check_internet_connection
from utils.database import get_database
from middleware.auth import get_current_user  # Optional auth - allows guests
from bson import ObjectId

from tools.tool_router import decide_tools
from tools.geocoding_tool import geocode_location
from tools.weather_tool import get_weather


# Setup logging
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)

router = APIRouter()

# ============= Models =============

class ChatRequest(BaseModel):
    message: str
    persona: str = "local_guide"
    context: Optional[dict] = None
    force_offline: Optional[bool] = False
    use_rag: Optional[bool] = True
    session_id: Optional[str] = None  # NEW: Track which chat session

class ChatResponse(BaseModel):
    response: str
    persona: str
    intent: str
    suggestions: list[str]
    response_source: str
    response_time_ms: int
    is_offline_mode: bool
    rag_info: Optional[Dict[str, Any]] = None
    chat_saved: bool = False
    session_id: Optional[str] = None  # NEW: Return session ID

class CreateSessionRequest(BaseModel):
    persona: str = "local_guide"
    title: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    title: str

# Initialize Groq service
groq_service = GroqService()

# ============= Chat Session Management =============

@router.post("/chat/sessions/new")
async def create_new_chat_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new chat session (notebook)
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        # user_id = ObjectId(current_user.get("_id") or current_user.get("id"))
        user_id = current_user.get("_id") or current_user.get("id")

        
        # Create new session
        new_session = {
            "user_id": user_id,
            "persona": request.persona,
            "title": request.title or "New Conversation",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.chats.insert_one(new_session)
        session_id = str(result.inserted_id)
        
        logger.info(f"✅ New chat session created: {session_id}")
        
        return {
            "session_id": session_id,
            "persona": request.persona,
            "title": request.title or "New Conversation",
            "created_at": new_session["created_at"].isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def get_all_chat_sessions(
    persona: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all chat sessions (notebooks) for user
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        # user_id = ObjectId(current_user.get("_id") or current_user.get("id"))
        user_id = current_user.get("_id") or current_user.get("id")

        
        # Build query
        query = {"user_id": user_id}
        if persona:
            query["persona"] = persona
        
        # Fetch sessions
        sessions = await db.chats.find(query).sort("updated_at", -1).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string
        for session in sessions:
            session["_id"] = str(session["_id"])
            session["user_id"] = str(session["user_id"])
        
        logger.info(f"✅ Found {len(sessions)} sessions")
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        # logger.error(f"❌ Error fetching sessions: {str(e)}")
        logger.exception("❌ Error fetching sessions")

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get specific chat session with all messages
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        # user_id = ObjectId(current_user.get("_id") or current_user.get("id"))
        user_id = current_user.get("_id") or current_user.get("id")

        
        # Fetch session
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert ObjectId
        session["_id"] = str(session["_id"])
        session["user_id"] = str(session["user_id"])
        
        return session
        
    except Exception as e:
        # logger.error(f"❌ Error fetching session: {str(e)}")
        logger.exception("❌ Error fetching sessions")

        raise HTTPException(status_code=500, detail=str(e))


@router.put("/chat/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update chat session title
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        # user_id = ObjectId(current_user.get("_id") or current_user.get("id"))
        user_id = current_user.get("_id") or current_user.get("id")

        
        result = await db.chats.update_one(
            {"_id": ObjectId(session_id), "user_id": user_id},
            {"$set": {"title": request.title, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Session title updated: {session_id}")
        
        return {"message": "Title updated", "title": request.title}
        
    except Exception as e:
        logger.error(f"❌ Error updating title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a chat session
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        # user_id = ObjectId(current_user.get("_id") or current_user.get("id"))
        user_id = current_user.get("_id") or current_user.get("id")

        
        result = await db.chats.delete_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Session deleted: {session_id}")
        
        return {"message": "Session deleted"}
        
    except Exception as e:
        logger.error(f"❌ Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Chat Endpoint (Updated) =============

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Send message to chat - creates or appends to session
    """
    logger.info("=" * 70)
    logger.info("💬 CHAT ENDPOINT CALLED")
    logger.info(f"📝 Message: {request.message[:50]}...")
    logger.info(f"🎭 Persona: {request.persona}")
    logger.info(f"🆔 Session ID: {request.session_id}")
    logger.info(f"🔐 Authenticated: {current_user is not None}")
    
    start_time = asyncio.get_event_loop().time()
    chat_saved = False
    session_id = request.session_id
    
    try:
        # Classify intent
        intent = classify_intent(request.message)
        tools_used = decide_tools(
             request.persona,
             intent,
             request.message
         )
        tool_context: Dict[str, Any] = {}
        # --------------------------------------------------
        # TOOL ORCHESTRATION — STEP 1 (GEOCODING)
        # --------------------------------------------------
        location_data = None
        if "geocoding" in tools_used:
            from utils.intents import extract_location

            location_query = extract_location(request.message)

            if location_query:
                location_data = await geocode_location(location_query)

                if location_data:
                    tool_context["location"] = location_data

                    logger.info(
                        f"🗺️ Geocoding used: "
                        f"{location_data.get('place_name')} | "
                        f"{location_data.get('city')}, {location_data.get('state')} "
                        f"({location_data.get('latitude')}, {location_data.get('longitude')})"
                    )

        # --------------------------------------------------
        # WEATHER TOOL
        # --------------------------------------------------

        if "weather" in tools_used and "location" in tool_context:
            loc = tool_context["location"]

            try:
                weather_data = await get_weather(
                    latitude=float(loc["latitude"]),
                    longitude=float(loc["longitude"])
                )

                if weather_data:
                    tool_context["weather"] = weather_data
                    logger.info("🌦️ Weather data retrieved using Open-Meteo")

            except Exception as e:
                logger.warning(f"Weather API failed: {e}")

        # --------------------------------------------------
        # SHORT-CIRCUIT: TOOL-ONLY WEATHER RESPONSE
        # --------------------------------------------------
        # if "weather" in tool_context and "location" in tool_context:
        #     w = tool_context["weather"]
        #     loc = tool_context["location"]

        #     response_text = (
        #         f"📍 **Weather forecast for {loc.get('place_name')} (next 7 days):**\n\n"
        #         f"- 🌡️ Max temp: {min(w['temp_max'])}°C – {max(w['temp_max'])}°C\n"
        #         f"- 🌡️ Min temp: {min(w['temp_min'])}°C – {max(w['temp_min'])}°C\n"
        #         f"- 🌧️ Rainfall: {sum(w['precipitation'])} mm (total)\n"
        #         f"- 💨 Wind speed: up to {max(w['wind_speed'])} km/h\n\n"
        #         f"This forecast is based on **live Open-Meteo data**."
        #     )

        #     end_time = asyncio.get_event_loop().time()
        #     response_time = int((end_time - start_time) * 1000)

        #     return ChatResponse(
        #         response=response_text,
        #         persona=request.persona,
        #         intent=intent,
        #         suggestions=["Best time to visit?", "Is it safe to travel?"],
        #         response_source="tool_weather",
        #         response_time_ms=response_time,
        #         is_offline_mode=False,
        #         rag_info={"rag_used": False},
        #         chat_saved=False,
        #         session_id=session_id
        #     )

        # Check connectivity
        if request.force_offline:
            return await _generate_local_response(request, intent, start_time, forced=True)
        
        is_online = await check_internet_connection()
        if not is_online:
            return await _generate_local_response(request, intent, start_time)
        
        # Get AI response
        try:
            logger.info("🤖 Calling Groq API...")
            logger.info(f"🧰 TOOL CONTEXT SENT TO LLM: {tool_context}")
            response_text, suggestions = await groq_service.generate_persona_response(
                message=request.message,
                persona=request.persona,
                intent=intent,
                context=request.context,
                tool_context=tool_context or {}
            )
            
            logger.info(f"✅ Groq response received ({len(response_text)} chars)")
            
            end_time = asyncio.get_event_loop().time()
            response_time = int((end_time - start_time) * 1000)
            
            # Get RAG info
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
            
            response_source = "groq_with_rag" if (rag_info and rag_info.get("rag_used")) else "groq"
            
            # Save to session if authenticated
            if current_user:
                logger.info("💾 Saving to chat session...")
                try:
                    session_id, chat_saved = await save_to_session(
                        user_id=current_user.get("_id") or current_user.get("id"),
                        persona=request.persona,
                        user_message=request.message,
                        bot_response=response_text,
                        intent=intent,
                        session_id=session_id
                    )
                    
                    if chat_saved:
                        logger.info(f"✅ Saved to session: {session_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error saving: {str(e)}")
            
            return ChatResponse(
                response=response_text,
                persona=request.persona,
                intent=intent,
                suggestions=suggestions,
                response_source=response_source,
                response_time_ms=response_time,
                is_offline_mode=False,
                rag_info=rag_info,
                chat_saved=chat_saved,
                session_id=session_id
            )
            
        except Exception as groq_error:
            logger.warning(f"Groq API failed: {str(groq_error)[:100]}")
            return await _generate_local_response(request, intent, start_time, api_error=True)
    
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def save_to_session(
    user_id: str,
    persona: str,
    user_message: str,
    bot_response: str,
    intent: str,
    session_id: Optional[str] = None
) -> tuple[str, bool]:
    """
    Save message to chat session
    Returns: (session_id, success)
    """
    try:
        db = get_database()
        # user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user_id = str(user_id)

        
        # Prepare messages
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow(),
            "intent": intent
        }
        
        bot_msg = {
            "role": "assistant",
            "content": bot_response,
            "timestamp": datetime.utcnow(),
            "persona": persona
        }
        
        # If session_id provided, append to existing
        if session_id:
            logger.info(f"📤 Appending to session: {session_id}")
            result = await db.chats.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {
                    "$push": {"messages": {"$each": [user_msg, bot_msg]}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info("✅ Appended to existing session")
                return session_id, True
            else:
                logger.warning("⚠️ Session not found, creating new")
        
        # Create new session
        # Generate title from first message
        title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        
        new_session = {
            "user_id": user_id,
            "persona": persona,
            "title": title,
            "messages": [user_msg, bot_msg],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.chats.insert_one(new_session)
        new_session_id = str(result.inserted_id)
        
        logger.info(f"✅ Created new session: {new_session_id}")
        return new_session_id, True
        
    except Exception as e:
        logger.error(f"❌ Save failed: {str(e)}")
        return None, False


# ============= Helper Functions =============

async def _generate_local_response(request, intent, start_time, forced=False, api_error=False):
    """Generate offline response"""
    try:
        response_text = generate_local_response(
            message=request.message,
            persona=request.persona,
            intent=intent,
            context=request.context or {}
        )
        
        if api_error:
            response_text += "\n\n🔸 *AI service temporarily unavailable*"
        
        suggestions = get_local_suggestions(intent, request.persona)
        end_time = asyncio.get_event_loop().time()
        response_time = int((end_time - start_time) * 1000)
        
        return ChatResponse(
            response=response_text,
            persona=request.persona,
            intent=intent,
            suggestions=suggestions,
            response_source="local_template",
            response_time_ms=response_time,
            is_offline_mode=True,
            rag_info={"rag_used": False},
            chat_saved=False
        )
    except Exception as e:
        logger.error(f"Local response failed: {str(e)}")
        raise


def get_local_suggestions(intent: str, persona: str) -> list[str]:
    """Generate suggestions"""
    base_suggestions = {
        "general": ["Plan my trip", "Weather info", "Best places"],
        "weather": ["Best time to visit?", "Monsoon season?"],
        "itinerary": ["Char Dham route?", "How many days?"],
        "spiritual": ["Temple legends", "Kedarnath significance"],
        "trekking": ["Valley of Flowers", "Trekking gear"],
    }
    return base_suggestions.get(intent, base_suggestions["general"])


# ============= Legacy Endpoints (for compatibility) =============

@router.get("/chat/history")
async def get_chat_history(
    current_user: dict = Depends(get_current_user),
    persona: Optional[str] = None,
    limit: int = 50
):
    """Legacy endpoint - redirects to sessions"""
    return await get_all_chat_sessions(persona, limit, current_user)


@router.delete("/chat/history/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Legacy endpoint - redirects to session delete"""
    return await delete_chat_session(chat_id, current_user)


# ============= Status Endpoints =============

@router.get("/connection-status")
async def connection_status():
    """Check connectivity"""
    internet_status = await check_internet_connection()
    groq_status = await groq_service.health_check()
    
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
        "rag_total_documents": rag_status.get("total_documents", 0)
    }
