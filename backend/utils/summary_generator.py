"""
AI-Powered Chat Summary Generator
Uses Groq API to create intelligent summaries of travel conversations
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate intelligent summaries using Groq API"""
    
    def __init__(self):
        """Initialize Groq client"""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = AsyncGroq(api_key=groq_api_key)
        self.model = "llama-3.1-8b-instant"  # Faster, good quality


    
    async def generate_summary(
        self,
        messages: List[Dict[str, Any]],
        session_title: str,
        persona: str
    ) -> Dict[str, Any]:
        """
        Generate intelligent summary from chat messages
        
        Args:
            messages: List of chat messages (role, content, timestamp)
            session_title: Title of the chat session
            persona: Persona used in the conversation
            
        Returns:
            Structured summary dict with key insights
        """
        try:
            logger.info(f"🤖 Generating summary for: {session_title}")
            
            # Format conversation for analysis
            conversation_text = self._format_conversation(messages)
            
            # Build specialized prompt
            system_prompt = self._build_summary_prompt(persona)
            
            # Call Groq API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation Title: {session_title}\n\n{conversation_text}"}
                ],
                temperature=0.3,  # Lower temperature for consistent summaries
                max_tokens=1500
            )
            
            summary_text = response.choices[0].message.content
            
            # Parse structured summary
            structured_summary = self._parse_summary(summary_text, messages, session_title)
            
            logger.info(f"✅ Summary generated successfully")
            return structured_summary
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {str(e)}")
            raise
    
    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into readable conversation text"""
        formatted = []
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp')
            
            # Format timestamp
            time_str = ""
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    time_str = dt.strftime("%I:%M %p")
                except:
                    time_str = ""
            
            role_label = "Traveler" if role == "user" else "Guide"
            formatted.append(f"[{time_str}] {role_label}: {content}")
        
        return "\n\n".join(formatted)
    
    def _build_summary_prompt(self, persona: str) -> str:
        """Build specialized prompt based on persona"""
        
        base_prompt = """You are an expert travel conversation analyzer. Your task is to create a comprehensive, structured summary of travel planning conversations.

Analyze the conversation and extract the following information in a clear, organized format:

**OUTPUT FORMAT (use markdown):**

## 🎯 Key Topics Discussed
- List 3-5 main topics or destinations

## 📍 Destinations & Places
- Primary destination(s)
- Specific places/attractions mentioned
- Geographic context

## 📅 Travel Planning Details
- Travel dates (if mentioned)
- Duration of trip
- Season/timing considerations
- Budget mentions (if any)

## 🎭 Activities & Interests
- Main activities discussed
- Special interests of traveler
- Type of experience sought

## 💡 Key Recommendations
- Top 3-5 recommendations given
- Why each recommendation matters

## ✅ Action Items
- Things traveler should do/book
- Preparations needed
- Items to research further

## 🌤️ Important Considerations
- Weather/climate info shared
- Safety/health considerations
- Cultural/practical tips

## 📊 Summary Statement
- 2-3 sentence executive summary of the entire conversation

Be concise but comprehensive. Use bullet points. Focus on actionable insights.
"""
        
        # Add persona-specific guidance
        persona_guidance = {
            "local_guide": "Focus on practical travel tips, local insights, and authentic experiences.",
            "spiritual_teacher": "Emphasize spiritual significance, temple details, and philosophical aspects.",
            "trek_companion": "Highlight trekking routes, difficulty levels, safety, and gear recommendations.",
            "cultural_expert": "Focus on cultural heritage, traditions, stories, and historical context."
        }
        
        guidance = persona_guidance.get(persona, persona_guidance["local_guide"])
        base_prompt += f"\n\n**Persona Context:** This conversation used a {persona.replace('_', ' ')} persona. {guidance}"
        
        return base_prompt
    
    def _parse_summary(
        self,
        summary_text: str,
        original_messages: List[Dict[str, Any]],
        title: str
    ) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        
        return {
            "session_title": title,
            "summary_content": summary_text,  # Full markdown summary
            "message_count": len(original_messages),
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "user_messages": len([m for m in original_messages if m.get('role') == 'user']),
                "assistant_messages": len([m for m in original_messages if m.get('role') == 'assistant']),
                "conversation_start": original_messages[0].get('timestamp') if original_messages else None,
                "conversation_end": original_messages[-1].get('timestamp') if original_messages else None
            }
        }


# Singleton instance
_summary_generator = None

def get_summary_generator() -> SummaryGenerator:
    """Get or create summary generator instance"""
    global _summary_generator
    if _summary_generator is None:
        _summary_generator = SummaryGenerator()
    return _summary_generator
