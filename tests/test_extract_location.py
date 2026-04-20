import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.intents import extract_location

queries = [
    "what is the temperature and weather in dehradun today?",
    "weather in delhi",
    "can I trek kedarnath in october?",
    "tell me about goa"
]

for q in queries:
    print(f"\nQUERY: {q}")
    print("EXTRACTED LOCATION:", extract_location(q))
