import cv2
import sys
from pathlib import Path
from ultralytics import YOLO

# Allow Python to find the backend package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.slot_manager import update_slot_status


# ============================================================
# 1. LOAD YOLO MODEL
# ============================================================

model = YOLO("yolo11n.pt")


# ============================================================
# 2. LOAD PARKING IMAGE
# ============================================================

image_path = (
    Path(__file__).resolve().parent
    / "test_data"
    / "parking_test.png"
)

print("Looking for image:")
print(image_path)

if not image_path.exists():
    print("ERROR: Image does not exist!")
    exit()

frame = cv2.imread(str(image_path))

if frame is None:
    print("ERROR: Could not read image.")
    exit()

print("Parking image loaded successfully.")


# ============================================================
# 3. PARKING SLOT COORDINATES
# ============================================================

parking_slots = {

    # TOP ROW
    "A1": (175, 90, 535, 445),
    "A2": (535, 90, 915, 445),
    "A3": (915, 90, 1295, 445),
    "A4": (1295, 90, 1665, 445),

    # BOTTOM ROW
    "A5": (175, 640, 535, 1070),
    "A6": (535, 640, 915, 1070),
    "A7": (915, 640, 1295, 1070),
    "A8": (1295, 640, 1665, 1070)
}


# ============================================================
# 4. VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}


# ============================================================
# 5. RUN YOLO
# ============================================================

results = model(
    frame,
    conf=0.45,
    iou=0.50,
    verbose=False
)


# ============================================================
# 6. INITIALIZE SLOT STATUS
# ============================================================

slot_status = {}

for slot_id in parking_slots:
    slot_status[slot_id] = "Available"


# ============================================================
# 7. PROCESS VEHICLES
# ============================================================

vehicle_count = 0


for result in results:

    for box in result.boxes:

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        # Ignore non-vehicles
        if class_id not in VEHICLE_CLASSES:
            continue

        vehicle_count += 1

        # Vehicle coordinates
        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        # Vehicle center
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        vehicle_name = VEHICLE_CLASSES[class_id]


        # ----------------------------------------------------
        # FIND PARKING SLOT
        # ----------------------------------------------------

        detected_slot = None

        for slot_id, slot in parking_slots.items():

            sx1, sy1, sx2, sy2 = slot

            if (
                sx1 <= center_x <= sx2
                and
                sy1 <= center_y <= sy2
            ):

                slot_status[slot_id] = "Occupied"

                detected_slot = slot_id

                break


        # ----------------------------------------------------
        # DRAW VEHICLE BOX
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )


        # ----------------------------------------------------
        # VEHICLE LABEL
        # ----------------------------------------------------

        label = f"{vehicle_name} {confidence:.2f}"

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        # ----------------------------------------------------
        # SHOW DETECTED SLOT
        # ----------------------------------------------------

        if detected_slot is not None:

            cv2.putText(
                frame,
                detected_slot,
                (x1, y2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )


# ============================================================
# 8. DISPLAY SLOT STATUS
# ============================================================

for slot_id, slot in parking_slots.items():

    x1, y1, x2, y2 = slot

    status = slot_status[slot_id]


    if status == "Occupied":

        status_color = (0, 0, 255)

    else:

        status_color = (0, 255, 0)


    # --------------------------------------------------------
    # SLOT STATUS TEXT ONLY
    # No large slot rectangles
    # --------------------------------------------------------

    text = f"{slot_id}: {status}"

    cv2.putText(
        frame,
        text,
        (x1 + 10, y1 + 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        status_color,
        2
    )


# ============================================================
# 9. CALCULATE STATISTICS
# ============================================================

total_slots = len(parking_slots)

occupied_slots = sum(
    1
    for status in slot_status.values()
    if status == "Occupied"
)

available_slots = (
    total_slots - occupied_slots
)


# ============================================================
# 10. DISPLAY STATISTICS
# ============================================================

cv2.putText(
    frame,
    f"Vehicles Detected: {vehicle_count}",
    (25, 40),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.9,
    (255, 255, 255),
    2
)

cv2.putText(
    frame,
    f"Available: {available_slots}",
    (25, 75),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.9,
    (0, 255, 0),
    2
)

cv2.putText(
    frame,
    f"Occupied: {occupied_slots}",
    (25, 110),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.9,
    (0, 0, 255),
    2
)


# ============================================================
# 11. PRINT RESULT
# ============================================================

print("\n================================")
print("SMART PARKING RESULT")
print("================================")

print(f"Total Slots     : {total_slots}")
print(f"Vehicles Found  : {vehicle_count}")
print(f"Occupied Slots  : {occupied_slots}")
print(f"Available Slots : {available_slots}")

print("\nSlot Status:")

for slot_id, status in slot_status.items():

    print(f"{slot_id} -> {status}")

    # Update SQLite database
    success = update_slot_status(
        slot_id,
        status
    )

    if success:
        print(
            f"Database updated: "
            f"{slot_id} = {status}"
        )
    else:
        print(
            f"Database update failed: "
            f"{slot_id}"
        )

print("================================")


# ============================================================
# 12. SHOW IMAGE
# ============================================================

cv2.imshow(
    "AI Smart Parking - Slot Detection",
    frame
)

cv2.waitKey(0)

cv2.destroyAllWindows()