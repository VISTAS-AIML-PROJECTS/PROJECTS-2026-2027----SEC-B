import json
from datetime import datetime, timedelta

from .database import get_connection


def _now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def notify_user(number_plate, category, message):
    connection = get_connection()
    existing = connection.execute(
        """
        SELECT notification_id FROM notifications
        WHERE number_plate = ? AND category = ? AND message = ?
        AND created_at >= ?
        LIMIT 1
        """,
        (
            number_plate.strip().upper().replace(" ", ""),
            category,
            message,
            (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        )
    ).fetchone()
    if existing:
        connection.close()
        return existing["notification_id"]
    connection.execute(
        """
        INSERT INTO notifications (number_plate, category, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (number_plate.strip().upper().replace(" ", ""), category, message, _now_string())
    )
    connection.commit()
    notification_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.close()
    return notification_id


def record_alert(alert_type, message, severity="Medium", number_plate=None,
                 slot_id=None, details=None):
    connection = get_connection()
    cursor = connection.cursor()
    cutoff = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        SELECT alert_id FROM parking_alerts
        WHERE alert_type = ? AND status = 'Open'
        AND COALESCE(number_plate, '') = COALESCE(?, '')
        AND COALESCE(slot_id, '') = COALESCE(?, '')
        AND created_at >= ?
        LIMIT 1
        """,
        (alert_type, number_plate, slot_id, cutoff)
    )
    existing = cursor.fetchone()
    if existing:
        connection.close()
        return existing["alert_id"]

    cursor.execute(
        """
        INSERT INTO parking_alerts
            (alert_type, severity, number_plate, slot_id, message, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert_type,
            severity,
            number_plate,
            slot_id,
            message,
            json.dumps(details or {}),
            _now_string(),
        )
    )
    alert_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return alert_id


def record_vision_observation(observation):
    number_plate = observation.get("number_plate", "").strip().upper().replace(" ", "") or None
    slot_id = observation.get("slot_id", "").strip().upper() or None
    alerts = []

    if number_plate and slot_id:
        connection = get_connection()
        session = connection.execute(
            """
            SELECT slot_id FROM parking_sessions
            WHERE status = 'Active' AND vehicle_id = (
                SELECT vehicle_id FROM vehicles WHERE number_plate = ?
            )
            ORDER BY session_id DESC LIMIT 1
            """,
            (number_plate,)
        ).fetchone()
        connection.close()
        if session and session["slot_id"] != slot_id:
            alerts.append((
                "Slot Mismatch",
                f"{number_plate} is assigned to {session['slot_id']} but detected in {slot_id}.",
                "High",
                session["slot_id"],
            ))

    checks = (
        ("vehicle_count", lambda value: value > 1, "Double Parking", "Multiple vehicles are detected in one parking slot.", "High"),
        ("improper_parking", bool, "Improper Parking", "A vehicle is outside its assigned parking area.", "Medium"),
        ("aisle_obstructed", bool, "Aisle Obstruction", "A vehicle is obstructing a configured aisle zone.", "High"),
    )
    for key, predicate, alert_type, message, severity in checks:
        if predicate(observation.get(key, 0)):
            alerts.append((alert_type, message, severity, slot_id))

    created = []
    for alert_type, message, severity, alert_slot in alerts:
        alert_id = record_alert(
            alert_type,
            message,
            severity,
            number_plate,
            alert_slot,
            observation,
        )
        created.append({"alert_id": alert_id, "type": alert_type, "message": message})
        if number_plate:
            notify_user(number_plate, "Parking Alert", message)

    return {"success": True, "alerts": created, "total": len(created)}


def get_open_alerts():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT alert_id, alert_type, severity, number_plate, slot_id,
               message, details, status, created_at
        FROM parking_alerts
        WHERE status = 'Open'
        AND lower(alert_type) NOT IN ('overstay', 'long stay')
        ORDER BY CASE severity WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,
                 created_at DESC
        """
    ).fetchall()
    connection.close()
    alerts = [dict(row) for row in rows]
    for alert in alerts:
        alert["details"] = json.loads(alert["details"] or "{}")
    return {"total": len(alerts), "alerts": alerts}


def get_user_notifications(number_plate):
    plate = number_plate.strip().upper().replace(" ", "")
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT notification_id, category, message, created_at, read_at
        FROM notifications WHERE number_plate = ?
        ORDER BY notification_id DESC LIMIT 100
        """,
        (plate,)
    ).fetchall()
    connection.close()
    return {"number_plate": plate, "notifications": [dict(row) for row in rows]}


def get_walk_in_sessions():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT ps.session_id, ps.slot_id, ps.entry_time, ps.status,
               v.number_plate, v.vehicle_type, u.name AS owner_name
        FROM parking_sessions ps
        JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
        LEFT JOIN users u ON u.user_id = v.user_id
        WHERE ps.entry_type = 'Walk-in'
        AND ps.status IN ('Active', 'Awaiting Payment')
        ORDER BY ps.session_id DESC
        """
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]