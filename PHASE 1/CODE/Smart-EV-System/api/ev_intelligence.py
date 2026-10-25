from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from shapely.geometry import Point, shape
from pymongo import MongoClient

try:
    from pulp import (
        LpBinary,
        LpMinimize,
        LpProblem,
        LpStatus,
        LpVariable,
        PULP_CBC_CMD,
        lpSum,
    )
except Exception:  # pragma: no cover
    LpBinary = LpMinimize = LpProblem = LpStatus = LpVariable = PULP_CBC_CMD = lpSum = None


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "model" / "main" / "energy_model_main.pkl"
DATASET_PATH = BASE_DIR / "data" / "main" / "EV_20K_Trips.csv"
STATION_CSV = BASE_DIR / "data" / "charging" / "india_charging_master.csv"
BOUNDARY_PATH = BASE_DIR / "data" / "boundary" / "chennai_district.geojson"

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGO_DB = os.getenv("MONGODB_DB", "EVTripPlanner")
STATION_COLLECTION = os.getenv("EV_STATION_COLLECTION", "ev_charging_stations")
RESERVE_SOC = 25.0
DEFAULT_POWER_KW = 50.0
DEFAULT_PRICE_RS_KWH = 18.0
FEATURES = [
    "Manufacturer", "Model", "Year", "Battery_Capacity_kWh", "Battery_Type",
    "Motor_Power_kW", "Vehicle_Weight_kg", "Distance_km", "Avg_Speed",
    "Ambient_Temp_C", "Weather", "Road_Type", "SOH_pct", "Driving_Style",
]

router = APIRouter(prefix="/api/ev", tags=["EV intelligence"])


class RoutePoint(BaseModel):
    lat: float
    lon: float


class AnalyzeRequest(BaseModel):
    vehicle: str
    initial_soc_pct: float = Field(default=80.0, ge=0, le=100)
    avg_speed_kmh: float = Field(default=35.0, ge=5, le=140)
    ambient_temp_c: float = Field(default=30.0, ge=-20, le=60)
    weather: str = "Clear"
    road_type: str = "Urban"
    soh_pct: float = Field(default=95.0, ge=50, le=100)
    driving_style: str = "Moderate"
    route: dict[str, Any]


class StationsRequest(BaseModel):
    route: dict[str, Any]


@lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise RuntimeError(f"Dataset not found: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    return df


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Energy model not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_boundary():
    if not BOUNDARY_PATH.exists():
        raise RuntimeError(f"Chennai boundary not found: {BOUNDARY_PATH}")
    payload = __import__("json").loads(BOUNDARY_PATH.read_text(encoding="utf-8"))
    return shape(payload["features"][0]["geometry"])


@lru_cache(maxsize=1)
def vehicle_specs() -> dict[str, dict[str, Any]]:
    df = load_dataset()
    req = ["Manufacturer", "Model", "Year", "Battery_Capacity_kWh", "Battery_Type", "Motor_Power_kW", "Vehicle_Weight_kg"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise RuntimeError(f"Dataset missing vehicle columns: {missing}")

    def mode_value(s: pd.Series, fallback: str = "Unknown") -> str:
        v = s.dropna().astype(str).str.strip()
        return v.mode().iloc[0] if not v.empty else fallback

    grouped = df.groupby(["Manufacturer", "Model"], dropna=False).agg(
        Year=("Year", "median"),
        Battery_Capacity_kWh=("Battery_Capacity_kWh", "median"),
        Battery_Type=("Battery_Type", mode_value),
        Motor_Power_kW=("Motor_Power_kW", "median"),
        Vehicle_Weight_kg=("Vehicle_Weight_kg", "median"),
        Record_Count=("Model", "size"),
    ).reset_index()

    out = {}
    for _, r in grouped.iterrows():
        manufacturer = str(r["Manufacturer"]).strip()
        model = str(r["Model"]).strip()
        label = f"{manufacturer} {model}".strip()
        out[label] = {
            "Manufacturer": manufacturer,
            "Model": model,
            "Year": float(r["Year"]),
            "Battery_Capacity_kWh": float(r["Battery_Capacity_kWh"]),
            "Battery_Type": str(r["Battery_Type"]),
            "Motor_Power_kW": float(r["Motor_Power_kW"]),
            "Vehicle_Weight_kg": float(r["Vehicle_Weight_kg"]),
            "Record_Count": int(r["Record_Count"]),
        }
    return out


def resolve_vehicle(name: str) -> dict[str, Any]:
    specs = vehicle_specs()
    q = str(name).strip().lower()
    exact = {k.lower(): v for k, v in specs.items()}
    if q in exact:
        return exact[q]

    for label, spec in specs.items():
        ml = spec["Model"].lower()
        if q == ml or q in ml or ml in q:
            return spec

    # Try token overlap, useful for labels such as "Tata Nexon EV" vs dataset "Nexon EV".
    qt = set(t for t in q.replace("-", " ").split() if len(t) > 2)
    best = None
    best_score = 0
    for label, spec in specs.items():
        lt = set(t for t in label.lower().replace("-", " ").split() if len(t) > 2)
        score = len(qt & lt)
        if score > best_score:
            best_score = score
            best = spec
    if best is not None and best_score >= 1:
        return best
    raise HTTPException(status_code=400, detail=f"Vehicle '{name}' was not found in the project ML dataset.")


def haversine_km(a_lat: float, a_lon: float, b_lat: np.ndarray, b_lon: np.ndarray) -> np.ndarray:
    r = 6371.0088
    la1 = np.radians(a_lat)
    la2 = np.radians(b_lat)
    dlat = la2 - la1
    dlon = np.radians(b_lon - a_lon)
    h = np.sin(dlat / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(h))


def route_arrays(route: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    geometry = route.get("geometry") or {}
    coords = geometry.get("coordinates") or []
    if len(coords) < 2:
        raise HTTPException(status_code=400, detail="Route geometry is missing or too short.")
    lons = np.asarray([float(c[0]) for c in coords], dtype=float)
    lats = np.asarray([float(c[1]) for c in coords], dtype=float)
    seg = haversine_km(lats[:-1], lons[:-1], lats[1:], lons[1:]) if False else None
    # Vectorized segment distance.
    r = 6371.0088
    lat1 = np.radians(lats[:-1]); lat2 = np.radians(lats[1:])
    dlat = lat2 - lat1; dlon = np.radians(lons[1:] - lons[:-1])
    h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    seg = 2 * r * np.arcsin(np.sqrt(h))
    cumulative = np.concatenate([[0.0], np.cumsum(seg)])
    return lats, lons, cumulative


@lru_cache(maxsize=1)
def station_boundary_filter() -> Any:
    return load_boundary()


def load_station_docs() -> pd.DataFrame:
    # Prefer MongoDB because the project is using MongoDB as its NoSQL data layer.
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        docs = list(client[MONGO_DB][STATION_COLLECTION].find({}, {"_id": 0}))
        if docs:
            return pd.DataFrame(docs)
    except Exception:
        pass

    if not STATION_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(STATION_CSV)


def canonical_station_df() -> pd.DataFrame:
    df = load_station_docs().copy()
    if df.empty:
        return df

    def first_col(options: list[str]) -> str | None:
        for c in options:
            if c in df.columns:
                return c
        return None

    lat_col = first_col(["Latitude", "latitude", "lat"])
    lon_col = first_col(["Longitude", "longitude", "lon"])
    name_col = first_col(["Station_Name", "station_name", "name", "Name"])
    if not lat_col or not lon_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["name"] = df[name_col].astype(str) if name_col else "Charging Station"
    out["lat"] = pd.to_numeric(df[lat_col], errors="coerce")
    out["lon"] = pd.to_numeric(df[lon_col], errors="coerce")

    status_col = first_col(["Status", "status", "Availability", "availability"])
    power_col = first_col(["Charging_Power_kW", "Power_kW", "Power", "power_kW"])
    price_col = first_col(["Cost_Per_Unit", "Price_per_kWh", "Price", "price_per_kWh"])
    address_col = first_col(["Address", "address", "Location", "location"])
    connector_col = first_col(["Connector_Type", "Connector", "connector_type"])

    out["status"] = df[status_col].astype(str) if status_col else "available"
    out["power_kw_raw"] = pd.to_numeric(df[power_col], errors="coerce") if power_col else np.nan
    out["price_raw"] = pd.to_numeric(df[price_col], errors="coerce") if price_col else np.nan
    out["address"] = df[address_col].astype(str) if address_col else ""
    out["connector"] = df[connector_col].astype(str) if connector_col else ""
    out = out.dropna(subset=["lat", "lon"]).copy()

    boundary = station_boundary_filter()
    inside = [boundary.covers(Point(float(x), float(y))) for x, y in zip(out["lon"], out["lat"])]
    out = out[np.asarray(inside)].copy()
    out["power_kw"] = out["power_kw_raw"].fillna(DEFAULT_POWER_KW)
    out["price_rs_kwh"] = out["price_raw"].fillna(DEFAULT_PRICE_RS_KWH)
    out["power_assumed"] = out["power_kw_raw"].isna()
    out["price_assumed"] = out["price_raw"].isna()
    return out.reset_index(drop=True)


def route_station_candidates(route: dict[str, Any], max_count: int = 12) -> pd.DataFrame:
    df = canonical_station_df()
    if df.empty:
        return df
    lats, lons, cumulative = route_arrays(route)
    step = max(1, len(lats) // 180)
    slat, slon, scum = lats[::step], lons[::step], cumulative[::step]
    if slat[-1] != lats[-1]:
        slat = np.append(slat, lats[-1]); slon = np.append(slon, lons[-1]); scum = np.append(scum, cumulative[-1])

    station_lat = df["lat"].to_numpy(float)
    station_lon = df["lon"].to_numpy(float)
    min_dist = np.full(len(df), np.inf)
    nearest_km = np.zeros(len(df))
    for la, lo, ck in zip(slat, slon, scum):
        dist = haversine_km(float(la), float(lo), station_lat, station_lon)
        mask = dist < min_dist
        min_dist[mask] = dist[mask]
        nearest_km[mask] = float(ck)

    df["distance_to_route_km"] = min_dist
    df["distance_from_origin_km"] = nearest_km
    df = df[df["distance_to_route_km"] <= 2.5].copy()
    if df.empty:
        return df

    # Keep stations in the driving direction and avoid immediate departure clutter.
    route_distance = float(cumulative[-1])
    df = df[(df["distance_from_origin_km"] >= 2.0) & (df["distance_from_origin_km"] <= route_distance - 1.0)].copy()
    if df.empty:
        return df

    # Prefer stations with better data completeness and closer route position spread.
    df["score"] = (
        -df["distance_to_route_km"] * 5
        -df["distance_from_origin_km"] * 0.01
        + (~df["power_assumed"]).astype(int) * 1.0
        + (~df["price_assumed"]).astype(int) * 1.0
    )
    # Spread results along the route for a useful map/list.
    df = df.sort_values("distance_from_origin_km").reset_index(drop=True)
    selected = []
    used_positions: list[float] = []
    for idx, row in df.iterrows():
        pos = float(row["distance_from_origin_km"])
        if any(abs(pos - p) < 2.0 for p in used_positions):
            continue
        selected.append(idx); used_positions.append(pos)
        if len(selected) >= max_count:
            break
    return df.loc[selected].reset_index(drop=True)


def predict_energy(spec: dict[str, Any], distance_km: float, avg_speed: float, temp: float, weather: str, road_type: str, soh: float, style: str) -> tuple[float, dict[str, Any]]:
    df = load_dataset()
    max_train_distance = float(pd.to_numeric(df["Distance_km"], errors="coerce").max())
    ref_distance = 250.0

    base = {
        "Manufacturer": spec["Manufacturer"],
        "Model": spec["Model"],
        "Year": spec["Year"],
        "Battery_Capacity_kWh": spec["Battery_Capacity_kWh"],
        "Battery_Type": spec["Battery_Type"],
        "Motor_Power_kW": spec["Motor_Power_kW"],
        "Vehicle_Weight_kg": spec["Vehicle_Weight_kg"],
        "Avg_Speed": avg_speed,
        "Ambient_Temp_C": temp,
        "Weather": weather,
        "Road_Type": road_type,
        "SOH_pct": soh,
        "Driving_Style": style,
    }

    model = load_model()

    def one(d: float) -> float:
        row = dict(base)
        row["Distance_km"] = float(d)
        pred = float(model.predict(pd.DataFrame([row], columns=FEATURES))[0])
        return max(0.0, pred)

    if distance_km <= max_train_distance:
        energy = one(distance_km)
        meta = {"method": "direct_XGBoost", "training_distance_max_km": round(max_train_distance, 2)}
    else:
        ref_energy = one(ref_distance)
        kwh_per_km = ref_energy / ref_distance
        energy = kwh_per_km * distance_km
        meta = {
            "method": "XGBoost_reference_efficiency_scaling",
            "reference_distance_km": ref_distance,
            "training_distance_max_km": round(max_train_distance, 2),
            "reference_energy_kwh": round(ref_energy, 3),
        }

    return energy, meta


def optimize_single_stop(spec: dict[str, Any], initial_soc: float, energy: float, route_distance: float, candidates: pd.DataFrame) -> dict[str, Any]:
    capacity = float(spec["Battery_Capacity_kWh"])
    initial_energy = capacity * initial_soc / 100.0
    reserve_energy = capacity * RESERVE_SOC / 100.0
    deficit = max(0.0, reserve_energy + energy - initial_energy)

    if deficit <= 0.0:
        return {
            "charging_needed": False,
            "charging_stops": [],
            "optimizer": "PuLP MILP (not required: trip feasible)",
            "message": "Trip can be completed while maintaining the 25% reserve.",
        }

    if candidates.empty:
        return {
            "charging_needed": True,
            "charging_stops": [],
            "optimizer": "PuLP MILP",
            "message": "Charging is required, but no route-near station was found.",
        }

    feasible = []
    kwh_per_km = energy / max(route_distance, 1e-9)
    for idx, row in candidates.iterrows():
        d = float(row["distance_from_origin_km"])
        e_to = kwh_per_km * d
        arrival_energy = initial_energy - e_to
        if arrival_energy + 1e-9 < reserve_energy:
            continue
        max_charge = max(0.0, capacity - arrival_energy)
        if max_charge + 1e-9 < deficit:
            continue
        feasible.append({"idx": idx, "e_to": e_to, "arrival_energy": arrival_energy, "max_charge": max_charge})

    if not feasible:
        return {
            "charging_needed": True,
            "charging_stops": [],
            "optimizer": "PuLP MILP",
            "message": "Charging is required, but no safely reachable station can satisfy the 25% reserve constraint.",
        }

    if LpProblem is None:
        raise HTTPException(status_code=500, detail="PuLP is not installed. Run: python -m pip install pulp")

    problem = LpProblem("EV_Charging_Stop_Optimization", LpMinimize)
    x = {f["idx"]: LpVariable(f"x_{f['idx']}", cat=LpBinary) for f in feasible}
    q = {f["idx"]: LpVariable(f"q_{f['idx']}", lowBound=0) for f in feasible}
    terms = []
    for f in feasible:
        i = f["idx"]
        row = candidates.loc[i]
        price = float(row["price_rs_kwh"])
        power = max(1.0, float(row["power_kw"]))
        detour = float(row["distance_to_route_km"])
        # Cost + charging time + small route-access penalty.
        terms.append(price * q[i] + 0.35 * (60.0 / power) * q[i] + 5.0 * detour * x[i])
        problem += q[i] >= deficit * x[i]
        problem += q[i] <= f["max_charge"] * x[i]
    problem += lpSum(x.values()) == 1
    problem += lpSum(q.values()) >= deficit
    problem += lpSum(q.values()) <= max(float(spec["Battery_Capacity_kWh"]), deficit)
    problem += lpSum(terms)
    problem.solve(PULP_CBC_CMD(msg=False))

    if LpStatus.get(problem.status) != "Optimal":
        return {
            "charging_needed": True,
            "charging_stops": [],
            "optimizer": "PuLP MILP",
            "message": "The charging optimization problem did not return an optimal solution.",
        }

    chosen = None
    for f in feasible:
        i = f["idx"]
        if float(x[i].value() or 0) > 0.5:
            chosen = candidates.loc[i]
            chosen_meta = f
            break

    if chosen is None:
        return {"charging_needed": True, "charging_stops": [], "optimizer": "PuLP MILP", "message": "No charging decision was selected."}

    charge = deficit
    power = max(1.0, float(chosen["power_kw"]))
    time_min = charge / power * 60.0
    cost = charge * float(chosen["price_rs_kwh"])
    pinfo = []
    if bool(chosen["power_assumed"]):
        pinfo.append("50 kW charging power assumed")
    if bool(chosen["price_assumed"]):
        pinfo.append("₹18/kWh charging price assumed")

    stop = {
        "name": str(chosen["name"]),
        "lat": float(chosen["lat"]),
        "lon": float(chosen["lon"]),
        "distance_from_origin_km": float(chosen["distance_from_origin_km"]),
        "distance_to_route_km": float(chosen["distance_to_route_km"]),
        "arrival_soc_pct": float(chosen_meta["arrival_energy"] / capacity * 100.0),
        "charge_amount_kwh": float(charge),
        "charging_power_kw": float(power),
        "charging_time_min": float(time_min),
        "charging_cost_rs": float(cost),
        "data_note": "; ".join(pinfo) if pinfo else "Station power and price available in source data",
        "connector": str(chosen.get("connector", "")),
        "address": str(chosen.get("address", "")),
    }
    return {
        "charging_needed": True,
        "charging_stops": [stop],
        "optimizer": "PuLP MILP",
        "message": f"Recommended charging stop selected using MILP while maintaining the {RESERVE_SOC:.0f}% minimum reserve.",
    }


@router.get("/vehicles")
def get_vehicles():
    specs = vehicle_specs()
    # Keep the selector usable: return models with at least 3 training records.
    out = []
    for name, spec in specs.items():
        if spec["Record_Count"] >= 3:
            out.append({"name": name, **spec})
    return {"vehicles": sorted(out, key=lambda x: x["name"].lower())}


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        spec = resolve_vehicle(req.vehicle)
        route_distance = float(req.route.get("distance_km") or 0.0)
        if route_distance <= 0:
            _, _, cumulative = route_arrays(req.route)
            route_distance = float(cumulative[-1])

        candidates = route_station_candidates(req.route, max_count=12)
        energy, meta = predict_energy(
            spec, route_distance, req.avg_speed_kmh, req.ambient_temp_c,
            req.weather, req.road_type, req.soh_pct, req.driving_style,
        )
        capacity = float(spec["Battery_Capacity_kWh"])
        reserve_energy = capacity * RESERVE_SOC / 100.0
        initial_energy = capacity * req.initial_soc_pct / 100.0
        kwh_per_km = energy / max(route_distance, 1e-9)
        arrival_soc = max(0.0, (initial_energy - energy) / capacity * 100.0)
        range_km = max(0.0, (initial_energy - reserve_energy) / max(kwh_per_km, 1e-9))

        opt = optimize_single_stop(spec, req.initial_soc_pct, energy, route_distance, candidates)
        charging_names = {s["name"] for s in opt.get("charging_stops", [])}
        station_payload = []
        for _, row in candidates.iterrows():
            station_payload.append({
                "name": str(row["name"]),
                "lat": float(row["lat"]), "lon": float(row["lon"]),
                "distance_from_origin_km": float(row["distance_from_origin_km"]),
                "distance_to_route_km": float(row["distance_to_route_km"]),
                "power_kw": float(row["power_kw"]),
                "price_rs_kwh": float(row["price_rs_kwh"]),
                "power_assumed": bool(row["power_assumed"]),
                "price_assumed": bool(row["price_assumed"]),
                "recommended": str(row["name"]) in charging_names,
                "address": str(row.get("address", "")),
                "connector": str(row.get("connector", "")),
            })

        return {
            "vehicle": {"name": req.vehicle, **spec},
            "route_distance_km": round(route_distance, 2),
            "predicted_energy_kwh": round(energy, 2),
            "energy_per_km_kwh": round(kwh_per_km, 4),
            "estimated_range_km": round(range_km, 1),
            "initial_soc_pct": round(req.initial_soc_pct, 1),
            "arrival_soc_pct": round(arrival_soc, 1),
            "reserve_soc_pct": RESERVE_SOC,
            "charging_needed": bool(opt.get("charging_needed")),
            "charging_stops": opt.get("charging_stops", []),
            "optimizer": opt.get("optimizer"),
            "message": opt.get("message"),
            "prediction_meta": meta,
            "station_count": len(station_payload),
            "stations": station_payload,
            "assumptions": {
                "charging_power_default_kw": DEFAULT_POWER_KW,
                "charging_price_default_rs_kwh": DEFAULT_PRICE_RS_KWH,
                "note": "Default charging power/price are explicitly marked as assumptions when station-specific values are unavailable.",
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"EV analysis failed: {exc}") from exc
