from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient, GEOSPHERE


ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "location" / "chennai_location_reference.csv"


def main() -> None:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "EVTripPlanner")

    if not CSV_FILE.exists():
        raise FileNotFoundError(CSV_FILE)

    df = pd.read_csv(CSV_FILE, dtype=str).fillna("")
    docs = []

    for _, row in df.iterrows():
        doc = row.to_dict()
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            doc["latitude"] = lat
            doc["longitude"] = lon
            doc["location"] = {"type": "Point", "coordinates": [lon, lat]}
        except (TypeError, ValueError):
            doc["latitude"] = None
            doc["longitude"] = None
            doc["location"] = None
        docs.append(doc)

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    col = db["chennai_locations"]

    col.delete_many({})
    if docs:
        col.insert_many(docs)

    col.create_index([("location", GEOSPHERE)])
    col.create_index([("normalized_name", 1)])
    col.create_index([("pincode", 1)])

    print(f"Inserted {len(docs):,} location reference records into {db_name}.chennai_locations")


if __name__ == "__main__":
    main()
