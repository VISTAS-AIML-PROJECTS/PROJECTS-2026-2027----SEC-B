import random
import time
import requests
from config.settings import CHENNAI_BOUNDS, OSRM_BASE_URL, COLLECTION_TRIPS, COLLECTION_VEHICLES
from src.database import get_db

def query_osrm(lat1, lon1, lat2, lon2):
    url = f"{OSRM_BASE_URL}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false&steps=false"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("code") == "Ok" and data.get("routes"):
                r = data["routes"][0]
                return r["distance"] / 1000.0, r["duration"] / 60.0
    except requests.exceptions.RequestException:
        pass
    return None, None

def calculate_energy(vehicle, distance_km, avg_speed_kmh, temp_c, style, soh):
    base_rate = (vehicle["weight_kg"] / 1400.0) * 0.14
    speed_factor = 1.0 + (max(0.0, avg_speed_kmh - 40.0) / 100.0) ** 1.3
    ac_factor = 1.0 + (max(0.0, temp_c - 30.0) * 0.012)
    style_mult = {"Eco": 0.90, "Moderate": 1.00, "Aggressive": 1.18}.get(style, 1.0)
    soh_mult = 1.0 + ((100.0 - soh) * 0.002)
    return round(distance_km * base_rate * speed_factor * ac_factor * style_mult * soh_mult, 4)

def generate_trips(target=2000):
    db = get_db()
    vehicles = list(db[COLLECTION_VEHICLES].find({}, {"_id": 0}))
    trips_col = db[COLLECTION_TRIPS]
    trips_col.delete_many({})

    print(f"Generating {target} Chennai trips via OSRM...")
    count = 0
    batch = []

    while count < target:
        lat1 = random.uniform(CHENNAI_BOUNDS["min_lat"], CHENNAI_BOUNDS["max_lat"])
        lon1 = random.uniform(CHENNAI_BOUNDS["min_lon"], CHENNAI_BOUNDS["max_lon"])
        lat2 = random.uniform(CHENNAI_BOUNDS["min_lat"], CHENNAI_BOUNDS["max_lat"])
        lon2 = random.uniform(CHENNAI_BOUNDS["min_lon"], CHENNAI_BOUNDS["max_lon"])

        dist, dur = query_osrm(lat1, lon1, lat2, lon2)
        time.sleep(0.12)  # Respect public OSRM rate limits

        if not dist or dist < 2.5:
            continue

        veh = random.choice(vehicles)
        spd = round(dist / (dur / 60.0), 1)
        tmp = round(random.uniform(28.0, 38.0), 1)
        wth = random.choice(["Sunny", "Cloudy", "Rain"])
        sty = random.choice(["Eco", "Moderate", "Aggressive"])
        soh = round(random.uniform(90.0, 100.0), 1)

        batch.append({
            "vehicle": veh,
            "start_location": {"type": "Point", "coordinates": [lon1, lat1]},
            "end_location": {"type": "Point", "coordinates": [lon2, lat2]},
            "distance_km": round(dist, 2),
            "duration_min": round(dur, 1),
            "avg_speed_kmh": spd,
            "ambient_temp_c": tmp,
            "weather": wth,
            "road_type": "City",
            "soh_pct": soh,
            "driving_style": sty,
            "energy_consumed_kwh": calculate_energy(veh, dist, spd, tmp, sty, soh)
        })
        count += 1

        if len(batch) >= 50:
            trips_col.insert_many(batch)
            batch = []
            print(f"Progress: {count}/{target} trips written to MongoDB...")

    if batch:
        trips_col.insert_many(batch)
    print("Done! MongoDB 'ev_trips' collection is fully populated.")

if __name__ == "__main__":
    generate_trips(2000)