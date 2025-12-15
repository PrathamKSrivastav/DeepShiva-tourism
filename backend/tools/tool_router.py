def decide_tools(persona: str, intent: str, message: str) -> list[str]:
    tools = []

    weather_intents = {
        "weather",
        "current_weather",
        "local_weather",
        "forecast",
        "climate",
        "trekking",
        "itinerary"
    }

    if intent in weather_intents:
        tools.extend(["geocoding", "weather"])

    return list(set(tools))
