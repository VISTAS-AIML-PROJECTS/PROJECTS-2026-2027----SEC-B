import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "parking.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_parking_slots():
    connection = get_connection()
    cursor = connection.cursor()

    # Floor 1: A1 - A10 (CCTV + Good lighting, near security)
    for i in range(1, 11):
        slot_id = f"A{i}"
        cursor.execute("""
            INSERT OR IGNORE INTO parking_slots
            (slot_id, floor, section, status)
            VALUES (?, ?, ?, ?)
        """, (
            slot_id, 1, "A",
            "Occupied" if i in (1, 3, 5, 7) else "Available"
        ))

    # Floor 2: B1 - B10 (CCTV, medium traffic)
    for i in range(1, 11):
        slot_id = f"B{i}"
        cursor.execute("""
            INSERT OR IGNORE INTO parking_slots
            (slot_id, floor, section, status)
            VALUES (?, ?, ?, ?)
        """, (
            slot_id, 2, "B",
            "Reserved" if i in (2, 4) else
            "Occupied" if i in (6, 8, 10) else "Available"
        ))

    # Floor 3: C1 - C10 (No CCTV, poor lighting, high congestion)
    for i in range(1, 11):
        slot_id = f"C{i}"
        cursor.execute("""
            INSERT OR IGNORE INTO parking_slots
            (slot_id, floor, section, status)
            VALUES (?, ?, ?, ?)
        """, (
            slot_id, 3, "C",
            "Occupied" if i in (1, 2, 3, 5, 9) else "Available",
        ))

    # Floor 4: D1 - D10 (CCTV, good lighting, low congestion — premium)
    for i in range(1, 11):
        slot_id = f"D{i}"
        cursor.execute("""
            INSERT OR IGNORE INTO parking_slots
            (slot_id, floor, section, status)
            VALUES (?, ?, ?, ?)
        """, (
            slot_id, 4, "D",
            "Reserved" if i in (1, 3, 5) else
            "Occupied" if i in (7, 9) else "Available"
        ))

    connection.commit()
    connection.close()

    print("40 parking slots created successfully!")


def get_all_slots():
    connection = get_connection()

    slots = connection.execute("""
        SELECT slot_id, floor, section, status
        FROM parking_slots
        ORDER BY floor, slot_id
    """).fetchall()

    connection.close()

    return [dict(slot) for slot in slots]


def get_slot(slot_id):
    connection = get_connection()

    slot = connection.execute("""
        SELECT slot_id, floor, section, status
        FROM parking_slots
        WHERE slot_id = ?
    """, (slot_id,)).fetchone()

    connection.close()

    if slot:
        return dict(slot)

    return None


def update_slot_status(slot_id, status):
    allowed_status = ["Available", "Occupied", "Reserved"]

    if status not in allowed_status:
        return False

    connection = get_connection()

    cursor = connection.execute("""
        UPDATE parking_slots
        SET status = ?
        WHERE slot_id = ?
    """, (status, slot_id))

    connection.commit()
    connection.close()

    return cursor.rowcount > 0


if __name__ == "__main__":
    create_parking_slots()

    print("\nParking Slots:")
    print("-" * 60)

    slots = get_all_slots()

    for slot in slots:
        print(
            f"{slot['slot_id']} | "
            f"Floor {slot['floor']} | "
            f"Section {slot['section']} | "
            f"{slot['status']}"
        )