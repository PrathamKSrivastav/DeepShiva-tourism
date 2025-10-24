import os
import asyncio
import logging
from typing import Tuple, List, Optional, Dict, Any
from groq import Groq
from rag.persona_rag import PersonaRAG
from rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
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
        def sync_request():
            try:
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10,
                    temperature=0.1,
                )
            except Exception as e:
                logger.error(f"Test request failed: {str(e)}")
                raise
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_request)
    
    async def generate_persona_response(
        self, 
        message: str, 
        persona: str, 
        intent: str,
        context: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """
        Generate response using Groq API with RAG enhancement
        """
        if not self.client:
            raise Exception("Groq API client not initialized")
        
        # Enhance query with RAG context
        rag_context = await self._get_rag_context(message, persona, intent, context)
        
        # Build persona-specific system message with RAG
        system_message = self._build_system_message_with_rag(persona, intent, rag_context)
        
        # Create the user message
        user_message = self._build_user_message(message, persona, intent, context)
        
        try:
            def sync_request():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, sync_request),
                timeout=self.timeout
            )
            
            response_text = response.choices[0].message.content
            
            # Enhance response with RAG citations if available
            if rag_context.get("has_rag_context", False):
                response_text = self._add_rag_citations(response_text, rag_context)
            
            # Generate contextual suggestions
            suggestions = await self._generate_suggestions_with_rag(message, persona, intent, rag_context)
            
            return response_text, suggestions
            
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
            
            logger.info(f"RAG context retrieved: {rag_context.get('retrieved_doc_count', 0)} docs")
            return rag_context
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"has_rag_context": False, "error": str(e)}
    
    def _build_system_message_with_rag(self, persona: str, intent: str, rag_context: Dict[str, Any]) -> str:
        """Build persona-specific system message enhanced with RAG context"""
        
        base_context = """You are an expert AI tourism guide for Uttarakhand, India - also known as Dev Bhoomi (Land of Gods). 
        
        Uttarakhand is famous for:
        - Char Dham pilgrimage sites (Kedarnath, Badrinath, Gangotri, Yamunotri)
        - Adventure trekking (Valley of Flowers, Roopkund, Kedarkantha)
        - Spiritual destinations (Rishikesh, Haridwar)
        - Hill stations (Mussoorie, Nainital, Auli)
        - Rich cultural heritage and mythology

        Current date: October 2025. Char Dham season is ending soon (closes by Diwali).
        
        IMPORTANT: Keep responses under 800 words, conversational, and informative.
        """
        
        # Add RAG context if available
        if rag_context.get("has_rag_context", False):
            base_context += f"""
        
        ADDITIONAL CONTEXT FROM RELIABLE SOURCES:
        I have access to verified information from {rag_context.get('source_count', 0)} reliable sources including official Uttarakhand government documents and verified tourism resources. Use this information to provide accurate, up-to-date responses.
        
        {rag_context.get('formatted_context', '')}
        """
        
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
            - Reference ancient texts, Puranas, Mahabharata connections
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
            context_info = f"\n\nUser's query seems related to {intent}. Use current information for Uttarakhand."
        
        user_message = f"""
        User Query: {message}
        
        Detected Intent: {intent}
        {context_info}
        
        Please respond as the {persona.replace('_', ' ').title()} persona. 
        Focus on Uttarakhand-specific information and use any available source context naturally.
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
                "What's the best time to visit Kedarnath?",
                "Current crowd levels at Char Dham sites?", 
                "Monsoon season precautions"
            ],
            "itinerary": [
                "How many days needed for Char Dham?",
                "Best route for first-time visitors",
                "Budget planning for pilgrimage"
            ],
            "spiritual": [
                "Temple opening/closing times",
                "Significance of Ganga Aarti", 
                "Meditation spots in Rishikesh"
            ],
            "trekking": [
                "Essential trekking gear list",
                "Valley of Flowers trek difficulty",
                "High altitude safety tips"
            ],
            "emergency": [
                "Altitude sickness precautions",
                "Nearest medical facilities",
                "Emergency evacuation procedures"
            ],
            "general": [
                "Plan my Uttarakhand adventure",
                "Best spiritual destinations",
                "Local food recommendations"
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
