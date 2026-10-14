import cv2
import os
import requests
from ultralytics import YOLO


# ============================================================
# CONFIG
# ============================================================

API_BASE = "http://127.0.0.1:8000"
CAMERA_INDEX = int(os.getenv("PARKING_CAMERA_INDEX", "0"))

# How many frames to wait before pushing an update to backend
# (avoids spamming the API every frame)
UPDATE_EVERY_N_FRAMES = 15


# ============================================================
# LOAD MODEL & CAMERA
# ============================================================

model = YOLO("yolo11n.pt")

camera = cv2.VideoCapture(CAMERA_INDEX)

if not camera.isOpened():
    print("ERROR: Could not open laptop camera.")
    exit()


# ============================================================
# PARKING SLOT COORDINATES
# Format: slot_id: (x1, y1, x2, y2)
# ============================================================

parking_slots = {

    "A1": (50, 100, 250, 220),
    "A2": (270, 100, 470, 220),
    "A3": (490, 100, 690, 220),
    "A4": (710, 100, 910, 220),

    "B1": (50, 250, 250, 370),
    "B2": (270, 250, 470, 370),
    "B3": (490, 250, 690, 370),
    "B4": (710, 250, 910, 370),
}

# Calibrate these rectangles to the vehicle lane in the camera view.
AISLE_ZONES = {
    "main-aisle": (50, 220, 910, 250),
}


VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}


# Track last known status to avoid redundant API calls
last_pushed_status = {
    slot_id: None
    for slot_id in parking_slots
}


# ============================================================
# HELPERS
# ============================================================

def calculate_center(x1, y1, x2, y2):
    return (x1 + x2) // 2, (y1 + y2) // 2


def point_inside_slot(point, slot):
    x, y = point
    x1, y1, x2, y2 = slot
    return x1 <= x <= x2 and y1 <= y <= y2


def rectangles_overlap(first, second):
    return (
        first[0] < second[2]
        and first[2] > second[0]
        and first[1] < second[3]
        and first[3] > second[1]
    )


# ============================================================
# PUSH STATUS TO BACKEND
# ============================================================

def push_slot_status(slot_id, status):
    try:
        requests.put(
            f"{API_BASE}/api/vision/slots/{slot_id}/status",
            json={"status": status},
            timeout=1
        )
    except Exception:
        pass  # Don't crash camera if backend is unreachable


# ============================================================
# MAIN LOOP
# ============================================================

print("AI Smart Parking Detection Started")
print("Press Q to exit")

frame_count = 0

while True:

    success, frame = camera.read()

    if not success:
        print("Could not read camera frame.")
        break

    frame_count += 1

    # Run YOLO
    results = model(frame, verbose=False)

    # Reset all slots to Available each frame
    slot_status = {
        slot_id: "Available"
        for slot_id in parking_slots
    }
    slot_vehicle_counts = {slot_id: 0 for slot_id in parking_slots}
    improper_slots = set()
    aisle_obstructed = False

    # -------------------------------------------------
    # Check detected vehicles
    # -------------------------------------------------

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if class_id not in VEHICLE_CLASSES:
                continue

            if confidence < 0.40:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            center = calculate_center(x1, y1, x2, y2)
            vehicle_box = (x1, y1, x2, y2)

            vehicle_name = VEHICLE_CLASSES[class_id]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)

            cv2.putText(
                frame,
                f"{vehicle_name} {confidence:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            overlapped_slots = [
                slot_id
                for slot_id, slot in parking_slots.items()
                if rectangles_overlap(vehicle_box, slot)
            ]

            for slot_id, slot in parking_slots.items():
                if point_inside_slot(center, slot):
                    slot_status[slot_id] = "Occupied"
                    slot_vehicle_counts[slot_id] += 1

            if len(overlapped_slots) > 1:
                improper_slots.update(overlapped_slots)

            if any(
                rectangles_overlap(vehicle_box, aisle)
                for aisle in AISLE_ZONES.values()
            ):
                aisle_obstructed = True

    # -------------------------------------------------
    # Push changed statuses to backend every N frames
    # -------------------------------------------------

    if frame_count % UPDATE_EVERY_N_FRAMES == 0:

        for slot_id, status in slot_status.items():

            if status != last_pushed_status[slot_id]:

                push_slot_status(slot_id, status)

                last_pushed_status[slot_id] = status

        for slot_id, vehicle_count in slot_vehicle_counts.items():
            if vehicle_count > 1 or slot_id in improper_slots:
                try:
                    requests.post(
                        f"{API_BASE}/api/vision/observations",
                        json={
                            "slot_id": slot_id,
                            "vehicle_count": vehicle_count,
                            "improper_parking": slot_id in improper_slots,
                        },
                        timeout=1
                    )
                except Exception:
                    pass

        if aisle_obstructed:
            try:
                requests.post(
                    f"{API_BASE}/api/vision/observations",
                    json={"aisle_obstructed": True},
                    timeout=1
                )
            except Exception:
                pass

    # -------------------------------------------------
    # Draw parking slots
    # -------------------------------------------------

    for slot_id, slot in parking_slots.items():

        x1, y1, x2, y2 = slot
        status = slot_status[slot_id]
        color = (0, 255, 0) if status == "Available" else (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

        cv2.putText(
            frame,
            f"{slot_id}: {status}",
            (x1 + 5, y1 + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    # -------------------------------------------------
    # Parking statistics overlay
    # -------------------------------------------------

    total_slots = len(parking_slots)
    occupied_slots = sum(
        1 for s in slot_status.values() if s == "Occupied"
    )
    available_slots = total_slots - occupied_slots

    cv2.putText(frame, f"Total: {total_slots}",
        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, f"Available: {available_slots}",
        (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.putText(frame, f"Occupied: {occupied_slots}",
        (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # API sync indicator
    sync_text = "SYNCING..." if frame_count % UPDATE_EVERY_N_FRAMES == 0 else "LIVE"
    cv2.putText(frame, sync_text,
        (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.imshow("AI Smart Parking - Slot Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()

print("Parking detection stopped.")