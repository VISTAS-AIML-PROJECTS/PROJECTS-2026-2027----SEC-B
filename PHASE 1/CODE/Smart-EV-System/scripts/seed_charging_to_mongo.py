from __future__ import annotations

import os
from pathlib import Path
import re

import pandas as pd
from pymongo import MongoClient, UpdateOne

BASE = Path(__file__).resolve().parents[1]
CSV = BASE / "data" / "charging" / "india_charging_master.csv"
URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
DB = os.getenv("MONGODB_DB", "EVTripPlanner")
COLL = os.getenv("EV_STATION_COLLECTION", "ev_charging_stations")

def norm(v: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(v or "").lower())).strip()

def main() -> None:
    if not CSV.exists():
        raise SystemExit(f"Charging CSV not found: {CSV}")
    df = pd.read_csv(CSV).fillna("")
    ops = []
    for _, r in df.iterrows():
        rec = {k: (v.item() if hasattr(v, "item") else v) for k, v in r.to_dict().items()}
        name = rec.get("Station_Name") or rec.get("name") or "Charging Station"
        lat = rec.get("Latitude")
        lon = rec.get("Longitude")
        if not str(lat).strip() or not str(lon).strip():
            continue
        key = f"{norm(name)}|{lat}|{lon}"
        rec["_station_key"] = key
        rec["_source"] = "project charging master CSV"
        ops.append(UpdateOne({"_station_key": key}, {"$set": rec}, upsert=True))

    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    col = client[DB][COLL]
    if ops:
        result = col.bulk_write(ops, ordered=False)
        print(f"Upserted into {DB}.{COLL}")
        print("inserted:", result.upserted_count, "updated:", result.modified_count)
    col.create_index("_station_key", unique=True)
    col.create_index([("Latitude", 1), ("Longitude", 1)])
    print("records:", col.count_documents({}))

if __name__ == "__main__":
    main()
