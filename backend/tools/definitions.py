# tools/definitions.py
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"}
                },
                "required": ["latitude", "longitude"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Get latitude and longitude for a place name",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The city or place name"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_treks",
            "description": "Search for trekking trails and hiking routes in India. Returns detailed trek information including difficulty, duration, altitude, best time to visit, and descriptions. Use this for ANY trek-related queries including 'treks near X', 'best treks in Y', 'tell me about Z trek'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Indian state or region name (e.g. 'Himachal Pradesh', 'Uttarakhand', 'Ladakh', 'Sikkim', 'Kashmir', 'Maharashtra', 'Karnataka'). Extract from queries like 'treks near Agra' -> 'Uttarakhand' (nearest trekking state)."
                    },
                    "trek_name": {
                        "type": "string",
                        "description": "Specific trek name to search for (e.g. 'Hampta Pass', 'Valley of Flowers', 'Kedarnath Trek', 'Roopkund'). Only use if user mentions a specific trek name."
                    }
                },
            "required": []
            }
        }
    }
]
