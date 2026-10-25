from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"

# Legacy files retained for initial migration
LEGACY_STATIONS_CSV = DATA_DIR / "charging" / "india_charging_master.csv"
SAVED_MODEL_PATH = MODEL_DIR / "main" / "energy_model_chennai.pkl"

# MongoDB connection settings
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "EVTripPlanner"

COLLECTION_VEHICLES = "vehicles"
COLLECTION_TRIPS = "ev_trips"
COLLECTION_STATIONS = "charging_stations"

# Chennai District Geographic Bounds
CHENNAI_BOUNDS = {
    "min_lat": 12.85,
    "max_lat": 13.20,
    "min_lon": 80.05,
    "max_lon": 80.33,
}
CHENNAI_CENTER = (13.0827, 80.2707)

# Battery & Charging Constraints
RESERVE_SOC_PCT = 25.0
ASSUMED_POWER_KW = 50.0
ASSUMED_COST_RS_PER_KWH = 18.0

OSRM_BASE_URL = "https://router.project-osrm.org"