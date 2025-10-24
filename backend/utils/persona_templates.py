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
    # Load relevant mock data
    weather_data = load_mock_data("weather")
    crowd_data = load_mock_data("crowd")
    festival_data = load_mock_data("festivals")
    emergency_data = load_mock_data("emergency")
    
    # Response generators for each persona
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

def generate_local_guide_response(message: str, intent: str, **data) -> str:
    """Local Guide persona - friendly, practical, conversational"""
    
    responses = {
        "weather": lambda: f"Hey there! Let me check the weather for you. {get_weather_info(data['weather'])} I'd suggest carrying layers - mountain weather can be unpredictable! Also, don't forget sunscreen even on cloudy days. The UV rays at high altitude are no joke!",
        
        "itinerary": lambda: f"Great question! For Char Dham, I'd recommend at least 10-12 days to do it comfortably. Start with Yamunotri (the easiest), then Gangotri, followed by Kedarnath, and finally Badrinath. The roads between these places are scenic but winding, so factor in travel time. Pro tip: Book your helicopter tickets in advance if you're short on time for Kedarnath!",
        
        "spiritual": lambda: f"The spiritual energy here is incredible! Each Char Dham temple has its own unique significance. Badrinath is dedicated to Lord Vishnu, while Kedarnath is one of the 12 Jyotirlingas of Lord Shiva. The best time for darshan is early morning - you'll beat the crowds and experience the serene atmosphere with the morning aarti. Trust me, it's magical!",
        
        "trekking": lambda: f"Ah, a fellow adventure lover! The Valley of Flowers trek is moderate difficulty - perfect for beginners with decent fitness. You'll need good trekking shoes, warm clothes (even in summer), rain gear, and a basic first-aid kit. {get_weather_info(data['weather'])} The trek is about 4-5 hours from Ghangaria. Start early to catch the flowers in full bloom!",
        
        "emergency": lambda: f"Safety first! Here's what you need to know: {get_emergency_info(data['emergency'])} Always keep these numbers handy. For altitude sickness, descend immediately and seek medical help. I also recommend travel insurance that covers high-altitude regions.",
        
        "festival": lambda: f"You're in for a treat! {get_festival_info(data['festivals'])} The local festivals are vibrant and give you a real taste of Uttarakhand's culture. During Ganga Dussehra in Rishikesh, the evening Ganga Aarti is absolutely mesmerizing - don't miss it!",
        
        "crowd": lambda: f"Good thinking to check crowd levels! {get_crowd_info(data['crowd'])} If you want a peaceful experience, I'd suggest visiting in May or September-October. The weather is pleasant and you'll avoid the peak rush.",
        
        "general": lambda: f"Welcome to Uttarakhand - Dev Bhoomi, the Land of Gods! This place has everything: spiritual temples, adventure treks, stunning valleys, and the warmest people you'll ever meet. Whether you're here for Char Dham pilgrimage, trekking in the Himalayas, or just to relax in hill stations like Mussoorie and Nainital, you're going to love it. What interests you most? I'm here to help plan your perfect trip!"
    }
    
    return responses.get(intent, responses["general"])()

def generate_spiritual_teacher_response(message: str, intent: str, **data) -> str:
    """Spiritual Teacher persona - serene, reflective, philosophical"""
    
    sanskrit_quotes = [
        "ॐ नमः शिवाय (Om Namah Shivaya) - I bow to Lord Shiva",
        "सत्यम् शिवम् सुन्दरम् (Satyam Shivam Sundaram) - Truth, Auspiciousness, Beauty",
        "तत् त्वम् असि (Tat Tvam Asi) - You are That",
        "हर हर गंगे (Har Har Gange) - Glory to Mother Ganga"
    ]
    
    responses = {
        "weather": lambda: f"The elements guide our journey, dear seeker. {get_weather_info(data['weather'])} Remember, every weather condition has its own beauty - rain purifies, sun energizes, and snow brings stillness. Embrace what nature offers. {random.choice(sanskrit_quotes)}",
        
        "itinerary": lambda: f"Your pilgrimage to Char Dham is not merely a journey through mountains, but an inward voyage to the divine self. Begin with Yamunotri, where Goddess Yamuna blesses with purity. Progress to Gangotri, the source of sacred Ganga. Then ascend to Kedarnath, where Lord Shiva resides in his primal form. Complete your circle at Badrinath, Lord Vishnu's meditation abode. {random.choice(sanskrit_quotes)} Take your time - the journey matters more than the destination.",
        
        "spiritual": lambda: f"In these sacred Himalayas, every stone whispers ancient wisdom. Kedarnath, one of the twelve Jyotirlingas, marks the place where Lord Shiva appeared in the form of a bull's hump. The Pandavas sought his blessings here after the great war. Badrinath shelters the sacred murti of Lord Vishnu in his meditation pose. It is said that Lord Shiva resides in Kedarnath during winter, while Badrinath represents Vishnu's eternal presence. {random.choice(sanskrit_quotes)} These are not mere temples but cosmic energy centers where heaven meets earth.",
        
        "trekking": lambda: f"The mountains are the abode of the divine. As you trek through these sacred paths, each step is a meditation, each breath a prayer. The Valley of Flowers is called 'Nandan Kanan' - the Garden of Lord Indra. {get_weather_info(data['weather'])} Walk mindfully, honor the silence, and you shall find not just flowers, but your inner self blooming. {random.choice(sanskrit_quotes)}",
        
        "emergency": lambda: f"While we walk the spiritual path, we must also honor this physical vessel. {get_emergency_info(data['emergency'])} The body is the temple of the soul. Care for it wisely. In high altitudes, listen to your body's wisdom. Altitude sickness is nature's way of asking you to slow down and acclimatize. {random.choice(sanskrit_quotes)}",
        
        "festival": lambda: f"Our festivals are sacred rhythms connecting us to cosmic cycles. {get_festival_info(data['festivals'])} Ganga Dussehra celebrates Mother Ganga's descent from Lord Shiva's locks to earth. During Maha Shivaratri, the energy at Shiva temples intensifies. Participate not as a spectator but as a devotee - immerse yourself fully. {random.choice(sanskrit_quotes)}",
        
        "crowd": lambda: f"Solitude is the soul's sanctuary. {get_crowd_info(data['crowd'])} While the crowds during Char Dham season bring collective devotion, true darshan often happens in quieter moments. Consider visiting during shoulder months - May or September. The divine presence is constant; the crowds are not. {random.choice(sanskrit_quotes)}",
        
        "general": lambda: f"Welcome, blessed soul, to Uttarakhand - Dev Bhoomi, where the divine and earthly realms merge. These mountains have witnessed millennia of tapasya (penance), meditation, and enlightenment. The great sages meditated here, Lord Shiva resides in Kailash beyond these peaks, and the sacred Ganga flows from Gangotri. Every element here carries spiritual vibration. {random.choice(sanskrit_quotes)} Open your heart, and these mountains will speak to your soul."
    }
    
    return responses.get(intent, responses["general"])()

def generate_trek_companion_response(message: str, intent: str, **data) -> str:
    """Trek Companion persona - adventurous, concise, safety-focused"""
    
    responses = {
        "weather": lambda: f"Weather check! {get_weather_info(data['weather'])} Quick tip: Always pack for the worst weather and hope for the best. Carry rain gear even if forecast looks clear. Mountains = unpredictable weather. Stay safe out there!",
        
        "itinerary": lambda: f"Char Dham circuit? That's a solid adventure! 10-12 days minimum. Route: Yamunotri → Gangotri → Kedarnath → Badrinath. Total distance: ~1,500 km. Road conditions: Average. Best months: May-June, Sep-Oct. Kedarnath involves a 16 km trek (or heli option). Fitness level required: Moderate. Book accommodations in advance!",
        
        "spiritual": lambda: f"The spiritual stuff? Each Dham sits at serious altitude: Yamunotri (3,293m), Gangotri (3,100m), Kedarnath (3,583m), Badrinath (3,300m). That's high enough for altitude concerns! The temples have incredible mountain backdrops. Early morning visits = less crowd + stunning sunrise views. Don't forget your camera!",
        
        "trekking": lambda: f"Valley of Flowers trek! Awesome choice. Quick specs: Distance: 13 km (one way from Ghangaria). Difficulty: Moderate. Duration: 4-5 hours. {get_weather_info(data['weather'])} Gear checklist: Sturdy trekking boots, trekking poles, rain jacket, warm layers, sun protection, water bottle, energy bars, basic med-kit. Start at dawn - afternoon rains are common. Let's do this!",
        
        "emergency": lambda: f"CRITICAL INFO - Save these! {get_emergency_info(data['emergency'])} Altitude sickness symptoms: Headache, nausea, dizziness, fatigue. Action: DESCEND immediately. No heroics. Carry Diamox if prescribed. Stay hydrated. Acclimatize properly. Your safety > summit/destination. Always!",
        
        "festival": lambda: f"Festival season can affect your trek logistics! {get_festival_info(data['festivals'])} Expect: Higher crowds, booked accommodations, increased prices. Upside: Amazing cultural experience, vibrant atmosphere. Book everything well in advance. Roads might be congested. Plan accordingly!",
        
        "crowd": lambda: f"Crowd intel: {get_crowd_info(data['crowd'])} Peak season (May-June): PACKED. Monsoon (July-Aug): Avoid - landslides, road closures. Best window: Sep-Oct - great weather, moderate crowds. Off-season: Nov-Apr (Most routes closed due to snow). Plan smart!",
        
        "general": lambda: f"Uttarakhand = Adventure paradise! Options: Char Dham pilgrimage trek, Valley of Flowers, Roopkund Mystery Lake, Kedarkantha winter trek, Har Ki Dun valley, Nanda Devi Base Camp. Activities: Trekking, camping, river rafting (Rishikesh), skiing (Auli), paragliding. Altitude range: 300m to 7,800m. Best base camps: Rishikesh, Dehradun, Joshimath. What's your adventure style? Let's gear up!"
    }
    
    return responses.get(intent, responses["general"])()

def generate_cultural_expert_response(message: str, intent: str, **data) -> str:
    """Cultural Expert persona - informative, mythological storytelling"""
    
    responses = {
        "weather": lambda: f"The climate of Uttarakhand is deeply connected to its mythology. {get_weather_info(data['weather'])} In ancient texts, it is said that Lord Indra, the God of Rain, showers his blessings upon these sacred mountains during the monsoon. The snow-capped peaks are believed to be the abode of the gods, where eternal winter preserves their divine presence.",
        
        "itinerary": lambda: f"The Char Dham Yatra is steeped in legend and history. According to Hindu mythology, this pilgrimage circuit was established by Adi Shankacharya in the 8th century CE to revive Hinduism. Yamunotri honors Goddess Yamuna, daughter of Sun God Surya. Gangotri marks where King Bhagirath's penance brought Ganga from heaven. Kedarnath houses the hump of the divine bull - Lord Shiva in disguise from the Pandavas. Badrinath is where Lord Vishnu meditated under a Badri tree, protected by a serpent. Each site connects to epic tales from Mahabharata and Puranas.",
        
        "spiritual": lambda: f"Allow me to share the profound legends. Kedarnath's origin lies in the Mahabharata era. After the great war, the Pandavas sought Lord Shiva's forgiveness for killing their kin. Shiva, unwilling to forgive them easily, took the form of a bull and dove into the ground. His hump emerged at Kedarnath, while other body parts appeared at the Panch Kedar sites. The temple was built by the Pandavas themselves! Badrinath has an equally fascinating tale - Lord Vishnu meditated here for thousands of years, and Goddess Lakshmi transformed into a Badri tree to shade him from harsh elements. These are not mere stories; they are the cultural DNA of this sacred land.",
        
        "trekking": lambda: f"The mountains of Uttarakhand feature prominently in our epics and puranas. The Valley of Flowers, known as 'Nandan Kanan' in Hindu mythology, is believed to be where celestial beings - Gandharvas and Apsaras - would descend. The Roopkund trek leads to the mysterious lake filled with ancient skeletons, locally called 'Mystery Lake' - research suggests they're from a 9th-century pilgrimage that met with disaster. {get_weather_info(data['weather'])} Every trail here has been walked by sages, kings, and pilgrims for millennia. You're literally walking through living history!",
        
        "emergency": lambda: f"In ancient times, pilgrims relied on local communities and ashrams for emergency care. The tradition of 'Atithi Devo Bhava' (Guest is God) ensured travelers were helped. Today, modern facilities complement this tradition: {get_emergency_info(data['emergency'])} The local communities still maintain rest houses called 'Dharamshalas' and provide aid. This cultural ethic of helping pilgrims continues from ages past.",
        
        "festival": lambda: f"Ah, the festivals! Each celebration here connects to ancient mythological events. {get_festival_info(data['festivals'])} Ganga Dussehra commemorates the day Goddess Ganga descended to earth from Lord Shiva's matted locks, as chronicled in the Bhagavata Purana. Maha Shivaratri celebrates Lord Shiva's cosmic dance and his marriage to Goddess Parvati - the energy at Himalayan Shiva temples is extraordinary this day. Kumbh Mela, held in Haridwar every 12 years, originates from the mythological churning of the ocean (Samudra Manthan) when drops of immortal nectar (amrit) fell at four locations. These festivals are living bridges to our 5,000-year-old Vedic civilization!",
        
        "crowd": lambda: f"The pilgrimage patterns have historical roots. {get_crowd_info(data['crowd'])} Traditionally, the Char Dham temples open on Akshaya Tritiya (April/May) and close on Diwali (Oct/Nov) due to heavy snowfall. This six-month window creates the peak season rush. In ancient times, only the most devoted made this arduous journey on foot, taking months. Today's accessibility has increased footfall significantly. Visiting during shoulder seasons offers a more contemplative experience, closer to how ancient pilgrims would have experienced these sacred sites.",
        
        "general": lambda: f"Welcome to Uttarakhand - in our ancient texts, this region is called 'Dev Bhoomi' and 'Kedarkhand.' The Skanda Purana dedicates entire chapters to these sacred mountains. This is where the Ganga descends, where Shiva meditated, where Pandavas walked, and where countless Rishis attained enlightenment. The cultural tapestry includes: Char Dham temples with 1,000+ year history, Panch Prayag (five sacred river confluences), Panch Kedar and Panch Badri temple circuits, ancient pilgrimage routes like the Nanda Devi Raj Jat (held every 12 years), traditional Garhwali and Kumaoni cultures with unique dance forms like Langvir Nritya and Chhopati. Every rock, river, and peak here has a story spanning millennia. What aspect of this magnificent cultural heritage intrigues you most?"
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
        return "Several beautiful festivals happen throughout the year here!"
    
    festivals = festival_data["festivals"][:2]
    info = []
    for fest in festivals:
        info.append(f"{fest['name']} ({fest['date']}) - {fest['description']}")
    
    return " Next up: " + " | ".join(info) + "."

def get_emergency_info(emergency_data: Dict) -> str:
    """Format emergency information"""
    if not emergency_data or "contacts" not in emergency_data:
        return "Emergency services are available throughout the region."
    
    contacts = emergency_data["contacts"][:2]
    info = []
    for contact in contacts:
        info.append(f"{contact['service']}: {contact['number']}")
    
    return " | ".join(info) + ". Keep these handy!"
