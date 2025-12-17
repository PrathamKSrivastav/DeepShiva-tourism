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
        self.model_name = os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct-0905")
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "800")) #1000 -> 800
        self.timeout = int(os.getenv("API_TIMEOUT_SECONDS", "60")) #10-> 30 -> 60
        logger.info(f"🤖 Groq Model: {self.model_name}")
        
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
        context: Optional[Dict[str, Any]] = None,
        tool_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        rag_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate response with retry logic for malformed tool calls"""
        
        if not self.client:
            raise Exception("Groq API client not initialized")
        
        context = context or {}
        rag_context = rag_context or {"has_rag_context": False}
        
        system_message = self._build_system_message_with_rag(
            persona, intent, rag_context, tool_context
        )
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
            
            # CHECK FOR TOOL CALLS
            if message_response.tool_calls:
                logger.info(f"🛠️ LLM requested {len(message_response.tool_calls)} tool calls")
                return {
                    "type": "tool_call",
                    "tool_calls": message_response.tool_calls,
                    "message": message_response,
                }
            
            # STANDARD TEXT RESPONSE
            response_text = message_response.content
            
            if rag_context.get("has_rag_context", False):
                response_text = self._add_rag_citations(response_text, rag_context)
            
            suggestions = await self._generate_suggestions_with_rag(
                message, persona, intent, rag_context
            )
            
            return {
                "type": "text",
                "response": response_text,
                "suggestions": suggestions,
            }
        
        except asyncio.TimeoutError:
            raise Exception("Groq API request timed out")
        
        except Exception as e:
            error_str = str(e)
            
            # 🔥 DETECT MALFORMED FUNCTION CALL ERROR
            if "tool_use_failed" in error_str or "Failed to call a function" in error_str:
                logger.warning("⚠️ Detected malformed function call, attempting to parse...")
                
                # Extract the malformed function call
                parsed_call = self._parse_malformed_function_call(error_str)
                
                if parsed_call:
                    logger.info(f"✅ Successfully parsed malformed call: {parsed_call['function_name']}")
                    return {
                        "type": "tool_call_malformed",
                        "parsed_call": parsed_call,
                        "original_error": error_str
                    }
            
            logger.error(f"Groq API error: {error_str}")
            raise Exception(f"Groq API failed: {error_str[:100]}")


    def _parse_malformed_function_call(self, error_message: str) -> Optional[Dict[str, Any]]:
        """
        Parse malformed function calls from Groq errors
        Handles:
        1. Nested calls (outer function wrapping inner)
        2. Open-ended XML tags (<function=name>{args})
        3. Strict XML tags (<function=name>{args}</function>)
        """
        import re
        import json
        
        try:
            # Extract the failed_generation content
            match = re.search(r"'failed_generation':\s*'([^']+)'", error_message)
            if not match:
                match = re.search(r'"failed_generation":\s*"([^"]+)"', error_message)
            
            if not match:
                # logger.warning("❌ Could not find failed_generation in error")
                return None
            
            failed_gen = match.group(1)
            logger.info(f"📝 Parsing failed generation: {failed_gen}")
            
            # PRIORITY 1: Check for NESTED function calls - extract INNER function
            # Example: <tool_code>...<function=inner>{...}</function>...</tool_code>
            nested_pattern = r'<function=(\w+)\s*\{[^}]*<function=(\w+)\s*(\{[^}]+\})</function>'
            nested_match = re.search(nested_pattern, failed_gen)
            
            if nested_match:
                outer_func = nested_match.group(1)
                inner_func = nested_match.group(2)
                inner_args = nested_match.group(3)
                
                logger.warning(f"🔄 NESTED CALL DETECTED: {outer_func} contains {inner_func}")
                logger.info(f"✅ Extracting INNER function to call first: {inner_func}")
                
                try:
                    arguments = json.loads(inner_args)
                    return {
                        "function_name": inner_func,
                        "arguments": arguments,
                        "id": f"call_recovered_{inner_func}",
                        "is_nested": True,
                        "outer_function": outer_func
                    }
                except json.JSONDecodeError as je:
                    logger.error(f"❌ Failed to parse nested JSON: {je}")
                    # Don't return None yet, try other patterns
            
            # PRIORITY 2: Handle Open-Ended XML style (Missing closing tag)
            # Matches: <function=name>{args}
            # This is common with Llama-3-8b-instant
            xml_open_pattern = r'<function=([a-zA-Z0-9_]+)>.*?({.*})'
            xml_match = re.search(xml_open_pattern, failed_gen)
            
            if xml_match:
                function_name = xml_match.group(1)
                json_args = xml_match.group(2)
                logger.info(f"✅ Extracted XML-style function (open): {function_name}")
                try:
                    arguments = json.loads(json_args)
                    return {
                        "function_name": function_name,
                        "arguments": arguments,
                        "id": f"call_recovered_{function_name}",
                    }
                except json.JSONDecodeError:
                     logger.warning("Could not parse JSON from open XML pattern, trying strict pattern...")

            # PRIORITY 3: Simple malformed calls (Strict XML with optional closing tag)
            # Matches: <function=name>{args}</function> OR <function=name>{args}
            func_pattern = r'<function=(\w+)\s*>?\s*(\{[^}]+\})(?:</function>)?'
            func_match = re.search(func_pattern, failed_gen)
            
            if not func_match:
                logger.warning(f"❌ Could not match any function pattern in: {failed_gen}")
                return None
            
            function_name = func_match.group(1)
            json_args = func_match.group(2)
            
            logger.info(f"✅ Extracted function: {function_name}, args: {json_args}")
            
            try:
                arguments = json.loads(json_args)
            except json.JSONDecodeError as je:
                logger.error(f"❌ JSON decode error: {je}")
                logger.error(f"Failed to parse: {json_args}")
                return None
            
            return {
                "function_name": function_name,
                "arguments": arguments,
                "id": f"call_recovered_{function_name}",
            }
        
        except Exception as e:
            logger.error(f"❌ Error parsing malformed call: {str(e)}")
            return None



    async def _get_rag_context(
        self,
        message: str,
        persona: str,
        intent: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get RAG context for the query (TRUNCATED)"""
        if not self.persona_rag:
            return {"has_rag_context": False}
        
        try:
            rag_context = await self.persona_rag.enhance_query_with_rag(
                query=message,
                persona=persona,
                intent=intent,
                context=context
            )
            
            # ✅ TRUNCATE RAG CONTEXT TO SAVE TOKENS
            if rag_context.get("formatted_context"):
                original_length = len(rag_context["formatted_context"])
                rag_context["formatted_context"] = rag_context["formatted_context"][:1000]  # Max 1200 chars ----- 1200 -> 1000
                logger.debug(f"RAG context truncated: {original_length} → {len(rag_context['formatted_context'])} chars")
            
            logger.debug(f"RAG docs: {rag_context.get('retrieved_doc_count', 0)}")
            return rag_context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"has_rag_context": False, "error": str(e)}

    
    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: Dict[str, Any], tool_context: Dict[str, Any]) -> str:
        """Build persona-specific system message enhanced with RAG context"""
        
        base_context = f"""You are a PAN-INDIA travel assistant with tools: geocode_location, get_weather, search_treks, get_hotel_rates.
        TOOL USAGE RULES:
        - Use `geocode_location` then `get_weather` for current conditions.
        - **CRITICAL**: If the user asks about "festivals", "holidays", "celebrations", or "events", you MUST call `get_indian_holidays`.
        - Use `get_treks` to find hiking trails near a location.
        - **NEW**: If user asks about "hotels", "stays", "accommodation", "prices", or "lodging", MUST call `get_hotel_rates`.
        - Do NOT output tool calls as text (like <function...>); use the proper tool call structure.
        - If you call a tool, output ONLY the tool call.
        - **CRITICAL**: Check the conversation history. If you have ALREADY called a tool with the same arguments, DO NOT call it again.
        
        - If the user asks to "PLAN" a trip:
            1. Search for treks/places FIRST (search_treks).
            2. Then get the WEATHER for the top location found (get_weather).
            3. Then check HOTELS/ACCOMMODATION availability (get_hotel_rates).
            4. Then check HOLIDAYS if a date is mentioned (get_indian_holidays).
            5. Synthesize all data into the final answer.
            
        TREKS
        - Any trek/trekking/hike query → MUST call search_treks.
        - Use region / trek_name as given.
        
        HOTELS
        - Any query about staying, room prices, or hotel suggestions → MUST call get_hotel_rates.
        - Always specify the city clearly (e.g., "hotels in Agra").
        
        FACTS
        - Do NOT invent numbers (km, days, altitude, prices, “250+ treks”, etc.).
        - If a number is not provided, use vague wording or admit uncertainty.
        - Do NOT mention internal tools or “my database” in answers.

        STYLE
        - Brief: 3-6 bullets or a short paragraph.
        - Practical, user-focused.
        - Answer in the user's language.

        CURRENT DATE: {date.today().isoformat()}
        IMPORTANT: Today is {date.today().strftime('%B %Y')}.
        - If user asks for "upcoming" holidays and it is late in the year (Dec), check BOTH current year and next year Q1.
        """

        # - If today is late in the year (Oct-Dec), "upcoming" means THIS YEAR after today and NEXT YEAR.
        
            # ✨ ADD HINGLISH RESPONSE MODE ✨
        if rag_context.get("response_language") == "hinglish":
            base_context += """

IMPORTANT: RESPONSE LANGUAGE - HINGLISH
The user spoke in Hindi. Please respond in HINGLISH (Hindi-English mix):
- Use simple English words mixed with Hindi
- Use Roman script (English letters) for Hindi words
- Examples:
  * "Aap Kedarnath ja sakte hain. Best time hai May-June."
  * "Weather abhi bahut accha hai. Temperature 15°C ke around hai."
  * "Yeh trek difficult hai, proper preparation chahiye."
- Keep it natural and conversational
- Use Hindi words that Indian tourists commonly understand

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
        
        if tool_context and tool_context.get("treks"):
            trek_data = tool_context["treks"]
            base_context += f"""

        --- LIVE TREK DATA ---
        Source: {trek_data.get('source', 'unknown')} ({'Fallback Dataset' if trek_data.get('using_fallback') else 'Live API'})

        Found {trek_data.get('trek_count', 0)} treks in {trek_data.get('region', 'searched area')}:

        """
        #-------------- disabled to have less token consumption --------------
        # for trek in trek_data.get('treks', [])[:5]:  # Show top 5
        #     base_context += f"""
        # Trek: {trek['name']}
        # - Difficulty: {trek.get('difficulty', 'Unknown')}
        # - Duration: {trek.get('duration', 'Unknown')}
        # - Altitude: {trek.get('altitude', 'Unknown')}
        # - Best Time: {trek.get('best_time', 'Unknown')}
        # - Description: {trek.get('description', 'N/A')[:200]}
        # """

        #     base_context += "\nUse this data to provide accurate trek recommendations.\n"

        if tool_context and tool_context.get("holidays"):
            h_data = tool_context["holidays"]
            base_context += f"""
            --- LIVE HOLIDAY DATA ---
            Source: Calendarific API (Official)
            - no need to say something like "checking for holidays", just search for data
            - show all the festivals without having an influence from the religion. like "holi->hindu, christmas->christian, ect." but no need to specify the religion, just know about the festival

            Confirmed Holidays:
            """
            
            if isinstance(h_data, list):
                for h in h_data:
                    # Extract date safely (Calendarific structure vs simplified)
                    d = h.get('date', {}).get('iso', h.get('date')) if isinstance(h.get('date'), dict) else h.get('date')
                    base_context += f"- {d}: {h.get('name')} ({h.get('type')})\n"
            else:
                base_context += "No holidays found.\n"

            base_context += "\nUse this to plan itineraries around closures or cultural events."
        
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
        
        # ✅ ADD THIS: Include extracted trek info
        if intent == "trekking":
            if context.get('extracted_region'):
                context_info += f"\n\n🏔️ IMPORTANT: User is asking about treks near/in {context['extracted_region']}. Use this region in your search_treks tool call."
            if context.get('extracted_trek_name'):
                context_info += f"\n🎯 Specific trek mentioned: {context['extracted_trek_name']}"
        
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
