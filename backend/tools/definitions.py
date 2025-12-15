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
    }
]
