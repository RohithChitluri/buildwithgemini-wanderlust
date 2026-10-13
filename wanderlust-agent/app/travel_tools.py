import base64
import json
import re
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional
from google import genai
from google.genai import types
from google.cloud import storage

PROJECT_ID = "qwiklabs-gcp-04-d4567446a77e"
BUCKET_NAME = "wanderlust-assets-qwiklabs-gcp-04-d4567446a77e"

# Destination coordinates lookup for high accuracy, with fallback to SF area coords
DESTINATION_COORDINATES = {
    "point reyes": (38.0416, -122.8028),
    "point-reyes-seashore": (38.0416, -122.8028),
    "napa": (38.2975, -122.2869),
    "napa valley": (38.2975, -122.2869),
    "napa-valley-wine-country": (38.2975, -122.2869),
    "muir woods": (37.8970, -122.5811),
    "muir-woods-redwoods": (37.8970, -122.5811),
    "tamalpais": (37.9235, -122.5965),
    "sausalito": (37.8590, -122.4853),
    "sausalito-waterfront": (37.8590, -122.4853),
    "half moon bay": (37.4636, -122.4286),
    "half-moon-bay-coastal": (37.4636, -122.4286),
    "san francisco": (37.7749, -122.4194),
    "sf": (37.7749, -122.4194),
}

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def get_live_weather(location_or_destination: str) -> Dict[str, Any]:
    """Fetches real-time weather conditions from Open-Meteo for any trip destination.

    Args:
        location_or_destination: Name or ID of the destination (e.g. 'Muir Woods', 'Half Moon Bay', 'Napa').

    Returns:
        A dictionary with live weather data: temperature, apparent temperature, humidity,
        wind speed, precipitation, and condition description.
    """
    loc_key = location_or_destination.lower().strip()
    coords = None
    for name, c in DESTINATION_COORDINATES.items():
        if name in loc_key or loc_key in name:
            coords = c
            break

    if not coords:
        coords = (37.7749, -122.4194)  # Default Bay Area center

    lat, lon = coords
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph"
    )

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "WanderlustAgent/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
            current = payload.get("current", {})

            w_code = current.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(w_code, "Partly cloudy")

            return {
                "destination": location_or_destination,
                "temperature_f": current.get("temperature_2m"),
                "feels_like_f": current.get("apparent_temperature"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "wind_speed_mph": current.get("wind_speed_10m"),
                "precipitation_inches": current.get("precipitation"),
                "condition": condition,
                "advisory": "Great conditions for an outdoor day-trip!" if current.get("precipitation", 0) == 0 else "Pack a rain jacket or umbrella.",
            }
    except Exception as e:
        return {
            "destination": location_or_destination,
            "error": f"Failed to fetch live weather: {str(e)}",
            "fallback": "Standard pleasant coastal temperate conditions.",
        }


def generate_trip_postcard(
    destination_name: str,
    style_or_vibe: str = "vintage travel poster",
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generates an AI scenic postcard image for a destination using gemini-3.1-flash-lite-image in the global region.
    Saves the image as a session artifact and uploads it to public Cloud Storage.

    Args:
        destination_name: The destination to depict (e.g. 'Muir Woods Redwood Cathedral', 'Point Reyes Lighthouse').
        style_or_vibe: Aesthetic vibe (e.g. 'vintage travel poster', 'golden hour photography', 'watercolor landscape').
        tool_context: The ADK ToolContext injected automatically by the framework.

    Returns:
        A dictionary with the public image URL, description, and status.
    """
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "-", destination_name.lower().strip())
    artifact_filename = f"{clean_name}.jpg"
    storage_object_name = f"postcards/{clean_name}-{uuid.uuid4().hex[:6]}.jpg"

    prompt = (
        f"A beautiful, high quality artistic {style_or_vibe} featuring {destination_name}. "
        "Scenic landscape composition, vibrant colors, atmospheric lighting, no watermarks, no distorted artifacts."
    )

    try:
        # Generate image using Vertex AI gemini-3.1-flash-lite-image in global location
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break
            if image_bytes:
                break

        if not image_bytes:
            return {
                "status": "error",
                "message": "Model generated response but did not include inline image data.",
            }

        # 1. Save artifact with tool_context so it shows in Playground's Artifacts panel
        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

        # 2. Upload same bytes directly to the public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{storage_object_name}"

        return {
            "status": "success",
            "destination": destination_name,
            "artifact_filename": artifact_filename,
            "image_url": public_url,
            "markdown_preview": f"![{destination_name}]({public_url})",
            "message": f"Successfully generated postcard for {destination_name}, saved to artifacts, and uploaded to Cloud Storage.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Postcard generation failed: {str(e)}",
        }


def generate_trip_video(
    destination_name: str,
    scene_description: str = "scenic cinematic view",
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generates a short video for a destination item using Google's Omni model (gemini-omni-flash-preview)
    in the global region.
    Saves the generated video as an artifact with tool_context.save_artifact so it shows up in the Playground's
    Artifacts panel, and uploads the video bytes to the public Cloud Storage bucket, returning its public URL.

    Args:
        destination_name: The destination or attraction to depict (e.g. 'Muir Woods Redwood Cathedral', 'Point Reyes Ocean Waves').
        scene_description: Visual description of the short video clip (e.g. 'cinematic waves crashing against coastal bluffs at golden hour').
        tool_context: The ADK ToolContext injected automatically by the framework.

    Returns:
        A dictionary with the public video URL, artifact filename, status, and message.
    """
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "-", destination_name.lower().strip())
    artifact_filename = f"{clean_name}.mp4"
    storage_object_name = f"videos/{clean_name}-{uuid.uuid4().hex[:6]}.mp4"

    prompt = (
        f"A short cinematic high quality video of {destination_name}. {scene_description}. "
        "Smooth camera motion, vibrant atmospheric lighting, realistic detail, no watermarks."
    )

    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            timeout=180.0,
        )

        if not interaction or not interaction.output_video or not interaction.output_video.data:
            return {
                "status": "error",
                "message": "Omni model did not return video data in output_video.",
            }

        # Decode video bytes from base64 string
        raw_data = interaction.output_video.data
        if isinstance(raw_data, str):
            video_bytes = base64.b64decode(raw_data)
        else:
            video_bytes = bytes(raw_data)

        mime_type = interaction.output_video.mime_type or "video/mp4"

        # 1. Save artifact with tool_context.save_artifact for Playground Artifacts panel
        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

        # 2. Upload video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(storage_object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{storage_object_name}"

        return {
            "status": "success",
            "destination": destination_name,
            "artifact_filename": artifact_filename,
            "video_url": public_url,
            "message": f"Successfully generated short video for {destination_name}, saved to artifacts, and uploaded to Cloud Storage.",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Video generation failed: {str(e)}",
        }


def discover_nearby_attractions(location_or_destination: str, limit: int = 4) -> Dict[str, Any]:
    """Finds real nearby attractions, scenic sights, and historical points of interest using the public Wikipedia GeoSearch API.

    Args:
        location_or_destination: Name of the destination or area (e.g. 'Muir Woods', 'Point Reyes', 'Napa Valley').
        limit: Maximum number of points of interest to return (default 4).

    Returns:
        A dictionary with the location and a list of real nearby points of interest with summaries and distances.
    """
    loc_key = location_or_destination.lower().strip()
    coords = None
    for name, c in DESTINATION_COORDINATES.items():
        if name in loc_key or loc_key in name:
            coords = c
            break

    if not coords:
        coords = (37.7749, -122.4194)

    lat, lon = coords
    url = (
        f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch"
        f"&gscoord={lat}|{lon}&gsradius=10000&gslimit={limit}&format=json"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WanderlustDayTripPlanner/1.0 (contact: travel@buildwithgemini.demo)"},
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("geosearch", [])
            if not pages:
                return {
                    "destination": location_or_destination,
                    "attractions": [],
                    "message": f"No nearby points of interest found within 10km of {location_or_destination}.",
                }

            page_ids = "|".join(str(p["pageid"]) for p in pages)
            extract_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&pageids={page_ids}"
                "&prop=extracts&exintro=true&explaintext=true&exsentences=1&format=json"
            )
            req_extract = urllib.request.Request(
                extract_url,
                headers={"User-Agent": "WanderlustDayTripPlanner/1.0 (contact: travel@buildwithgemini.demo)"},
            )
            with urllib.request.urlopen(req_extract, timeout=6) as extract_resp:
                extract_data = json.loads(extract_resp.read().decode("utf-8")).get("query", {}).get("pages", {})

            attractions = []
            for p in pages:
                pid = str(p["pageid"])
                summary = extract_data.get(pid, {}).get("extract", "")
                attractions.append({
                    "title": p.get("title"),
                    "distance_miles": round(p.get("dist", 0) * 0.000621371, 1),
                    "summary": summary,
                })

            return {
                "destination": location_or_destination,
                "attractions": attractions,
            }

    except Exception as e:
        return {
            "destination": location_or_destination,
            "error": f"Failed to retrieve nearby points of interest: {str(e)}",
        }
