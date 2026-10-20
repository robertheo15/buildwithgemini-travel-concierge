# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any
from google.cloud import firestore

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.8-flash"
PROJECT_ID = "qwiklabs-gcp-03-cec237a37b41"
COLLECTION_NAME = "destinations"
AGENT_ENGINE_ID = "projects/679613387131/locations/us-central1/reasoningEngines/2261005199910895616"
MEMORY_BANK_ID = "2261005199910895616"
SANDBOX_RESOURCE_NAME = "projects/679613387131/locations/us-central1/reasoningEngines/2261005199910895616/sandboxEnvironments/8150210754994241536"

_db_client = None

def get_firestore_client() -> firestore.Client:
    """Return a lazy singleton Firestore client hardcoded to the specific project ID."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def list_destinations(style_filter: Optional[str] = None, max_budget_usd: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve curated travel destinations from the Firestore catalog with optional filtering.

    Args:
        style_filter: Optional keyword to filter destinations by travel style (e.g. 'food', 'nature', 'culture', 'adventure').
        max_budget_usd: Optional maximum average daily budget in USD to filter destinations.

    Returns:
        A list of matching destination records including name, country, description, budget tier, daily cost, and highlights.
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if max_budget_usd is not None and data.get("avg_daily_budget_usd", 0) > max_budget_usd:
            continue
        if style_filter:
            styles = [s.lower() for s in data.get("travel_style", [])]
            if style_filter.lower() not in styles and style_filter.lower() not in data.get("description", "").lower():
                continue
        results.append(data)
    return results


def get_destination_details(destination_id_or_name: str) -> Dict[str, Any]:
    """Get complete details for a specific destination by its ID or name from Firestore.

    Args:
        destination_id_or_name: The slug ID (e.g. 'kyoto-japan') or partial name of the destination.

    Returns:
        The full destination record, or an error message if not found.
    """
    db = get_firestore_client()
    # Try direct document lookup first
    slug = destination_id_or_name.strip().lower().replace(" ", "-")
    doc_ref = db.collection(COLLECTION_NAME).document(slug)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()

    # Fallback to query by name or id match
    docs = db.collection(COLLECTION_NAME).stream()
    query = destination_id_or_name.lower()
    for d in docs:
        data = d.to_dict()
        if (query in d.id.lower() or 
            query in data.get("name", "").lower() or 
            query in data.get("country", "").lower()):
            return data
    return {"error": f"Destination '{destination_id_or_name}' not found in the catalog."}


def add_destination(
    name: str,
    country: str,
    description: str,
    best_season: str,
    travel_styles: List[str],
    avg_daily_budget_usd: int,
    highlights: List[str],
    local_dishes: List[str],
) -> Dict[str, Any]:
    """Add a new custom destination to the Firestore catalog.

    Args:
        name: Name of the destination (e.g., 'Lisbon, Portugal').
        country: Country where the destination is located.
        description: Brief overview of the location and what makes it special.
        best_season: Recommended time of year to visit.
        travel_styles: List of styles/tags (e.g., ['food', 'historic', 'coastal']).
        avg_daily_budget_usd: Estimated average daily spending in USD.
        highlights: Key attractions or must-do activities.
        local_dishes: Notable regional foods or drinks to try.

    Returns:
        Confirmation status and the newly created destination record.
    """
    db = get_firestore_client()
    slug = name.strip().lower().replace(",", "").replace(" ", "-")
    data = {
        "id": slug,
        "name": name,
        "country": country,
        "description": description,
        "best_season": best_season,
        "travel_style": [s.strip().lower() for s in travel_styles],
        "budget_tier": "$" if avg_daily_budget_usd < 100 else ("$$" if avg_daily_budget_usd <= 200 else "$$$"),
        "avg_daily_budget_usd": avg_daily_budget_usd,
        "highlights": highlights,
        "local_dishes": local_dishes,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection(COLLECTION_NAME).document(slug).set(data)
    return {"status": "success", "message": f"Destination '{name}' saved successfully.", "destination": data}


def get_live_destination_weather(destination: str) -> Dict[str, Any]:
    """Fetch live real-world weather and forecast for any travel destination using the Open-Meteo public API.

    Args:
        destination: City or destination name (e.g., 'Kyoto', 'Reykjavik', 'Oaxaca', 'Rome', 'Banff').

    Returns:
        A dictionary with live weather metrics (temperature, humidity, wind speed, weather condition, forecast).
    """
    import json
    import urllib.parse
    import urllib.request

    try:
        # Step 1: Geocode city name to lat/lon
        city_encoded = urllib.parse.quote(destination.split(",")[0].strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_encoded}&count=1&language=en&format=json"
        geo_req = urllib.request.Request(geo_url, headers={"User-Agent": "TravelConcierge/1.0"})
        with urllib.request.urlopen(geo_req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        results = geo_data.get("results")
        if not results:
            return {"error": f"Could not find coordinates for destination '{destination}'."}

        place = results[0]
        lat = place["latitude"]
        lon = place["longitude"]
        resolved_name = f"{place.get('name')}, {place.get('country')}"

        # Step 2: Fetch current weather & 3-day forecast
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=3"
        )
        weather_req = urllib.request.Request(weather_url, headers={"User-Agent": "TravelConcierge/1.0"})
        with urllib.request.urlopen(weather_req, timeout=5) as resp:
            w_data = json.loads(resp.read().decode("utf-8"))

        current = w_data.get("current", {})
        temp_c = current.get("temperature_2m")
        temp_f = round((temp_c * 9 / 5) + 32, 1) if temp_c is not None else None

        wmo_codes = {
            0: "Clear sky ☀️",
            1: "Mainly clear 🌤️",
            2: "Partly cloudy ⛅",
            3: "Overcast ☁️",
            45: "Foggy 🌫️",
            51: "Light drizzle 🌦️",
            61: "Slight rain 🌧️",
            63: "Moderate rain 🌧️",
            71: "Slight snow 🌨️",
            80: "Rain showers 🌦️",
            95: "Thunderstorm ⛈️",
        }
        condition = wmo_codes.get(current.get("weather_code", 0), "Fair")

        return {
            "destination": resolved_name,
            "coordinates": {"latitude": lat, "longitude": lon},
            "condition": condition,
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "packing_tip": "Dress warm and bring layers" if (temp_c is not None and temp_c < 12) else (
                "Lightweight clothes, sun protection, and hydration" if (temp_c is not None and temp_c > 24) else
                "Comfortable walking shoes and a light jacket"
            ),
        }
    except Exception as e:
        return {"error": f"Failed to fetch live weather: {str(e)}"}


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a destination city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    q = query.lower()
    if "sf" in q or "san francisco" in q:
        tz_identifier = "America/Los_Angeles"
    elif "kyoto" in q or "tokyo" in q or "japan" in q:
        tz_identifier = "Asia/Tokyo"
    elif "reykjavik" in q or "iceland" in q:
        tz_identifier = "Atlantic/Reykjavik"
    elif "oaxaca" in q or "mexico" in q:
        tz_identifier = "America/Mexico_City"
    elif "banff" in q or "canada" in q:
        tz_identifier = "America/Edmonton"
    elif "rome" in q or "italy" in q:
        tz_identifier = "Europe/Rome"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def save_trip_itinerary(
    destination: str,
    days: int,
    title: str,
    daily_plan: List[Dict[str, Any]],
    estimated_total_usd: Optional[int] = None,
) -> Dict[str, Any]:
    """Save a planned trip itinerary to Firestore.

    Args:
        destination: Destination name or slug (e.g. 'Kyoto, Japan').
        days: Number of days in the itinerary.
        title: Catchy title for the trip (e.g. '3-Day Kyoto Cultural Deep Dive').
        daily_plan: List of day-by-day itineraries. Each day is a dictionary with keys:
                    'day' (int), 'theme' (str), 'activities' (list of str), and 'recommended_meals' (list of str).
        estimated_total_usd: Optional total estimated cost in USD.

    Returns:
        Confirmation status, trip ID, and the saved itinerary details.
    """
    db = get_firestore_client()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    slug_base = destination.strip().lower().replace(",", "").replace(" ", "-")
    trip_id = f"trip-{slug_base}-{int(datetime.datetime.now().timestamp())}"

    itinerary_data = {
        "id": trip_id,
        "destination": destination,
        "title": title,
        "days": days,
        "daily_plan": daily_plan,
        "estimated_total_usd": estimated_total_usd,
        "created_at": now_str,
    }
    db.collection("itineraries").document(trip_id).set(itinerary_data)
    return {
        "status": "success",
        "trip_id": trip_id,
        "message": f"Saved {days}-day itinerary for {destination} to Firestore.",
        "itinerary": itinerary_data,
    }


async def generate_memories_callback(callback_context: CallbackContext):
    """After each turn, send the session events to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

agent_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a knowledgeable and inspiring Travel Concierge assistant. "
        "You remember the traveler's stated preferences, dietary restrictions, preferred travel styles, "
        "and personal facts across conversations and use them to personalize your recommendations. "
        "CRITICAL: Always remember and prioritize all user allergies (e.g. food, peanut, seafood, gluten, drug, environmental). "
        "Whenever a user mentions any allergy or intolerance, ensure it is acknowledged, remembered across sessions, "
        "and strictly respected in every itinerary, restaurant recommendation, or food tip. Never recommend foods containing their allergens. "
        "You help travelers explore destinations, discover culinary specialties and key highlights, "
        "and plan vacations tailored to their preferences and budget. "
        "Use the destination catalog tools (list_destinations, get_destination_details, add_destination) "
        "to check and manage destination recommendations from the Firestore database. "
        "When a user asks to plan or build an itinerary for a destination, use save_trip_itinerary "
        "to create and save their tailored day-by-day plan to the Firestore itineraries collection. "
        "You can also check weather and local time for destinations. "
        "You have a secure Python code sandbox. If a user asks for complex budget calculations, cost modeling, "
        "or customized data analysis, write and execute Python code in the sandbox to calculate the exact results."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=agent_instruction,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        list_destinations,
        get_destination_details,
        add_destination,
        save_trip_itinerary,
        get_live_destination_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

