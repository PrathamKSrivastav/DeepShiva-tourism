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
        self.timeout = int(os.getenv("API_TIMEOUT_SECONDS", "90")) #10-> 30 -> 60 -> 90
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
                logger.info("✅ RAG components initialized with Qdrant Cloud")
            else:
                logger.warning("⚠️ RAG components initialized with ChromaDB fallback only")
                
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
        tools: Optional[List[Dict[str, Any]]] = None,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:


        """
        Generate response using Groq API with RAG enhancement and conversation history
        """
        if not self.client:
            raise Exception("Groq API client not initialized")
    
        # Ensure context is not None
        context = context or {}  # ← ADD THIS LINE

        # Enhance query with RAG context
        if not rag_context: 
            logger.info("⚠️ No RAG context provided, fetching fallback...")
            rag_context = await self._get_rag_context(message, persona, intent, context)

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
    
    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: dict, tool_context: dict) -> str:
        """
        Builds a highly optimized system prompt for RAG + Agents.
        """
        # 1. Base Identity
        base_prompt = f"You are a {persona} guide for India. Intent: {intent}.\n"

        # 2. Inject RAG Context (The "Truth")
        if rag_context and rag_context.get("has_rag_context"):
            # Truncate to avoid token overflow (~6000 chars is plenty for Llama3-70b)
            context_text = rag_context.get("formatted_context", "")[:6000]
            base_prompt += f"\n### OFFICIAL KNOWLEDGE BASE (PRIORITY):\n{context_text}\n"
            base_prompt += "INSTRUCTION: Answer strictly using this Knowledge Base if possible.\n"

        # 3. Inject Tool Results (Real-time Data)
        if tool_context:
            import json
            # Filter huge lists to save tokens (e.g. only top 5 treks)
            clean_tool_context = tool_context.copy()
            if "treks" in clean_tool_context:
                # Keep only summary info for treks to save space
                trek_data = clean_tool_context["treks"]
                clean_tool_context["treks"] = {
                    "count": trek_data.get("trek_count"),
                    "region": trek_data.get("region"),
                    "top_treks": trek_data.get("treks", [])[:5] # Only top 5
                }

            base_prompt += f"\n### LIVE TOOL RESULTS:\n{json.dumps(clean_tool_context, indent=2)}\n"
            base_prompt += "INSTRUCTION: Use these results to answer specific questions (e.g., weather, prices).\n"

        # 4. Hinglish Support
        if rag_context and rag_context.get("response_language") == "hinglish":
            base_prompt += """
            IMPORTANT: RESPONSE LANGUAGE - HINGLISH
            The user spoke in Hindi. Please respond in HINGLISH (Hindi-English mix):
            - Use simple English words mixed with Hindi.
            - Use Roman script (English letters).
            - Example: "Weather abhi bahut accha hai. Temperature 15°C ke around hai."
            """

        # 5. Persona Instructions
        persona_instructions = {
            "local_guide": """
            STYLE: Friendly, casual, "Hey there!", "Pro tip".
            Focus on practical logistics, costs, and insider tips.
            """,
            "spiritual_teacher": """
            STYLE: Serene, wise, philosophical.
            Include Sanskrit phrases with translations. Focus on inner transformation.
            """,
            "trek_companion": """
            STYLE: Energetic, safety-focused, concise.
            Focus on gear, difficulty, weather, and safety.
            """,
            "cultural_expert": """
            STYLE: Scholarly yet engaging storyteller.
            Focus on history, legends, and cultural significance.
            """
        }
        base_prompt += f"\n### PERSONA GUIDELINES:\n{persona_instructions.get(persona, persona_instructions['local_guide'])}\n"

        # 6. Final Rules
        base_prompt += """
        ### FINAL RULES:
        1. If the answer is in the KNOWLEDGE BASE, use it. DO NOT invent facts.
        2. If 'LIVE TOOL RESULTS' contains the info, ANSWER the user. DO NOT call the tool again.
        3. Keep answers concise (under 4 sentences unless asked for details).
        """
        
        return base_prompt

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
