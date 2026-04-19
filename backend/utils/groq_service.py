import os
import asyncio
import logging
from typing import Tuple, List, Optional, Dict, Any

from sklearn import base
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
        self.model_name = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")#hehe
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.7")) # 0.7 -> 0.3 -> 0.5
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "800")) #1000 -> 800
        self.timeout = int(os.getenv("API_TIMEOUT_SECONDS", "120")) #10-> 30 -> 60 -> 90 ->120
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
        """Initialize RAG components with Qdrant support"""
        try:
            # Get Qdrant credentials from environment
            qdrant_host = os.getenv("QDRANT_HOST")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            qdrant_dim = int(os.getenv("QDRANT_DIM", 384))
            
            # Initialize VectorStoreManager with Qdrant support
            self.vector_store = VectorStoreManager(
                persist_directory="data/vector_db",
                embedding_model_name="all-MiniLM-L6-v2",
                qdrant_host=qdrant_host,
                qdrant_api_key=qdrant_api_key,
                qdrant_dim=qdrant_dim
            )
            
            self.persona_rag = PersonaRAG(self.vector_store)
            
            # Log Qdrant status
            if self.vector_store._cloud_available():
                logger.info(" RAG components initialized with Qdrant Cloud")
            else:
                logger.warning(" RAG components initialized with ChromaDB fallback only")
                
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
        rag_context: Optional[Dict[str, Any]] = None,  # ← Can be pre-fetched
        skip_rag: bool = False  # ← NEW: Explicit control to skip RAG
    ) -> Tuple[str, List[str]]:
        """
        Generate response using Groq API with RAG enhancement and conversation history
        
        Args:
            message: User's input message
            persona: Selected persona (local_guide, spiritual_teacher, etc.)
            intent: Classified intent (spiritual, trekking, etc.)
            context: Additional context dictionary
            tool_context: Results from tool executions
            conversation_history: Previous messages in conversation
            tools: Available tools for function calling
            rag_context: PRE-FETCHED RAG context (avoids duplicate retrieval)
            skip_rag: Explicitly skip RAG retrieval (for offline mode)
        """
        if not self.client:
            raise Exception("Groq API client not initialized")
    
        # Ensure context is not None
        context = context or {}

        # ⭐ FIX: Only retrieve RAG context if not already provided
        if rag_context is None and not skip_rag:
            logger.info("🔍 Fetching RAG context (not pre-cached)")
            rag_context = await self._get_rag_context(message, persona, intent, context)
        elif rag_context:
            logger.info(" Using pre-cached RAG context (no duplicate retrieval)")
        elif skip_rag:
            logger.info("⏭️ RAG retrieval skipped (offline mode)")
            rag_context = {"has_rag_context": False}
        else:
            # Fallback
            rag_context = {"has_rag_context": False}

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
                    # ⭐ OPTIMIZATION: Log but don't repeat the same info
                    logger.debug(f"💬 Including {len(conversation_history)} previous messages for context")
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
                logger.warning(" Detected malformed function call, attempting to parse...")
                
                # Extract the malformed function call
                parsed_call = self._parse_malformed_function_call(error_str)
                
                if parsed_call:
                    logger.info(f" Successfully parsed malformed call: {parsed_call['function_name']}")
                    return {
                        "type": "tool_call_malformed",
                        "parsed_call": parsed_call,
                        "original_error": error_str
                    }
            
            logger.error(f"Groq API error: {error_str}")
            raise Exception(f"Groq API failed: {error_str[:100]}")

        # Wrapper to allow public access to the internal RAG method
    async def get_rag_context(self, message: str, persona: str, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Public wrapper for RAG retrieval"""
        return await self._get_rag_context(message, persona, intent, context)


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
                # logger.warning(" Could not find failed_generation in error")
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
                logger.info(f" Extracting INNER function to call first: {inner_func}")
                
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
                    logger.error(f" Failed to parse nested JSON: {je}")
                    # Don't return None yet, try other patterns
            
            # PRIORITY 2: Handle Open-Ended XML style (Missing closing tag)
            # Matches: <function=name>{args}
            # This is common with Llama-3-8b-instruct
            xml_open_pattern = r'<function=([a-zA-Z0-9_]+)>.*?({.*})'
            xml_match = re.search(xml_open_pattern, failed_gen)
            
            if xml_match:
                function_name = xml_match.group(1)
                json_args = xml_match.group(2)
                logger.info(f" Extracted XML-style function (open): {function_name}")
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
                logger.warning(f" Could not match any function pattern in: {failed_gen}")
                return None
            
            function_name = func_match.group(1)
            json_args = func_match.group(2)
            
            logger.info(f" Extracted function: {function_name}, args: {json_args}")
            
            try:
                arguments = json.loads(json_args)
            except json.JSONDecodeError as je:
                logger.error(f" JSON decode error: {je}")
                logger.error(f"Failed to parse: {json_args}")
                return None
            
            return {
                "function_name": function_name,
                "arguments": arguments,
                "id": f"call_recovered_{function_name}",
            }
        
        except Exception as e:
            logger.error(f" Error parsing malformed call: {str(e)}")
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
            
            #  TRUNCATE RAG CONTEXT TO SAVE TOKENS
            if rag_context.get("formatted_context"):
                original_length = len(rag_context["formatted_context"])
                rag_context["formatted_context"] = rag_context["formatted_context"][:2000]  # Max 1200 chars ----- 1200 -> 1000 -> 2000
                logger.debug(f"RAG context truncated: {original_length} → {len(rag_context['formatted_context'])} chars")
            
            logger.debug(f"RAG docs: {rag_context.get('retrieved_doc_count', 0)}")
            return rag_context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"has_rag_context": False, "error": str(e)}
    
    # def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: dict, tool_context: dict) -> str:
    #     """
    #     Builds a highly optimized system prompt for RAG + Agents.
    #     """
    #     # 1. Base Identity
    #     base_prompt = f"You are a {persona} guide for India. Intent: {intent}.\n"

    #     # 2. Inject RAG Context (The "Truth")
    #     if rag_context and rag_context.get("has_rag_context"):
    #         # Truncate to avoid token overflow (~6000 chars is plenty for Llama3-70b)
    #         context_text = rag_context.get("formatted_context", "")[:6000]
    #         base_prompt += f"\n### OFFICIAL KNOWLEDGE BASE (PRIORITY):\n{context_text}\n"
    #         base_prompt += "INSTRUCTION: Answer strictly using this Knowledge Base(if possible). IMPORTANT But use tools whenever possible.\n"
    #         # GEOGRAPHICAL VALIDATION
    #         if rag_context.get('query_location'):
    #             base_prompt += f"\n\nCRITICAL LOCATION FILTER: User asked about {rag_context['query_location']}. REJECT any information about other locations. Only use data specifically about {rag_context['query_location']}."

    #     # 3. Inject Tool Results (Real-time Data)
    #     if tool_context:
    #         import json
    #         # Filter huge lists to save tokens (e.g. only top 5 treks)
    #         clean_tool_context = tool_context.copy()
    #         if "treks" in clean_tool_context:
    #             # Keep only summary info for treks to save space
    #             trek_data = clean_tool_context["treks"]
    #             clean_tool_context["treks"] = {
    #                 "count": trek_data.get("trek_count"),
    #                 "region": trek_data.get("region"),
    #                 "top_treks": trek_data.get("treks", [])[:5] # Only top 5
    #             }

    #         base_prompt += f"\n### LIVE TOOL RESULTS:\n{json.dumps(clean_tool_context, indent=2)}\n"
    #         base_prompt += "INSTRUCTION: Use these results to answer specific questions (e.g., weather, prices).\n"

    #     # 4. Hinglish Support
    #     if rag_context and rag_context.get("response_language") == "hinglish":
    #         base_prompt += """
    #         IMPORTANT: RESPONSE LANGUAGE - HINGLISH
    #         The user spoke in Hindi. Please respond in HINGLISH (Hindi-English mix):
    #         - Use simple English words mixed with Hindi.
    #         - Use Roman script (English letters).
    #         - Example: "Weather abhi bahut accha hai. Temperature 15°C ke around hai."
    #         """

    #     # 5. Persona Instructions
    #     persona_instructions = {
    #         "local_guide": """
    #         STYLE: Friendly, casual, for example- "Hey there!", "Pro tip".
    #         Focus on practical logistics, costs, and insider tips. Act as a Local tour guide
    #         """,
    #         "spiritual_teacher": """
    #         STYLE: Serene, wise, philosophical.
    #         Include Sanskrit phrases with translations. Focus on inner transformation.
    #         """,
    #         "trek_companion": """
    #         STYLE: Energetic, safety-focused, concise. be like a trek instructor.
    #         Focus on gear, difficulty, weather, and safety.
    #         """,
    #         "cultural_expert": """
    #         STYLE: Scholarly yet engaging storyteller. act as someone who has deep knowledge about indian culture and history.
    #         Focus on history, legends, and cultural significance.
    #         """
    #     }
    #     base_prompt += f"\n### PERSONA GUIDELINES:\n{persona_instructions.get(persona, persona_instructions['local_guide'])}\n"

    #     # 6. Final Rules
    #     base_prompt += """
    #     # FINAL RULES - ANTI-HALLUCINATION
    #     1. ONLY answer if the KNOWLEDGE BASE or LIVE TOOL RESULTS explicitly contain the information.
    #     2. If you lack specific information, say: "I don't have verified information about [topic]. Please refine your query."
    #     3. NEVER invent place names, prices, addresses, phone numbers, or specific details. try to call geocoding tool if location is not found in rag context.
    #     4. NEVER extrapolate from similar contexts (e.g., don't suggest Sikkim locations for Delhi queries)
    #     5. If tool results are empty or irrelevant, explicitly state: "No relevant information found for your query." then and only then proceed to general advice through rag content.
    #     6. STRICTLY respect geographical boundaries - only suggest places in the queried location
    #     7. If LIVE TOOL RESULTS contains the info, ANSWER the user. DO NOT call the tool again.
    #     8. Keep answers concise (under 4 sentences unless asked for details).
    #     """

        
    #     return base_prompt

    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: dict, tool_context: dict) -> str:
        """
        Optimized system prompt for RAG + Agents (token-efficient) with CORRECT tool names.
        """
        base_prompt = f"You are a {persona} guide for India (Intent: {intent}). You're AGENTIC - call tools to get real-time data.\n"
        from datetime import datetime
        base_prompt += f"CURRENT DATE: {datetime.now().strftime('%Y-%m-%d')}. Do not provide information for past dates unless explicitly asked about history.\n"
        
        #  CORRECTED: Intent-Based Tool Enforcement (EXACT function names from your tools)
        REQUIRED_TOOLS = {
            "itinerary": ["get_holidays", "get_weather", "get_hotel_rates", "geocode_location"],
            "accommodation": ["get_hotel_rates", "geocode_location"],
            "trekking": ["search_treks", "get_weather", "geocode_location"],
            "weather": ["get_weather", "geocode_location"],
            "events": ["get_holidays"],
            "navigation": ["geocode_location"]
        }
        
        required = REQUIRED_TOOLS.get(intent, [])
        if required and not tool_context:
            base_prompt += f"\n🚨 MUST CALL TOOLS: {', '.join(required)}. Don't answer generically - call tools NOW!\n"
        
        # RAG Context
        if rag_context and rag_context.get("has_rag_context"):
            context_text = rag_context.get("formatted_context", "")[:5000]
            base_prompt += f"\n### KNOWLEDGE BASE:\n{context_text}\n"
            if rag_context.get('query_location'):
                base_prompt += f" LOCATION FILTER: Only info about {rag_context['query_location']} - reject others.\n"
        
        # Tool Results
        if tool_context:
            import json
            clean_ctx = tool_context.copy()
            if "treks" in clean_ctx:
                trek_data = clean_ctx["treks"]
                clean_ctx["treks"] = {"count": trek_data.get("trek_count"), "region": trek_data.get("region"), "top_treks": trek_data.get("treks", [])[:5]}
            base_prompt += f"\n### LIVE TOOL DATA:\n{json.dumps(clean_ctx, indent=2)}\n Use these real-time results.\n"
        
        # Critical Rules (condensed)
        base_prompt += """
    ### PRIORITY RULES:
    **USE TOOLS (not RAG) for:** Hotels, Weather, Events, Navigation, Current Prices
    **USE RAG for:** History, Culture, Temples, Scriptures, Trekking Peaks (mountaineering)

    **TOOL USAGE GUIDE:**
    - Hotels → get_hotel_rates(city) - Required for accommodation queries
    - Weather → get_weather(lat, lon) - Get coords first with geocode_location(city)
    - Events/Holidays → get_holidays(year, month, quarter)
    - Navigation/Coords → geocode_location(query)
    - Treks/Hiking → search_treks(region, trek_name) - For hiking trails only
    - Peaks/Mountaineering → Use RAG (ingested CSV data)

    **MULTI-STEP WORKFLOW:**
    1. For hotels: geocode_location(city) → get_weather(lat, lon) → get_hotel_rates(city)
    2. For trip planning: get_holidays() → geocode_location() → get_weather() → get_hotel_rates()
    3. For trekking: geocode_location(region) → search_treks(region) → get_weather()

    **IMPORTANT:**
    - If RAG lacks info → Call tools
    - Already have tool results? → Use them (don't re-call)
    - For mountaineering PEAKS → Use RAG (your CSV data with exact heights)
    - For hiking TRAILS → Use search_treks tool
    """
        
        # Hinglish
        if rag_context and rag_context.get("response_language") == "hinglish":
            base_prompt += "🇮🇳 RESPOND IN HINGLISH (Hindi-English mix, Roman script).\n"
        
        # Persona (ultra-condensed)
        persona_styles = {
            "local_guide": "Friendly, practical tips. Focus: logistics, costs, safety.",
            "spiritual_teacher": "Serene, wise. Focus: inner wisdom, Sanskrit teachings.",
            "trek_companion": "Energetic, safety-first. Focus: gear, difficulty, permits.",
            "cultural_expert": "Scholarly storyteller. Focus: history, legends, traditions."
        }
        base_prompt += f"\n**PERSONA:** {persona_styles.get(persona, persona_styles['local_guide'])}\n"
        
        # Anti-Hallucination (compressed)
        base_prompt += """
    ### NO HALLUCINATIONS:
     Never invent: names, prices, addresses, dates
     Never extrapolate across locations
     Only answer from Knowledge Base OR Tool Results
     No info? Say: "No verified info for [query]"
    Keep concise (3-4 sentences unless asked)
    """
        
        return base_prompt




    def _build_user_message(self, message: str, persona: str, intent: str, context: Dict[str, Any]) -> str:
        """Build the complete user message with context"""
        context_info = ""
        
        if intent in ["weather", "crowd", "festival", "emergency"]:
            context_info = f"\n\nUser's query seems related to {intent}. Use current information for India."
        
        #  ADD THIS: Include extracted trek info
        if intent == "trekking":
            if context.get('extracted_region'):
                context_info += f"\n\n IMPORTANT: User is asking about treks near/in {context['extracted_region']}. Use this region in your search_treks tool call."
            if context.get('extracted_trek_name'):
                context_info += f"\n Specific trek mentioned: {context['extracted_trek_name']}"
        
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
            citation_note = f"\n\n *Response enhanced with information from {rag_context['source_count']} verified sources*"
            return response_text + citation_note
        
        return response_text
    
    async def verify_response_against_sources(self, user_query: str, response: str, rag_context: dict, tool_context: dict) -> tuple[bool, str]:
        """
        Verify if response contains hallucinations by checking against sources.
        Returns: (is_valid, explanation)
        """
        if not self.client:
            return True, "verification_skipped_no_client"
        
        # Skip verification if no sources to check against
        if not rag_context.get('hasragcontext') and not tool_context:
            return True, "no_sources_to_verify"
        
        source_text = ""
        if rag_context.get('hasragcontext'):
            source_text += f"RAG CONTEXT: {rag_context.get('formatted_context', '')[:1500]}\n\n"
        if tool_context:
            import json
            source_text += f"TOOL RESULTS: {json.dumps(tool_context, indent=2)[:1500]}"
        
        verification_prompt = f"""You are a strict hallucination detector for a travel chatbot.

        USER QUERY: {user_query}

        ASSISTANT RESPONSE:
        {response}

        SOURCE DATA:
        {source_text}

        TASK: Check if the response contains FABRICATED INFORMATION (invented places, fake names, wrong locations, made-up numbers).

        IMPORTANT RULES:
        - Paraphrasing is ALLOWED (e.g., "magical" for "special")
        - Related nearby attractions are ALLOWED if contextually relevant
        - General travel advice is ALLOWED
        - Minor stylistic differences are ALLOWED
        - ONLY flag as hallucination if: invented place names, wrong city/location, fake specific details (prices, addresses, phone numbers)

        Answer in ONE of these formats:
        - "VALID" - if response is grounded in sources or reasonable travel advice
        - "HALLUCINATION: [brief 1-sentence explanation of what was invented]" - ONLY for serious fabrications
        """
        
        try:
            result = await self._raw_generate(
                system_prompt="You are a hallucination detector. Only flag serious fabrications, not stylistic choices.",
                user_prompt=verification_prompt
            )
            
            verification_result = result[0].strip()
            
            # Only flag if explicitly says HALLUCINATION
            if verification_result.startswith("HALLUCINATION:"):
                # Extract just the brief explanation
                explanation = verification_result.replace("HALLUCINATION:", "").strip()
                logger.warning(f"Hallucination: {explanation[:200]}")  # Limit log length
                return False, explanation
            
            return True, "VALID"
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return True, "verification_error"  # Don't block response on verification errors

    
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
