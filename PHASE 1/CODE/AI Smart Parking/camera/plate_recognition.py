import cv2
import easyocr
import re
from pathlib import Path
from ultralytics import YOLO


# ============================================================
# 1. LOAD MODELS
# ============================================================

print("Loading YOLO...")

model = YOLO("yolo11n.pt")

print("Loading EasyOCR...")

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

print("Models loaded successfully.")


# ============================================================
# 2. CLEAN OCR TEXT
# ============================================================

def clean_plate(text):

    text = text.upper()

    text = re.sub(
        r'[^A-Z0-9]',
        '',
        text
    )

    return text


# ============================================================
# 3. OCR FUNCTION
# ============================================================

def read_plate_from_crop(vehicle_crop):

    if vehicle_crop is None:
        return None

    if vehicle_crop.size == 0:
        return None


    # --------------------------------------------------------
    # Enlarge vehicle image
    # --------------------------------------------------------

    enlarged = cv2.resize(
        vehicle_crop,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )


    # --------------------------------------------------------
    # Convert to grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )


    # --------------------------------------------------------
    # Improve contrast
    # --------------------------------------------------------

    gray = cv2.equalizeHist(gray)


    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    results = reader.readtext(
        gray,
        detail=1,
        paragraph=False
    )


    best_plate = None
    best_confidence = 0


    for detection in results:

        bbox, text, confidence = detection

        cleaned = clean_plate(text)


        # Ignore very short text
        if len(cleaned) < 4:
            continue


        # Must contain at least one number
        if not any(
            char.isdigit()
            for char in cleaned
        ):
            continue


        if confidence > best_confidence:

            best_plate = cleaned
            best_confidence = confidence


    if best_plate is not None:

        return {
            "plate": best_plate,
            "confidence": round(
                float(best_confidence),
                2
            )
        }


    return None


# ============================================================
# 4. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":


    # --------------------------------------------------------
    # Image path
    # --------------------------------------------------------

    image_path = (
        Path(__file__).resolve().parent
        / "test_data"
        / "parking_test.png"
    )


    print("\nImage:")
    print(image_path)


    frame = cv2.imread(
        str(image_path)
    )


    if frame is None:

        print(
            "ERROR: Could not load image."
        )

        exit()


    print(
        "\nRunning vehicle detection..."
    )


    # --------------------------------------------------------
    # Detect vehicles
    # --------------------------------------------------------

    results = model(
        frame,
        conf=0.45,
        iou=0.50,
        verbose=False
    )


    vehicle_number = 0


    # --------------------------------------------------------
    # Process each vehicle
    # --------------------------------------------------------

    for result in results:

        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )


            # Only cars and motorcycles
            if class_id not in [2, 3]:
                continue


            vehicle_number += 1


            # Vehicle coordinates

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )


            # Keep coordinates inside image

            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(
                frame.shape[1],
                x2
            )

            y2 = min(
                frame.shape[0],
                y2
            )


            # Crop vehicle

            vehicle_crop = frame[
                y1:y2,
                x1:x2
            ]


            vehicle_name = (
                "Car"
                if class_id == 2
                else "Motorcycle"
            )


            print(
                f"\nVehicle {vehicle_number}: "
                f"{vehicle_name}"
            )


            # ------------------------------------------------
            # OCR
            # ------------------------------------------------

            plate = read_plate_from_crop(
                vehicle_crop
            )


            if plate:

                print(
                    f"Number Plate: "
                    f"{plate['plate']}"
                )

                print(
                    f"OCR Confidence: "
                    f"{plate['confidence']}"
                )


                label = (
                    f"{vehicle_name} | "
                    f"{plate['plate']}"
                )

            else:

                print(
                    "Number Plate: "
                    "Not detected"
                )

                label = (
                    f"{vehicle_name} | "
                    "Plate not detected"
                )


            # ------------------------------------------------
            # Draw vehicle box
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )


            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )


    # ========================================================
    # DISPLAY
    # ========================================================

    print("\n================================")
    print("NUMBER PLATE RECOGNITION")
    print("================================")
    print(
        f"Vehicles processed: "
        f"{vehicle_number}"
    )
    print("================================")


    cv2.imshow(
        "AI Smart Parking - ANPR",
        frame
    )

    cv2.waitKey(0)

    cv2.destroyAllWindows()