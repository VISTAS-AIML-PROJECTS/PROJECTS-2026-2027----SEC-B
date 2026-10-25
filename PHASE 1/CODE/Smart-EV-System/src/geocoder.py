from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any

import pandas as pd
import requests
from shapely.geometry import Point, shape

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None


def _norm(value: str) -> str:
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _tokens(value: str) -> list[str]:
    stop = {
        "no", "number", "door", "flat", "apt", "apartment", "house",
        "plot", "chennai", "madras", "tamil", "nadu", "india", "pin",
        "pincode", "postcode"
    }
    return [t for t in _norm(value).split() if len(t) > 1 and t not in stop]


def _numbers(value: str) -> list[str]:
    return re.findall(r"\b\d+[a-z]?\b", str(value).lower())


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "nan"} else text


ROAD_WORDS = {
    "street", "st", "road", "rd", "lane", "ln", "avenue", "ave",
    "salai", "main", "cross", "extension", "ext", "highway", "bypass",
    "junction", "circle"
}


def _looks_like_full_address(query: str) -> bool:
    q = query.lower()
    return bool(re.search(r"\b\d+[a-z]?\b", q)) or any(
        w in q for w in [
            "street", "st.", "road", "rd", "avenue", "ave", "salai",
            "main road", "cross road", "cross st", "lane", "nagar", "layout",
            "flat", "apartment", "apt", "door", "plot", "house"
        ]
    )


class ChennaiGeocoder:
    """Chennai address/search layer.

    Search order:
      1) local MongoDB cache of Greater Chennai Corporation road/address GIS data
      2) local project street/reference indexes
      3) submitted Nominatim search
      4) Photon fallback if Nominatim is unavailable

    Live results are candidates. The caller must not silently choose a candidate
    as an exact house address unless the returned data explicitly contains the
    requested house number.
    """

    def __init__(
        self,
        boundary_path: Path,
        reference_csv_path: Path,
        street_csv_path: Path | None = None,
        user_agent: str = "EVTripPlanner/3.0 (academic project)",
        min_interval_s: float = 1.05,
        cache_path: Path | None = None,
    ):
        self.boundary_path = Path(boundary_path)
        self.reference_csv_path = Path(reference_csv_path)
        self.street_csv_path = Path(street_csv_path or self.boundary_path.parent.parent / "location" / "chennai_streets.csv")
        self.postcode_path = self.boundary_path.parent.parent / "location" / "verified_street_postcodes.json"
        self.user_agent = user_agent
        self.min_interval_s = min_interval_s
        self._last_request = 0.0
        self._polygon = None
        self._reference = None
        self._streets = None
        self._postcode_map = None
        self.cache_path = Path(cache_path or self.boundary_path.parent.parent / "location" / "geocode_cache.sqlite3")
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._mongo = None
        self._init_cache()

    def _init_cache(self) -> None:
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS geocode_cache (query TEXT PRIMARY KEY, response TEXT NOT NULL, cached_at REAL NOT NULL)"
            )

    @property
    def polygon(self):
        if self._polygon is None:
            payload = json.loads(self.boundary_path.read_text(encoding="utf-8"))
            self._polygon = shape(payload["features"][0]["geometry"])
        return self._polygon

    @property
    def reference(self) -> pd.DataFrame:
        if self._reference is None:
            if self.reference_csv_path.exists():
                df = pd.read_csv(self.reference_csv_path, dtype=str).fillna("")
                for col in ["latitude", "longitude"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                self._reference = df
            else:
                self._reference = pd.DataFrame(columns=[
                    "name", "normalized_name", "type", "pincode", "taluk",
                    "latitude", "longitude", "source", "source_url", "verified_level"
                ])
        return self._reference

    @property
    def streets(self) -> pd.DataFrame:
        if self._streets is None:
            if self.street_csv_path.exists():
                self._streets = pd.read_csv(self.street_csv_path, dtype=str).fillna("")
            else:
                self._streets = pd.DataFrame(columns=[
                    "name", "normalized_name", "source", "latitude", "longitude", "segment_count"
                ])
        return self._streets

    @property
    def postcode_map(self) -> dict[str, dict[str, Any]]:
        if self._postcode_map is None:
            try:
                self._postcode_map = json.loads(self.postcode_path.read_text(encoding="utf-8"))
            except Exception:
                self._postcode_map = {}
        return self._postcode_map

    def _mongo_collection(self):
        if self._mongo is not None:
            return self._mongo
        if MongoClient is None:
            return None
        try:
            client = MongoClient(
                os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017"),
                serverSelectionTimeoutMS=1200,
                connectTimeoutMS=1200,
            )
            client.admin.command("ping")
            self._mongo = client[os.getenv("MONGO_DB", "EVTripPlanner")]["gcc_roads_2025"]
            return self._mongo
        except Exception:
            self._mongo = None
            return None

    def _verified_postcode(self, road: str) -> str:
        return str(self.postcode_map.get(_norm(road), {}).get("pincode", ""))

    def _score_text(self, query: str, *parts: str) -> float:
        qn = _norm(query)
        qtokens = _tokens(query)
        text = _norm(" ".join(str(p or "") for p in parts))
        if not qtokens:
            return 0.0
        matched = sum(1 for t in qtokens if t in text)
        token_score = 100.0 * matched / len(qtokens)
        sequence = SequenceMatcher(None, qn, text).ratio() * 30.0
        return min(100.0, token_score * 0.75 + sequence)

    def _road_phrase(self, query: str) -> str:
        q = _norm(query)
        # Keep the street/road phrase but remove house number and generic city terms.
        q = re.sub(r"\b(no|number|door|flat|apt|apartment|house|plot)\b", " ", q)
        q = re.sub(r"\b\d+[a-z]?\b", " ", q)
        q = re.sub(r"\b(chennai|madras|tamil|nadu|india)\b", " ", q)
        return " ".join(q.split())

    def _local_gcc_matches(self, query: str, limit: int) -> list[dict[str, Any]]:
        coll = self._mongo_collection()
        if coll is None:
            return []

        qn = _norm(query)
        qtokens = _tokens(query)
        query_nums = _numbers(query)
        road_words = [t for t in qtokens if t in ROAD_WORDS]
        specific = [t for t in qtokens if t not in ROAD_WORDS]

        # Pull a reasonably broad candidate pool, then score locally.
        clauses = []
        for t in qtokens[:8]:
            pattern = re.escape(t)
            clauses.extend([
                {"normalized_road": {"$regex": pattern, "$options": "i"}},
                {"normalized_address": {"$regex": pattern, "$options": "i"}},
                {"normalized_locality": {"$regex": pattern, "$options": "i"}},
            ])
        if not clauses:
            return []

        docs = list(coll.find({"$or": clauses}).limit(250))
        out: list[dict[str, Any]] = []

        for d in docs:
            road = _clean(d.get("road_name"))
            addr = _clean(d.get("address"))
            locality = _clean(d.get("locality"))
            area = _clean(d.get("area_name"))

            road_n = _norm(road)
            addr_n = _norm(addr)
            loc_n = _norm(locality)
            area_n = _norm(area)
            combined = " ".join(x for x in [road_n, addr_n, loc_n, area_n] if x)

            # Exact road-bearing queries must match every specific road token.
            matched_specific = [t for t in specific if t in road_n or t in addr_n]
            matched_locality = [t for t in specific if t in loc_n or t in area_n]

            # If there are specific tokens, reject unrelated roads instead of
            # returning records merely because they contain generic words like
            # "street" or "road".
            if specific and not all(t in combined for t in specific):
                continue

            score = 0.0
            if specific:
                road_specific = [t for t in specific if t in road_n or t in addr_n]
                score += 65.0 * (len(road_specific) / len(specific))

            # Exact contiguous road phrase gets a strong bonus.
            road_phrase = " ".join(t for t in qtokens if t not in {"chennai", "madras"})
            if road_phrase and road_phrase in road_n:
                score += 30.0

            # Locality requested explicitly.
            if "kosapet" in qn and "kosapet" in loc_n:
                score += 25.0
            elif locality and any(t in loc_n for t in specific):
                score += 10.0

            # Generic road words present in the actual road name.
            if road_words:
                present = sum(1 for t in road_words if t in road_n)
                score += 8.0 * (present / len(road_words))

            if query_nums:
                road_addr_nums = set(_numbers(road) + _numbers(addr))
                score += 25.0 if any(n in road_addr_nums for n in query_nums) else -12.0

            # Small similarity bonus for spelling variations.
            score += SequenceMatcher(None, qn, _norm(f"{road} {locality}")).ratio() * 12.0

            lat = d.get("latitude")
            lon = d.get("longitude")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                continue
            if not self.polygon.covers(Point(float(lon), float(lat))):
                continue

            pincode = _clean(d.get("pincode")) or self._verified_postcode(road)
            display_base = addr or road or locality or area
            display_parts = [x for x in [display_base, locality, "Chennai, Tamil Nadu", pincode] if x]

            out.append({
                "display_name": ", ".join(display_parts),
                "lat": float(lat),
                "lon": float(lon),
                "type": "road_address",
                "category": "gcc_gis",
                "source": "Greater Chennai Corporation GIS / EDPMobile2025",
                "source_url": "https://gisgcc.chennaicorporation.gov.in/",
                "pincode": pincode,
                "road": road,
                "neighbourhood": locality,
                "suburb": area,
                "city": "Chennai",
                "district": "Chennai",
                "match_score": max(0.0, min(100.0, score)),
                "verified_level": "gcc_gis_candidate",
            })

        # Deduplicate exact coordinates and prioritize the strongest match.
        dedup: dict[tuple[float, float], dict[str, Any]] = {}
        for item in out:
            key = (round(item["lat"], 7), round(item["lon"], 7))
            if key not in dedup or item["match_score"] > dedup[key]["match_score"]:
                dedup[key] = item
        return sorted(dedup.values(), key=lambda x: (-x["match_score"], x["display_name"]))[:limit]

    def _local_matches(self, query: str, limit: int) -> list[dict[str, Any]]:
        qn = _norm(query)
        if not qn:
            return []
        results: list[dict[str, Any]] = []
        seen = set()

        for _, row in self.reference.iterrows():
            name = str(row.get("name", ""))
            norm = str(row.get("normalized_name", ""))
            if not norm:
                continue
            score = 100 if norm == qn else 90 if norm.startswith(qn) else 75 if qn in norm else 0
            if score == 0:
                q_tokens = set(qn.split())
                n_tokens = set(norm.split())
                if q_tokens and q_tokens.issubset(n_tokens):
                    score = 80
            if score == 0:
                continue
            lat, lon = row.get("latitude"), row.get("longitude")
            if pd.isna(lat) or pd.isna(lon):
                continue
            key = (round(float(lat), 7), round(float(lon), 7), name.lower())
            if key in seen:
                continue
            seen.add(key)
            pincode = str(row.get("pincode", "")) or self._verified_postcode(name)
            results.append({
                "display_name": f"{name}, Chennai, Tamil Nadu" + (f" {pincode}" if pincode else ""),
                "lat": float(lat), "lon": float(lon), "type": str(row.get("type", "")),
                "category": "local_reference", "source": str(row.get("source", "")),
                "source_url": str(row.get("source_url", "")), "pincode": pincode,
                "taluk": str(row.get("taluk", "")), "match_score": score,
                "verified_level": str(row.get("verified_level", "")),
            })

        for _, row in self.streets.iterrows():
            name = str(row.get("name", ""))
            norm = str(row.get("normalized_name", ""))
            if not norm:
                continue
            score = 92 if norm == qn else 82 if norm.startswith(qn) else 72 if qn in norm else 0
            if score == 0:
                # Useful for multi-word queries such as "sachidanandam street kosapet".
                if all(t in norm for t in _tokens(query) if t not in {"kosapet"}):
                    score = 68
            if not score:
                continue
            lat = pd.to_numeric(row.get("latitude", ""), errors="coerce")
            lon = pd.to_numeric(row.get("longitude", ""), errors="coerce")
            if pd.isna(lat) or pd.isna(lon):
                continue
            pincode = self._verified_postcode(name)
            display = f"{name}, Chennai, Tamil Nadu" + (f" {pincode}" if pincode else "")
            results.append({
                "display_name": display, "lat": float(lat), "lon": float(lon),
                "type": "street_reference", "category": "local_street",
                "source": str(row.get("source", "OpenStreetMap road graph")),
                "source_url": "https://www.openstreetmap.org/",
                "pincode": pincode, "taluk": "", "match_score": score,
                "verified_level": "road_name_reference",
            })

        results.sort(key=lambda x: (-x["match_score"], x["display_name"]))
        return results[:limit]

    def _cache_get(self, query: str) -> list[dict[str, Any]] | None:
        with sqlite3.connect(self.cache_path) as con:
            row = con.execute("SELECT response FROM geocode_cache WHERE query = ?", (query,)).fetchone()
        return json.loads(row[0]) if row else None

    def _cache_put(self, query: str, response: list[dict[str, Any]]) -> None:
        with sqlite3.connect(self.cache_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO geocode_cache(query,response,cached_at) VALUES (?,?,?)",
                (query, json.dumps(response), time.time()),
            )

    def _filter_live(self, query: str, items: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
        out = []
        road_phrase = self._road_phrase(query)
        query_nums = _numbers(query)
        for item in items:
            try:
                lat = float(item["lat"]); lon = float(item["lon"])
            except Exception:
                continue
            if not self.polygon.covers(Point(lon, lat)):
                continue
            display = str(item.get("display_name", ""))
            road = str(item.get("road", ""))
            neigh = str(item.get("neighbourhood", ""))
            suburb = str(item.get("suburb", ""))
            score = self._score_text(query, display, road, neigh, suburb)
            if road_phrase and len(road_phrase) >= 5:
                if road_phrase in _norm(display) or road_phrase in _norm(road):
                    score += 25
                else:
                    # Don't let an unrelated road become the first result for a road-specific query.
                    if not any(tok in _norm(road) or tok in _norm(display) for tok in road_phrase.split()):
                        score -= 45
            if query_nums:
                addr_nums = _numbers(display)
                score += 20 if any(n in addr_nums for n in query_nums) else -5
            item["match_score"] = max(0.0, min(100.0, score))
            item["source"] = source
            out.append(item)
        out.sort(key=lambda x: (-float(x.get("match_score", 0)), x.get("display_name", "").lower()))
        return out

    def _nominatim_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        cached = self._cache_get(_norm(query))
        if cached is not None:
            return cached[:limit]

        wait = self.min_interval_s - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        q = query.strip()
        if "chennai" not in q.lower():
            q = f"{q}, Chennai, Tamil Nadu, India"
        params = {
            "q": q, "format": "jsonv2", "limit": min(max(limit, 1), 10),
            "countrycodes": "in", "addressdetails": 1, "namedetails": 1,
            "dedupe": 1, "bounded": 1, "viewbox": self._viewbox(),
        }
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Accept-Language": "en",
        }
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=15)
            self._last_request = time.monotonic()
            r.raise_for_status()
            out = []
            for item in r.json():
                addr = item.get("address", {})
                out.append({
                    "display_name": item.get("display_name", q),
                    "lat": float(item["lat"]), "lon": float(item["lon"]),
                    "type": item.get("type"), "category": item.get("category"),
                    "source_url": "https://www.openstreetmap.org/",
                    "pincode": addr.get("postcode", ""), "road": addr.get("road", ""),
                    "neighbourhood": addr.get("neighbourhood", ""), "suburb": addr.get("suburb", ""),
                    "city": addr.get("city") or addr.get("town") or addr.get("municipality", ""),
                    "district": addr.get("state_district") or addr.get("county", ""),
                    "verified_level": "live_osm_geocode_candidate",
                })
            out = self._filter_live(query, out, "OpenStreetMap / Nominatim")
            self._cache_put(_norm(query), out)
            return out[:limit]
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code != 403:
                raise

        # Fallback after Nominatim 403.
        p = {
            "q": q, "limit": min(max(limit, 1), 10), "lang": "en", "bbox": self._photon_bbox()
        }
        r = requests.get(
            "https://photon.komoot.io/api/", params=p,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"}, timeout=15
        )
        r.raise_for_status()
        out = []
        for feature in r.json().get("features", []):
            coords = feature.get("geometry", {}).get("coordinates", [])
            props = feature.get("properties", {})
            if len(coords) < 2:
                continue
            house = props.get("housenumber", "")
            street = props.get("street", "")
            name = props.get("name", "")
            city = props.get("city") or props.get("locality") or props.get("district", "")
            display = ", ".join(x for x in [
                f"{house} {street}".strip() if (house or street) else "",
                name if name and name not in street else "",
                city, props.get("state", "Tamil Nadu"), props.get("postcode", "")
            ] if x)
            out.append({
                "display_name": display or q, "lat": float(coords[1]), "lon": float(coords[0]),
                "type": props.get("osm_value"), "category": props.get("osm_key"),
                "source_url": "https://photon.komoot.io/", "pincode": props.get("postcode", ""),
                "road": street, "neighbourhood": props.get("district", "") or props.get("locality", ""),
                "suburb": props.get("locality", ""), "city": city,
                "district": props.get("county", ""), "verified_level": "live_osm_geocode_candidate",
            })
        out = self._filter_live(query, out, "OpenStreetMap / Photon")
        self._cache_put(_norm(query), out)
        return out[:limit]

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        query = " ".join(str(query).strip().split())
        if len(query) < 3:
            return []
        limit = min(max(limit, 1), 10)

        local_gcc = self._local_gcc_matches(query, limit)
        local = self._local_matches(query, limit)

        # For a road-specific query, a strong GCC match suppresses live geocoder
        # noise. For weak/no GCC matches, supplement with OSM candidates.
        strong_gcc = local_gcc and float(local_gcc[0].get("match_score", 0)) >= 75.0
        if strong_gcc:
            live = []
        else:
            live = self._nominatim_search(query, limit)

        return self._merge(local_gcc + local, live, limit)

    @staticmethod
    def _merge(primary: list[dict[str, Any]], secondary: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        out, seen = [], set()
        for item in primary + secondary:
            lat, lon = item.get("lat"), item.get("lon")
            if lat is None or lon is None:
                key = ("text", _norm(item.get("display_name", "")))
            else:
                key = ("point", round(float(lat), 6), round(float(lon), 6))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        priority = {
            "gcc_gis_candidate": 0,
            "locality_reference": 1,
            "road_name_reference": 2,
            "live_osm_geocode_candidate": 3,
        }
        out.sort(key=lambda x: (priority.get(x.get("verified_level", ""), 4), -float(x.get("match_score", 0))))
        return out[:limit]

    def _viewbox(self) -> str:
        minx, miny, maxx, maxy = self.polygon.bounds
        return f"{minx},{maxy},{maxx},{miny}"

    def _photon_bbox(self) -> str:
        minx, miny, maxx, maxy = self.polygon.bounds
        return f"{minx},{miny},{maxx},{maxy}"
