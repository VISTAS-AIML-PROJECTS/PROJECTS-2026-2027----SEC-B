import cv2
import easyocr
import os
import re
import sys
import time
import requests
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.entry_manager import normalize_detected_plate


# ============================================================
# CONFIG
# ============================================================

API_BASE = "http://127.0.0.1:8000"
CAMERA_INDEX = int(os.getenv("PARKING_CAMERA_INDEX", "0"))
SCAN_ID = os.getenv("PARKING_SCAN_ID", "")

# Seconds to wait before the same plate can trigger entry again
COOLDOWN_SECONDS = 10
CONFIRMATION_WINDOW_SECONDS = 8
SCAN_TIMEOUT_SECONDS = 45
SHOW_CAMERA = os.getenv("PARKING_SHOW_CAMERA", "0") == "1"
PARKING_SLOTS = {
    "A1": (50, 100, 250, 220),
    "A2": (270, 100, 470, 220),
    "A3": (490, 100, 690, 220),
    "A4": (710, 100, 910, 220),
    "B1": (50, 250, 250, 370),
    "B2": (270, 250, 470, 370),
    "B3": (490, 250, 690, 370),
    "B4": (710, 250, 910, 370),
}


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text


def find_observed_slot(points):
    center_x = int(sum(point[0] for point in points) / len(points) / 1.5)
    center_y = int(sum(point[1] for point in points) / len(points) / 1.5)
    for slot_id, (x1, y1, x2, y2) in PARKING_SLOTS.items():
        if x1 <= center_x <= x2 and y1 <= center_y <= y2:
            return slot_id
    return ""


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

if SHOW_CAMERA:
    preview_ok, preview_frame = cap.read()
    if preview_ok:
        preview = cv2.resize(preview_frame, None, fx=1.5, fy=1.5)
        cv2.putText(
            preview,
            "Loading vehicle and plate models...",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.namedWindow("AI Smart Parking - ANPR Camera", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "AI Smart Parking - ANPR Camera",
            cv2.WND_PROP_TOPMOST,
            1,
        )
        cv2.imshow("AI Smart Parking - ANPR Camera", preview)
        cv2.waitKey(1)

print("Loading vehicle and plate models...")
vehicle_model = YOLO("yolo11n.pt")
reader = easyocr.Reader(['en'], gpu=False)
print("Models loaded. Starting camera recognition.")


# Track recently processed plates to avoid duplicate entries
recently_processed = {}  # plate -> timestamp
candidate_plate = ""
candidate_count = 0
candidate_last_seen = 0
last_seen_plate = ""
action_completed = False

last_entry_result = ""  # shown on screen
gate_mode = os.getenv("PARKING_GATE_MODE", "ENTRY").upper()


# ============================================================
# MAIN LOOP
# ============================================================

scan_started_at = time.monotonic()

while True:

    if time.monotonic() - scan_started_at >= SCAN_TIMEOUT_SECONDS:
        print("Camera scan timed out without a confirmed plate.")
        break

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read camera.")
        break

    display = cv2.resize(frame, None, fx=1.5, fy=1.5)

    if SHOW_CAMERA:
        cv2.namedWindow("AI Smart Parking - ANPR Camera", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "AI Smart Parking - ANPR Camera",
            cv2.WND_PROP_TOPMOST,
            1,
        )
        cv2.imshow("AI Smart Parking - ANPR Camera", display)
        cv2.waitKey(1)

    vehicle_results = vehicle_model(frame, verbose=False)
    detected_vehicles = []
    vehicle_classes = {2: "Car", 3: "Bike", 5: "Bus", 7: "Truck"}
    for result in vehicle_results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            if class_id not in vehicle_classes or float(box.conf[0]) < 0.40:
                continue
            coordinates = tuple(map(int, box.xyxy[0]))
            detected_vehicles.append((coordinates, vehicle_classes[class_id]))
            cv2.rectangle(display, (int(coordinates[0] * 1.5), int(coordinates[1] * 1.5)),
                          (int(coordinates[2] * 1.5), int(coordinates[3] * 1.5)), (255, 255, 0), 2)

    results = reader.readtext(
        display,
        detail=1,
        paragraph=False,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        canvas_size=2560,
        mag_ratio=1.5,
        min_size=8,
    )

    detected_plate = None
    detected_points = []
    detected_vehicle_type = "Car"

    for detection in results:

        bbox, text, confidence = detection

        cleaned = normalize_detected_plate(clean_text(text))

        if cleaned:

            if confidence >= 0.30:

                detected_plate = cleaned
                last_seen_plate = cleaned

                points = [
                    (int(p[0]), int(p[1]))
                    for p in detection[0]
                ]
                detected_points = points
                plate_center = (
                    sum(point[0] for point in points) / len(points) / 1.5,
                    sum(point[1] for point in points) / len(points) / 1.5,
                )
                for (x1, y1, x2, y2), vehicle_type in detected_vehicles:
                    if x1 <= plate_center[0] <= x2 and y1 <= plate_center[1] <= y2:
                        detected_vehicle_type = vehicle_type
                        break

                cv2.polylines(
                    display,
                    [__import__('numpy').array(points)],
                    True,
                    (0, 255, 0),
                    3
                )

                cv2.putText(
                    display,
                    f"Plate: {detected_plate}",
                    (points[0][0], max(points[0][1] - 10, 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

                break

    now = time.time()
    if detected_plate:
        if detected_plate == candidate_plate and now - candidate_last_seen <= CONFIRMATION_WINDOW_SECONDS:
            candidate_count += 1
        else:
            candidate_plate = detected_plate
            candidate_count = 1
        candidate_last_seen = now
    elif candidate_last_seen and now - candidate_last_seen > CONFIRMATION_WINDOW_SECONDS:
        candidate_plate = ""
        candidate_count = 0
        candidate_last_seen = 0

    # ----------------------------------------------------------
    # AUTO ENTRY — trigger if plate not in cooldown
    # ----------------------------------------------------------

    if detected_plate and candidate_count >= 2 and not action_completed:

        now = time.time()

        last_seen = recently_processed.get(
            detected_plate, 0
        )

        if now - last_seen > COOLDOWN_SECONDS:

            recently_processed[detected_plate] = now

            try:
                response = requests.post(
                    f"{API_BASE}/api/camera/detection",
                    json={
                        "number_plate": detected_plate,
                        "vehicle_type": detected_vehicle_type,
                        "source": "camera",
                        "scan_id": SCAN_ID,
                        "mode": gate_mode,
                    },
                    timeout=5,
                )
                response.raise_for_status()
                action_result = response.json().get("action_result", {})
                if action_result.get("success"):
                    if gate_mode == "ENTRY":
                        last_entry_result = f"Slot {action_result.get('slot_id')} assigned"
                    else:
                        last_entry_result = f"Exit recorded: ₹{action_result.get('amount', 0)} due"
                else:
                    last_entry_result = action_result.get("message", "Parking action failed")
                action_completed = True
            except (requests.RequestException, ValueError) as error:
                last_entry_result = f"Could not register plate: {error}"

            observed_slot = find_observed_slot(detected_points) if detected_points else ""
            if observed_slot:
                try:
                    requests.post(
                        f"{API_BASE}/api/vision/observations",
                        json={
                            "number_plate": detected_plate,
                            "slot_id": observed_slot,
                            "vehicle_count": 1,
                        },
                        timeout=2,
                    )
                except requests.RequestException:
                    pass

            last_entry_result = f"{last_entry_result} | {detected_plate} ({detected_vehicle_type})"

    # ----------------------------------------------------------
    # DISPLAY
    # ----------------------------------------------------------

    display_plate = detected_plate or last_seen_plate

    status = f"{gate_mode} | PLATE: {display_plate}" if display_plate else "PLATE: Move plate closer"

    if SHOW_CAMERA:
        cv2.putText(
            display, status,
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9,
            (255, 255, 255), 2
        )

        if last_entry_result:
            cv2.putText(
                display, last_entry_result,
                (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 255), 2
            )

        cv2.setWindowProperty(
            "AI Smart Parking - ANPR Camera",
            cv2.WND_PROP_TOPMOST,
            1,
        )
        cv2.imshow("AI Smart Parking - ANPR Camera", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('e'):
            gate_mode = "EXIT" if gate_mode == "ENTRY" else "ENTRY"
            recently_processed.clear()
            last_entry_result = f"Gate mode: {gate_mode}"
        if key == ord('q'):
            break


cap.release()
if SHOW_CAMERA:
    cv2.destroyAllWindows()