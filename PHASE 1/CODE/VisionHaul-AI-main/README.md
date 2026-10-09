# VisionHaul AI - Heavy Vehicle CCTV Surveillance & Logistics Command Center

An end-to-end intelligent CCTV heavy vehicle surveillance and monitoring system based on the multi-task AI processing pipeline:

```
                         CCTV / VIDEO
                              │
                              ▼
                       ┌────────────┐
                       │  YOLOv26   │
                       │    TRUCK   │
                       │  DETECTION │
                       └──────┬─────┘
                              │
                         TRUCK ONLY
                              │
                              ▼
                       ┌────────────┐
                       │ ByteTrack  │
                       │  TRACKING  │
                       └──────┬─────┘
                              │
                           TRK001
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
     SPEED DETECTION     LICENSE PLATE       MTL-ViT
          │               DETECTION         CLASSIFICATION
          │                   │                    │
          ▼                   ▼             ┌──────┼──────┐
       72 km/h             PaddleOCR         ▼      ▼      ▼
          │                   │            TYPE   COLOR ATTRIBUTES
          │               TN38AB1234
          │                   │
          ▼                   ▼
   SPEED > LIMIT?       BLOCKLIST CHECK
      │      │             │       │
     NO     YES          NO       YES
      │      │             │       │
      │      ▼             │       ▼
      │  OVERSPEED         │   SUSPICIOUS /
      │    ALERT           │   BLOCKLIST ALERT
      │      │             │       │
      └──────┴─────────────┴───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ ALERT MANAGER│
                  └──────┬───────┘
                         │
                         ▼
                 AUTHORIZED PERSON
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           🔊 SOUND    📧 EMAIL   🖥️ DASHBOARD
              │          │          │
              └──────────┼──────────┘
                         │
                         ▼
                  CARGO ANALYSIS
                         │
                         ▼
                ARRIVAL / DEPARTURE
                         │
                         ▼
                    VISIT COUNT
                         │
                         ▼
                   MYSQL / SQLITE
                         │
                         ▼
                  FLASK REST API
                         │
                         ▼
                  REACT DASHBOARD
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            LIVE      HISTORY    ANALYTICS
            CCTV       SEARCH        │
                                    ▼
                           DAILY / MONTHLY /
                           YEARLY STATISTICS
```

---

## 🚀 Key Features

1. **CCTV / Multi-Source Video Processing**:
   - High-Definition Realistic Surveillance Simulator (highways, toll booths, port gates).
   - Live Webcam capture (Camera 0 / 1).
   - Video File Upload (MP4, AVI, MKV) for offline analysis.
   - RTSP live IP CCTV streams.

2. **YOLO Heavy Vehicle Detection (`TRUCK ONLY`)**:
   - Specialized filtering for Heavy Vehicles (Container trucks, tankers, tippers, flatbeds).
   - Eliminates non-commercial vehicle noise.

3. **ByteTrack Multi-Object Tracking**:
   - Persistent ID assignment (`TRK001`, `TRK002`).
   - Kalman filter motion state estimation and trajectory tracking.

4. **Parallel AI Analysis Engines**:
   - **Speed Detection**: Pixel displacement & homography velocity calculation in km/h (`72 km/h`) & overspeed threshold check (`Speed > Limit`).
   - **License Plate OCR (ALPR / ANPR)**: Bounding box plate extraction, character recognition (`TN38AB1234`), and real-time database blocklist / watchlist check.
   - **MTL-ViT Multi-Task Classification**:
     - **Vehicle Type**: Flatbed, Container Carrier, Petroleum Tanker, Tipper / Dump, Box Truck, Mixer.
     - **Color**: White, Yellow, Blue, Red, Silver, Black, Orange, Green.
     - **Cargo State**: Loaded, Empty Bed, Canvas Tarp, Hazmat Placard, Sealed ISO Container.

5. **Alert Manager Core**:
   - 🔊 **Sound Alarm**: Web Audio API synthesized security siren.
   - 📧 **Email Dispatcher**: SMTP incident notifications with metadata.
   - 🖥️ **Dashboard HUD**: Real-time push banners & telemetry warnings.

6. **Logistics & Cargo Analytics**:
   - Automatic Arrival and Departure gate event matching.
   - Lifetime and daily **Visit Count** tracking per license plate.
   - Dwell time & cargo turnaround efficiency.

7. **Database Persistence**:
   - SQLAlchemy ORM with MySQL support and zero-config SQLite out-of-the-box fallback.

8. **React Surveillance Command Center**:
   - Modern Glassmorphism dark mode with high-contrast neon accents.
   - Live CCTV HUD stream with interactive AI layer toggles.
   - Daily / Monthly / Yearly traffic volume interactive charts.
   - 1-Click CSV and PDF audit report exports.

---

## 🛠️ Quick Start

### 1. Start the Flask Backend Server
```bash
# In the project root:
python backend/app.py
```
*Backend runs on `http://localhost:5000` with REST APIs and `/api/stream/video_feed`.*

### 2. Start the React Frontend Dashboard
```bash
# In another terminal:
cd frontend
npm.cmd run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 🧪 Running Automated Tests
```bash
python -m unittest discover -s tests
```
Runs 11 test suites verifying tracker persistence, speed estimation, OCR blocklist checks, ViT classification, alert manager dispatches, visit counters, and Flask REST API endpoints.
