from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime
from utils.groq_service import GroqService
from utils.intents import classify_intent, extract_trek_info, is_trek_query
from utils.persona_templates import generate_response as generate_local_response
from utils.connection_checker import check_internet_connection
from utils.database import get_database
from middleware.auth import get_current_user  # Optional auth - allows guests
from bson import ObjectId
import json

from tools.tool_router import decide_tools
from tools.geocoding_tool import geocode_location
from tools.weather_tool import get_weather
from tools.holiday_tool import get_holidays
from tools.trek_tool import search_treks
from tools.hotel_tool import get_hotel_rates

from localmodel.llm_engine import LLMEngine


from utils.pdf_generator import ChatPDFGenerator
import os
from fastapi.responses import FileResponse

# ADD THESE IMPORTS (after line ~20)
from utils.summary_generator import get_summary_generator
from utils.summary_pdf_generator import SummaryPDFGenerator


# Setup logging
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)

router = APIRouter()


# Add this near other helper functions or imports
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
        },
        {
            "type": "function",
            "function": {
                "name": "get_holidays",  # 🟢 FIX 1: Name must match the import
                "description": "Get public holidays for India. To see the whole year, fetch by QUARTERS (Q1, Q2, Q3, Q4) to avoid data truncation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer", 
                            "description": "Year (e.g. 2025). Required."
                        },
                        "quarter": {
                            "type": "integer", 
                            "description": "Quarter of the year (1=Jan-Mar, 2=Apr-Jun, 3=Jul-Sep, 4=Oct-Dec). Recommended for better visibility."
                        },
                        "month": {
                            "type": "integer", 
                            "description": "Specific month (1-12). Use only for narrow searches."
                        }
                    },
                    "required": ["year"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_treks",
                "description": "Search for trekking trails and hiking routes in India. Returns detailed info (difficulty, duration, altitude, best time). Use this for queries like 'treks near Mumbai', 'hikes in Uttarakhand', or specific trek names.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "State or region name. IF the query mentions a city (e.g., 'near Mumbai', 'near Pune'), map it to the trekking region (e.g., 'Maharashtra'). Examples: 'near Agra' -> 'Uttarakhand', 'near Bangalore' -> 'Karnataka'."
                        },
                        "trek_name": {
                            "type": "string",
                            "description": "Specific trek name (e.g., 'Kalsubai', 'Valley of Flowers'). Leave empty if searching by region."
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_hotel_rates",
                "description": "Get current hotel prices and availability for a specific city. Use this when users ask for 'hotel prices', 'places to stay', or 'accommodation costs'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name (e.g., 'Agra', 'Mumbai', 'Manali')."
                        },
                        "checkin_date": {
                            "type": "string",
                            "description": "Check-in date in YYYY-MM-DD format. If not specified, defaults to tomorrow."
                        }
                    },
                    "required": ["city"]
                }
            }
        },
    ]

async def execute_tool(func_name: str, args: Dict) -> Optional[Dict]:
    """
    Execute a tool by name and return its result
    Used for both normal and recovered (malformed) tool calls
    """
    try:
        if func_name == "geocode_location":
            logger.info(f"📍 Calling Geocode: {args.get('query')}")
            return await geocode_location(args.get('query'))
        
        elif func_name == "get_weather":
            logger.info(f"🌦️ Calling Weather: {args}")
            return await get_weather(
                latitude=args.get('latitude'),
                longitude=args.get('longitude')
            )
        
        elif func_name == "search_treks":
            logger.info(f"🏔️ Calling Trek Search: {args}")
            return await search_treks(
                region=args.get('region'),
                trek_name=args.get('trek_name')
            )
        
        else:
            logger.error(f"❌ Unknown tool: {func_name}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Tool execution failed for {func_name}: {str(e)}")
        return None

def build_offline_system_prompt(persona: str, rag_context: dict) -> str:
    """
    Simplified system prompt for offline GGUF model
    - No tool references
    - Strict anti-hallucination rules
    - Simpler instructions
    """
    
    # Base instructions for offline mode
    base_prompt = """You are a helpful tourism assistant for India.

CRITICAL RULES:
1. You do NOT have access to real-time data (weather, current events, prices)
2. If asked about current/live information, clearly state: "I don't have access to real-time data. Please check online sources for current information."
3. Do NOT invent specific numbers, dates, temperatures, or prices
4. Do NOT generate code or tool usage examples
5. Only use information from the provided CONTEXT below
6. Keep responses SHORT (2-4 sentences maximum)
7. Be honest when you don't know something

"""
    
    # Add RAG context if available
    if rag_context.get("has_rag_context"):
        base_prompt += f"""
    VERIFIED CONTEXT (use ONLY this information):
    {rag_context.get('formatted_context', '')[:1500]}

    """
    if rag_context.get("trek_hints"):
        hints = rag_context["trek_hints"]
        base_prompt += f"""
        USER QUERY CONTEXT:
        The user is asking about treks/hiking.
        """
        if hints.get("trek_name"):
            base_prompt += f"- Specific Trek: {hints['trek_name']}\n"
        if hints.get("region"):
            base_prompt += f"- Region of Interest: {hints['region']}\n"
        base_prompt += "\n"
    
    # Add persona-specific tone (simplified)
    persona_tones = {
        "local_guide": "Respond in a friendly, casual tone. Share practical travel tips.",
        "spiritual_teacher": "Respond in a calm, reverent tone. Focus on spiritual significance.",
        "trek_companion": "Respond in an energetic, safety-focused tone. Emphasize preparation.",
        "cultural_expert": "Respond in an informative, storytelling tone. Share cultural insights."
    }
    
    tone = persona_tones.get(persona, persona_tones["local_guide"])
    base_prompt += f"\nTONE: {tone}\n"
    
    return base_prompt


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
llm_engine = LLMEngine()

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
        logger.info("=" * 50)
        logger.info("📥 GET /chat/sessions called")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))

        
        # Build query
        query = {"user_id": user_id}
        if persona:
            query["persona"] = persona
        
        logger.info(f"📊 Query: {query}")
        
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
        logger.error(f"❌ Error fetching sessions: {str(e)}")
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

# ============= PDF Export =============

@router.get("/chat/sessions/{session_id}/export/pdf")
async def export_session_as_pdf(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Export chat session as PDF
    Returns downloadable PDF file
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"📥 Exporting session to PDF: {session_id}")
        
        db = get_database()
        # ✅ FIXED: Use string type to match how sessions are stored
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        # Fetch session
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id  # Now matches the stored string type
        })
        
        if not session:
            logger.warning(f"⚠️ Session not found: {session_id}")
            logger.warning(f"⚠️ Searched for user_id: {user_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Session found with {len(session.get('messages', []))} messages")
        
        # Create temp directory if it doesn't exist
        temp_dir = "temp_pdfs"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate filename
        safe_title = session.get("title", "chat").replace(" ", "_")[:30]
        filename = f"{safe_title}_{session_id[:8]}.pdf"
        filepath = os.path.join(temp_dir, filename)
        
        logger.info(f"📄 Generating PDF: {filepath}")
        
        # Generate PDF
        pdf_generated = ChatPDFGenerator.create_pdf(
            session_title=session.get("title", "Chat Session"),
            persona=session.get("persona", "local_guide"),
            messages=session.get("messages", []),
            output_path=filepath
        )
        
        if not pdf_generated:
            logger.error("❌ PDF generation returned False")
            raise HTTPException(status_code=500, detail="PDF generation failed")
        
        logger.info(f"✅ PDF ready for download: {filepath}")
        
        # Return file for download
        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Export error: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Chat Endpoint (Updated) =============

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Agentic Chat Endpoint with Offline Fallback:
    1. Try Groq with tools (Optimized Agent Loop)
    2. If Groq fails → fallback to local LLM (no tools)
    """
    logger.info("==" * 35)
    logger.info("💬 CHAT ENDPOINT (AGENT MODE WITH FALLBACK) CALLED")
    start_time = asyncio.get_event_loop().time()
    session_id = request.session_id
    
    # Initialize
    conversation_history = []
    tool_context = {}
    intent = classify_intent(request.message)
    
    # Initialize context for the session
    context = request.context or {}

    # Update context for trek queries
    if intent == "trekking" or is_trek_query(request.message):
        trek_name, region = extract_trek_info(request.message)
        logger.info(f"🏔️ Trek Query Detected!")
        logger.info(f"   - Extracted Trek Name: {trek_name or 'Not specified'}")
        logger.info(f"   - Extracted Region: {region or 'Not specified'}")
        
        if region:
            context['extracted_region'] = region
        if trek_name:
            context['extracted_trek_name'] = trek_name

    # Fetch conversation history
    if session_id and current_user:
        try:
            conversation_history = await _get_conversation_history(
                session_id, current_user, limit=4
            )
            logger.info(f"📜 Loaded {len(conversation_history)} messages for context")
        except Exception as e:
            logger.warning(f"⚠️ Could not load history: {str(e)}")
    
    # ⭐ OPTIMIZATION: Fetch RAG context ONCE and cache it
    rag_context = {"has_rag_context": False}
    if request.use_rag and groq_service.persona_rag:
        try:
            logger.info("🔍 Fetching RAG context (ONE-TIME RETRIEVAL)")
            rag_context = await groq_service._get_rag_context(
                request.message, request.persona, intent, context
            )
            logger.info(f"✅ RAG context retrieved: {len(rag_context.get('formatted_context', ''))} chars")
        except Exception as e:
            logger.warning(f"⚠️ RAG failed: {str(e)}")

    
    # ==========================================
    # TRY GROQ WITH AGENTIC TOOLS FIRST
    # ==========================================
    use_local_fallback = request.force_offline
    final_response_text = ""
    final_suggestions = []
    response_source = "groq"
    
    # 🟢 OPTIMIZATION: Track called tools to prevent loops
    called_tools = set()

    if not use_local_fallback:
        try:
            # Check if Groq is available
            if not await groq_service.health_check():
                logger.warning("⚠️ Groq health check failed, switching to local")
                use_local_fallback = True
            else:
                # ==========================================
                # OPTIMIZED AGENT LOOP
                # ==========================================
                max_turns = 5
                current_turn = 0
                tools_schema = get_tools_schema()
                
                while current_turn < max_turns:
                    current_turn += 1
                    logger.info(f"🔄 Agent Turn {current_turn}/{max_turns}")
                    
                    # Call Groq
                    result = await groq_service.generate_persona_response(
                        message=request.message,
                        persona=request.persona,
                        intent=intent,
                        context=context,
                        tool_context=tool_context,
                        conversation_history=conversation_history,
                        tools=tools_schema,
                        rag_context=rag_context,
                    )

                    # CASE A: LLM wants to call tools
                    if result["type"] == "tool_call":
                        tool_calls = result["tool_calls"]
                        llm_message = result["message"]
                        
                        # 🟢 CRITICAL FIX: Filter out duplicate calls to prevent loops
                        unique_tool_calls = []
                        for tc in tool_calls:
                            # Create a unique signature: func_name + arguments
                            call_signature = f"{tc.function.name}:{tc.function.arguments}"
                            if call_signature in called_tools:
                                logger.warning(f"⚠️ Skipping duplicate tool call: {call_signature}")
                                continue
                            
                            called_tools.add(call_signature)
                            unique_tool_calls.append(tc)
                        
                        # If no new tools to call, break the loop or force an answer
                        if not unique_tool_calls:
                            logger.info("🛑 No new tool calls needed. Forcing completion.")
                            # Add a system nudge to history to force an answer next turn
                            conversation_history.append({
                                "role": "tool", # Pretend to be a tool system message
                                "tool_call_id": tool_calls[0].id, # Reuse ID to satisfy API strictness
                                "name": "system_guard",
                                "content": "Error: You have already called these tools. Do not call them again. Summarize the data you have."
                            })
                            continue

                        # Add LLM's message to history (only if we have valid calls)
                        conversation_history.append({
                            "role": "assistant",
                            "content": llm_message.content or "",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                } for tc in unique_tool_calls
                            ]
                        })
                        
                        # Execute VALID, UNIQUE tools
                        for tool_call in unique_tool_calls:
                            func_name = tool_call.function.name
                            try:
                                args = json.loads(tool_call.function.arguments)
                            except json.JSONDecodeError:
                                logger.error(f"❌ Failed to decode args for {func_name}")
                                continue
                            
                            tool_result = None
                            
                            # --- Tool Execution Logic ---
                            if func_name == "geocode_location":
                                logger.info(f"📍 Calling Geocode: {args.get('query')}")
                                tool_result = await geocode_location(args.get('query'))
                                if tool_result:
                                    tool_context["location"] = tool_result
                            
                            elif func_name == "get_weather":
                                logger.info(f"🌦️ Calling Weather: {args}")
                                tool_result = await get_weather(
                                    latitude=args.get('latitude'),
                                    longitude=args.get('longitude')
                                )
                                if tool_result:
                                    tool_context["weather"] = tool_result
                            
                            elif func_name == "get_hotel_rates":
                                logger.info(f"🏨 Calling Hotels: {args}")
                                # Import it at the top of chat.py first: from tools.hotel_tool import get_hotel_rates
                                tool_result = await get_hotel_rates(
                                    city=args.get('city'),
                                    checkin_date=args.get('checkin_date')
                                )
                                if tool_result and "hotels" in tool_result:
                                    tool_context["hotels"] = tool_result

                            elif func_name == "get_holidays":
                                year = args.get('year')
                                month = args.get('month')
                                quarter = args.get('quarter')
                                logger.info(f"🎉 Calling Holidays for: {year} (Q{quarter}/M{month})")
                                
                                holidays_data = await get_holidays(year=year, month=month, quarter=quarter)
                                
                                # 🟢 Date Filtering Logic
                                from datetime import datetime
                                today_str = datetime.now().strftime("%Y-%m-%d")
                                current_year = datetime.now().year
                                
                                if year == current_year:
                                    holidays_data = [
                                        h for h in holidays_data 
                                        if h.get('date', {}).get('iso', '9999-99-99') >= today_str
                                    ]
                                
                                if not holidays_data:
                                    if year == current_year:
                                        tool_result = f"No upcoming holidays left in {year}. Please search for {year + 1} (Q1)."
                                    else:
                                        tool_result = "No holidays found."
                                else:
                                    simplified_list = []
                                    for h in holidays_data:
                                        d = h.get('date', {}).get('iso', 'Unknown')
                                        n = h.get('name', 'Unknown')
                                        t_raw = h.get('type')
                                        t = t_raw[0] if isinstance(t_raw, list) and t_raw else 'Public'
                                        simplified_list.append(f"{d}: {n} ({t})")
                                    tool_result = "\n".join(simplified_list[:50])

                            elif func_name == "search_treks":
                                logger.info(f"🏔️ Calling Trek Search: {args}")
                                tool_result = await search_treks(
                                    region=args.get('region'),
                                    trek_name=args.get('trek_name')
                                )
                                if tool_result:
                                    tool_context["treks"] = tool_result
                                    logger.info(f"✅ Found {tool_result.get('trek_count', 0)} treks")
                            
                            # --- 🟢 OPTIMIZED HISTORY STORAGE ---
                            # We summarize what goes into history to save tokens. 
                            # Full data is in tool_context for the system prompt.
                            
                            history_content = ""
                            if not tool_result:
                                history_content = "Error: Tool failed or returned no data."
                            elif func_name == "search_treks":
                                count = tool_result.get('trek_count', 0)
                                names = [t.get('name') for t in tool_result.get('treks', [])[:5]]
                                history_content = json.dumps({
                                    "status": "success", 
                                    "found": count, 
                                    "top_5": names, 
                                    "note": "Full details available in system context."
                                })
                            elif func_name == "get_holidays":
                                content_str = str(tool_result)
                                history_content = content_str[:250] + "...(truncated)" if len(content_str) > 250 else content_str
                            else:
                                history_content = json.dumps(tool_result)

                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": history_content
                            })
                        
                        # Continue loop to get LLM's final response
                        continue
                    
                    # CASE B: LLM returned final text response
                    elif result["type"] == "text":
                        final_response_text = result["response"]
                        final_suggestions = result["suggestions"]
                        response_source = "groq"
                        break
                
                # If loop finished without text, provide fallback
                if not final_response_text:
                    final_response_text = "I'm having trouble processing your request with tools. Let me try a different approach."
                    use_local_fallback = True

        except Exception as e:
            logger.error(f"❌ Groq agent failed: {str(e)}")
            use_local_fallback = True
    
    # ==========================================
    # FALLBACK TO LOCAL LLM (NO TOOLS)
    # ==========================================
    if use_local_fallback:
        logger.warning("⚠️ Using local LLM fallback (no tools available)")
        try:
            system_prompt = build_offline_system_prompt(
                persona=request.persona,
                rag_context=rag_context
            )
            
            final_response_text, response_source = await llm_engine.generate(
                system_prompt=system_prompt,
                user_prompt=request.message,
                conversation_history=[],  # Local model doesn't handle history well
                force_offline=True
            )
            
            final_suggestions = []
            response_source = "local"
            
        except Exception as e:
            logger.error(f"❌ Local LLM also failed: {str(e)}")
            final_response_text = (
                "I apologize, but I'm currently experiencing technical difficulties "
                "with both my online and offline systems. Please try again in a moment."
            )
            final_suggestions = []
            response_source = "error"
    
    # ==========================================
    # FINALIZE RESPONSE
    # ==========================================
    end_time = asyncio.get_event_loop().time()
    response_time = int((end_time - start_time) * 1000)
    
    # Save to session if authenticated
    chat_saved = False
    if current_user:
        try:
            session_id, chat_saved = await save_to_session(
                user_id=current_user.get("_id") or current_user.get("id"),
                persona=request.persona,
                user_message=request.message,
                bot_response=final_response_text,
                intent=intent,
                session_id=session_id
            )
            if chat_saved:
                logger.info(f"✅ Saved to session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Save failed: {str(e)}")
    
    return ChatResponse(
        response=final_response_text,
        persona=request.persona,
        intent=intent,
        suggestions=final_suggestions,
        response_source=response_source,
        response_time_ms=response_time,
        is_offline_mode=(response_source == "local"),
        rag_info={"rag_used": rag_context.get("has_rag_context", False)},
        chat_saved=chat_saved,
        session_id=session_id
    )

async def _get_conversation_history(
    session_id: str,
    current_user: dict,
    limit: int = 4
) -> List[Dict[str, str]]:
    """Fetch conversation history from session"""
    try:
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session or "messages" not in session:
            return []
        
        messages = session["messages"][-(limit * 2):] if len(session["messages"]) > limit * 2 else session["messages"]
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"❌ Error fetching history: {str(e)}")
        return []


async def save_to_session(
    user_id: str,
    persona: str,
    user_message: str,
    bot_response: str,
    intent: str,
    session_id: Optional[str] = None
) -> tuple[str, bool]:
    """Save message to chat session"""
    try:
        db = get_database()
        user_id = str(user_id)
        
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
        
        if session_id:
            result = await db.chats.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {
                    "$push": {"messages": {"$each": [user_msg, bot_msg]}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                return session_id, True
        
        # Create new session
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
        return str(result.inserted_id), True
        
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
        "trekking": [
            "Best treks in Himachal Pradesh", 
            "Tell me about Valley of Flowers", 
            "Beginner treks in Uttarakhand",
            "When to trek in Ladakh"
        ],
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


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Delete a chat session (notebook) and all its messages
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")

        logger.info(f"🗑️ Deleting chat session: {session_id}")

        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))

        # Verify ownership and delete
        result = await db.chats.delete_one(
            {"_id": ObjectId(session_id), "user_id": user_id}
        )

        if result.deleted_count == 0:
            logger.warning(f"⚠️ Session not found or unauthorized: {session_id}")
            raise HTTPException(
                status_code=404,
                detail="Session not found or you don't have permission to delete it",
            )

        logger.info(f"✅ Session deleted successfully: {session_id}")

        # Optional: Clean up related files (PDFs, summaries, etc.)
        try:
            temp_dir = "temp_pdfs"
            if os.path.exists(temp_dir):
                # Remove any PDFs associated with this session
                for filename in os.listdir(temp_dir):
                    if session_id[:8] in filename:
                        file_path = os.path.join(temp_dir, filename)
                        os.remove(file_path)
                        logger.info(f"🧹 Cleaned up temp file: {filename}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning (non-critical): {str(e)}")

        return {
            "success": True,
            "message": "Chat session deleted successfully",
            "session_id": session_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting session: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete session: {str(e)}"
        )


@router.delete("/chat/history/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Legacy endpoint - redirects to session delete"""
    return await delete_chat_session(chat_id, current_user)


# ============= SUMMARY GENERATION ENDPOINTS (ADD BEFORE STATUS ENDPOINTS) =============

@router.post("/chat/sessions/{session_id}/summary")
async def generate_session_summary(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI-powered summary of chat session
    Uses Groq API to analyze conversation and create insights
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"🤖 Generating summary for session: {session_id}")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        # Fetch session
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session:
            logger.warning(f"⚠️ Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = session.get("messages", [])
        if len(messages) < 2:
            raise HTTPException(
                status_code=400,
                detail="Not enough messages to generate summary (minimum 2 required)"
            )
        
        logger.info(f"📊 Analyzing {len(messages)} messages")
        
        # Generate summary using Groq AI
        summary_generator = get_summary_generator()
        summary_data = await summary_generator.generate_summary(
            messages=messages,
            session_title=session.get("title", "Untitled Conversation"),
            persona=session.get("persona", "local_guide")
        )
        
        # Save summary to database
        await db.chats.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "summary": summary_data,
                    "summary_generated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"✅ Summary generated and saved for session: {session_id}")
        
        return {
            "success": True,
            "summary": summary_data,
            "message": "Summary generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Summary generation error: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/chat/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get existing summary for a session (without regenerating)
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        # Fetch session
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        summary = session.get("summary")
        if not summary:
            raise HTTPException(status_code=404, detail="No summary found. Generate one first.")
        
        return {
            "success": True,
            "summary": summary,
            "generated_at": session.get("summary_generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{session_id}/summary/pdf")
async def download_summary_pdf(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Download summary as formatted PDF
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"📥 Downloading summary PDF for session: {session_id}")
        
        db = get_database()
        user_id = str(current_user.get("_id") or current_user.get("id"))
        
        # Fetch session
        session = await db.chats.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        summary = session.get("summary")
        if not summary:
            raise HTTPException(
                status_code=404,
                detail="No summary found. Generate summary first."
            )
        
        # Create temp directory
        temp_dir = "temp_pdfs"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate filename
        safe_title = session.get("title", "summary").replace(" ", "_")[:30]
        filename = f"Summary_{safe_title}_{session_id[:8]}.pdf"
        filepath = os.path.join(temp_dir, filename)
        
        logger.info(f"📄 Generating summary PDF: {filepath}")
        
        # Generate PDF
        pdf_generated = SummaryPDFGenerator.create_summary_pdf(
            summary_data=summary,
            output_path=filepath
        )
        
        if not pdf_generated:
            raise HTTPException(status_code=500, detail="PDF generation failed")
        
        logger.info(f"✅ Summary PDF ready: {filepath}")
        
        # Return file
        return FileResponse(
            filepath,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Summary PDF download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Status Endpoints =============

@router.get("/connection-status")
async def connection_status():
    """Check connectivity and service status"""
    internet_status = await check_internet_connection()
    groq_status = await groq_service.health_check()
    
    rag_status = {"rag_enabled": False}
    if hasattr(groq_service, 'get_rag_status'):
        try:
            rag_status = await groq_service.get_rag_status()
        except Exception as e:
            logger.error(f"Error getting RAG status: {str(e)}")
    
    # Check if local model is loaded
    local_model_status = llm_engine.is_model_loaded()
    
    return {
        "internet_connected": internet_status,
        "groq_api_available": groq_status,
        "local_model_loaded": local_model_status,  # ← NEW
        "rag_enabled": rag_status.get("rag_enabled", False),
        "rag_total_documents": rag_status.get("total_documents", 0)
    }
