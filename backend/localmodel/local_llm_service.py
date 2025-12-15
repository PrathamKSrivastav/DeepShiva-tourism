from llama_cpp import Llama
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

class LocalLLMService:
    _llm = None

    @classmethod
    def get_llm(cls):
        if cls._llm is None:
            logger.info("🧠 Loading local GGUF model")
            cls._llm = Llama(
                model_path=str(MODEL_PATH),
                n_ctx=1024,
                n_threads=6,
                n_batch=64,
                use_mmap=False,
                use_mlock=False,
                verbose=False
            )
        return cls._llm

    @classmethod
    def generate(cls, system_prompt: str, user_prompt: str) -> str:
        llm = cls.get_llm()

        prompt = f"""<|system|>
{system_prompt}
<|user|>
{user_prompt}
<|assistant|>
"""

        out = llm(
            prompt,
            max_tokens=512,
            temperature=0.3,
            stop=["<|eot_id|>", "</s>"]
        )

        return out["choices"][0]["text"].strip()
