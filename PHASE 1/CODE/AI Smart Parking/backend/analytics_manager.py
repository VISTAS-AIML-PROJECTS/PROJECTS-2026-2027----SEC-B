from datetime import datetime
from .database import get_connection


# ============================================================
# LOG PARKING HISTORY
# ============================================================

def log_parking_history():

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) AS occupied,
            SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available
        FROM parking_slots
        """
    )

    counts = cursor.fetchone()

    total = counts["total"] or 0
    occupied = counts["occupied"] or 0
    available = counts["available"] or 0

    cursor.execute(
        """
        SELECT
            COUNT(*) AS entries
        FROM parking_sessions
        WHERE DATE(entry_time) = DATE('now')
        AND strftime('%H', entry_time) = ?
        """,
        (now.strftime("%H"),)
    )

    entry_count = cursor.fetchone()["entries"] or 0

    cursor.execute(
        """
        SELECT
            COUNT(*) AS exits
        FROM parking_sessions
        WHERE DATE(exit_time) = DATE('now')
        AND strftime('%H', exit_time) = ?
        AND status = 'Completed'
        """,
        (now.strftime("%H"),)
    )

    exit_count = cursor.fetchone()["exits"] or 0

    cursor.execute(
        """
        INSERT INTO parking_history
        (
            timestamp,
            day_of_week,
            hour,
            total_slots,
            occupied_slots,
            available_slots,
            entry_count,
            exit_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now.strftime("%Y-%m-%d %H:%M:%S"),
            now.strftime("%A"),
            now.hour,
            total,
            occupied,
            available,
            entry_count,
            exit_count
        )
    )

    connection.commit()
    connection.close()


# ============================================================
# OCCUPANCY RATE BY HOUR (TODAY)
# ============================================================

def get_hourly_occupancy():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            hour,
            AVG(CAST(occupied_slots AS REAL) / NULLIF(total_slots, 0) * 100)
                AS occupancy_rate,
            AVG(occupied_slots) AS avg_occupied,
            AVG(available_slots) AS avg_available
        FROM parking_history
        WHERE DATE(timestamp) = DATE('now')
        GROUP BY hour
        ORDER BY hour
        """
    )

    rows = cursor.fetchall()

    connection.close()

    hourly = [
        {
            "hour": row["hour"],
            "hour_label": f"{row['hour']:02d}:00",
            "occupancy_rate": round(row["occupancy_rate"] or 0, 1),
            "avg_occupied": round(row["avg_occupied"] or 0, 1),
            "avg_available": round(row["avg_available"] or 0, 1)
        }
        for row in rows
    ]

    return hourly


# ============================================================
# PEAK HOUR (TODAY)
# ============================================================

def get_peak_hour():

    hourly = get_hourly_occupancy()

    if not hourly:
        return None

    return max(
        hourly,
        key=lambda x: x["occupancy_rate"]
    )


# ============================================================
# REVENUE SUMMARY
# ============================================================

def get_revenue_summary():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS today_revenue,
            COUNT(*) AS today_sessions
        FROM parking_sessions
        WHERE DATE(exit_time) = DATE('now')
        AND status = 'Completed'
        """
    )

    today = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total_revenue,
            COUNT(*) AS total_sessions
        FROM parking_sessions
        WHERE status = 'Completed'
        """
    )

    overall = cursor.fetchone()

    connection.close()

    return {
        "today_revenue": round(today["today_revenue"], 2),
        "today_sessions": today["today_sessions"],
        "total_revenue": round(overall["total_revenue"], 2),
        "total_sessions": overall["total_sessions"]
    }


# ============================================================
# FULL OCCUPANCY ANALYTICS
# ============================================================

def get_occupancy_analytics():

    hourly = get_hourly_occupancy()

    peak = get_peak_hour()

    revenue = get_revenue_summary()

    connection = get_connection()
    cursor = connection.cursor()

    # Overall today occupancy
    cursor.execute(
        """
        SELECT
            AVG(CAST(occupied_slots AS REAL) / NULLIF(total_slots, 0) * 100)
                AS avg_occupancy
        FROM parking_history
        WHERE DATE(timestamp) = DATE('now')
        """
    )

    row = cursor.fetchone()

    avg_occupancy_today = round(
        row["avg_occupancy"] or 0,
        1
    )

    # Total entries and exits today
    cursor.execute(
        """
        SELECT
            COUNT(*) AS entries
        FROM parking_sessions
        WHERE DATE(entry_time) = DATE('now')
        """
    )

    entries_today = cursor.fetchone()["entries"]

    cursor.execute(
        """
        SELECT
            COUNT(*) AS exits
        FROM parking_sessions
        WHERE DATE(exit_time) = DATE('now')
        AND status = 'Completed'
        """
    )

    exits_today = cursor.fetchone()["exits"]

    connection.close()

    return {

        "success": True,

        "date": datetime.now().strftime("%Y-%m-%d"),

        "avg_occupancy_today":
            avg_occupancy_today,

        "entries_today":
            entries_today,

        "exits_today":
            exits_today,

        "peak_hour":
            peak,

        "hourly_breakdown":
            hourly,

        "revenue":
            revenue

    }
