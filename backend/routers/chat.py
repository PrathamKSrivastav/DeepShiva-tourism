from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import json
from datetime import datetime

from utils.groq_service import GroqService
from utils.intents import classify_intent
# from utils.persona_templates import generate_response as generate_local_response # (Optional if used)
from utils.connection_checker import check_internet_connection
from utils.database import get_database, save_to_session
from middleware.auth import get_current_user
from bson import ObjectId

# Tools
from tools.geocoding_tool import geocode_location
from tools.weather_tool import get_weather

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
groq_service = GroqService()

# ============= Helper Models & Functions =============

class ChatRequest(BaseModel):
    message: str
    persona: str = "local_guide"
    context: Optional[dict] = None
    force_offline: Optional[bool] = False
    use_rag: Optional[bool] = True
    session_id: Optional[str] = None

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
    session_id: Optional[str] = None

class CreateSessionRequest(BaseModel):
    persona: str = "local_guide"
    title: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    title: str

def get_tools_schema():
    return [
        {
            "type": "function",
            "function": {
                "name": "geocode_location",
                "description": "Get latitude and longitude for a city or place name. Use this before getting weather.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The city or place name to find (e.g. 'Dehradun', 'Mumbai')"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather forecast for coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {"type": "number", "description": "Latitude of the location"},
                        "longitude": {"type": "number", "description": "Longitude of the location"}
                    },
                    "required": ["latitude", "longitude"]
                }
            }
        }
    ]

async def get_session_history_as_context(session_id: str, limit: int = 6):
    """
    Fetch recent messages from a session to provide context to the LLM.
    """
    try:
        if not session_id:
            return []
            
        db = get_database()
        session = await db.chats.find_one({"_id": ObjectId(session_id)})
        
        if not session or "messages" not in session:
            return []
        
        # Get last N messages (limit * 2 because we have user+bot pairs)
        messages = session["messages"][-(limit * 2):] if len(session["messages"]) > limit * 2 else session["messages"]
        
        # Convert to Groq format
        conversation_history = []
        for msg in messages:
            conversation_history.append({
                "role": msg["role"],  # "user" or "assistant"
                "content": msg["content"]
            })
        
        return conversation_history
        
    except Exception as e:
        logger.error(f"❌ Error fetching conversation history: {str(e)}")
        return []

# ============= Session Management Endpoints =============

@router.post("/chat/sessions/new")
async def create_new_chat_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat session (notebook)"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = current_user.get("_id") or current_user.get("id")
        
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
    """Get all chat sessions (notebooks) for user"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        query = {"user_id": user_id}
        if persona:
            query["persona"] = persona
            
        sessions = await db.chats.find(query).sort("updated_at", -1).limit(limit).to_list(length=limit)
        
        for session in sessions:
            session["_id"] = str(session["_id"])
            session["user_id"] = str(session["user_id"])
            
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"❌ Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific chat session with all messages"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = current_user.get("_id") or current_user.get("id")
        
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session["_id"] = str(session["_id"])
        session["user_id"] = str(session["user_id"])
        
        return session
    except Exception as e:
        logger.exception("❌ Error fetching session")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chat session"""
    try:
        if not current_user:
             raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
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

@router.put("/chat/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update chat session title"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        db = get_database()
        user_id = current_user.get("_id") or current_user.get("id")
        
        result = await db.chats.update_one(
            {"_id": ObjectId(session_id), "user_id": user_id},
            {"$set": {"title": request.title, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {"message": "Title updated", "title": request.title}
    except Exception as e:
        logger.error(f"❌ Error updating title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= MAIN CHAT ENDPOINT (AGENT MODE) =============

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Agentic Chat Endpoint: Uses LLM to decide tool usage in a loop
    """
    logger.info("=" * 70)
    logger.info("💬 CHAT ENDPOINT (AGENT MODE) CALLED")
    
    start_time = asyncio.get_event_loop().time()
    session_id = request.session_id
    
    # 1. Initialize History & Context
    conversation_history = [] 
    
    # [OPTIONAL] Load history from DB if session_id exists
    if session_id:
        conversation_history = await get_session_history_as_context(session_id)
    
    tool_context = {} 

    # --- NEW BLOCK: FORCE WEATHER CHECK (To prevent "I can't connect" errors) ---
    lower_msg = request.message.lower()
    if any(k in lower_msg for k in ["weather", "climate", "temperature", "rain", "forecast"]):
        logger.info("⚡ FORCE-TRIGGER: Detected weather intent, running tools manually...")
        # 1. Ask LLM to extract city ONLY (Fast, no RAG)
        extraction_prompt = [
            {"role": "system", "content": "Extract the city name from the user's query. Return ONLY the city name. If none, return 'None'."},
            {"role": "user", "content": request.message}
        ]
        try:
            city_resp = await groq_service.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=extraction_prompt,
                max_tokens=10
            )
            city_name = city_resp.choices[0].message.content.strip()
            if city_name and city_name.lower() != "none":
                logger.info(f"⚡ FORCE-TRIGGER: Extracted city '{city_name}'")
                # 2. Manual Tool Execution
                geo_data = await geocode_location(city_name)
                if geo_data:
                    tool_context["location"] = geo_data
                    weather_data = await get_weather(geo_data["latitude"], geo_data["longitude"])
                    if weather_data:
                        # SIMPLIFY DATA TO SAVE TOKENS
                        simple_weather = {
                            "dates": weather_data.get("daily", {}).get("time", [])[:3],
                            "max_temp": weather_data.get("daily", {}).get("temperature_2m_max", [])[:3],
                            "min_temp": weather_data.get("daily", {}).get("temperature_2m_min", [])[:3],
                            "precip_sum": weather_data.get("daily", {}).get("precipitation_sum", [])[:3]
                        }
                        tool_context["weather"] = simple_weather
                        logger.info(f"⚡ FORCE-TRIGGER: Pre-loaded simplified weather data for {city_name}")
        except Exception as e:
            logger.error(f"Force trigger failed: {e}")
    # --- END NEW BLOCK ---
    
    # Still classify intent for RAG context (optional but helpful)
    intent = classify_intent(request.message) 
    
    # 2. THE AGENT LOOP
    max_turns = 5
    current_turn = 0
    final_response_text = ""
    final_suggestions = []
    
    # Get tool definitions
    tools_schema = get_tools_schema()
    
    while current_turn < max_turns:
        current_turn += 1
        logger.info(f"🔄 Agent Turn {current_turn}/{max_turns}")
        
        # Call Groq Service
        result = await groq_service.generate_persona_response(
            message=request.message,
            persona=request.persona,
            intent=intent,
            context=request.context or {},
            tool_context=tool_context,
            conversation_history=conversation_history,
            tools=tools_schema
        )
        
        # CASE A: LLM Wants to Run Tools
        if result["type"] == "tool_call":
            tool_calls = result["tool_calls"]
            llm_message = result["message"]
            
            # Add LLM's request to history so it knows it asked
            conversation_history.append(llm_message)
            
            # Execute each tool requested
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to decode arguments for {func_name}")
                    continue

                tool_result = None
                
                if func_name == "geocode_location":
                    logger.info(f"📍 Agent calling Geocode: {args.get('query')}")
                    tool_result = await geocode_location(args.get('query'))
                    if tool_result:
                        tool_context["location"] = tool_result
                        
                elif func_name == "get_weather":
                    logger.info(f"🌦️ Agent calling Weather: {args}")
                    tool_result = await get_weather(
                        latitude=args.get('latitude'),
                        longitude=args.get('longitude')
                    )
                    if tool_result:
                        # SIMPLIFY HERE TOO
                        simple_weather = {
                            "dates": tool_result.get("daily", {}).get("time", [])[:3],
                            "max_temp": tool_result.get("daily", {}).get("temperature_2m_max", [])[:3],
                            "min_temp": tool_result.get("daily", {}).get("temperature_2m_min", [])[:3]
                        }
                        tool_context["weather"] = simple_weather

                # Add result to history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps(simple_weather if tool_result else {"error": "failed"})
                })
            
            # Loop continues to next turn...

        # CASE B: LLM Returned Final Text
        elif result["type"] == "text":
            final_response_text = result["response"]
            final_suggestions = result["suggestions"]
            break # Exit loop
            
    # Fallback if loop finishes without text
    if not final_response_text:
        final_response_text = "I'm having trouble connecting to my tools. Let me answer based on my general knowledge."

    # 3. Construct Final Response
    end_time = asyncio.get_event_loop().time()
    response_time = int((end_time - start_time) * 1000)

    # Save to session (DB)
    if current_user:
        try:
             session_id, _ = await save_to_session(
                user_id=current_user.get("_id") or current_user.get("id"),
                persona=request.persona,
                user_message=request.message,
                bot_response=final_response_text,
                intent=intent,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"❌ Error saving session: {str(e)}")

    return ChatResponse(
        response=final_response_text,
        persona=request.persona,
        intent=intent,
        suggestions=final_suggestions,
        response_source="groq_agent",
        response_time_ms=response_time,
        is_offline_mode=False,
        rag_info={"rag_used": True}, 
        chat_saved=bool(current_user),
        session_id=session_id
    )
