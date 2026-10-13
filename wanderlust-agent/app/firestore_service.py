"""Firestore database client and data access layer for Wanderlust Agent."""
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Explicit hardcoded project ID so Firestore resolves (default) correctly
# both locally and on Agent Platform (where GOOGLE_CLOUD_PROJECT is the project number).
FIRESTORE_PROJECT = "qwiklabs-gcp-04-d4567446a77e"
DESTINATIONS_COLLECTION = "destinations"


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client pinned to the explicit project ID."""
    return firestore.Client(project=FIRESTORE_PROJECT)


def list_destinations(max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetches destinations from the Firestore catalog."""
    db = get_firestore_client()
    docs = db.collection(DESTINATIONS_COLLECTION).limit(max_results).stream()
    return [doc.to_dict() for doc in docs]


def search_destinations_by_vibe(keyword: str) -> List[Dict[str, Any]]:
    """Searches destinations matching a vibe, keyword, or category."""
    db = get_firestore_client()
    docs = db.collection(DESTINATIONS_COLLECTION).stream()
    kw = keyword.lower().strip()
    results = []
    for doc in docs:
        data = doc.to_dict()
        vibe = data.get("vibe", "").lower()
        category = data.get("category", "").lower()
        name = data.get("name", "").lower()
        description = data.get("description", "").lower()
        if kw in vibe or kw in category or kw in name or kw in description:
            results.append(data)
    return results


def add_custom_destination(
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
    """Adds or updates a destination in the Firestore catalog."""
    db = get_firestore_client()
    doc_ref = db.collection(DESTINATIONS_COLLECTION).document(destination_id)
    doc_data = {
        "id": destination_id,
        "name": name,
        "category": category,
        "vibe": vibe,
        "estimated_cost_tier": estimated_cost_tier,
        "duration_hours": duration_hours,
        "distance_miles": distance_miles,
        "description": description,
        "highlights": highlights or [],
    }
    doc_ref.set(doc_data)
    return {"status": "success", "destination": doc_data}
