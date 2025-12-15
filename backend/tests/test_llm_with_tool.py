import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import asyncio
from utils.groq_service import GroqService

async def test():
    groq = GroqService()

    fake_tool_context = {
        "location": {
            "place_name": "Kedarnath",
            "city": "Rudraprayag",
            "state": "Uttarakhand",
            "country": "India",
            "latitude": "30.7346",
            "longitude": "79.0669"
        }
    }

    response, _ = await groq.generate_persona_response(
        message="can I trek kedarnath in october?",
        persona="trek_companion",
        intent="trekking",
        context={},
        tool_context=fake_tool_context
    )

    print("\nLLM RESPONSE:\n", response)

if __name__ == "__main__":
    asyncio.run(test())
