from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from typing import Optional
import difflib
import os
import subprocess
import sys
import uuid

from backend.database import create_tables, get_connection

from backend.slot_manager import (
    create_parking_slots,
    get_all_slots,
    get_slot,
    update_slot_status
)

from backend.entry_manager import (
    register_vehicle,
    normalize_detected_plate,
    vehicle_entry,
    vehicle_exit,
    find_my_car,
    get_vehicle_by_slot,
    get_vehicle_history
)

from backend.analytics_manager import (
    get_occupancy_analytics,
    log_parking_history
)

from backend.auth_manager import (
    admin_login,
    verify_token,
    admin_logout,
    user_login
)

from backend.anomaly_manager import (
    get_all_anomalies
)

from backend.booking_manager import (
    book_slot,
    get_booking_details,
    get_all_bookings,
    cancel_expired_bookings
)

from ml.parking_prediction import (
    train_model,
    predict_availability,
    predict_floor_congestion
)

from backend.billing_manager import HOURLY_RATES
from backend.monitoring_manager import (
    get_open_alerts,
    get_user_notifications,
    get_walk_in_sessions,
    notify_user,
    record_vision_observation
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(

    title="AI Smart Parking System",

    description=(
        "AI-Based Smart Parking System with "
        "Predictive Availability and Vision Monitoring"
    ),

    version="1.0"
)

last_camera_detection = {
    "number_plate": "",
    "vehicle_type": "Car",
    "source": "camera",
    "detected_at": "",
    "scan_id": "",
    "mode": "ENTRY",
    "action_result": None,
}

camera_process = None
active_camera_scan_id = ""


# ============================================================
# INITIALIZATION
# ============================================================

create_tables()

create_parking_slots()


print("Training parking availability model...")

prediction_model = train_model()

print("Parking prediction model ready!")


# ============================================================
# REQUEST MODELS
# ============================================================

class SlotStatusUpdate(BaseModel):
    status: str


class VehicleRegistration(BaseModel):

    name: str

    number_plate: str

    vehicle_type: str = "Car"

    phone: str = ""

    email: str = ""


class VehicleEntry(BaseModel):

    number_plate: str

    vehicle_type: str = "Car"


class VehicleExit(BaseModel):

    number_plate: str


class ParkingBooking(BaseModel):

    name: str

    number_plate: str

    vehicle_type: str = "Car"

    slot_id: str

    phone: str = ""

    email: str = ""

    start_time: str = ""

    end_time: str = ""


class AdminLogin(BaseModel):
    username: str
    password: str


class VisionObservation(BaseModel):
    number_plate: str = ""
    slot_id: str = ""
    vehicle_count: int = 0
    improper_parking: bool = False
    aisle_obstructed: bool = False


class VisionSlotStatus(BaseModel):
    status: str


class CameraDetection(BaseModel):
    number_plate: str = ""
    vehicle_type: str = "Car"
    source: str = "camera"
    scan_id: str = ""
    mode: str = "ENTRY"


class CameraTrigger(BaseModel):
    mode: str = "entry"


# ============================================================
# AUTH DEPENDENCY
# ============================================================

def require_auth(x_token: Optional[str] = Header(None)):
    admin = verify_token(x_token)
    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Please log in."
        )
    return admin


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard():

    dashboard_file = FRONTEND_DIR / "index.html"

    if not dashboard_file.exists():

        raise HTTPException(
            status_code=404,
            detail="Dashboard file not found"
        )

    return FileResponse(
        dashboard_file
    )


@app.get("/user")
def user_dashboard():

    user_file = FRONTEND_DIR / "user.html"

    if not user_file.exists():

        raise HTTPException(
            status_code=404,
            detail="User page not found"
        )

    return FileResponse(user_file)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "message":
            "AI Smart Parking System API is running",

        "status":
            "success",

        "dashboard":
            "/dashboard",

        "api_documentation":
            "/docs"

    }


# ============================================================
# ALL SLOTS
# ============================================================

@app.get("/api/slots")
def all_slots():

    slots = get_all_slots()

    return {

        "total_slots":
            len(slots),

        "slots":
            slots

    }


# ============================================================
# SINGLE SLOT
# ============================================================

@app.get("/api/slots/{slot_id}")
def single_slot(slot_id: str):

    slot = get_slot(slot_id)

    if slot is None:

        raise HTTPException(
            status_code=404,
            detail="Parking slot not found"
        )

    return slot


# ============================================================
# SLOT DETAILS
# ============================================================

@app.get("/api/slots/{slot_id}/details")
def slot_details(slot_id: str):

    slot = get_slot(slot_id)

    if slot is None:

        raise HTTPException(
            status_code=404,
            detail="Parking slot not found"
        )

    # --------------------------------------------------------
    # AVAILABLE
    # --------------------------------------------------------

    if slot["status"] == "Available":

        return {

            "success": True,

            "slot_type":
                "Available",

            "message":
                "Slot available for booking.",

            "slot":
                dict(slot)

        }

    # --------------------------------------------------------
    # OCCUPIED
    # --------------------------------------------------------

    if slot["status"] == "Occupied":

        vehicle = get_vehicle_by_slot(
            slot_id
        )

        return {

            "success": True,

            "slot_type":
                "Occupied",

            "slot":
                dict(slot),

            "vehicle":
                vehicle

        }

    # --------------------------------------------------------
    # RESERVED
    # --------------------------------------------------------

    if slot["status"] == "Reserved":

        booking = get_booking_details(
            slot_id
        )

        return {

            "success": True,

            "slot_type":
                "Reserved",

            "slot":
                dict(slot),

            "booking":
                booking

        }


# ============================================================
# UPDATE SLOT
# ============================================================

@app.put("/api/slots/{slot_id}/status")
def change_slot_status(
    slot_id: str,
    data: SlotStatusUpdate
):

    allowed = {
        "Available",
        "Occupied",
        "Reserved"
    }

    if data.status not in allowed:

        raise HTTPException(
            status_code=400,
            detail="Invalid slot status"
        )

    success = update_slot_status(
        slot_id,
        data.status
    )

    if not success:

        raise HTTPException(
            status_code=400,
            detail="Invalid slot ID or status"
        )

    return {

        "success": True,

        "message":
            f"{slot_id} updated successfully",

        "slot":
            get_slot(slot_id)

    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/statistics")
def statistics():

    slots = get_all_slots()

    total = len(slots)

    available = sum(
        1
        for slot in slots
        if slot["status"] == "Available"
    )

    occupied = sum(
        1
        for slot in slots
        if slot["status"] == "Occupied"
    )

    reserved = sum(
        1
        for slot in slots
        if slot["status"] == "Reserved"
    )

    return {

        "total":
            total,

        "available":
            available,

        "occupied":
            occupied,

        "reserved":
            reserved

    }


# ============================================================
# REGISTER VEHICLE
# ============================================================

@app.post("/api/register")
def register_vehicle_api(
    data: VehicleRegistration
):

    return register_vehicle(

        data.name,

        data.number_plate,

        data.vehicle_type,

        data.phone,

        data.email

    )


# ============================================================
# CAMERA DETECTION STATUS
# ============================================================

@app.post("/api/camera/detection")
def camera_detection_api(data: CameraDetection):
    if data.scan_id and data.scan_id != active_camera_scan_id:
        raise HTTPException(status_code=409, detail="Camera scan has expired")

    number_plate = normalize_detected_plate(data.number_plate)
    if not number_plate:
        raise HTTPException(status_code=422, detail="Detected text is not a valid vehicle plate")
    vehicle_type = data.vehicle_type.strip().title() if data.vehicle_type else "Car"
    mode = data.mode.strip().upper()
    if mode not in {"ENTRY", "EXIT"}:
        raise HTTPException(status_code=400, detail="Invalid camera mode")

    if (
        data.scan_id
        and last_camera_detection["scan_id"] == data.scan_id
        and last_camera_detection["number_plate"] == number_plate
    ):
        return {
            "success": True,
            "number_plate": number_plate,
            "vehicle_type": last_camera_detection["vehicle_type"],
            "source": last_camera_detection["source"],
            "detected_at": last_camera_detection["detected_at"],
            "scan_id": data.scan_id,
            "mode": last_camera_detection["mode"],
            "action_result": last_camera_detection["action_result"],
        }

    action_result = (
        vehicle_entry(number_plate, vehicle_type)
        if mode == "ENTRY"
        else vehicle_exit(number_plate)
    )

    last_camera_detection["number_plate"] = number_plate
    last_camera_detection["vehicle_type"] = vehicle_type
    last_camera_detection["source"] = data.source or "camera"
    last_camera_detection["detected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_camera_detection["scan_id"] = data.scan_id or active_camera_scan_id
    last_camera_detection["mode"] = mode
    last_camera_detection["action_result"] = action_result
    return {
        "success": True,
        "number_plate": last_camera_detection["number_plate"],
        "vehicle_type": last_camera_detection["vehicle_type"],
        "source": last_camera_detection["source"],
        "detected_at": last_camera_detection["detected_at"],
        "scan_id": last_camera_detection["scan_id"],
        "mode": last_camera_detection["mode"],
        "action_result": action_result,
    }


@app.post("/api/camera/start")
def camera_start_api(data: CameraTrigger):
    global camera_process, active_camera_scan_id

    normalized_mode = (data.mode or "entry").strip().upper()
    if normalized_mode not in {"ENTRY", "EXIT"}:
        normalized_mode = "ENTRY"

    if camera_process is not None and camera_process.poll() is None:
        camera_process.terminate()
        try:
            camera_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            camera_process.kill()
            camera_process.wait()

    active_camera_scan_id = uuid.uuid4().hex
    last_camera_detection.update({
        "number_plate": "",
        "vehicle_type": "Car",
        "source": normalized_mode.lower(),
        "detected_at": "",
        "scan_id": active_camera_scan_id,
        "mode": normalized_mode,
        "action_result": None,
    })

    script_path = BASE_DIR / "camera" / "plate_camera.py"
    env = os.environ.copy()
    env["PARKING_GATE_MODE"] = normalized_mode
    env["PARKING_SCAN_ID"] = active_camera_scan_id
    env["PARKING_SHOW_CAMERA"] = "1"

    creation_flags = 0
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

    camera_process = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        env=env,
        creationflags=creation_flags,
    )

    return {
        "success": True,
        "already_running": False,
        "mode": normalized_mode,
        "pid": camera_process.pid,
        "scan_id": active_camera_scan_id,
    }


@app.get("/api/camera/latest")
def camera_latest_detection_api(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {
        "number_plate": last_camera_detection["number_plate"],
        "vehicle_type": last_camera_detection["vehicle_type"],
        "source": last_camera_detection["source"],
        "detected_at": last_camera_detection["detected_at"],
        "scan_id": last_camera_detection["scan_id"],
        "mode": last_camera_detection["mode"],
        "action_result": last_camera_detection["action_result"],
    }


# ============================================================
# VEHICLE ENTRY
# ============================================================

@app.post("/api/entry")
def vehicle_entry_api(
    data: VehicleEntry
):

    return vehicle_entry(

        data.number_plate,

        data.vehicle_type

    )


# ============================================================
# VEHICLE EXIT
# ============================================================

@app.post("/api/exit")
def vehicle_exit_api(
    data: VehicleExit
):

    return vehicle_exit(
        data.number_plate
    )


# ============================================================
# FIND MY CAR
# ============================================================

@app.get("/api/find-car/{number_plate}")
def find_car(number_plate: str):

    result = find_my_car(
        number_plate
    )

    if not result["success"]:

        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return result


# ============================================================
# BOOK SLOT
# ============================================================

@app.post("/api/book")
def create_booking(
    data: ParkingBooking
):

    result = book_slot(

        name=data.name,

        number_plate=data.number_plate,

        vehicle_type=data.vehicle_type,

        slot_id=data.slot_id,

        phone=data.phone,

        email=data.email,

        start_time=data.start_time,

        end_time=data.end_time

    )

    if not result["success"]:

        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    notify_user(
        data.number_plate,
        "Booking Confirmed",
        f"Slot {result['slot_id']} is reserved for vehicle {data.number_plate.upper()}.",
    )

    return result


# ============================================================
# CANCEL EXPIRED BOOKINGS
# ============================================================

@app.post("/api/bookings/cancel-expired")
def expire_bookings(expiry_minutes: int = 30):

    return cancel_expired_bookings(expiry_minutes)


# ============================================================
# BOOKING DETAILS
# ============================================================

@app.get("/api/bookings/{slot_id}")
def booking_details(slot_id: str):

    booking = get_booking_details(
        slot_id
    )

    if booking is None:

        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return {

        "success": True,

        "booking":
            booking

    }


# ============================================================
# ALL BOOKINGS
# ============================================================

@app.get("/api/bookings")
def all_bookings():

    bookings = get_all_bookings()

    return {

        "success": True,

        "total":
            len(bookings),

        "bookings":
            bookings

    }


# ============================================================
# AI PREDICTION
# ============================================================

@app.get("/api/prediction")
def parking_prediction():

    try:

        prediction_30 = predict_availability(
            prediction_model,
            30
        )

        prediction_60 = predict_availability(
            prediction_model,
            60
        )

        prediction_90 = predict_availability(
            prediction_model,
            90
        )

        return {

            "success": True,

            "current_status": {

                "total_slots":
                    prediction_30["total_slots"],

                "occupied":
                    prediction_30["current_occupied"],

                "available":
                    prediction_30["current_available"]

            },

            "prediction": {

                "30_minutes":
                    prediction_30[
                        "predicted_available"
                    ],

                "60_minutes":
                    prediction_60[
                        "predicted_available"
                    ],

                "90_minutes":
                    prediction_90[
                        "predicted_available"
                    ]

            },

            "details": {

                "30_minutes":
                    prediction_30,

                "60_minutes":
                    prediction_60,

                "90_minutes":
                    prediction_90

            }

        }

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=
                f"Prediction error: {str(error)}"

        )


# ============================================================
# PAYMENT CONFIRMATION
# ============================================================

@app.post("/api/payments/{session_id}/pay")
def confirm_payment(session_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.payment_id,
            p.amount,
            p.payment_status,
            ps.slot_id,
            ps.entry_time,
            ps.exit_time,
            ps.duration_minutes,
            v.number_plate,
            v.vehicle_type,
            u.name
        FROM payments p
        JOIN parking_sessions ps
            ON p.session_id = ps.session_id
        JOIN vehicles v
            ON ps.vehicle_id = v.vehicle_id
        LEFT JOIN users u
            ON v.user_id = u.user_id
        WHERE p.session_id = ?
        ORDER BY p.payment_id DESC
        LIMIT 1
        """,
        (session_id,)
    )

    payment = cursor.fetchone()

    if payment is None:

        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Payment record not found"
        )

    if payment["payment_status"] == "Paid":

        connection.close()

        return {
            "success": True,
            "message": "Already paid.",
            "receipt": dict(payment)
        }

    cursor.execute(
        """
        UPDATE payments
        SET payment_status = 'Paid'
        WHERE session_id = ?
        """,
        (session_id,)
    )

    cursor.execute(
        """
        UPDATE parking_sessions
        SET status = 'Completed'
        WHERE session_id = ? AND status = 'Awaiting Payment'
        """,
        (session_id,)
    )

    cursor.execute(
        """
        UPDATE parking_slots
        SET status = 'Available'
        WHERE slot_id = ? AND status = 'Occupied'
        """,
        (payment["slot_id"],)
    )

    connection.commit()

    receipt = dict(payment)
    receipt["payment_status"] = "Paid"

    connection.close()

    notify_user(
        payment["number_plate"],
        "Payment Receipt",
        f"Payment of ₹{payment['amount']:.2f} was received. Slot {payment['slot_id']} is released.",
    )

    return {
        "success": True,
        "message": "Payment confirmed. Thank you!",
        "receipt": receipt
    }


# ============================================================
# VEHICLE HISTORY
# ============================================================

@app.get("/api/vehicles/{number_plate}/history")
def vehicle_history(number_plate: str):

    result = get_vehicle_history(number_plate)

    if not result["success"]:

        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    return result


@app.get("/api/vehicles/{number_plate}/bookings")
def vehicle_bookings(number_plate: str):
    plate = number_plate.strip().upper().replace(" ", "")
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT b.booking_id, b.slot_id, b.booking_time, b.start_time,
               b.end_time, b.status, v.number_plate, v.vehicle_type
        FROM bookings b
        JOIN vehicles v ON v.vehicle_id = b.vehicle_id
        WHERE v.number_plate = ?
        ORDER BY b.booking_id DESC
        """,
        (plate,)
    ).fetchall()
    connection.close()
    bookings = [dict(row) for row in rows]
    return {"number_plate": plate, "total": len(bookings), "bookings": bookings}


@app.get("/api/vehicles/{number_plate}/payments")
def vehicle_payments(number_plate: str):
    plate = number_plate.strip().upper().replace(" ", "")
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT p.payment_id, p.session_id, p.amount, p.payment_time,
               p.payment_status, ps.slot_id, ps.duration_minutes
        FROM payments p
        JOIN parking_sessions ps ON ps.session_id = p.session_id
        JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
        WHERE v.number_plate = ?
        ORDER BY p.payment_id DESC
        """,
        (plate,)
    ).fetchall()
    connection.close()
    payments = [dict(row) for row in rows]
    return {"number_plate": plate, "total": len(payments), "payments": payments}


# ============================================================
# OCCUPANCY ANALYTICS
# ============================================================

@app.get("/api/analytics/occupancy")
def occupancy_analytics():

    return get_occupancy_analytics()


@app.post("/api/analytics/log")
def log_snapshot():

    log_parking_history()

    return {
        "success": True,
        "message": "Parking snapshot logged."
    }


# ============================================================
# FLOOR CONGESTION PREDICTION
# ============================================================

@app.get("/api/prediction/floors")
def floor_congestion_prediction(minutes: int = 30):

    try:

        results = predict_floor_congestion(
            prediction_model,
            minutes
        )

        return {
            "success": True,
            "minutes_ahead": minutes,
            "floors": results
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Floor prediction error: {str(error)}"
        )


# ============================================================
# ADMIN SUMMARY
# ============================================================

@app.get("/api/admin/summary")
def admin_summary():

    connection = __import__(
        "backend.database", fromlist=["get_connection"]
    ).get_connection()
    cursor = connection.cursor()

    # Total revenue
    cursor.execute("""
        SELECT
            COUNT(*) AS total_sessions,
            SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) AS active_now,
            SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed
        FROM parking_sessions
    """)
    sessions = dict(cursor.fetchone())

    cursor.execute("""
        SELECT
            COALESCE(SUM(amount), 0) AS total_revenue,
            COUNT(*) AS total_payments,
            SUM(CASE WHEN payment_status='Paid' THEN amount ELSE 0 END) AS collected,
            SUM(CASE WHEN payment_status='Pending' THEN amount ELSE 0 END) AS pending
        FROM payments
    """)
    payments = dict(cursor.fetchone())

    # Recent 10 sessions
    cursor.execute("""
        SELECT
            ps.session_id,
            ps.slot_id,
            ps.entry_time,
            ps.exit_time,
            ps.duration_minutes,
            ps.amount,
            ps.status,
            v.number_plate,
            v.vehicle_type,
            u.name AS owner_name,
            p.payment_status
        FROM parking_sessions ps
        JOIN vehicles v ON ps.vehicle_id = v.vehicle_id
        LEFT JOIN users u ON v.user_id = u.user_id
        LEFT JOIN payments p ON ps.session_id = p.session_id
        ORDER BY ps.session_id DESC
        LIMIT 15
    """)
    recent = [dict(r) for r in cursor.fetchall()]

    # Total vehicles registered
    cursor.execute("SELECT COUNT(*) AS cnt FROM vehicles")
    total_vehicles = cursor.fetchone()["cnt"]

    connection.close()

    return {
        "success":        True,
        "sessions":       sessions,
        "payments":       payments,
        "total_vehicles": total_vehicles,
        "recent_sessions": recent
    }


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(data: AdminLogin):
    result = admin_login(data.username, data.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@app.post("/api/auth/logout")
def logout(x_token: Optional[str] = Header(None)):
    return admin_logout(x_token)


@app.get("/api/auth/verify")
def verify(x_token: Optional[str] = Header(None)):
    admin = verify_token(x_token)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"success": True, "username": admin["username"], "role": admin["role"]}


@app.post("/api/auth/user/login")
def user_portal_login(data: AdminLogin):
    result = user_login(data.username, data.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


# ============================================================
# ANOMALY DETECTION
# ============================================================

@app.get("/api/anomalies")
def anomalies():
    detected = get_all_anomalies()
    alerts = (get_open_alerts()["alerts"] + detected["anomalies"])[:len(get_all_slots())]
    return {
        "total": len(alerts),
        "high": sum(alert["severity"] == "High" for alert in alerts),
        "medium": sum(alert["severity"] == "Medium" for alert in alerts),
        "low": sum(alert["severity"] == "Low" for alert in alerts),
        "anomalies": alerts,
    }


@app.post("/api/vision/observations")
def vision_observation(data: VisionObservation):
    return record_vision_observation(data.model_dump())


@app.put("/api/vision/slots/{slot_id}/status")
def vision_slot_status(slot_id: str, data: VisionSlotStatus):
    if data.status not in {"Available", "Occupied"}:
        raise HTTPException(status_code=400, detail="Invalid vision slot status")
    connection = get_connection()
    protected = connection.execute(
        """
        SELECT 1
        FROM parking_sessions ps
        WHERE ps.slot_id = ? AND ps.status IN ('Active', 'Awaiting Payment')
        UNION ALL
        SELECT 1
        FROM bookings b
        WHERE b.slot_id = ? AND b.status = 'Confirmed'
        LIMIT 1
        """,
        (slot_id, slot_id)
    ).fetchone()
    connection.close()
    if protected:
        return {"success": True, "protected": True, "slot": get_slot(slot_id)}
    if not update_slot_status(slot_id, data.status):
        raise HTTPException(status_code=404, detail="Parking slot not found")
    return {"success": True, "protected": False, "slot": get_slot(slot_id)}


@app.get("/api/notifications/{number_plate}")
def user_notifications(number_plate: str):
    return get_user_notifications(number_plate)


@app.get("/api/admin/walk-ins")
def admin_walk_ins():
    sessions = get_walk_in_sessions()
    return {"total": len(sessions), "sessions": sessions}


@app.get("/api/admin/vehicles")
def admin_vehicles():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT v.vehicle_id, v.number_plate, v.vehicle_type,
               u.name AS owner_name, u.phone, u.email,
               ps.slot_id, ps.entry_time, ps.status AS parking_status
        FROM vehicles v
        LEFT JOIN users u ON u.user_id = v.user_id
        LEFT JOIN parking_sessions ps ON ps.session_id = (
            SELECT MAX(session_id) FROM parking_sessions
            WHERE vehicle_id = v.vehicle_id AND status IN ('Active', 'Awaiting Payment')
        )
        ORDER BY v.vehicle_id DESC
        """
    ).fetchall()
    connection.close()
    vehicles = [dict(row) for row in rows]
    return {"total": len(vehicles), "vehicles": vehicles}


@app.get("/api/admin/billing")
def admin_billing():
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT p.payment_id, p.session_id, p.amount, p.payment_time,
               p.payment_status, ps.slot_id, ps.duration_minutes,
               v.number_plate, v.vehicle_type
        FROM payments p
        JOIN parking_sessions ps ON ps.session_id = p.session_id
        JOIN vehicles v ON v.vehicle_id = ps.vehicle_id
        ORDER BY p.payment_id DESC
        """
    ).fetchall()
    connection.close()
    payments = [dict(row) for row in rows]
    return {"total": len(payments), "payments": payments, "hourly_rates": HOURLY_RATES}


@app.get("/api/billing/rates")
def billing_rates():
    return {
        "currency": "INR",
        "hourly_rates": HOURLY_RATES,
        "policy": "First two hours at base rate; later hours use 1.5x.",
    }


# ============================================================
# FUZZY PLATE MATCH
# ============================================================

@app.get("/api/vehicles/search")
def fuzzy_plate_search(q: str):

    q = q.strip().upper().replace(" ", "")

    if len(q) < 3:
        raise HTTPException(
            status_code=400,
            detail="Query too short. Enter at least 3 characters."
        )

    connection = __import__(
        "backend.database", fromlist=["get_connection"]
    ).get_connection()

    cursor = connection.cursor()
    cursor.execute("SELECT number_plate, vehicle_type FROM vehicles")
    all_plates = cursor.fetchall()
    connection.close()

    plates = [row["number_plate"] for row in all_plates]

    # difflib close matches
    close = difflib.get_close_matches(q, plates, n=5, cutoff=0.5)

    # Also include plates that contain the query as substring
    substring_matches = [
        p for p in plates
        if q in p and p not in close
    ]

    results = close + substring_matches[:3]

    plate_map = {row["number_plate"]: row["vehicle_type"] for row in all_plates}

    return {
        "query":   q,
        "matches": [
            {"number_plate": p, "vehicle_type": plate_map[p]}
            for p in results
        ]
    }


# ============================================================

