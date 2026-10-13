"""Seed destinations catalog into Firestore."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-d4567446a77e"

SAMPLE_DESTINATIONS = [
    {
        "id": "point-reyes-seashore",
        "name": "Point Reyes National Seashore",
        "category": "Nature & Wildlife",
        "vibe": "scenic, misty, hiking, coastal",
        "best_season": "Fall, Spring",
        "estimated_cost_tier": "$",
        "duration_hours": 6,
        "distance_miles": 45,
        "description": "Dramatic windswept coastlines, historic lighthouse, and hiking trails through coastal wilderness.",
        "highlights": ["Point Reyes Lighthouse", "Elephant Seal Overlook", "Chimney Rock Trail"],
    },
    {
        "id": "napa-valley-wine-country",
        "name": "Napa Valley Wine Tasting & Picnic",
        "category": "Culinary & Relaxation",
        "vibe": "luxury, romantic, food & wine, relaxed",
        "best_season": "Summer, Fall",
        "estimated_cost_tier": "$$$",
        "duration_hours": 8,
        "distance_miles": 55,
        "description": "World-class vineyards, artisanal olive oil tastings, and scenic vineyard train journeys.",
        "highlights": ["Historic Cellars", "Oxbow Public Market", "Oakville Grocery Picnic"],
    },
    {
        "id": "muir-woods-redwoods",
        "name": "Muir Woods & Mt. Tamalpais",
        "category": "Nature & Adventure",
        "vibe": "forest, peaceful, majestic redwoods, hiking",
        "best_season": "Year-round",
        "estimated_cost_tier": "$$",
        "duration_hours": 5,
        "distance_miles": 18,
        "description": "Ancient towering coastal redwoods in Cathedral Grove followed by sweeping Pacific views atop Mt. Tam.",
        "highlights": ["Cathedral Grove", "Dipsea Trail snippet", "East Peak Panoramic Overlook"],
    },
    {
        "id": "sausalito-waterfront",
        "name": "Sausalito Artists Waterfront & Ferry",
        "category": "Culture & Leisure",
        "vibe": "charming, seaside, art galleries, easy-paced",
        "best_season": "Spring, Summer, Fall",
        "estimated_cost_tier": "$$",
        "duration_hours": 4,
        "distance_miles": 10,
        "description": "Mediterranean-style seaside town famous for floating homes, waterfront cafes, and boutique art studios.",
        "highlights": ["Golden Gate Ferry Ride", "Bridgeway Promenade", "Houseboat Community"],
    },
    {
        "id": "half-moon-bay-coastal",
        "name": "Half Moon Bay & Coastal Bluffs",
        "category": "Coastal Escape",
        "vibe": "beaches, pumpkin patches, tidepools, seafood",
        "best_season": "Summer, Fall",
        "estimated_cost_tier": "$$",
        "duration_hours": 6,
        "distance_miles": 30,
        "description": "Charming coastal village with bluff-top walking trails, sandy coves, and fresh clam chowder spots.",
        "highlights": ["Mavericks Beach View", "Half Moon Bay Coastal Trail", "Historic Main Street"],
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    print(f"Seeding destinations to Firestore in project '{PROJECT_ID}'...")
    for item in SAMPLE_DESTINATIONS:
        doc_id = item["id"]
        collection_ref.document(doc_id).set(item)
        print(f"  ✓ Added destination: {item['name']} ({doc_id})")

    print(f"\nSuccessfully seeded {len(SAMPLE_DESTINATIONS)} destinations.")


if __name__ == "__main__":
    seed_database()
