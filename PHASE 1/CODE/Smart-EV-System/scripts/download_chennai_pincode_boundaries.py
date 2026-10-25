from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "location" / "chennai_pincode_boundaries.geojson"
URL = "https://livingatlas.esri.in/server/rest/services/IAB2024/IN_Postal_Code_Boundaries_2024/MapServer/0/query"


def main() -> None:
    # 600xxx covers Chennai's PIN series. The final point-in-polygon check
    # is restricted to the project's Chennai District boundary at runtime.
    params = {
        "where": "pin_code LIKE '600%'",
        "outFields": "pin_code,office_name,office_type,circle_name,region_name,division_name,district,state,latitude,longitude",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    headers = {
        "User-Agent": "EVTripPlanner/4.0 (academic project)",
        "Accept": "application/geo+json,application/json",
    }

    response = requests.get(URL, params=params, headers=headers, timeout=120)
    response.raise_for_status()
    payload = response.json()

    if payload.get("type") != "FeatureCollection":
        raise RuntimeError(f"Unexpected response from PIN service: {payload}")

    features = payload.get("features", [])
    if not features:
        raise RuntimeError("No Chennai 600xxx PIN polygons were returned.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(features):,} 600xxx PIN polygons to {OUT}")
    print("Source: Esri India postal boundary layer, based on Department of Posts dataset.")


if __name__ == "__main__":
    main()
