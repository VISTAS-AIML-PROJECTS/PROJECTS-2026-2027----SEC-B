from __future__ import annotations

from pathlib import Path
from typing import Optional
import requests

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from shapely.geometry import Point
from src.chennai_location_resolver import ChennaiLocationResolver
from config.settings import BASE_DIR, COLLECTION_VEHICLES, DB_NAME, MONGO_URI
from src.database import get_db
from src.geocoder import ChennaiGeocoder
from src.navigation import ChennaiRouter

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph" / "chennai_drive.graphml"
BOUNDARY_PATH = ROOT / "data" / "boundary" / "chennai_district.geojson"

app = FastAPI(title="Chennai EV Trip Planner API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = ChennaiRouter(GRAPH_PATH, BOUNDARY_PATH)
REFERENCE_CSV_PATH = BASE_DIR / "data" / "location" / "chennai_location_reference.csv"

geocoder = ChennaiGeocoder(
    BOUNDARY_PATH,
    REFERENCE_CSV_PATH
)

location_resolver = ChennaiLocationResolver()
class PointModel(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RouteRequest(BaseModel):
    origin: PointModel
    destination: PointModel
    alternatives: int = Field(default=3, ge=1, le=4)


def check_inside_chennai(point: PointModel) -> None:
    try:
        inside = router.boundary.covers(Point(point.lon, point.lat))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"District boundary unavailable: {exc}") from exc
    if not inside:
        raise HTTPException(
            status_code=400,
            detail="The selected location is outside the Chennai District project scope.",
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "graph_ready": GRAPH_PATH.exists(),
        "boundary_ready": BOUNDARY_PATH.exists(),
        "database": DB_NAME,
    }


@app.get("/api/geocode")
def geocode(q: str = Query(min_length=3, max_length=200)):
    if not BOUNDARY_PATH.exists():
        raise HTTPException(status_code=500, detail="Chennai boundary has not been built yet.")
    try:
        results = geocoder.search(q)
        return {"query": q, "results": results, "scope": "Chennai District"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Address search failed: {exc}") from exc


@app.get("/api/vehicles")
def vehicles():
    db = get_db()
    docs = list(db[COLLECTION_VEHICLES].find({}, {"_id": 0}).sort("model", 1))
    return {"vehicles": docs}
@app.get("/api/reverse-geocode")
def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    try:
        result = location_resolver.resolve(lat, lon)

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Location resolution failed: {exc}"
        ) from exc
    point = Point(lon, lat)

    if not BOUNDARY_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Chennai boundary has not been built yet."
        )

    try:
        if not router.boundary.covers(point):
            raise HTTPException(
                status_code=400,
                detail="The current location is outside the Chennai District project scope."
            )

        headers = {
            "User-Agent": "EVTripPlanner/2.0 (academic project)",
            "Accept": "application/json",
            "Accept-Language": "en",
        }

        # Primary reverse geocoder: Nominatim
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "zoom": 18,
                "addressdetails": 1,
                "layer": "address",
            },
            headers=headers,
            timeout=15,
        )

        if response.ok:
            item = response.json()
            addr = item.get("address", {})

            return {
                "display_name": item.get(
                    "display_name",
                    f"{lat:.6f}, {lon:.6f}"
                ),
                "lat": lat,
                "lon": lon,
                "pincode": addr.get("postcode", ""),
                "road": addr.get("road", ""),
                "neighbourhood": addr.get("neighbourhood", ""),
                "suburb": addr.get("suburb", ""),
                "city": (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("municipality", "")
                ),
                "source": "OpenStreetMap / Nominatim",
            }

        # Fallback: Photon
        photon = requests.get(
            "https://photon.komoot.io/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "lang": "en",
            },
            headers=headers,
            timeout=15,
        )
        photon.raise_for_status()

        features = photon.json().get("features", [])
        if not features:
            raise HTTPException(
                status_code=404,
                detail="No address could be resolved for the current location."
            )

        props = features[0].get("properties", {})
        street = props.get("street", "")
        house = props.get("housenumber", "")
        name = props.get("name", "")

        display_name = ", ".join(
            x for x in [
                f"{house} {street}".strip() if (house or street) else "",
                name if name and name != street else "",
                props.get("locality", ""),
                props.get("city", ""),
                props.get("state", "Tamil Nadu"),
                props.get("postcode", ""),
            ]
            if x
        )

        return {
            "display_name": display_name or f"{lat:.6f}, {lon:.6f}",
            "lat": lat,
            "lon": lon,
            "pincode": props.get("postcode", ""),
            "road": street,
            "neighbourhood": props.get("district", ""),
            "suburb": props.get("locality", ""),
            "city": props.get("city", ""),
            "source": "OpenStreetMap / Photon",
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Reverse geocoding failed: {exc}"
        ) from exc


@app.post("/api/route")
def route(body: RouteRequest):
    check_inside_chennai(body.origin)
    check_inside_chennai(body.destination)

    if not GRAPH_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Road graph is not built. Run: python scripts/build_chennai_network.py",
        )

    try:
        return router.routes(
            (body.origin.lat, body.origin.lon),
            (body.destination.lat, body.destination.lon),
            k=body.alternatives,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Route calculation failed: {exc}") from exc

# EV intelligence extension: XGBoost energy/range + PuLP charging optimization.
from api.ev_intelligence import router as ev_intelligence_router
app.include_router(ev_intelligence_router)

from api.route_diverse import register_diverse_routes
register_diverse_routes(app)

