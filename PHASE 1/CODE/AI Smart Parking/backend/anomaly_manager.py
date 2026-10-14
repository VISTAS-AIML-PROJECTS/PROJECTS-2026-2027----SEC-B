from datetime import datetime
from .database import get_connection
from .slot_manager import get_all_slots


# ============================================================
# NO-SHOW BOOKING (booked slot, vehicle never arrived > 30 min)
# ============================================================

# ============================================================
# ============================================================

def detect_no_show_bookings(expiry_minutes=30):

    connection = get_connection()
    cursor = connection.cursor()

    cutoff = (
        datetime.now()
        .__class__.now()
    )

    cursor.execute("""
        SELECT
            b.booking_id,
            b.slot_id,
            b.booking_time,
            v.number_plate,
            u.name AS owner_name
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        WHERE b.status = 'Confirmed'
        AND NOT EXISTS (
            SELECT 1 FROM parking_sessions ps
            WHERE ps.vehicle_id = b.vehicle_id
            AND ps.slot_id = b.slot_id
            AND ps.status = 'Active'
        )
    """)

    bookings = cursor.fetchall()
    connection.close()

    anomalies = []

    for b in bookings:

        try:
            booked_at = datetime.strptime(
                b["booking_time"], "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            continue

        minutes_waiting = (
            datetime.now() - booked_at
        ).total_seconds() / 60

        if minutes_waiting >= expiry_minutes:

            anomalies.append({
                "type":         "No-Show Booking",
                "severity":     "Low",
                "booking_id":   b["booking_id"],
                "slot_id":      b["slot_id"],
                "number_plate": b["number_plate"],
                "owner_name":   b["owner_name"] or "Unknown",
                "booking_time": b["booking_time"],
                "minutes_waiting": round(minutes_waiting, 1),
                "message": (
                    f"Booking #{b['booking_id']} for {b['number_plate']} "
                    f"has not arrived after {round(minutes_waiting, 1)} min."
                )
            })

    return anomalies


# ============================================================
# DUPLICATE ACTIVE SESSIONS (same plate, 2 slots)
# ============================================================

def detect_duplicate_sessions():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            v.number_plate,
            COUNT(ps.session_id) AS active_count,
            GROUP_CONCAT(ps.slot_id) AS slots
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.vehicle_id
        WHERE ps.status = 'Active'
        GROUP BY ps.vehicle_id
        HAVING active_count > 1
    """)

    rows = cursor.fetchall()
    connection.close()

    anomalies = []

    for row in rows:
        anomalies.append({
            "type":         "Duplicate Session",
            "severity":     "High",
            "number_plate": row["number_plate"],
            "active_count": row["active_count"],
            "slots":        row["slots"],
            "message": (
                f"{row['number_plate']} has {row['active_count']} "
                f"active sessions in slots: {row['slots']}."
            )
        })

    return anomalies


# ============================================================
# ALL ANOMALIES
# ============================================================

def _limit_anomalies_to_capacity(anomalies):
    slot_count = len(get_all_slots())
    if slot_count <= 0:
        return anomalies

    seen = set()
    limited = []
    for item in anomalies:
        key = (
            item.get("type"),
            item.get("slot_id"),
            item.get("number_plate"),
            item.get("session_id"),
            item.get("booking_id")
        )
        if key in seen:
            continue
        seen.add(key)
        limited.append(item)
        if len(limited) >= slot_count:
            break

    return limited


def get_all_anomalies():

    no_shows    = detect_no_show_bookings()
    duplicates  = detect_duplicate_sessions()

    all_anomalies = _limit_anomalies_to_capacity(no_shows + duplicates)

    high   = [a for a in all_anomalies if a["severity"] == "High"]
    medium = [a for a in all_anomalies if a["severity"] == "Medium"]
    low    = [a for a in all_anomalies if a["severity"] == "Low"]

    return {
        "total":      len(all_anomalies),
        "high":       len(high),
        "medium":     len(medium),
        "low":        len(low),
        "anomalies":  high + medium + low
    }
