from datetime import datetime, timedelta
from .database import get_connection


# ============================================================
# NORMALIZE
# ============================================================

def normalize_plate(number_plate):

    return (
        number_plate
        .strip()
        .upper()
        .replace(" ", "")
    )


def normalize_vehicle_type(vehicle_type):

    allowed = {
        "Car",
        "Bike",
        "Bus",
        "Truck"
    }

    if not vehicle_type:
        return "Car"

    vehicle_type = vehicle_type.strip().title()

    if vehicle_type not in allowed:
        return "Car"

    return vehicle_type


# ============================================================
# BOOK SLOT
# ============================================================

def book_slot(
    name,
    number_plate,
    vehicle_type,
    slot_id,
    phone="",
    email="",
    start_time="",
    end_time=""
):

    number_plate = normalize_plate(
        number_plate
    )

    vehicle_type = normalize_vehicle_type(
        vehicle_type
    )

    slot_id = slot_id.strip().upper()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CHECK SLOT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *

            FROM parking_slots

            WHERE slot_id = ?

            LIMIT 1
            """,
            (
                slot_id,
            )
        )

        slot = cursor.fetchone()

        if slot is None:

            return {
                "success": False,
                "message": "Parking slot not found."
            }

        if slot["status"] != "Available":

            return {

                "success": False,

                "message":
                    f"Slot {slot_id} is not available."

            }

        # ----------------------------------------------------
        # CHECK VEHICLE
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *

            FROM vehicles

            WHERE number_plate = ?

            LIMIT 1
            """,
            (
                number_plate,
            )
        )

        vehicle = cursor.fetchone()

        # ----------------------------------------------------
        # CHECK ACTIVE SESSION
        # ----------------------------------------------------

        if vehicle:

            cursor.execute(
                """
                SELECT session_id

                FROM parking_sessions

                WHERE vehicle_id = ?

                AND status = 'Active'

                LIMIT 1
                """,
                (
                    vehicle["vehicle_id"],
                )
            )

            active_session = cursor.fetchone()

            if active_session:

                connection.close()

                return {

                    "success": False,

                    "message":
                        "This vehicle is already parked."

                }

        # ----------------------------------------------------
        # CREATE / FIND USER
        # ----------------------------------------------------

        user_id = None

        if vehicle:

            user_id = vehicle["user_id"]

        else:

            if phone or email:

                cursor.execute(
                    """
                    SELECT user_id

                    FROM users

                    WHERE
                        (phone = ? AND phone != '')
                        OR
                        (email = ? AND email != '')

                    LIMIT 1
                    """,
                    (
                        phone,
                        email
                    )
                )

                existing_user = cursor.fetchone()

            else:

                existing_user = None

            if existing_user:

                user_id = existing_user["user_id"]

                cursor.execute(
                    """
                    UPDATE users

                    SET
                        name = ?,
                        phone = ?,
                        email = ?

                    WHERE user_id = ?
                    """,
                    (
                        name,
                        phone,
                        email,
                        user_id
                    )
                )

            else:

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

        # ----------------------------------------------------
        # CREATE / UPDATE VEHICLE
        # ----------------------------------------------------

        if vehicle:

            vehicle_id = vehicle["vehicle_id"]

            cursor.execute(
                """
                UPDATE vehicles

                SET
                    user_id = ?,
                    vehicle_type = ?

                WHERE vehicle_id = ?
                """,
                (
                    user_id,
                    vehicle_type,
                    vehicle_id
                )
            )

        else:

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

        # ----------------------------------------------------
        # BOOKING TIME
        # ----------------------------------------------------

        booking_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if not start_time:
            start_time = booking_time

        # ----------------------------------------------------
        # CREATE BOOKING
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO bookings
            (
                vehicle_id,
                slot_id,
                booking_time,
                start_time,
                end_time,
                status
            )
            VALUES (?, ?, ?, ?, ?, 'Confirmed')
            """,
            (
                vehicle_id,
                slot_id,
                booking_time,
                start_time,
                end_time
            )
        )

        booking_id = cursor.lastrowid

        # ----------------------------------------------------
        # RESERVE SLOT
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE parking_slots

            SET status = 'Reserved'

            WHERE slot_id = ?
            """,
            (
                slot_id,
            )
        )

        connection.commit()

        return {

            "success": True,

            "message":
                "Parking slot booked successfully.",

            "booking_id":
                booking_id,

            "slot_id":
                slot_id,

            "vehicle_number":
                number_plate,

            "vehicle_type":
                vehicle_type,

            "owner":
                name,

            "booking_time":
                booking_time,

            "status":
                "Confirmed"

        }

    except Exception as error:

        connection.rollback()

        return {

            "success": False,

            "message":
                f"Booking error: {str(error)}"

        }

    finally:

        connection.close()


# ============================================================
# CANCEL EXPIRED BOOKINGS
# ============================================================

def cancel_expired_bookings(expiry_minutes=30):

    connection = get_connection()
    cursor = connection.cursor()

    cutoff_time = (
        datetime.now()
        - timedelta(minutes=expiry_minutes)
    ).strftime("%Y-%m-%d %H:%M:%S")

    # Find confirmed bookings older than cutoff
    # with no active parking session
    cursor.execute(
        """
        SELECT
            b.booking_id,
            b.slot_id,
            b.vehicle_id,
            b.booking_time

        FROM bookings b

        WHERE b.status = 'Confirmed'

        AND b.booking_time <= ?

        AND NOT EXISTS (
            SELECT 1
            FROM parking_sessions ps
            WHERE ps.vehicle_id = b.vehicle_id
            AND ps.slot_id = b.slot_id
            AND ps.status = 'Active'
        )
        """,
        (cutoff_time,)
    )

    expired = cursor.fetchall()

    cancelled_ids = []

    for booking in expired:

        # Cancel booking
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'Cancelled'
            WHERE booking_id = ?
            """,
            (booking["booking_id"],)
        )

        # Release slot back to Available
        cursor.execute(
            """
            UPDATE parking_slots
            SET status = 'Available'
            WHERE slot_id = ?
            AND status = 'Reserved'
            """,
            (booking["slot_id"],)
        )

        cancelled_ids.append(booking["booking_id"])

    connection.commit()
    connection.close()

    return {

        "success": True,

        "cancelled_count":
            len(cancelled_ids),

        "cancelled_booking_ids":
            cancelled_ids,

        "message":
            f"{len(cancelled_ids)} expired booking(s) cancelled."

    }


# ============================================================
# GET BOOKING DETAILS
# ============================================================

def get_booking_details(slot_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            b.booking_id,
            b.slot_id,
            b.booking_time,
            b.start_time,
            b.end_time,
            b.status,

            v.number_plate,
            v.vehicle_type,

            u.name,
            u.phone,
            u.email

        FROM bookings b

        JOIN vehicles v
            ON b.vehicle_id = v.vehicle_id

        LEFT JOIN users u
            ON v.user_id = u.user_id

        WHERE b.slot_id = ?

        AND b.status = 'Confirmed'

        ORDER BY b.booking_id DESC

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


# ============================================================
# ALL BOOKINGS
# ============================================================

def get_all_bookings():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            b.booking_id,
            b.slot_id,
            b.booking_time,
            b.start_time,
            b.end_time,
            b.status,

            v.number_plate,
            v.vehicle_type,

            u.name

        FROM bookings b

        JOIN vehicles v
            ON b.vehicle_id = v.vehicle_id

        LEFT JOIN users u
            ON v.user_id = u.user_id

        ORDER BY b.booking_id DESC
        """
    )

    bookings = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return bookings