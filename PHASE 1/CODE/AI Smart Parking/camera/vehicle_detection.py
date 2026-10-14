import cv2
from ultralytics import YOLO


model = YOLO("yolo11n.pt")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open laptop camera.")
    exit()


# COCO vehicle classes
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}


print("AI Smart Parking Vehicle Detection Started")
print("Detecting: Car, Motorcycle, Bus, Truck")
print("Press Q to exit")


while True:

    success, frame = camera.read()

    if not success:
        break

    results = model(
        frame,
        verbose=False
    )

    vehicle_count = 0

    for result in results:

        boxes = result.boxes

        for box in boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if class_id in VEHICLE_CLASSES:

                vehicle_count += 1

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                vehicle_name = VEHICLE_CLASSES[class_id]

                label = (
                    f"{vehicle_name} "
                    f"{confidence:.2f}"
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    # Display vehicle count
    cv2.putText(
        frame,
        f"Vehicles Detected: {vehicle_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "AI Smart Parking - Vehicle Detection",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()

print("Camera stopped.")