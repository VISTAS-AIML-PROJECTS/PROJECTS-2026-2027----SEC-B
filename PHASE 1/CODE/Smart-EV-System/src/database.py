import pymongo
import pandas as pd
from config.settings import (
    MONGO_URI,
    DB_NAME,
    COLLECTION_STATIONS,
    COLLECTION_TRIPS,
    COLLECTION_VEHICLES,
    CHENNAI_BOUNDS
)

_client = None

def get_db():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME]

def init_db():
    """Initializes collections and geospatial 2dsphere indexes."""
    db = get_db()
    db[COLLECTION_STATIONS].create_index([("location", pymongo.GEOSPHERE)])
    db[COLLECTION_TRIPS].create_index([("start_location", pymongo.GEOSPHERE)])
    db[COLLECTION_TRIPS].create_index([("end_location", pymongo.GEOSPHERE)])
    print(f"MongoDB '{DB_NAME}' initialized with 2dsphere geospatial indexes.")

def load_trips_as_dataframe():
    """Pulls all synthetic trips from MongoDB directly into a pandas DataFrame."""
    db = get_db()
    trips = list(db[COLLECTION_TRIPS].find({}, {"_id": 0}))
    if not trips:
        return pd.DataFrame()

    rows = []
    for t in trips:
        v = t.get("vehicle", {})
        rows.append({
            "Manufacturer": v.get("manufacturer"),
            "Model": v.get("model"),
            "Year": v.get("year"),
            "Battery_Capacity_kWh": v.get("battery_capacity_kwh"),
            "Motor_Power_kW": v.get("motor_power_kw"),
            "Vehicle_Weight_kg": v.get("weight_kg"),
            "Distance_km": t.get("distance_km"),
            "Duration_min": t.get("duration_min"),
            "Avg_Speed": t.get("avg_speed_kmh"),
            "Ambient_Temp_C": t.get("ambient_temp_c"),
            "Weather": t.get("weather"),
            "Road_Type": t.get("road_type"),
            "SOH_pct": t.get("soh_pct"),
            "Driving_Style": t.get("driving_style", "Moderate"),
            "Energy_Consumed_kWh": t.get("energy_consumed_kwh"),
        })
    return pd.DataFrame(rows)