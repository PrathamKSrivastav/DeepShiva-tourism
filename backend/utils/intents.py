import re
from typing import Dict, List

# Intent keywords mapping
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "weather": [
        "weather", "temperature", "rain", "cold", "hot", "climate",
        "forecast", "sunny", "cloudy", "snow", "monsoon"
    ],
    "itinerary": [
        "itinerary", "plan", "trip", "visit", "route", "days",
        "travel plan", "pilgrimage", "tour", "journey"
    ],
    "spiritual": [
        "spiritual", "prayer", "worship", "faith",
        "meditation", "sacred", "holy", "pilgrimage",
        "religion", "belief", "tradition"
    ],
    "trekking": [
        "trek", "hike", "mountain", "adventure", "trail",
        "expedition", "altitude"
    ],
    "emergency": [
        "emergency", "hospital", "doctor", "medical", "help", "urgent",
        "accident", "sick", "injured", "ambulance", "rescue", "safety"
    ],
    "festival": [
        "festival", "celebration", "event", "fair", "cultural",
        "ganga dussehra", "kumbh", "ceremony", "mela"
    ],
    "crowd": [
        "crowd", "busy", "crowded", "people", "tourist", "rush",
        "peak season", "off season", "queue", "waiting"
    ],
    "accommodation": [
        "hotel", "stay", "accommodation", "lodge", "guesthouse",
        "booking", "room", "where to stay"
    ],
    "food": [
        "food", "restaurant", "eat", "cuisine", "local dish",
        "meal", "breakfast", "lunch", "dinner"
    ]
}

def classify_intent(message: str) -> str:
    """
    Classify user intent based on keyword matching
    
    Args:
        message: User's input message
        
    Returns:
        Classified intent category
    """
    message_lower = message.lower()
    
    # Score each intent based on keyword matches
    intent_scores = {}
    
    for intent, keywords in INTENT_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in message_lower:
                # Give higher weight to exact word matches
                if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
                    score += 2
                else:
                    score += 1
        
        if score > 0:
            intent_scores[intent] = score
    
    # Return intent with highest score
    if intent_scores:
        return max(intent_scores, key=intent_scores.get)
    
    return "general"

def extract_location(message: str) -> str:
    """
    Extract location names from user message
    
    Args:
        message: User's input message
        
    Returns:
        Extracted location or empty string
    """
    locations = [
        "delhi", "varanasi", "ayodhya", "mathura", "ujjain",
        "mumbai", "chennai", "kolkata", "bengaluru",
        "kedarnath", "badrinath"
    ]

    
    message_lower = message.lower()
    
    for location in locations:
        if location in message_lower:
            return location.title()
    
    return ""
