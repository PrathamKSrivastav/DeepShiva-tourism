from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import json
from datetime import datetime

from utils.groq_service import GroqService
from utils.intents import classify_intent
from utils.persona_templates import generate_response as generate_local_response 
from utils.connection_checker import check_internet_connection
from utils.database import get_database, save_to_session
from middleware.auth import get_current_user
from bson import ObjectId

# Tools
from tools.geocoding_tool import geocode_location
from tools.weather_tool import get_weather

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
groq_service = GroqService()

# --- Models & Helper Functions (Keep your existing ones) ---
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

def get_tools_schema():
    return [
        {
            "type": "function",
            "function": {
                "name": "geocode_location",
                "description": "Get latitude and longitude for a city.",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather forecast.",
                "parameters": {"type": "object", "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"}}, "required": ["latitude", "longitude"]}
            }
        }
    ]

async def get_session_history_as_context(session_id: str, limit: int = 6):
    try:
        if not session_id: return []
        db = get_database()
        session = await db.chats.find_one({"_id": ObjectId(session_id)})
        if not session or "messages" not in session: return []
        messages = session["messages"][-(limit * 2):] if len(session["messages"]) > limit * 2 else session["messages"]
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    except Exception:
        return []

# --- Session Endpoints (Keep your existing ones) ---
# ... (create_new_chat_session, get_all_chat_sessions, delete_chat_session) ...


# ============= MAIN CHAT ENDPOINT (FIXED) =============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: Optional[dict] = Depends(get_current_user)):
    start_time = asyncio.get_event_loop().time()
    session_id = request.session_id
    intent = classify_intent(request.message)

    # 1. OFFLINE CHECK
    is_online = await check_internet_connection()
    if request.force_offline or not is_online:
        logger.warning("⚠️ Offline mode")
        local_result = generate_local_response(request.message, request.persona, intent=intent, context=request.context or {})
        
        if isinstance(local_result, tuple):
            response_text, suggestions = local_result[0], (local_result[1] if len(local_result) > 1 else [])
        else:
            response_text, suggestions = str(local_result), []

        if current_user:
             await save_to_session(user_id=current_user.get("_id") or current_user.get("id"), persona=request.persona, user_message=request.message, bot_response=response_text, intent=intent, session_id=session_id)
        return ChatResponse(response=response_text, persona=request.persona, intent=intent, suggestions=suggestions, response_source="local_model", response_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000), is_offline_mode=True, chat_saved=bool(current_user), session_id=session_id)

    # 2. ONLINE AGENT PREP
    conversation_history = await get_session_history_as_context(session_id) if session_id else []
    tool_context = {}

    # FORCE WEATHER (Simplified Pre-Fetch)
    if any(k in request.message.lower() for k in ["weather", "rain", "temperature"]):
        try:
             city_resp = await groq_service.client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Extract city from: {request.message}. Output ONLY city name."}])
             city = city_resp.choices[0].message.content.strip()
             if city and "none" not in city.lower():
                 geo = await geocode_location(city)
                 if geo:
                     tool_context["location"] = geo
                     weather = await get_weather(geo["latitude"], geo["longitude"])
                     if weather:
                         tool_context["weather"] = {
                             "dates": weather.get("daily", {}).get("time", [])[:3],
                             "max_temp": weather.get("daily", {}).get("temperature_2m_max", [])[:3],
                             "min_temp": weather.get("daily", {}).get("temperature_2m_min", [])[:3]
                         }
        except Exception: pass

    # 3. AGENT LOOP (STRICTER LIMITS)
    final_response_text = ""
    final_suggestions = []
    
    try:
        current_turn = 0
        max_turns = 3  # <--- REDUCED FROM 5 TO 3 TO PREVENT LOOPS
        
        while current_turn < max_turns:
            current_turn += 1
            
            # CRITICAL FIX: After turn 2, FORCE text generation by hiding tools
            active_tools = get_tools_schema() if current_turn < 3 else None
            
            result = await groq_service.generate_persona_response(
                request.message, 
                request.persona, 
                intent, 
                request.context, 
                tool_context, 
                conversation_history, 
                tools=active_tools  # <--- This forces text response on last turn
            )
            
            if result["type"] == "text":
                final_response_text = result["response"]
                final_suggestions = result["suggestions"]
                break
            
            elif result["type"] == "tool_call":
                conversation_history.append(result["message"])
                for tool in result["tool_calls"]:
                    func = tool.function.name
                    args = json.loads(tool.function.arguments)
                    tool_res = None
                    save_content = None
                    
                    if func == "geocode_location":
                        tool_res = await geocode_location(args.get("query"))
                        if tool_res: 
                            tool_context["location"] = tool_res
                            save_content = tool_res
                    elif func == "get_weather":
                        tool_res = await get_weather(args.get("latitude"), args.get("longitude"))
                        if tool_res:
                            simple = {
                                "dates": tool_res.get("daily", {}).get("time", [])[:3],
                                "max_temp": tool_res.get("daily", {}).get("temperature_2m_max", [])[:3],
                                "min_temp": tool_res.get("daily", {}).get("temperature_2m_min", [])[:3]
                            }
                            tool_context["weather"] = simple
                            save_content = simple
                    
                    # Store result as string to save tokens
                    conversation_history.append({"role": "tool", "tool_call_id": tool.id, "name": func, "content": json.dumps(save_content) if save_content else "Failed"})

    except Exception as e:
        logger.error(f"Groq failed: {e}. Fallback to local.")
        local_result = generate_local_response(request.message, request.persona, intent=intent, context=request.context or {})
        if isinstance(local_result, tuple):
            final_response_text, final_suggestions = local_result[0], (local_result[1] if len(local_result) > 1 else [])
        else:
            final_response_text, final_suggestions = str(local_result), []
    
    if not final_response_text: 
        final_response_text = "I'm having trouble thinking right now."

    if current_user:
         await save_to_session(user_id=current_user.get("_id") or current_user.get("id"), persona=request.persona, user_message=request.message, bot_response=final_response_text, intent=intent, session_id=session_id)

    return ChatResponse(response=final_response_text, persona=request.persona, intent=intent, suggestions=final_suggestions, response_source="groq_agent", response_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000), is_offline_mode=False, chat_saved=bool(current_user), session_id=session_id)