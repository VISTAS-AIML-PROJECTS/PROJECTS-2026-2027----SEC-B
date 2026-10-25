from __future__ import annotations

import csv
import os
import re
import time
from pathlib import Path

import requests
from pymongo import MongoClient, UpdateOne

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "location" / "gcc_roads_2025.csv"
URL = "https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCDepts/EDPMobile2025/FeatureServer/0/query"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("MONGO_DB", "EVTripPlanner")
COLL = "gcc_roads_2025"
BATCH = 500
PAGE = 2000
FIELDS = [
    "area_name", "locality", "area_id", "locality_id", "road_name", "gis_id",
    "department", "street_location", "address", "new_zone", "new_ward",
    "latitude", "longitude"
]


def norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split())


def fetch_all() -> list[dict]:
    rows = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": ",".join(FIELDS),
            "returnGeometry": "false",
            "resultRecordCount": PAGE,
            "resultOffset": offset,
            "orderByFields": "objectid",
            "f": "json",
        }
        r = requests.get(URL, params=params, timeout=60, headers={
            "User-Agent": "EVTripPlanner/3.0 academic project",
            "Accept": "application/json",
        })
        r.raise_for_status()
        payload = r.json()
        if "error" in payload:
            raise RuntimeError(payload["error"])
        features = payload.get("features", [])
        if not features:
            break
        for feat in features:
            a = feat.get("attributes", {})
            if not a.get("latitude") or not a.get("longitude"):
                continue
            try:
                lat = float(a["latitude"])
                lon = float(a["longitude"])
            except (TypeError, ValueError):
                continue
            a["latitude"] = lat
            a["longitude"] = lon
            a["normalized_road"] = norm(a.get("road_name", ""))
            a["normalized_address"] = norm(a.get("address", ""))
            a["normalized_locality"] = norm(a.get("locality", ""))
            a["pincode"] = (re.search(r"\b(\d{6})\b", str(a.get("address", ""))) or [None, ""])[1]
            rows.append(a)
        print(f"Fetched {len(rows):,} road records...", flush=True)
        if len(features) < PAGE:
            break
        offset += PAGE
        time.sleep(0.1)
    return rows


def main() -> None:
    rows = fetch_all()
    if not rows:
        raise RuntimeError("GCC GIS returned no usable road records")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(FIELDS + ["normalized_road", "normalized_address", "normalized_locality", "pincode"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    coll = client[DB_NAME][COLL]
    ops = []
    for r in rows:
        key = r.get("gis_id") or f"{r.get('road_name','')}|{r.get('latitude')}|{r.get('longitude')}"
        doc = dict(r)
        doc["_source"] = "Greater Chennai Corporation GIS / EDPMobile2025"
        ops.append(UpdateOne({"_gcc_key": key}, {"$set": {**doc, "_gcc_key": key}}, upsert=True))
        if len(ops) >= BATCH:
            coll.bulk_write(ops, ordered=False)
            ops.clear()
    if ops:
        coll.bulk_write(ops, ordered=False)

    coll.create_index([("normalized_road", 1)])
    coll.create_index([("normalized_address", 1)])
    coll.create_index([("normalized_locality", 1)])
    coll.create_index([("latitude", 1), ("longitude", 1)])
    print(f"Saved {len(rows):,} GCC road records to {OUT}")
    print(f"Upserted into {DB_NAME}.{COLL}")


if __name__ == "__main__":
    main()
