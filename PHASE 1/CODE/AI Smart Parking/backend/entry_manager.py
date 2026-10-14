from datetime import datetime
import re
from .database import get_connection
from .billing_manager import calculate_dynamic_bill
from .monitoring_manager import notify_user


# ============================================================
# SUPPORTED VEHICLE TYPES
# ============================================================

SUPPORTED_VEHICLE_TYPES = {
    "Car",
    "Bike",
    "Bus",
    "Truck"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_plate(number_plate):

    return (
        number_plate
        .strip()
        .upper()
        .replace(" ", "")
    )


def normalize_detected_plate(number_plate):
    plate = normalize_plate(number_plate)
    if len(plate) not in {9, 10}:
        return ""

    digit_confusions = str.maketrans({
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "9",
    })
    letter_confusions = str.maketrans({
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    })
    series_end = len(plate) - 4
    normalized = (
        plate[:2]
        + plate[2:4].translate(digit_confusions)
        + plate[4:series_end].translate(letter_confusions)
        + plate[series_end:].translate(digit_confusions)
    )
    if re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}", normalized):
        return normalized
    return ""


def normalize_vehicle_type(vehicle_type):

    if not vehicle_type:
        return "Car"

    vehicle_type = vehicle_type.strip().title()

    if vehicle_type not in SUPPORTED_VEHICLE_TYPES:
        return "Car"

    return vehicle_type


# ============================================================
# VEHICLE REGISTRATION
# ============================================================

def register_vehicle(
    name,
    number_plate,
    vehicle_type="Car",
    phone="",
    email=""
):

    number_plate = normalize_plate(number_plate)

    vehicle_type = normalize_vehicle_type(
        vehicle_type
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check existing vehicle
        cursor.execute(
            """
            SELECT
                vehicle_id,
                user_id,
                number_plate,
                vehicle_type
            FROM vehicles
            WHERE number_plate = ?
            LIMIT 1
            """,
            (number_plate,)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE vehicles
                SET vehicle_type = ?
                WHERE vehicle_id = ?
                """,
                (
                    vehicle_type,
                    existing["vehicle_id"]
                )
            )

            connection.commit()
            connection.close()

            return {
                "success": True,
                "message": "Vehicle already registered",
                "vehicle_id": existing["vehicle_id"],
                "number_plate": number_plate,
                "vehicle_type": vehicle_type
            }

        # Create user
        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                phone,
                email
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                phone,
                email
            )
        )

        user_id = cursor.lastrowid

        # Create vehicle
        cursor.execute(
            """
            INSERT INTO vehicles
            (
                user_id,
                number_plate,
                vehicle_type
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                number_plate,
                vehicle_type
            )
        )

        vehicle_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return {
            "success": True,
            "message": "Vehicle registered successfully",
            "vehicle_id": vehicle_id,
            "number_plate": number_plate,
            "vehicle_type": vehicle_type
        }

    except Exception as error:

        connection.rollback()
        connection.close()

        return {
            "success": False,
            "message": str(error)
        }


# ============================================================
# FIND VEHICLE
# ============================================================

def find_vehicle(number_plate):

    number_plate = normalize_plate(
        number_plate
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            v.vehicle_id,
            v.number_plate,
            v.vehicle_type,

            u.user_id,
            u.name,
            u.phone,
            u.email

        FROM vehicles v

        LEFT JOIN users u
            ON v.user_id = u.user_id

        WHERE v.number_plate = ?

        LIMIT 1
        """,
        (number_plate,)
    )

    vehicle = cursor.fetchone()

    connection.close()

    if vehicle:
        return dict(vehicle)

    return None


# ============================================================
# FIND AVAILABLE SLOT
# ============================================================

def find_available_slot():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT available.*
        FROM parking_slots AS available
        WHERE available.status = 'Available'
        ORDER BY
            (
                SELECT COUNT(*)
                FROM parking_slots AS occupied
                WHERE occupied.floor = available.floor
                AND occupied.status = 'Occupied'
            ),
            available.floor,
            available.section,
            available.slot_id

        LIMIT 1
        """
    )

    slot = cursor.fetchone()

    connection.close()

    if slot:
        return dict(slot)

    return None


# ============================================================
# VEHICLE ENTRY
# ============================================================

def vehicle_entry(
    number_plate,
    vehicle_type="Car"
):

    number_plate = normalize_plate(
        number_plate
    )

    vehicle_type = normalize_vehicle_type(
        vehicle_type
    )

    vehicle = find_vehicle(
        number_plate
    )

    # --------------------------------------------------------
    # AUTO REGISTER VEHICLE
    # --------------------------------------------------------

    if vehicle is None:

        registration = register_vehicle(
            "Unknown Owner",
            number_plate,
            vehicle_type
        )

        if not registration["success"]:

            return registration

        vehicle = find_vehicle(
            number_plate
        )

    # --------------------------------------------------------
    # CHECK ACTIVE SESSION
    # --------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *

        FROM parking_sessions

        WHERE vehicle_id = ?

        AND status = 'Active'

        ORDER BY session_id DESC

        LIMIT 1
        """,
        (
            vehicle["vehicle_id"],
        )
    )

    active_session = cursor.fetchone()

    connection.close()

    if active_session:

        return {

            "success": False,

            "message":
                "Vehicle is already inside parking",

            "number_plate":
                number_plate,

            "vehicle_type":
                vehicle["vehicle_type"],

            "slot_id":
                active_session["slot_id"],

            "session_id":
                active_session["session_id"],

            "entry_time":
                active_session["entry_time"]

        }

    # --------------------------------------------------------
    # HONOR A CONFIRMED BOOKING, OTHERWISE BALANCE WALK-INS
    # --------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT p.*, b.booking_id
        FROM bookings AS b
        JOIN parking_slots AS p ON p.slot_id = b.slot_id
        WHERE b.vehicle_id = ?
        AND b.status = 'Confirmed'
        AND p.status = 'Reserved'
        ORDER BY b.booking_id DESC
        LIMIT 1
        """,
        (vehicle["vehicle_id"],)
    )
    booked_slot = cursor.fetchone()
    connection.close()

    booking_id = None
    if booked_slot:
        slot = dict(booked_slot)
        booking_id = slot.pop("booking_id")
    else:
        slot = find_available_slot()

    if slot is None:

        return {

            "success": False,

            "message":
                "No parking slot available",

            "number_plate":
                number_plate

        }

    # --------------------------------------------------------
    # ENTRY TIME
    # --------------------------------------------------------

    entry_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        connection.execute("BEGIN IMMEDIATE")
        cursor.execute(
            """
            SELECT session_id
            FROM parking_sessions
            WHERE vehicle_id = ? AND status IN ('Active', 'Awaiting Payment')
            LIMIT 1
            """,
            (vehicle["vehicle_id"],)
        )
        if cursor.fetchone():
            connection.rollback()
            connection.close()
            return {
                "success": False,
                "message": "Vehicle already has an active parking session",
                "number_plate": number_plate,
            }

        expected_status = "Reserved" if booking_id is not None else "Available"
        cursor.execute(
            """
            UPDATE parking_slots
            SET status = 'Occupied'
            WHERE slot_id = ? AND status = ?
            """,
            (slot["slot_id"], expected_status)
        )
        if cursor.rowcount == 0:
            connection.rollback()
            connection.close()
            return {
                "success": False,
                "message": "The assigned slot is no longer available. Please retry.",
                "number_plate": number_plate,
            }

        # Create session
        cursor.execute(
            """
            INSERT INTO parking_sessions
            (
                vehicle_id,
                slot_id,
                entry_time,
                status,
                entry_type
            )
            VALUES (?, ?, ?, 'Active', ?)
            """,
            (
                vehicle["vehicle_id"],
                slot["slot_id"],
                entry_time,
                "Booking" if booking_id is not None else "Walk-in"
            )
        )

        session_id = cursor.lastrowid

        if booking_id is not None:
            cursor.execute(
                """
                UPDATE bookings
                SET status = 'Checked In'
                WHERE booking_id = ?
                AND status = 'Confirmed'
                """,
                (booking_id,)
            )

        connection.commit()

    except Exception as error:

        connection.rollback()
        connection.close()

        return {

            "success": False,

            "message":
                f"Entry error: {str(error)}"

        }

    connection.close()

    notify_user(
        number_plate,
        "Parking Entry",
        f"Vehicle entered and was assigned to slot {slot['slot_id']}.",
    )

    return {

        "success": True,

        "message":
            "Vehicle entry recorded",

        "session_id":
            session_id,

        "vehicle_id":
            vehicle["vehicle_id"],

        "number_plate":
            number_plate,

        "vehicle_type":
            vehicle["vehicle_type"],

        "owner_name":
            vehicle["name"]
            or "Unknown Owner",

        "phone":
            vehicle["phone"]
            or "Not Available",

        "email":
            vehicle["email"]
            or "Not Available",

        "slot_id":
            slot["slot_id"],

        "entry_type":
            "Booking" if booking_id is not None else "Walk-in",

        "booking_id":
            booking_id,

        "floor":
            slot["floor"],

        "section":
            slot["section"],

        "entry_time":
            entry_time,

        "status":
            "Active"

    }


# ============================================================
# VEHICLE EXIT
# ============================================================

def vehicle_exit(number_plate):

    number_plate = normalize_plate(
        number_plate
    )

    vehicle = find_vehicle(
        number_plate
    )

    if vehicle is None:

        return {

            "success": False,

            "message":
                "Vehicle not registered",

            "number_plate":
                number_plate

        }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *

        FROM parking_sessions

        WHERE vehicle_id = ?

        AND status = 'Active'

        ORDER BY session_id DESC

        LIMIT 1
        """,
        (
            vehicle["vehicle_id"],
        )
    )

    session = cursor.fetchone()

    if session is None:

        connection.close()

        return {

            "success": False,

            "message":
                "No active parking session found",

            "number_plate":
                number_plate

        }

    # --------------------------------------------------------
    # CALCULATE DURATION
    # --------------------------------------------------------

    entry_time = datetime.strptime(
        session["entry_time"],
        "%Y-%m-%d %H:%M:%S"
    )

    exit_time = datetime.now()

    duration = int(
        (
            exit_time - entry_time
        ).total_seconds() / 60
    )

    duration = max(
        duration,
        1
    )

    # --------------------------------------------------------
    bill = calculate_dynamic_bill(
        vehicle["vehicle_type"],
        duration
    )
    amount = bill["amount"]

    exit_time_string = (
        exit_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # --------------------------------------------------------
    # COMPLETE SESSION
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE parking_sessions

        SET
            exit_time = ?,
            duration_minutes = ?,
            amount = ?,
            status = 'Awaiting Payment'

        WHERE session_id = ?
        """,
        (
            exit_time_string,
            duration,
            amount,
            session["session_id"]
        )
    )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO payments
        (
            session_id,
            amount,
            payment_time,
            payment_status
        )
        VALUES (?, ?, ?, 'Pending')
        """,
        (
            session["session_id"],
            amount,
            exit_time_string
        )
    )

    connection.commit()
    connection.close()

    notify_user(
        number_plate,
        "Payment Due",
        f"Parking charge of ₹{amount:.2f} is ready for payment.",
    )

    return {

        "success": True,

        "message":
            "Vehicle exit calculated",

        "session_id":
            session["session_id"],

        "number_plate":
            number_plate,

        "vehicle_type":
            vehicle["vehicle_type"],

        "owner_name":
            vehicle["name"]
            or "Unknown Owner",

        "slot_id":
            session["slot_id"],

        "entry_time":
            session["entry_time"],

        "exit_time":
            exit_time_string,

        "duration_minutes":
            duration,

        "amount":
            amount,

        "bill":
            bill,

        "payment_status":
            "Pending",

        "status":
            "Awaiting Payment"

    }


# ============================================================
# FIND MY CAR / BIKE
# ============================================================

def find_my_car(number_plate):

    number_plate = normalize_plate(
        number_plate
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            ps.session_id,
            ps.slot_id,
            ps.entry_time,
            ps.status,

            p.floor,
            p.section,

            v.number_plate,
            v.vehicle_type,

            u.name AS owner_name,
            u.phone,
            u.email

        FROM parking_sessions ps

        JOIN vehicles v
            ON ps.vehicle_id = v.vehicle_id

        JOIN parking_slots p
            ON ps.slot_id = p.slot_id

        LEFT JOIN users u
            ON v.user_id = u.user_id

        WHERE v.number_plate = ?

        AND ps.status = 'Active'

        ORDER BY ps.session_id DESC

        LIMIT 1
        """,
        (
            number_plate,
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return {

            "success": False,

            "message":
                "No active parking session found for this vehicle.",

            "vehicle_number":
                number_plate

        }

    return {

        "success": True,

        "message":
            "Vehicle location found successfully.",

        "vehicle_number":
            result["number_plate"],

        "vehicle_type":
            result["vehicle_type"],

        "owner_name":
            result["owner_name"]
            or "Unknown Owner",

        "phone":
            result["phone"]
            or "Not Available",

        "email":
            result["email"]
            or "Not Available",

        "session_id":
            result["session_id"],

        "floor":
            result["floor"],

        "section":
            result["section"],

        "slot_id":
            result["slot_id"],

        "entry_time":
            result["entry_time"],

        "status":
            result["status"]

    }


# ============================================================
# VEHICLE HISTORY
# ============================================================

def get_vehicle_history(number_plate):

    number_plate = normalize_plate(number_plate)

    vehicle = find_vehicle(number_plate)

    if vehicle is None:

        return {
            "success": False,
            "message": "Vehicle not found.",
            "number_plate": number_plate
        }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            ps.session_id,
            ps.slot_id,
            ps.entry_time,
            ps.exit_time,
            ps.duration_minutes,
            ps.amount,
            ps.status,
            p.floor,
            p.section

        FROM parking_sessions ps

        JOIN parking_slots p
            ON ps.slot_id = p.slot_id

        WHERE ps.vehicle_id = ?

        ORDER BY ps.session_id DESC
        """,
        (vehicle["vehicle_id"],)
    )

    sessions = [
        dict(row)
        for row in cursor.fetchall()
    ]

    # Aggregate stats
    completed = [
        s for s in sessions
        if s["status"] == "Completed"
    ]

    total_spent = sum(
        s["amount"] or 0
        for s in completed
    )

    total_minutes = sum(
        s["duration_minutes"] or 0
        for s in completed
    )

    # Most used slot
    slot_counts = {}
    for s in completed:
        slot_counts[s["slot_id"]] = (
            slot_counts.get(s["slot_id"], 0) + 1
        )

    favourite_slot = (
        max(slot_counts, key=slot_counts.get)
        if slot_counts
        else None
    )

    connection.close()

    return {

        "success": True,

        "number_plate":
            number_plate,

        "owner_name":
            vehicle["name"] or "Unknown Owner",

        "vehicle_type":
            vehicle["vehicle_type"],

        "phone":
            vehicle["phone"] or "Not Available",

        "email":
            vehicle["email"] or "Not Available",

        "total_visits":
            len(completed),

        "total_spent":
            round(total_spent, 2),

        "total_hours_parked":
            round(total_minutes / 60, 2),

        "favourite_slot":
            favourite_slot,

        "sessions":
            sessions

    }


# ============================================================
# GET VEHICLE DETAILS BY SLOT
# ============================================================

def get_vehicle_by_slot(slot_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            ps.session_id,
            ps.slot_id,
            ps.entry_time,
            ps.status,

            v.vehicle_id,
            v.number_plate,
            v.vehicle_type,

            u.user_id,
            u.name AS owner_name,
            u.phone,
            u.email

        FROM parking_sessions ps

        JOIN vehicles v
            ON ps.vehicle_id = v.vehicle_id

        LEFT JOIN users u
            ON v.user_id = u.user_id

        WHERE ps.slot_id = ?

        AND ps.status = 'Active'

        ORDER BY ps.session_id DESC

        LIMIT 1
        """,
        (
            slot_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return dict(result)