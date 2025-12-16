import requests
import json

API_BASE = "http://localhost:8000/api/rag"

# Sample Uttarakhand tourism data
sample_data = [
    {
        "title": "Kedarnath Temple Information",
        "content": "Kedarnath Temple is located at 3,583m altitude. Temple opens from Akshaya Tritiya (April/May) to Diwali (October/November). The 16 km trek from Gaurikund takes 6-7 hours. Helicopter services available from Phata, Sersi, and Guptkashi. Accommodation available at Kedarnath and Gaurikund. Temperature ranges from 0°C to 18°C.",
        "content_type": "spiritual"
    },
    {
        "title": "Badrinath Pilgrimage Guide",
        "content": "Badrinath Temple dedicated to Lord Vishnu, located at 3,300m. Accessible by road from Rishikesh (300 km, 10 hours). Temple remains open same season as Kedarnath. Key attractions: Tapt Kund (hot springs), Brahma Kapal, Mana Village (last Indian village). Weather: Cold throughout the year, carry warm clothes.",
        "content_type": "spiritual"
    },
    {
        "title": "Rishikesh Adventure Activities",
        "content": "Rishikesh offers river rafting on Ganga (Grade I to IV rapids), bungee jumping (83m India's highest), flying fox, zip-lining, camping. Best season: September to June. River rafting: ₹500-1500 per person. Bungee jumping: ₹3500. Safety gear provided by licensed operators.",
        "content_type": "trekking"
    },
    {
        "title": "Valley of Flowers National Park",
        "content": "UNESCO World Heritage Site featuring 500+ flower species. Trek: 13 km from Ghangaria base camp. Blooming season: July-September. Trek difficulty: Moderate. Permit required: ₹150 Indians, ₹600 foreigners. Stay at Ghangaria. Restricted area, camping not allowed inside valley.",
        "content_type": "trekking"
    },
    {
        "title": "Uttarakhand Tourism Helpline",
        "content": "24x7 Tourism Helpline: 1364. Emergency Services: Police 100, Ambulance 108, Disaster Management 1070. Online portal: uttarakhandtourism.gov.in for Char Dham registration, hotel bookings, permits. COVID-19 guidelines: Check latest protocols before travel.",
        "content_type": "government"
    },
    {
        "title": "Garhwali Culture and Festivals",
        "content": "Major festivals: Ganga Dussehra (June), Harela (July), Nanda Devi Raj Jat (every 12 years), Phool Dei (spring). Traditional dance: Langvir Nritya, Barada Nati. Cuisine: Kafuli, Chainsoo, Jhangora, Singal, Arsa. Traditional attire: Ghagra-Pichora for women, Churidar-Kurta for men.",
        "content_type": "cultural"
    },
    {
        "title": "Mussoorie Hill Station",
        "content": "Queen of Hills, located at 2,005m altitude. Distance from Dehradun: 35 km. Key attractions: Kempty Falls, Gun Hill, Lal Tibba, Camel's Back Road, Mall Road. Best season: March-June, September-November. Activities: Cable car rides, horse riding, shopping. Average temperature: 10°C-25°C.",
        "content_type": "general"
    },
    {
        "title": "Haridwar Religious Significance",
        "content": "One of seven holiest cities in Hinduism. Har Ki Pauri: Daily Ganga Aarti at sunset (6-7 PM). Kumbh Mela held every 12 years (next 2028). Ardh Kumbh every 6 years. Key temples: Mansa Devi, Chandi Devi, Maya Devi. Distance from Delhi: 220 km. Well-connected by train and road.",
        "content_type": "spiritual"
    }
]

# Load data
for item in sample_data:
    print(f"Adding: {item['title']}...")
    response = requests.post(
        f"{API_BASE}/add-text-content",
        json=item
    )
    result = response.json()
    print(f"  ✓ Added {result.get('chunks_count', 0)} chunks to {result.get('collection', 'unknown')}")
    print()

print(" Sample data loaded successfully!")

# Verify
response = requests.get(f"{API_BASE}/content-stats")
stats = response.json()
print(f"\n📊 Total documents in vector DB: {stats.get('total_documents', 0)}")
print(f"Collections: {list(stats.get('collections', {}).keys())}")
