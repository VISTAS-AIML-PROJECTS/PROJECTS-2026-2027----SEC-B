# AI Smart Parking

FastAPI, SQLite, YOLO11, and EasyOCR parking workflow with separate admin and user portals.

## Run

```powershell
python -m pip install -r requirements.txt
python -m pip install --force-reinstall --no-deps opencv-python==4.11.0.86
python -m uvicorn backend.main:app --reload
```

The camera preview requires GUI-enabled OpenCV. Reinstalling this wheel after the requirements is important because EasyOCR also depends on the headless OpenCV package, which does not support `cv2.imshow`.

Open `/dashboard` for the admin portal, `/user` for the user portal, or `/docs` for the API. Demo credentials seeded into an empty database are `admin / admin123` and `user / user123`.

Run the unit tests with `python -m pytest`; standalone camera demos are not collected as tests.

## Parking Flow

1. `camera/plate_camera.py` runs YOLO vehicle detection before EasyOCR. Press `E` to switch the gate between entry and exit. Entry verifies a confirmed plate booking and otherwise records a walk-in. Exit creates a bill; the bay is released only after payment confirmation.
2. `camera/parking_detection.py` updates unassigned bay occupancy and reports double parking, bay overlap, and aisle obstruction to the backend. Calibrate `parking_slots` and `AISLE_ZONES` to the camera image before using alerts operationally. Use separate camera devices or configure the capture index if running both camera scripts at once.
3. Alerts and in-app notifications are persisted in SQLite. Slot mismatch observations use `POST /api/vision/observations` with `number_plate` and the detected `slot_id`.

Walk-in allocation chooses an available bay on the floor with the fewest occupied bays. Confirmed bookings keep their reserved bay. Slot updates from vision do not overwrite confirmed bookings or active/pending sessions.

## Billing

Base hourly rates in INR are Bike 10, Car 20, Bus 40, and Truck 40. The first two billable hours use the base rate; later hours use 1.5x. `/api/billing/rates` exposes the current rates and policy. Payment confirmation is currently a demo action, not a payment-provider integration.

## Main Records

SQLite stores users, vehicles, parking slots, bookings, parking sessions, parking history, payments, admin credentials, parking alerts, and user notifications. Legacy safety-score fields are ignored by the API and are not created for new databases.
