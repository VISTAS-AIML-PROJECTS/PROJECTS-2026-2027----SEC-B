from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None


ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "data" / "location" / "chennai_pincode_boundaries.geojson"
BOUNDARY_PATH = ROOT / "data" / "boundary" / "chennai_district.geojson"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class ChennaiLocationResolver:
    """Resolve a Chennai GPS point using local GCC road data + postal polygons.

    Address text comes from the GCC road/address collection when available.
    PIN code comes from the local postal-boundary polygon, not from Nominatim.
    """

    def __init__(self) -> None:
        self._boundary = None
        self._pin_features: list[tuple[Any, dict[str, Any]]] = []
        self._pin_tree: STRtree | None = None
        self._mongo = None

    @property
    def boundary(self):
        if self._boundary is None:
            payload = json.loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
            self._boundary = shape(payload["features"][0]["geometry"])
        return self._boundary

    def _load_pins(self) -> None:
        if self._pin_tree is not None or not PIN_PATH.exists():
            return
        payload = json.loads(PIN_PATH.read_text(encoding="utf-8"))
        geoms = []
        for feature in payload.get("features", []):
            geom = feature.get("geometry")
            props = feature.get("properties", {})
            if not geom:
                continue
            polygon = shape(geom)
            geoms.append(polygon)
            self._pin_features.append((polygon, props))
        self._pin_tree = STRtree(geoms) if geoms else None

    def _mongo_collection(self):
        if self._mongo is not None:
            return self._mongo
        if MongoClient is None:
            return None
        try:
            client = MongoClient(
                os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017"),
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
            )
            client.admin.command("ping")
            self._mongo = client[os.getenv("MONGO_DB", "EVTripPlanner")]["gcc_roads_2025"]
            return self._mongo
        except Exception:
            return None

    def _find_pin(self, point: Point) -> dict[str, Any] | None:
        self._load_pins()
        if self._pin_tree is None:
            return None

        matches = self._pin_tree.query(point, predicate="intersects")
        if len(matches) == 0:
            return None

        # Shapely 2 STRtree returns indices for query().
        for idx in matches:
            polygon, props = self._pin_features[int(idx)]
            if polygon.covers(point):
                return {
                    "pincode": str(props.get("pin_code") or ""),
                    "office_name": str(props.get("office_name") or ""),
                    "district": str(props.get("district") or ""),
                    "state": str(props.get("state") or ""),
                }
        return None

    def _find_gcc(self, lat: float, lon: float) -> dict[str, Any] | None:
        coll = self._mongo_collection()
        if coll is None:
            return None
        try:
            doc = coll.find_one(
                {
                    "location": {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat],
                            },
                            "$maxDistance": 1000,
                        }
                    }
                }
            )
        except Exception:
            return None
        if not doc:
            return None

        glat = doc.get("latitude")
        glon = doc.get("longitude")
        if glat is None or glon is None:
            return None
        try:
            distance_km = haversine_km(lat, lon, float(glat), float(glon))
        except Exception:
            distance_km = None

        return {
            "road_name": str(doc.get("road_name") or ""),
            "address": str(doc.get("address") or ""),
            "locality": str(doc.get("locality") or ""),
            "area_name": str(doc.get("area_name") or ""),
            "ward": str(doc.get("new_ward") or ""),
            "zone": str(doc.get("new_zone") or ""),
            "match_distance_km": distance_km,
        }

    def resolve(self, lat: float, lon: float) -> dict[str, Any]:
        point = Point(lon, lat)
        if not self.boundary.covers(point):
            raise ValueError("Location is outside Chennai District project scope.")

        pin = self._find_pin(point)
        gcc = self._find_gcc(lat, lon)

        road = gcc.get("road_name", "") if gcc else ""
        address = gcc.get("address", "") if gcc else ""
        locality = gcc.get("locality", "") if gcc else ""
        area = gcc.get("area_name", "") if gcc else ""

        base = address or road or locality or area or "Current location"
        parts = [base]
        if locality and locality.lower() not in base.lower():
            parts.append(locality)
        elif area and area.lower() not in base.lower():
            parts.append(area)
        parts += ["Chennai", "Tamil Nadu"]
        if pin and pin.get("pincode"):
            parts.append(pin["pincode"])

        return {
            "display_name": ", ".join([p for p in parts if p]),
            "lat": lat,
            "lon": lon,
            "pincode": pin.get("pincode", "") if pin else "",
            "pincode_office": pin.get("office_name", "") if pin else "",
            "road": road,
            "address": address,
            "locality": locality,
            "area": area,
            "ward": gcc.get("ward", "") if gcc else "",
            "zone": gcc.get("zone", "") if gcc else "",
            "road_match_distance_km": gcc.get("match_distance_km") if gcc else None,
            "address_source": "Greater Chennai Corporation GIS / EDPMobile2025" if gcc else "No local GCC road match",
            "pincode_source": "Postal PIN boundary (Department of Posts dataset)" if pin else "No local PIN polygon match",
        }
