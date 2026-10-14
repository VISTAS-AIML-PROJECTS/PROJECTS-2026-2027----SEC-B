import sqlite3
from pathlib import Path

# Database location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "parking.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    """)

    # Vehicles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            number_plate TEXT UNIQUE NOT NULL,
            vehicle_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Parking slots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            slot_id TEXT PRIMARY KEY,
            floor INTEGER NOT NULL,
            section TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available'
        )
    """)

    # Bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            slot_id TEXT,
            booking_time TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'Confirmed',
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
            FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
        )
    """)

    # Parking history for ML
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            day_of_week TEXT,
            hour INTEGER,
            total_slots INTEGER,
            occupied_slots INTEGER,
            available_slots INTEGER,
            entry_count INTEGER,
            exit_count INTEGER
        )
    """)

    # Parking sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            slot_id TEXT,
            entry_time TEXT,
            exit_time TEXT,
            duration_minutes INTEGER,
            amount REAL,
            status TEXT DEFAULT 'Active',
            entry_type TEXT DEFAULT 'Walk-in',
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
            FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'Medium',
            number_plate TEXT,
            slot_id TEXT,
            message TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            number_plate TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            read_at TEXT
        )
    """)

    # Payments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            amount REAL,
            payment_time TEXT,
            payment_status TEXT DEFAULT 'Pending',
            FOREIGN KEY (session_id) REFERENCES parking_sessions(session_id)
        )
    """)

    # Admin users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            admin_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            role       TEXT DEFAULT 'admin'
        )
    """)

    # Seed default admin and user if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO admin_users (username, password, role)
        VALUES ('admin', 'admin123', 'admin')
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO admin_users (username, password, role)
        VALUES ('user', 'user123', 'user')
    """)

    session_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(parking_sessions)")
    }
    if "entry_type" not in session_columns:
        cursor.execute(
            "ALTER TABLE parking_sessions ADD COLUMN entry_type TEXT DEFAULT 'Walk-in'"
        )

    connection.commit()
    connection.close()

    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()