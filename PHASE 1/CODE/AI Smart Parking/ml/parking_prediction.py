import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "database" / "parking.db"


def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# GET HISTORICAL PARKING DATA
# ============================================================

def get_history():

    connection = get_connection()

    query = """
        SELECT
            timestamp,
            day_of_week,
            hour,
            total_slots,
            occupied_slots,
            available_slots,
            entry_count,
            exit_count
        FROM parking_history
        ORDER BY timestamp
    """

    data = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    return data


# ============================================================
# CREATE DEMO TRAINING DATA
# ============================================================

def create_demo_data():

    data = []

    total_slots = 20

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    for day in range(7):

        day_name = days[day]

        # 8 AM to 11 PM
        for hour in range(8, 24):

            # -------------------------------
            # Morning
            # -------------------------------

            if hour < 11:

                occupied = 4 + (hour - 8) * 2


            # -------------------------------
            # Afternoon
            # -------------------------------

            elif hour < 16:

                occupied = 10 + (hour - 11)


            # -------------------------------
            # Evening peak
            # -------------------------------

            elif hour < 20:

                occupied = 14 + (hour - 16) * 1.5


            # -------------------------------
            # Night
            # -------------------------------

            else:

                occupied = 18 - (hour - 20) * 2


            # Weekend demand
            if day >= 5:

                occupied += 2


            # Random variation
            occupied += np.random.randint(
                -2,
                3
            )


            occupied = int(
                max(
                    0,
                    min(
                        total_slots,
                        occupied
                    )
                )
            )


            available = (
                total_slots - occupied
            )


            # Entry activity
            entry_count = max(
                0,
                int(
                    np.random.normal(
                        5,
                        2
                    )
                )
            )


            # Exit activity
            exit_count = max(
                0,
                int(
                    np.random.normal(
                        3,
                        1
                    )
                )
            )


            data.append({

                "day": day,

                "day_of_week": day_name,

                "hour": hour,

                "total_slots": total_slots,

                "occupied_slots": occupied,

                "available_slots": available,

                "entry_count": entry_count,

                "exit_count": exit_count

            })


    return pd.DataFrame(data)


# ============================================================
# TRAIN RANDOM FOREST MODEL
# ============================================================

def train_model():

    history = get_history()


    # --------------------------------------------------------
    # Use demo data if database history is insufficient
    # --------------------------------------------------------

    if len(history) < 20:

        print(
            "Not enough historical data."
        )

        print(
            "Using generated parking history for training."
        )

        history = create_demo_data()

    else:

        print(
            f"Using {len(history)} historical records."
        )


    # --------------------------------------------------------
    # Convert day name to number
    # --------------------------------------------------------

    day_mapping = {

        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6

    }


    history["day"] = (
        history["day_of_week"]
        .map(day_mapping)
    )


    # --------------------------------------------------------
    # ML FEATURES
    # --------------------------------------------------------

    features = [

        "day",

        "hour",

        "total_slots",

        "occupied_slots",

        "entry_count",

        "exit_count"

    ]


    X = history[features]

    y = history["available_slots"]


    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    model = RandomForestRegressor(

        n_estimators=150,

        random_state=42,

        max_depth=10

    )


    model.fit(
        X,
        y
    )


    print(
        "ML model trained successfully!"
    )


    return model


# ============================================================
# GET CURRENT PARKING STATUS
# ============================================================

def get_current_status():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN status = 'Occupied'
                    THEN 1
                    ELSE 0
                END
            ) AS occupied
        FROM parking_slots
        """
    )


    result = cursor.fetchone()

    connection.close()


    total_slots = (
        result["total"]
        if result["total"]
        else 20
    )


    occupied_slots = (
        result["occupied"]
        if result["occupied"]
        else 0
    )


    available_slots = (
        total_slots
        - occupied_slots
    )


    return (
        total_slots,
        occupied_slots,
        available_slots
    )


# ============================================================
# ESTIMATE PARKING DEMAND
# ============================================================

def get_demand(hour):

    # --------------------------------------------------------
    # Returns expected vehicle entries and exits.
    # --------------------------------------------------------

    if 17 <= hour <= 20:

        # Evening peak
        return 6, 2


    elif 11 <= hour <= 16:

        # Afternoon
        return 4, 3


    elif 8 <= hour <= 10:

        # Morning
        return 3, 2


    else:

        # Night
        return 2, 4


# ============================================================
# PREDICT PARKING AVAILABILITY
# ============================================================

def predict_availability(

    model,

    minutes_ahead=30

):

    # --------------------------------------------------------
    # Current time
    # --------------------------------------------------------

    now = datetime.now()


    future_time = (
        now
        + timedelta(
            minutes=minutes_ahead
        )
    )


    # --------------------------------------------------------
    # Current parking status
    # --------------------------------------------------------

    (
        total_slots,
        current_occupied,
        current_available
    ) = get_current_status()


    # --------------------------------------------------------
    # Future time information
    # --------------------------------------------------------

    future_day = (
        future_time.weekday()
    )

    future_hour = (
        future_time.hour
    )


    # --------------------------------------------------------
    # Current time information
    # --------------------------------------------------------

    current_day = (
        now.weekday()
    )

    current_hour = (
        now.hour
    )


    # --------------------------------------------------------
    # Estimate current activity
    # --------------------------------------------------------

    current_entries, current_exits = (
        get_demand(
            current_hour
        )
    )


    # --------------------------------------------------------
    # Estimate future activity
    # --------------------------------------------------------

    future_entries, future_exits = (
        get_demand(
            future_hour
        )
    )


    # ========================================================
    # RANDOM FOREST BASELINE PREDICTION
    # ========================================================

    current_input = pd.DataFrame([{

        "day": current_day,

        "hour": current_hour,

        "total_slots": total_slots,

        "occupied_slots": current_occupied,

        "entry_count": current_entries,

        "exit_count": current_exits

    }])


    future_input = pd.DataFrame([{

        "day": future_day,

        "hour": future_hour,

        "total_slots": total_slots,

        "occupied_slots": current_occupied,

        "entry_count": future_entries,

        "exit_count": future_exits

    }])


    # Predict current baseline

    current_ml_prediction = model.predict(
        current_input
    )[0]


    # Predict future baseline

    future_ml_prediction = model.predict(
        future_input
    )[0]


    # ========================================================
    # CALCULATE TIME-BASED PARKING CHANGE
    # ========================================================

    intervals = (
        minutes_ahead / 30
    )


    # --------------------------------------------------------
    # Net parking demand
    #
    # Positive value = more vehicles entering
    # Negative value = more vehicles leaving
    # --------------------------------------------------------

    net_demand = (
        future_entries
        - future_exits
    )


    demand_change = (
        net_demand
        * intervals
    )


    # ========================================================
    # MODEL + REAL-TIME DATA
    # ========================================================

    # Difference between ML baseline and current real state

    baseline_difference = (
        current_available
        - current_ml_prediction
    )


    # Future prediction

    predicted_available = (

        future_ml_prediction

        + baseline_difference

        - demand_change

    )


    # ========================================================
    # SMALL TIME TREND
    # ========================================================

    # Add a small progression factor so that
    # 30 / 60 / 90 minute forecasts are not identical.

    time_progression = (
        minutes_ahead / 30
    )


    if future_entries > future_exits:

        predicted_available -= (
            0.5 * time_progression
        )

    else:

        predicted_available += (
            0.5 * time_progression
        )


    # ========================================================
    # LIMIT PREDICTION
    # ========================================================

    predicted_available = int(
        round(
            max(
                0,
                min(
                    total_slots,
                    predicted_available
                )
            )
        )
    )


    predicted_occupied = (
        total_slots
        - predicted_available
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "prediction_time":
            future_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "minutes_ahead":
            minutes_ahead,

        "total_slots":
            total_slots,

        "current_occupied":
            current_occupied,

        "current_available":
            current_available,

        "predicted_occupied":
            predicted_occupied,

        "predicted_available":
            predicted_available,

        "estimated_entries":
            future_entries,

        "estimated_exits":
            future_exits

    }


# ============================================================
# PREDICT CONGESTION PER FLOOR
# ============================================================

def predict_floor_congestion(model, minutes_ahead=30):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            floor,
            section,
            COUNT(*) AS total,
            SUM(CASE WHEN status='Occupied' THEN 1 ELSE 0 END) AS occupied,
            SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS available,
            AVG(CASE WHEN status='Occupied' THEN 1.0 ELSE 0.0 END) * 100
                AS occupancy_pct
        FROM parking_slots
        GROUP BY floor
        ORDER BY floor
    """)

    floors = cursor.fetchall()
    connection.close()

    now = datetime.now()
    future_time = now + timedelta(minutes=minutes_ahead)
    future_hour = future_time.hour
    future_day = future_time.weekday()
    future_entries, future_exits = get_demand(future_hour)

    results = []

    for floor in floors:

        total = floor["total"]
        occupied = floor["occupied"] or 0
        available = floor["available"] or 0
        current_pct = round(floor["occupancy_pct"] or 0, 1)

        # Use model to predict available slots for this floor
        # Scale entry/exit by floor proportion
        total_all = sum(f["total"] for f in floors)
        floor_ratio = total / total_all if total_all > 0 else 0.25

        floor_entries = max(1, round(future_entries * floor_ratio * 4))
        floor_exits = max(1, round(future_exits * floor_ratio * 4))

        input_data = pd.DataFrame([{
            "day": future_day,
            "hour": future_hour,
            "total_slots": total,
            "occupied_slots": occupied,
            "entry_count": floor_entries,
            "exit_count": floor_exits
        }])

        predicted_available = int(round(
            max(0, min(total, model.predict(input_data)[0]))
        ))

        predicted_occupied = total - predicted_available
        predicted_pct = round(predicted_occupied / total * 100, 1)

        # Congestion level
        if predicted_pct >= 85:
            congestion_level = "Critical"
        elif predicted_pct >= 65:
            congestion_level = "High"
        elif predicted_pct >= 40:
            congestion_level = "Medium"
        else:
            congestion_level = "Low"

        # Will it fill up?
        will_fill = predicted_pct >= 90

        results.append({
            "floor": floor["floor"],
            "section": floor["section"],
            "total_slots": total,
            "current_occupied": occupied,
            "current_available": available,
            "current_occupancy_pct": current_pct,
            "predicted_occupied": predicted_occupied,
            "predicted_available": predicted_available,
            "predicted_occupancy_pct": predicted_pct,
            "congestion_level": congestion_level,
            "will_fill_up": will_fill,
            "minutes_ahead": minutes_ahead
        })

    return results


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "AI PARKING AVAILABILITY PREDICTION"
    )

    print(
        "======================================"
    )


    # --------------------------------------------------------
    # Train model
    # --------------------------------------------------------

    model = train_model()


    # --------------------------------------------------------
    # Current status
    # --------------------------------------------------------

    (
        total,
        occupied,
        available
    ) = get_current_status()


    print()

    print(
        "CURRENT PARKING STATUS"
    )

    print(
        "--------------------------------------"
    )

    print(
        f"Total Slots     : {total}"
    )

    print(
        f"Occupied Slots  : {occupied}"
    )

    print(
        f"Available Slots : {available}"
    )


    # --------------------------------------------------------
    # Future predictions
    # --------------------------------------------------------

    print()

    print(
        "FUTURE AVAILABILITY"
    )

    print(
        "--------------------------------------"
    )


    for minutes in [30, 60, 90]:

        result = predict_availability(

            model,

            minutes

        )


        print()

        print(
            f"After {minutes} minutes:"
        )

        print(
            f"Prediction Time       : "
            f"{result['prediction_time']}"
        )

        print(
            f"Predicted Occupied   : "
            f"{result['predicted_occupied']}"
        )

        print(
            f"Predicted Available  : "
            f"{result['predicted_available']}"
        )

        print(
            f"Estimated Entries    : "
            f"{result['estimated_entries']}"
        )

        print(
            f"Estimated Exits      : "
            f"{result['estimated_exits']}"
        )


    print()

    print(
        "======================================"
    )

    print(
        "Prediction completed successfully!"
    )

    print(
        "======================================"
    )