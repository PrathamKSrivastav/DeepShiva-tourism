import os
import asyncio
import logging
from typing import Tuple, List, Optional, Dict, Any
from groq import Groq
from rag.persona_rag import PersonaRAG
from rag.vector_store import VectorStoreManager
from datetime import datetime

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
        self.timeout = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
        
        self.vector_store = None
        self.persona_rag = None
        self._init_rag_components()
        
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print("DEBUG: Groq client with RAG initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
                self.client = None
        else:
            logger.warning("GROQ_API_KEY not found - only offline mode available")

    def _init_rag_components(self):
        try:
            self.vector_store = VectorStoreManager()
            self.persona_rag = PersonaRAG(self.vector_store)
            logger.info("RAG components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {str(e)}")
            self.vector_store = None
            self.persona_rag = None

    async def generate_persona_response(
        self, 
        message: str, 
        persona: str, 
        intent: str, 
        context: Optional[Dict[str, Any]] = None,
        tool_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        if not self.client:
            raise Exception("Groq API client not initialized")
            
        context = context or {}
        rag_context = await self._get_rag_context(message, persona, intent, context)
        system_message = self._build_system_message_with_rag(persona, intent, rag_context, tool_context)
        user_message = self._build_user_message(message, persona, intent, context)
        
        try:
            def sync_request():
                messages = [{"role": "system", "content": system_message}]
                if conversation_history:
                    logger.info(f"💬 Including {len(conversation_history)} previous messages for context")
                    messages.extend(conversation_history)
                messages.append({"role": "user", "content": user_message})
                
                kwargs = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                return self.client.chat.completions.create(**kwargs)

            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, sync_request),
                timeout=self.timeout
            )
            
            message_response = response.choices[0].message

            if message_response.tool_calls:
                logger.info(f"🛠️ LLM requested {len(message_response.tool_calls)} tool calls")
                return {
                    "type": "tool_call",
                    "tool_calls": message_response.tool_calls,
                    "message": message_response 
                }

            response_text = message_response.content
            if rag_context.get("has_rag_context", False):
                response_text = self._add_rag_citations(response_text, rag_context)

            suggestions = await self._generate_suggestions_with_rag(message, persona, intent, rag_context)
            
            return {
                "type": "text",
                "response": response_text,
                "suggestions": suggestions
            }

        except asyncio.TimeoutError:
            raise Exception("Groq API request timed out")
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise Exception(f"Groq API failed: {str(e)[:100]}")

    async def _get_rag_context(self, message: str, persona: str, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.persona_rag:
            return {"has_rag_context": False}
        try:
            rag_context = await self.persona_rag.enhance_query_with_rag(
                query=message, persona=persona, intent=intent, context=context
            )
            return rag_context
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"has_rag_context": False, "error": str(e)}

    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: Dict[str, Any], tool_context: Dict[str, Any]) -> str:
        # NOTICE: The placeholder below is just {date}, not {date.today()}
        base_context = """You are a PAN-INDIA AI knowledge assistant for travel, culture, spirituality, and local insights across India.
        PRIORITY & CONFLICT RESOLUTION:
        1. **Live Tools First**: For dynamic queries (weather, status), tool data is PRIMARY.
        2. **RAG Context Second**: Use RAG for history/culture.
        3. **Conflict Rule**: Tool data overrides RAG context for live conditions.

        TOOL USAGE RULES:
        - Use `geocode_location` then `get_weather` for current conditions.
        - Do NOT hallucinate weather.

        Current date: {date}.
        IMPORTANT: Keep responses under 800 words."""

        if tool_context:
            base_context += "\n\n=== LIVE TOOL DATA (Use this as PRIMARY source) ===\n"
            if "location" in tool_context:
                loc = tool_context["location"]
                base_context += f"Location: {loc.get('place_name', 'Unknown')}\n"
            if "weather" in tool_context:
                w = tool_context["weather"]
                # SAFE ACCESS
                max_t = w.get("max_temp") or w.get("temp_max") or []
                min_t = w.get("min_temp") or w.get("temp_min") or []
                dates = w.get("dates") or []
                base_context += f"Weather Forecast (Next 3 days):\nDates: {dates}\nMax Temps: {max_t}\nMin Temps: {min_t}\n"

        if rag_context.get("has_rag_context", False):
            base_context += "\n\n=== RETRIEVED KNOWLEDGE ===\n"
            base_context += rag_context.get("context_string", "")
            
        # Passing a simple string date here
        return base_context.format(date=datetime.now().strftime("%Y-%m-%d"))

    def _build_user_message(self, message: str, persona: str, intent: str, context: Dict[str, Any]) -> str:
        return f"User Query: {message}\nContext: {context}"

    def _add_rag_citations(self, response_text: str, rag_context: Dict[str, Any]) -> str:
        if "sources" in rag_context and rag_context["sources"]:
            response_text += "\n\nSources:\n"
            seen = set()
            for source in rag_context["sources"]:
                if source not in seen:
                    response_text += f"- {source}\n"
                    seen.add(source)
        return response_text

    async def _generate_suggestions_with_rag(self, message: str, persona: str, intent: str, rag_context: Dict[str, Any]) -> List[str]:
        return ["Tell me more", "Nearby places", "Best time to visit"]
