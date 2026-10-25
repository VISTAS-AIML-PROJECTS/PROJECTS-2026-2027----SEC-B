from __future__ import annotations

import os
from pymongo import MongoClient

URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB = os.getenv("MONGO_DB", "EVTripPlanner")
COLL = "gcc_roads_2025"


def main() -> None:
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    c = client[DB][COLL]

    updated = 0
    for doc in c.find({}, {"latitude": 1, "longitude": 1, "location": 1}):
        try:
            lat = float(doc["latitude"])
            lon = float(doc["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if doc.get("location") == {"type": "Point", "coordinates": [lon, lat]}:
            continue
        c.update_one(
            {"_id": doc["_id"]},
            {"$set": {"location": {"type": "Point", "coordinates": [lon, lat]}}},
        )
        updated += 1

    c.create_index([("location", "2dsphere")])
    print(f"Added/updated {updated:,} GCC location points")
    print("Created 2dsphere index on EVTripPlanner.gcc_roads_2025.location")


if __name__ == "__main__":
    main()
