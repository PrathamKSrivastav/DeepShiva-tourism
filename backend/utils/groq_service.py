import os
import asyncio
import logging
from typing import Tuple, List, Optional, Dict, Any
from groq import Groq
from rag.persona_rag import PersonaRAG
from rag.vector_store import VectorStoreManager
from datetime import date

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
        
        # Initialize RAG components
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
        """Initialize RAG components"""
        try:
            self.vector_store = VectorStoreManager()
            self.persona_rag = PersonaRAG(self.vector_store)
            logger.info("RAG components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {str(e)}")
            self.vector_store = None
            self.persona_rag = None
    
    async def health_check(self) -> bool:
        # return True
        """Check if Groq API is accessible"""
        if not self.client:
            return False
        
        try:
            response = await asyncio.wait_for(
                self._make_test_request(),
                timeout=5.0
            )
            return True
        except Exception as e:
            logger.warning(f"Groq API health check failed: {str(e)[:100]}")
            return False
    
    async def _make_test_request(self):
        """Make a simple test request to verify API connectivity"""
        # def sync_request():
        #     try:
        #         return self.client.chat.completions.create(
        #             model=self.model_name,
        #             messages=[{"role": "user", "content": "Hello"}],
        #             max_tokens=10,
        #             temperature=0.1,
        #         )
        #     except Exception as e:
        #         logger.error(f"Test request failed: {str(e)}")
        #         raise
        
        # loop = asyncio.get_event_loop()
        # return await loop.run_in_executor(None, sync_request)
    
    async def generate_persona_response(
        self,
        message: str,
        persona: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None,  # ← Changed: Optional with default
        tool_context: Optional[Dict[str, Any]] = None,  # ← Already optional, kept
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, List[str]]:


        """
        Generate response using Groq API with RAG enhancement and conversation history
        """
        if not self.client:
            raise Exception("Groq API client not initialized")
    
        # Ensure context is not None
        context = context or {}  # ← ADD THIS LINE

        # Enhance query with RAG context
        rag_context = await self._get_rag_context(message, persona, intent, context or {})

        # Build persona-specific system message with RAG
        system_message = self._build_system_message_with_rag(persona, intent, rag_context, tool_context)
        
        # Create the user message
        user_message = self._build_user_message(message, persona, intent, context)

        try:
            def sync_request():
                # Build messages array with conversation history
                messages = [{"role": "system", "content": system_message}]
                
                # ADD CONVERSATION HISTORY (last 4 messages)
                if conversation_history:
                    logger.info(f"💬 Including {len(conversation_history)} previous messages for context")
                    messages.extend(conversation_history)
                
                # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                # Prepare API arguments
                kwargs = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                }
                
                # Add tools if provided
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
            
            # CHECK FOR TOOL CALLS
            if message_response.tool_calls:
                logger.info(f"🛠️ LLM requested {len(message_response.tool_calls)} tool calls")
                return {
                    "type": "tool_call",
                    "tool_calls": message_response.tool_calls,
                    "message": message_response  # Return full message object for history
                }

            # STANDARD TEXT RESPONSE
            response_text = message_response.content

            # Enhance response with RAG citations if available
            if rag_context.get("has_rag_context", False):
                response_text = self._add_rag_citations(response_text, rag_context)

            # Generate contextual suggestions
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
    
    async def _get_rag_context(
        self, 
        message: str, 
        persona: str, 
        intent: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get RAG context for the query"""
        if not self.persona_rag:
            return {"has_rag_context": False}
        
        try:
            rag_context = await self.persona_rag.enhance_query_with_rag(
                query=message,
                persona=persona,
                intent=intent,
                context=context
            )
            
            logger.debug(f"RAG docs: {rag_context.get('retrieved_doc_count', 0)}")
            return rag_context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"has_rag_context": False, "error": str(e)}
    
    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: Dict[str, Any], tool_context: Dict[str, Any]) -> str:
        """Build persona-specific system message enhanced with RAG context"""
        
        base_context = """You are a PAN-INDIA AI knowledge assistant for travel, culture, spirituality, and local insights across India. You have access to two tools: `geocode_location` and `get_weather`.

        PRIORITY & CONFLICT RESOLUTION:
        1.  **Live Tools First**: For any dynamic query (e.g., "weather", "climate", "temperature", "current status"), you MUST use tools. Tool data is always more current and accurate than RAG context.
        2.  **RAG Context Second**: Use RAG for static, historical, or general knowledge (e.g., itineraries, culture, history).
        3.  **Conflict Rule**: Even if the RAG context contains general weather information (like "it is cold in winter"), you MUST STILL call the `get_weather` tool for a live forecast. Do not let RAG context prevent you from using tools for live data.

        TOOL USAGE RULES:
        - If the user asks for "current", "today's", or "now" weather, you MUST use `geocode_location` first, then `get_weather`.
        - Do NOT guess or hallucinate weather data.
        - If you need a location's coordinates, call `geocode_location`.
        - Do NOT output tool calls as text (like <function...>); use the proper tool call structure.

        CORE RULES:
        - Do NOT assume a state, city, or region unless explicitly mentioned.
        - If tool data is present, it is the single source of truth. Summarize it naturally.

        RESPONSE STYLE:
        - Default responses must be SHORT (3-6 bullet points or a short paragraph).

        Current date: {date.today().isoformat()}.
        IMPORTANT: Keep responses under 800 words, conversational, and informative.
        """

        
        # Add RAG context if available
        if rag_context.get("has_rag_context", False):
            base_context += f"""
        
        ADDITIONAL CONTEXT FROM RELIABLE SOURCES:
        I have access to verified information from {rag_context.get('source_count', 0)} reliable sources including official Indian government documents and verified tourism resources. Use this information to provide accurate, up-to-date responses.
        
        {rag_context.get('formatted_context', '')}
        """
        if tool_context and tool_context.get("location"):
            loc = tool_context["location"]
            base_context += f"""
            --- LIVE LOCATION DATA ---
            The following location was identified using Mappls Geocoding
            and should be treated as FACTUAL:
            - Place: {loc.get("place_name")}
            - City: {loc.get("city")}
            - State: {loc.get("state")}
            - Country: {loc.get("country")}
            - Latitude: {loc.get("latitude")}
            - Longitude: {loc.get("longitude")}

            Do NOT assume a different location.
            If advice depends on geography, base it on this data.
            """
        if tool_context and tool_context.get("weather"):
            w = tool_context["weather"]
            base_context += f"""
            --- LIVE WEATHER FORECAST (NEXT 7 DAYS) ---
            Source: Open-Meteo (real-time forecast)

            This weather data is REAL and CURRENT.
            You MUST use it instead of generic knowledge.
            If weather is present, do NOT say you lack real-time access.


            Dates: {w["dates"]}
            Max Temperatures (°C): {w["temp_max"]}
            Min Temperatures (°C): {w["temp_min"]}
            Precipitation (mm): {w["precipitation"]}
            Max Wind Speed (km/h): {w["wind_speed"]}

            Use this data to:
            - assess safety
            - suggest suitable dates
            - warn about bad conditions
            Do NOT guess weather.
            """
            logger.info(f"🧰 TOOL CONTEXT SENT TO LLM: {tool_context}")
        
        persona_instructions = {
            "local_guide": """
            You are a FRIENDLY LOCAL GUIDE - warm, conversational, and practical. 
            - Use casual, approachable language like "Hey there!", "Trust me", "Pro tip"
            - Share insider knowledge and practical tips
            - Focus on real travel logistics, costs, timing
            - Be encouraging and enthusiastic
            - When you have specific source information, mention it naturally: "According to the latest tourism board info..."
            """,
            
            "spiritual_teacher": """
            You are a SPIRITUAL TEACHER - serene, wise, and philosophical.
            - Use reverent, peaceful language with occasional Sanskrit terms
            - Include Sanskrit phrases with translations: "Om Namah Shivaya (I bow to Shiva)"
            - Share spiritual significance, legends, and mythological stories
            - Focus on inner transformation and sacred experiences
            - Weave source information seamlessly into spiritual narratives
            - Be gentle, reflective, and inspiring
            """,
            
            "trek_companion": """
            You are an ADVENTURE TREK COMPANION - enthusiastic, safety-focused, concise.
            - Use energetic language with adventure terms
            - Focus heavily on safety, gear, difficulty levels, weather
            - Be direct and practical with bullet-point style info when helpful
            - Include specific details: distances, altitudes, timings
            - Emphasize preparation and responsible trekking
            - Reference official sources for safety information: "Latest government advisories show..."
            """,
            
            "cultural_expert": """
            You are a CULTURAL EXPERT and mythological storyteller - scholarly yet engaging.
            - Share rich historical context, legends, and cultural stories
            - Reference historical texts and traditions ONLY when relevant.Do not assume a religious framework unless specified.
            - Explain cultural significance behind places and rituals
            - Use storytelling elements: "Legend says...", "In ancient times..."
            - Be informative but captivating, like a museum guide
            - Cite historical sources when available: "According to historical documents..."
            """
        }
        
        return base_context + persona_instructions.get(persona, persona_instructions["local_guide"])
    
    def _build_user_message(self, message: str, persona: str, intent: str, context: Dict[str, Any]) -> str:
        """Build the complete user message with context"""
        context_info = ""
        if intent in ["weather", "crowd", "festival", "emergency"]:
            context_info = f"\n\nUser's query seems related to {intent}. Use current information for India."
        
        user_message = f"""
        User Query: {message}
        
        Detected Intent: {intent}
        {context_info}
        
        Please respond as the {persona.replace('_', ' ').title()} persona. 
        Focus on India-specific information and use any available source context naturally.
        """
        
        return user_message
    
    def _add_rag_citations(self, response_text: str, rag_context: Dict[str, Any]) -> str:
        """Add RAG source citations to the response"""
        sources = rag_context.get("sources", [])
        if not sources:
            return response_text
        
        # Add a subtle indicator that verified sources were used
        if rag_context.get("source_count", 0) > 0:
            citation_note = f"\n\n📚 *Response enhanced with information from {rag_context['source_count']} verified sources*"
            return response_text + citation_note
        
        return response_text
    
    async def _generate_suggestions_with_rag(
        self, 
        message: str, 
        persona: str, 
        intent: str, 
        rag_context: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions enhanced with RAG context"""
        
        base_suggestions = {
            "weather": [
                "Best time to visit different regions of India?",
                "How does monsoon affect travel in India?"
            ],
            "itinerary": [
                "How many days are ideal for a multi-city trip in India?",
                "Best travel routes for first-time visitors"
            ],
            "spiritual": [
                "Major pilgrimage traditions across India",
                "Famous spiritual destinations by region"
            ],
            "general": [
                "Plan a trip across India",
                "Explore India's cultural diversity"
            ]

        }
        
        suggestions = base_suggestions.get(intent, base_suggestions["general"]).copy()
        
        # Enhance suggestions based on RAG content
        if rag_context.get("has_rag_context", False):
            # Add content-specific suggestions based on retrieved documents
            content_types = [
                source.get("content_type", "general") 
                for source in rag_context.get("sources", [])
            ]
            
            if "government" in content_types:
                suggestions.append("Latest government policies and regulations")
            
            if "cultural" in content_types:
                suggestions.append("Cultural festivals and traditions")
            
            if "trekking" in content_types and intent != "trekking":
                suggestions.append("Adventure trekking opportunities")
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    async def get_rag_status(self) -> Dict[str, Any]:
        """Get RAG system status"""
        if not self.persona_rag:
            return {"rag_enabled": False, "status": "not_initialized"}
        
        try:
            return await self.persona_rag.get_rag_health_status()
        except Exception as e:
            logger.error(f"Error getting RAG status: {str(e)}")
            return {"rag_enabled": False, "status": "error", "error": str(e)}
        
    async def _raw_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, List[str]]:
        """
        Raw generation method for LLMEngine fallback compatibility
        """
        if not self.client:
            raise Exception("Groq API client not initialized")
        
        def sync_request():
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_prompt})
            
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, sync_request),
            timeout=self.timeout
        )
        
        return response.choices[0].message.content, []
