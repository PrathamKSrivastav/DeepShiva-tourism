import json
from pathlib import Path
from typing import Dict, Any
import random

DATA_DIR = Path(__file__).parent.parent / "data"

def load_mock_data(data_type: str) -> Dict:
    """Load mock data from JSON files"""
    try:
        with open(DATA_DIR / f"{data_type}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def generate_response(message: str, persona: str, intent: str, context: Dict[str, Any]) -> str:
    """
    Generate persona-specific response based on intent and context
    
    Args:
        message: User's input message
        persona: Selected persona ID
        intent: Classified intent
        context: Additional context information
        
    Returns:
        Generated response text
    """
    weather_data = load_mock_data("weather")
    crowd_data = load_mock_data("crowd")
    festival_data = load_mock_data("festivals")
    emergency_data = load_mock_data("emergency")

    generators = {
        "local_guide": generate_local_guide_response,
        "spiritual_teacher": generate_spiritual_teacher_response,
        "trek_companion": generate_trek_companion_response,
        "cultural_expert": generate_cultural_expert_response
    }

    generator = generators.get(persona, generate_local_guide_response)

    return generator(
        message=message,
        intent=intent,
        weather=weather_data,
        crowd=crowd_data,
        festivals=festival_data,
        emergency=emergency_data
    )

# ------------------------------------------------------------------
# LOCAL GUIDE (India-wide, practical)
# ------------------------------------------------------------------

def generate_local_guide_response(message: str, intent: str, **data) -> str:
    """Local Guide persona - friendly, practical, conversational"""

    responses = {
        "weather": lambda: (
            f"Here's a quick weather snapshot for you. {get_weather_info(data['weather'])} "
            "In India, weather can change fast depending on region — mountains, coastlines, "
            "and plains behave very differently. Carry light layers and stay hydrated."
        ),

        "itinerary": lambda: (
            "India offers many travel circuits — spiritual, cultural, and adventure-based. "
            "The ideal duration depends on terrain, distances, and pace. "
            "Himalayan routes need acclimatization, while city or temple circuits are quicker. "
            "Tell me the region or travel style you're considering, and I'll tailor it."
        ),

        "spiritual": lambda: (
            "India's spiritual landscape is incredibly diverse — from ancient places of worship and "
            "river ghats to monasteries and meditation centers. Early mornings are usually "
            "best for a peaceful experience. If you have a specific tradition or place in mind, "
            "I can guide you more precisely."
        ),

        "trekking": lambda: (
            "India has excellent trekking across the Himalayas, Western Ghats, and desert regions. "
            f"{get_weather_info(data['weather'])} "
            "Good footwear, hydration, and weather awareness are essential everywhere. "
            "Let me know your experience level and region to suggest the right trail."
        ),

        "emergency": lambda: (
            f"Safety first. {get_emergency_info(data['emergency'])} "
            "If you're traveling in remote or high-altitude regions, keep buffer days, "
            "carry basic medicines, and save local emergency numbers."
        ),

        "festival": lambda: (
            f"India celebrates festivals throughout the year, often with regional variations. "
            f"{get_festival_info(data['festivals'])} "
            "Festivals can affect crowds and transport, but they're also a great way to "
            "experience local culture."
        ),

        "crowd": lambda: (
            f"{get_crowd_info(data['crowd'])} "
            "Peak seasons usually coincide with holidays and festivals. "
            "If you prefer quieter travel, consider shoulder months."
        ),

        "general": lambda: (
            "Welcome! India is a land of remarkable diversity — mountains, rivers, deserts, "
            "coastlines, spiritual centers, and vibrant cities. Whether you're exploring for "
            "culture, devotion, adventure, or food, there's something meaningful everywhere. "
            "What would you like to explore?"
        )
    }

    return responses.get(intent, responses["general"])()

# ------------------------------------------------------------------
# SPIRITUAL TEACHER (Pan-Indian philosophy)
# ------------------------------------------------------------------

def generate_spiritual_teacher_response(message: str, intent: str, **data) -> str:
    """Spiritual Teacher persona - serene, reflective, philosophical"""

    # sanskrit_quotes = [
    #     "ॐ नमः शिवाय (Om Namah Shivaya)",
    #     "तत् त्वम् असि (Tat Tvam Asi)",
    #     "सत्यम् शिवम् सुन्दरम् (Truth, Auspiciousness, Beauty)",
    #     "वसुधैव कुटुम्बकम् (The world is one family)"
    # ]
    wisdom_quotes = [
        "Reflection and mindfulness bring clarity.",
        "Silence and stillness are shared paths across traditions.",
        "Many cultures seek meaning through service and compassion.",
        "Inner growth often begins with self-awareness."
    ]


    responses = {
        "weather": lambda: (
            f"The elements shape every journey. {get_weather_info(data['weather'])} "
            "Each season carries its own rhythm and lesson. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "itinerary": lambda: (
            "A spiritual journey in India is not measured by distance alone, but by intention. "
            "Sacred rivers, places of worship, meditation centers, monasteries, and pilgrimage routes exist across the land. "
            "Move slowly, listen inwardly, and let the journey unfold naturally. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "spiritual": lambda: (
            "India's spiritual traditions — Vedantic, Bhakti, Shaiva, Shakta, Buddhist, and Jain — "
            "all point toward self-realization. places of worship, meditation centers, and sacred spaces act as anchors for inner focus, "
            "but true transformation arises from awareness and humility. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "trekking": lambda: (
            "Walking through nature can itself be a form of meditation. "
            f"{get_weather_info(data['weather'])} "
            "Move with respect for the land, conserve energy, and remain mindful. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "emergency": lambda: (
            f"{get_emergency_info(data['emergency'])} "
            "The body is the vehicle of the soul — care for it with attentiveness. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "festival": lambda: (
            "Festivals in India align human life with cosmic cycles — light and darkness, "
            "harvest and renewal, devotion and gratitude. "
            f"{get_festival_info(data['festivals'])} "
            f"{random.choice(wisdom_quotes)}"
        ),

        "crowd": lambda: (
            f"{get_crowd_info(data['crowd'])} "
            "Solitude deepens awareness, but collective devotion also carries power. "
            "Choose what nourishes your spirit. "
            f"{random.choice(wisdom_quotes)}"
        ),

        "general": lambda: (
            "Welcome, seeker. India's spiritual heritage spans thousands of years and countless paths. "
            "Every river, mountain, and temple carries layers of meaning. "
            "Approach with reverence, curiosity, and openness. "
            f"{random.choice(wisdom_quotes)}"
        )
    }

    return responses.get(intent, responses["general"])()

# ------------------------------------------------------------------
# TREK COMPANION (India-wide, safety-first)
# ------------------------------------------------------------------

def generate_trek_companion_response(message: str, intent: str, **data) -> str:
    """Trek Companion persona - adventurous, concise, safety-focused"""

    responses = {
        "weather": lambda: (
            f"Weather update: {get_weather_info(data['weather'])} "
            "India's terrain varies a lot — always prepare for sudden changes."
        ),

        "itinerary": lambda: (
            "Planning an outdoor or adventure route? Duration depends on terrain and access. "
            "Mountain regions need acclimatization days; forests and plateaus need buffer time. "
            "Share the region and difficulty level for a sharper plan."
        ),

        "spiritual": lambda: (
            "Many spiritual sites in India are located in challenging terrain. "
            "Altitude, heat, and crowd management matter. "
            "Early starts and hydration make a big difference."
        ),

        "trekking": lambda: (
            f"Trek prep essentials: fitness, footwear, hydration, weather awareness. "
            f"{get_weather_info(data['weather'])} "
            "Start early, pace yourself, and never ignore warning signs."
        ),

        "emergency": lambda: (
            f"IMPORTANT: {get_emergency_info(data['emergency'])} "
            "If symptoms worsen, descend or seek help immediately. Safety always comes first."
        ),

        "festival": lambda: (
            f"Festival seasons can impact routes and logistics. {get_festival_info(data['festivals'])} "
            "Expect crowds and plan transport and accommodation early."
        ),

        "crowd": lambda: (
            f"{get_crowd_info(data['crowd'])} "
            "For outdoor activities, shoulder seasons often give the best balance of weather and space."
        ),

        "general": lambda: (
            "India offers adventure across mountains, forests, coasts, and deserts. "
            "From long treks to short nature escapes, preparation is key. "
            "Tell me what kind of terrain excites you."
        )
    }

    return responses.get(intent, responses["general"])()

# ------------------------------------------------------------------
# CULTURAL EXPERT (India-wide, comparative)
# ------------------------------------------------------------------

def generate_cultural_expert_response(message: str, intent: str, **data) -> str:
    """Cultural Expert persona - informative, historical, comparative"""

    responses = {
        "weather": lambda: (
            f"Climate has shaped Indian culture for millennia. {get_weather_info(data['weather'])} "
            "Monsoons, winters, and dry seasons influence agriculture, architecture, and festivals."
        ),

        "itinerary": lambda: (
            "India's cultural journeys can be organized by region, dynasty, or tradition. "
            "Temple circuits, heritage cities, and pilgrimage routes evolved over centuries, "
            "reflecting political and spiritual history."
        ),

        "spiritual": lambda: (
            "Indian spirituality is not a single tradition but a constellation of philosophies. "
            "Texts like the Vedas, Upanishads, Puranas, and Buddhist scriptures inform practices "
            "that vary widely across regions."
        ),

        "trekking": lambda: (
            f"Many trekking routes in India follow ancient trade paths or pilgrimage trails. "
            f"{get_weather_info(data['weather'])} "
            "These routes connect geography with history and living tradition."
        ),

        "emergency": lambda: (
            f"{get_emergency_info(data['emergency'])} "
            "Historically, inns, monasteries, and places of worship supported travelers — a tradition "
            "that modern infrastructure now complements."
        ),

        "festival": lambda: (
            f"Indian festivals often share common themes but differ by region. "
            f"{get_festival_info(data['festivals'])} "
            "These variations reveal local history, climate, and belief systems."
        ),

        "crowd": lambda: (
            f"{get_crowd_info(data['crowd'])} "
            "Crowd patterns today reflect ancient calendars combined with modern mobility."
        ),

        "general": lambda: (
            "India's cultural heritage spans thousands of years — shaped by empires, philosophies, "
            "trade, and geography. Languages, rituals, food, and art forms change every few hundred "
            "kilometers, creating one of the world's richest living cultures."
        )
    }

    return responses.get(intent, responses["general"])()

# Helper functions to format mock data

def get_weather_info(weather_data: Dict) -> str:
    """Format weather information"""
    if not weather_data or "locations" not in weather_data:
        return "Current weather looks good for travel!"
    
    locations = weather_data["locations"][:2]  # Show first 2 locations
    info = []
    for loc in locations:
        info.append(f"{loc['location']}: {loc['temperature']}, {loc['condition']}")
    
    return " | ".join(info) + "."

def get_crowd_info(crowd_data: Dict) -> str:
    """Format crowd information"""
    if not crowd_data or "locations" not in crowd_data:
        return "Crowd levels are moderate right now."
    
    locations = crowd_data["locations"][:2]
    info = []
    for loc in locations:
        info.append(f"{loc['location']} is currently {loc['level'].lower()}")
    
    return " | ".join(info) + "."

def get_festival_info(festival_data: Dict) -> str:
    """Format festival information"""
    if not festival_data or "festivals" not in festival_data:
        return "Several festivals take place across different regions of India."
    
    festivals = festival_data["festivals"][:2]
    info = []
    for fest in festivals:
        info.append(f"{fest['name']} ({fest['date']}) - {fest['description']}")
    
    return " Next up: " + " | ".join(info) + "."

def get_emergency_info(emergency_data: Dict) -> str:
    """Format emergency information"""
    if not emergency_data or "contacts" not in emergency_data:
        return "Emergency services are available across India."
    
    contacts = emergency_data["contacts"][:2]
    info = []
    for contact in contacts:
        info.append(f"{contact['service']}: {contact['number']}")
    
    return " | ".join(info) + ". Keep these handy!"
