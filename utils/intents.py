import re
from typing import Dict, List, Optional, Tuple

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
        # ⬇️ EXPANDED TREK KEYWORDS ⬇️
        "trek", "trekking", "hike", "hiking", "mountain", "adventure", "trail",
        "expedition", "altitude", "climb", "climbing", "mountaineering",
        "peak", "summit", "pass", "valley", "camping", "backpacking",
        "difficulty", "duration", "gear", "altitude sickness", "acclimatization"
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

# ⬇️ NEW: Famous trek names for recognition ⬇️
FAMOUS_TREKS = [
    "hampta pass", "valley of flowers", "kedarnath", "roopkund", "chadar",
    "markha valley", "goechala", "sandakphu", "kuari pass", "pin parvati",
    "har ki dun", "nag tibba", "triund", "kareri lake", "bhrigu lake",
    "chandrashila", "deoriatal", "gomukh tapovan", "stok kangri", "kang yatse",
    "dzongri", "singalila", "rupin pass", "bali pass", "kalindi khal"
]

# ⬇️ NEW: Indian trekking regions ⬇️
TREKKING_REGIONS = [
    "himachal pradesh", "himachal", "uttarakhand", "ladakh", "sikkim",
    "kashmir", "maharashtra", "karnataka", "western ghats", "sahyadri",
    "manali", "leh", "dharamshala", "rishikesh", "gangtok"
]


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


# ⬇️ UPDATED: Better stop words ⬇️
STOP_WORDS = {
    "today", "tomorrow", "week", "next week", "next",
    "weather", "temperature", "forecast",
    "climate", "conditions", "current", "currently", "now",
    "tell", "me", "about", "show", "find", "what", "where",
    "is", "are", "the", "in", "at", "for", "trek", "trekking"
}


def extract_location(message: str) -> Optional[str]:
    """
    Extract location from user message
    
    Args:
        message: User's input message
    
    Returns:
        Extracted location string or None
    """
    msg = message.lower()
    
    # Remove stop words
    for w in STOP_WORDS:
        msg = msg.replace(w, " ")
    
    # Remove punctuation
    msg = re.sub(r"[^\w\s]", "", msg)
    
    # Clean up multiple spaces
    msg = " ".join(msg.split())
    
    # Common Indian cities / proper nouns heuristic
    tokens = msg.split()
    tokens = [t for t in tokens if len(t) > 2]
    
    if not tokens:
        return None
    
    # Return the LAST meaningful token group (1-2 words)
    if len(tokens) >= 2:
        return " ".join(tokens[-2:]).title()
    elif len(tokens) == 1:
        return tokens[0].title()
    
    return None


# ⬇️ NEW: Extract trek-specific information ⬇️
def extract_trek_info(message: str) -> tuple[Optional[str], Optional[str]]:
    """Extract trek name and region from message"""
    message_lower = message.lower()
    
    # Known trek names (add more as needed)
    trek_keywords = [
        'hampta pass', 'valley of flowers', 'roopkund', 'kedarnath',
        'pin parvati', 'chadar trek', 'markha valley', 'goechala',
        'sandakphu', 'kuari pass', 'brahmatal', 'har ki dun'
    ]
    
    trek_name = None
    for trek in trek_keywords:
        if trek in message_lower:
            trek_name = trek.title()
            break
    
    # Extract region
    region_keywords = {
        # States
        'himachal': 'Himachal Pradesh',
        'uttarakhand': 'Uttarakhand',
        'ladakh': 'Ladakh',
        'sikkim': 'Sikkim',
        'kashmir': 'Kashmir',
        'maharashtra': 'Maharashtra',
        'karnataka': 'Karnataka',
        'kerala': 'Kerala',
        'rajasthan': 'Rajasthan',
        
        # Cities → Nearest trekking region
        'agra': 'Uttarakhand',
        'mathura': 'Uttarakhand',
        'vrindavan': 'Uttarakhand',
        'delhi': 'Uttarakhand',
        'noida': 'Uttarakhand',
        'gurgaon': 'Uttarakhand',
        'jaipur': 'Rajasthan',
        'mumbai': 'Maharashtra',
        'pune': 'Maharashtra',
        'bangalore': 'Karnataka',
        'chennai': 'Tamil Nadu'
    }
    
    region = None
    for key, value in region_keywords.items():
        if key in message_lower:
            region = value
            break
    
    return trek_name, region



# ⬇️ NEW: Helper to check if query is trek-related ⬇️
def is_trek_query(message: str) -> bool:
    """
    Quick check if message is about trekking
    
    Args:
        message: User's input message
    
    Returns:
        True if trek-related, False otherwise
    """
    message_lower = message.lower()
    
    trek_indicators = ["trek", "hike", "trail", "mountain", "pass", "valley", "peak", "climb"]
    
    return any(indicator in message_lower for indicator in trek_indicators)
