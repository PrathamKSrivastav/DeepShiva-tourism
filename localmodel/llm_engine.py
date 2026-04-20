import logging
from typing import List, Dict, Tuple, Optional
from localmodel.local_llm_service import LocalLLMService
from utils.connection_checker import check_internet_connection
from utils.groq_service import GroqService

logger = logging.getLogger(__name__)

class LLMEngine:
    def __init__(self):
        self.groq = GroqService()
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        force_offline: bool = False
    ) -> Tuple[str, str]:
        """
        Hybrid generation: Groq → Local fallback
        Returns: (response_text, source)
        """
        if not force_offline:
            try:
                if await check_internet_connection():
                    response, _ = await self.groq._raw_generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        conversation_history=conversation_history
                    )
                    return response, "groq"
            except Exception as e:
                logger.warning(f"⚠️ Groq failed → fallback: {str(e)[:80]}")
        
        # Fallback to local GGUF model
        response = LocalLLMService.generate(system_prompt, user_prompt)
        return response, "local"
    
    def is_model_loaded(self) -> bool:
        """Check if local model is available"""
        try:
            LocalLLMService.get_llm()
            return True
        except:
            return False
