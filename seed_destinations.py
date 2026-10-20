import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-cec237a37b41"
COLLECTION_NAME = "destinations"

SEED_DESTINATIONS = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto, Japan",
        "country": "Japan",
        "description": "Historic capital renowned for classical Buddhist temples, gardens, imperial palaces, Shinto shrines, and traditional wooden houses.",
        "best_season": "Spring (March-May) or Autumn (October-November)",
        "travel_style": ["culture", "food", "historic", "relaxing"],
        "budget_tier": "$$",
        "avg_daily_budget_usd": 150,
        "highlights": ["Fushimi Inari Taisha", "Arashiyama Bamboo Grove", "Gion District", "Kinkaku-ji"],
        "local_dishes": ["Kaiseki", "Matcha parfaits", "Yudofu", "Ramen"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "reykjavik-iceland",
        "name": "Reykjavik & Golden Circle, Iceland",
        "country": "Iceland",
        "description": "Dramatic volcanic landscapes, cascading waterfalls, geothermal lagoons, and dancing Northern Lights.",
        "best_season": "Summer (June-August) for hiking, Winter (November-March) for auroras",
        "travel_style": ["adventure", "nature", "outdoor", "photography"],
        "budget_tier": "$$$",
        "avg_daily_budget_usd": 280,
        "highlights": ["Thingvellir National Park", "Gullfoss Waterfall", "Blue Lagoon", "Geysir"],
        "local_dishes": ["Rúgbrauð", "Kjötsúpa (lamb soup)", "Arctic char"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "oaxaca-mexico",
        "name": "Oaxaca City, Mexico",
        "country": "Mexico",
        "description": "Culinary capital of Mexico brimming with indigenous markets, colorful colonial architecture, mezcal distilleries, and artisan crafts.",
        "best_season": "October to April (warm, dry days and festive celebrations)",
        "travel_style": ["food", "culture", "budget-friendly", "arts"],
        "budget_tier": "$",
        "avg_daily_budget_usd": 85,
        "highlights": ["Monte Albán", "Hierve el Agua", "Tlacolula Market", "Santo Domingo Church"],
        "local_dishes": ["Mole Oaxaqueño", "Tlayudas", "Tasajo", "Artisanal Mezcal"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "banff-canada",
        "name": "Banff National Park, Canada",
        "country": "Canada",
        "description": "Turquoise alpine lakes nestled under rugged Canadian Rocky peaks, rich wildlife, and world-class alpine adventures.",
        "best_season": "Summer (July-August) for turquoise lakes, Winter (December-March) for skiing",
        "travel_style": ["nature", "adventure", "hiking", "scenic"],
        "budget_tier": "$$$",
        "avg_daily_budget_usd": 240,
        "highlights": ["Lake Louise", "Moraine Lake", "Icefields Parkway", "Banff Gondola"],
        "local_dishes": ["Bison burgers", "Alberta beef", "Poutine", "BeaverTails"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    },
    {
        "id": "rome-italy",
        "name": "Rome, Italy",
        "country": "Italy",
        "description": "The Eternal City with thousands of years of art, architecture, ancient ruins, and world-renowned Italian culinary traditions.",
        "best_season": "Spring (April-May) or Autumn (September-October)",
        "travel_style": ["history", "culture", "food", "walkable"],
        "budget_tier": "$$",
        "avg_daily_budget_usd": 175,
        "highlights": ["Colosseum", "Vatican Museums", "Pantheon", "Trastevere neighborhood"],
        "local_dishes": ["Cacio e Pepe", "Carbonara", "Supplì", "Artisanal Gelato"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connected to Firestore project: {PROJECT_ID}")
    for item in SEED_DESTINATIONS:
        doc_ref = db.collection(COLLECTION_NAME).document(item["id"])
        doc_ref.set(item)
        print(f"Seeded destination: {item['name']} ({item['id']})")
    print("Seeding complete!")

if __name__ == "__main__":
    seed()
