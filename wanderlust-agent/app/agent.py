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

from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.firestore_service import (
    FIRESTORE_PROJECT,
    add_custom_destination,
    list_destinations,
    search_destinations_by_vibe,
)
from app.travel_tools import (
    get_live_weather,
    generate_trip_postcard,
    generate_trip_video,
    discover_nearby_attractions,
)

MODEL = "gemini-3.8-flash"


def get_all_destinations(max_results: int = 10) -> List[Dict[str, Any]]:
    """Retrieves curated day-trip destinations from the Firestore catalog.

    Args:
        max_results: Maximum number of destinations to retrieve. Defaults to 10.

    Returns:
        A list of destination dictionaries with details such as name, vibe,
        cost tier, duration, distance, and highlights.
    """
    return list_destinations(max_results=max_results)


def search_destinations(query: str) -> List[Dict[str, Any]]:
    """Searches the day-trip catalog by vibe, scenery, interest, or keyword (e.g. 'coastal', 'wine', 'hiking').

    Args:
        query: The vibe or keyword to search for (e.g., 'forest', 'romantic', 'ocean', 'relaxed').

    Returns:
        A list of matching destination items from the database.
    """
    return search_destinations_by_vibe(keyword=query)


def save_destination(
    destination_id: str,
    name: str,
    category: str,
    vibe: str,
    estimated_cost_tier: str,
    duration_hours: int,
    distance_miles: int,
    description: str,
    highlights: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Adds a new day-trip destination to the Firestore catalog.

    Args:
        destination_id: Unique slug identifier for the destination (e.g. 'monterey-bay-aquarium').
        name: Human-readable name of the destination.
        category: Category (e.g. 'Nature', 'Coastal', 'Culinary', 'Adventure').
        vibe: Descriptive vibe tags (e.g. 'scenic, ocean, marine wildlife').
        estimated_cost_tier: '$', '$$', or '$$$'.
        duration_hours: Recommended trip duration in hours.
        distance_miles: Approximate distance in miles from the Bay Area origin.
        description: Summary of what makes this day-trip special.
        highlights: Key sights or activities at the destination.

    Returns:
        A confirmation dictionary with the saved destination record.
    """
    return add_custom_destination(
        destination_id=destination_id,
        name=name,
        category=category,
        vibe=vibe,
        estimated_cost_tier=estimated_cost_tier,
        duration_hours=duration_hours,
        distance_miles=distance_miles,
        description=description,
        highlights=highlights,
    )


def fetch_live_weather(destination_name: str) -> Dict[str, Any]:
    """Fetches real-time weather conditions, temperature, humidity, wind, and forecast for any destination.

    Args:
        destination_name: Name of the destination or area (e.g. 'Muir Woods', 'Napa Valley', 'Half Moon Bay', 'Point Reyes').

    Returns:
        A dictionary with live weather data and an outdoor excursion advisory.
    """
    return get_live_weather(destination_name)


def create_scenic_postcard(
    destination_name: str,
    tool_context: ToolContext,
    style_or_vibe: str = "vintage travel poster",
) -> Dict[str, Any]:
    """Generates an AI scenic postcard image of a destination and stores it in the public Cloud Storage bucket.
    The generated image is saved as a session artifact for the Playground's Artifacts panel and uploaded to GCS.

    Args:
        destination_name: The destination or landmark to depict (e.g. 'Point Reyes Lighthouse', 'Muir Woods Redwoods').
        tool_context: The ADK session ToolContext (injected automatically).
        style_or_vibe: Artistic style (e.g. 'vintage travel poster', 'golden hour photography', 'cozy watercolor').

    Returns:
        A dictionary with the public image URL, description, and status.
    """
    return generate_trip_postcard(destination_name, style_or_vibe=style_or_vibe, tool_context=tool_context)


def create_scenic_video(
    destination_name: str,
    tool_context: ToolContext,
    scene_description: str = "scenic cinematic view",
) -> Dict[str, Any]:
    """Generates a short video for a destination item using Google's Omni model (gemini-omni-flash-preview)
    in the global region.
    Saves the generated video as an artifact with tool_context.save_artifact so it shows up in the Playground's
    Artifacts panel, and uploads the video bytes to the public Cloud Storage bucket, returning its public URL.

    Args:
        destination_name: The destination or landmark to depict (e.g. 'Muir Woods Redwood Cathedral', 'Point Reyes Ocean Waves').
        tool_context: The ADK session ToolContext (injected automatically).
        scene_description: Visual description of the short video clip (e.g. 'cinematic waves crashing against coastal bluffs at sunset').

    Returns:
        A dictionary with the public video URL, artifact filename, status, and message.
    """
    return generate_trip_video(
        destination_name=destination_name,
        scene_description=scene_description,
        tool_context=tool_context,
    )


def find_nearby_points_of_interest(location_name: str, limit: int = 4) -> Dict[str, Any]:
    """Finds real historical sights, trailheads, and points of interest near any destination using the public Wikipedia GeoSearch API.

    Args:
        location_name: Name of the destination or area (e.g. 'Muir Woods', 'Point Reyes', 'Half Moon Bay', 'Napa Valley').
        limit: Maximum number of points of interest to return (default 4).

    Returns:
        A dictionary with nearby attractions, summaries, and distance in miles.
    """
    return discover_nearby_attractions(location_name, limit=limit)


async def generate_memories_callback(callback_context: CallbackContext):
    """After each turn, send the session events to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name="projects/362824801733/locations/us-east1/reasoningEngines/2454652012428525568/sandboxEnvironments/4017958535521370112"
    ),
    after_agent_callback=generate_memories_callback,
    instruction="""You are Wanderlust, an expert AI travel concierge specializing in curated day-trips.
You help travelers discover, customize, and plan unforgettable day-trips based on their mood, interests, and budget.
You remember the user's stated travel preferences, dietary restrictions, favorite vibes, budget constraints, and past trips from previous conversations, and use them to personalize your recommendations.

Capabilities and Tool Guidelines:
1. Catalog Queries: Always query the Firestore catalog using search_destinations or get_all_destinations to recommend real places.
2. Saving Favorites: If the traveler wants to save a custom spot or new recommendation, use save_destination.
3. Live Weather: Whenever asked about weather, current conditions, or what to wear/pack, call fetch_live_weather to provide actual real-time data.
4. Visual Postcards: When the user asks for a photo, postcard, picture, or visual of a destination, call create_scenic_postcard and embed the resulting image URL in your response using markdown syntax: ![Destination](image_url).
5. Scenic Videos: When the user asks for a video, motion clip, or animation of a destination or item, call create_scenic_video and provide the public video URL.
6. Nearby Points of Interest: When the user asks what else is nearby, what sights to see in the area, or trailheads/landmarks nearby, call find_nearby_points_of_interest to fetch real geolocated places.
7. Safe Code Execution: You have access to a secure Python sandbox. When calculations, data conversions, gas/mileage budget modeling, or custom algorithms are needed, write and execute Python code.

Be enthusiastic, inspiring, and concise. Highlight drive times, vibes, and must-see stops.""",
    tools=[
        PreloadMemoryTool(),
        get_all_destinations,
        search_destinations,
        save_destination,
        fetch_live_weather,
        create_scenic_postcard,
        create_scenic_video,
        find_nearby_points_of_interest,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
