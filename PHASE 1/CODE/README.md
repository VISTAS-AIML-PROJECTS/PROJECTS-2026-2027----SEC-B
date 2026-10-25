# Wrapture

AI-powered sustainable packaging recommendation platform.

## Architecture

```
React Frontend (port 3000)
        ↓  HTTP
Flask Backend (port 5000)
        ↓
┌─────────────────────────────────────┐
│  Services                           │
│  MobileNetV2 Material Classifier    │
│  YOLO11s Product Detector (pending) │
│  ABO Product Catalog (42,650 items) │
│  Packrift Packaging Catalog (2,209) │
│  Deterministic Packaging Engine     │
│  DistilBERT Review Analyzer         │
│  OpenAI LLM Chatbot                 │
│  SQLite Usage Database              │
└─────────────────────────────────────┘
```

See `docs/ARCHITECTURE.md` for full details.

---

## Prerequisites

- Node.js 18+
- Python 3.10+
- pip

---

## Backend Setup

```bash
cd wrapture-main/backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Edit .env and set LLM_API_KEY if you want TrashGPT to work

# Start the backend
python app.py
# Flask runs on http://localhost:5000
```

---

## Frontend Setup

```bash
cd wrapture-main

# Install dependencies
npm install

# The .env already contains REACT_APP_API_URL=http://localhost:5000
# Start the frontend
npm start
# React runs on http://localhost:3000
```

---

## Running Tests

```bash
cd wrapture-main/backend
venv\Scripts\activate
python -m pytest tests/ -v
```

---

## Environment Variables

### Frontend (`wrapture-main/.env`)

| Variable | Default | Description |
|---|---|---|
| `REACT_APP_API_URL` | `http://localhost:5000` | Flask backend URL |
| `REACT_APP_GOOGLE_MAPS_API_KEY` | _(empty)_ | Google Maps JS API key — required for Recycling Locator |

### Backend (`wrapture-main/backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | LLM provider for TrashGPT (`openai` or `none`) |
| `LLM_API_KEY` | _(empty)_ | OpenAI API key — TrashGPT disabled if empty |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `FLASK_PORT` | `5000` | Flask port |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `GOOGLE_MAPS_API_KEY` | _(empty)_ | Google Maps server-side key — required for Recycling Locator |

### Configuring the Recycling Center Locator

The Recycling Locator uses **Google Maps Platform** (Maps JavaScript API +
Places API (New)). Two separate keys are used:

- `REACT_APP_GOOGLE_MAPS_API_KEY` — loaded in the browser to render the
  interactive map tiles (Maps JavaScript API only).
- `GOOGLE_MAPS_API_KEY` — kept server-side in `backend/.env`. The Flask
  backend uses this to call the Places API (New) so the key is never
  exposed to the browser.

**Setup steps:**

1. Go to https://console.cloud.google.com/
2. Create or select a project and enable billing.
3. Enable these APIs:
   - **Maps JavaScript API** (for map tile rendering in the browser)
   - **Places API (New)** (for recycling center search, called server-side)
   - **Geocoding API** (for manual address → coordinates lookup)
4. Create two API keys (or one restricted key per use):
   - Browser key: restrict to your domain; enable Maps JavaScript API.
   - Server key: restrict to your server IP; enable Places API (New) + Geocoding API.
5. Add to `wrapture-main/.env`:
   ```
   REACT_APP_GOOGLE_MAPS_API_KEY=AIza...
   ```
6. Add to `wrapture-main/backend/.env`:
   ```
   GOOGLE_MAPS_API_KEY=AIza...
   ```
7. Restart both servers (`npm start` from `wrapture-main/`).

**How recycling search works:**

- The browser asks for the user's geolocation (Geolocation API).
- If denied, the user enters a city/address which is geocoded via the
  Maps Geocoding API (browser-side, using the Maps JS key).
- The frontend calls `GET /api/recycling/nearby?lat=&lng=&radius=`.
- The Flask backend calls Google Places API (New) Nearby Search with
  `includedTypes: ["recycling_center"]`.
- If that returns zero results, a text search fallback is used.
- Results are normalized — only real API fields are returned.
- Straight-line distance (Haversine) is calculated from user coordinates
  to each place. It is labelled "Approx. X km away" — not driving distance.
- `accepted_materials` is always `"Accepted materials not verified"` because
  the Places API does not return material acceptance data.
- No fake recycling centers are shown under any failure condition.

**Field mask (cost control):**

The backend requests only these fields from Places API (New):
`places.id`, `places.displayName`, `places.formattedAddress`,
`places.location`, `places.googleMapsUri`, `places.primaryType`,
`places.types`, `places.currentOpeningHours`, `places.nationalPhoneNumber`,
`places.websiteUri`, `places.rating`, `places.userRatingCount`.

No wildcard `*` is used.

---

### Configuring TrashGPT

TrashGPT is an LLM-powered sustainability assistant. It uses the OpenAI API
with a pretrained general-purpose model. It was **not** trained by Wrapture.

1. Obtain an OpenAI API key from https://platform.openai.com/api-keys
2. Add it to `backend/.env`:
   ```
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-...
   LLM_MODEL=gpt-4o-mini
   ```
3. Restart the Flask backend.

If `LLM_API_KEY` is empty, TrashGPT returns a `NOT_CONFIGURED` response
and the frontend displays a configuration notice. No fake answer is returned.

---

## Adding the YOLO Product Detector

When YOLO11s training is complete in Google Colab:

1. Export `best.pt` from Colab.
2. Place it at `backend/models/yolo/best.pt`.
3. Create `backend/models/yolo/classes.json`:
   ```json
   ["laptop","cell_phone","keyboard","mouse","bottle","cup",
    "backpack","handbag","book","clock","vase","chair",
    "remote","scissors","teddy_bear"]
   ```
4. Restart the Flask backend — it will auto-load the model.

The Vision Scanner will then run the full pipeline:
Camera → YOLO → ABO lookup → Material classifier → Packaging recommendation.

---

## Data Sources

- **ABO catalog**: `public/wrapture_abo_products.json` — 42,650 dimension-valid products
- **Packrift catalog**: `public/data/wrapture_packaging_catalog.json` — 2,209 packaging records
- **Material model**: `public/models/wrapture-material/` (TF.js) and `model_conversion/content/wrapture_material_model/` (SavedModel)

---

## EcoShop — Packrift Catalog

EcoShop loads `public/data/wrapture_packaging_catalog.json` directly in the
browser (2,209 records). No backend call is made for catalog browsing.

**Real fields displayed:**

| Field | Displayed as |
|---|---|
| `title` | Product title |
| `sku` | SKU |
| `family` | Family tag (Boxes / Mailers / Poly Bags) |
| `product_type` | Type tag |
| `length_in`, `width_in`, `height_in` | Dimensions |
| `material` | Material (human-readable label) |
| `unit_price` | Per-unit price in USD |
| `pack_quantity` | Pack quantity |
| `protection_evidence` | Evidence strings (e.g. "ECT-32", "double wall") |
| `co2e_recycling_mt` | Converted to kg, labelled as modeled recycling CO₂e |
| `canonical_product_url` | "View source product" link |

**Fields not available / not displayed:**
- Ratings — not in catalog → not shown
- Reviews — not in catalog → not shown
- Live stock/inventory — not in catalog → "Availability not verified"
- `snapshot_price` — never shown as unit price

---

## API Endpoints

See `docs/API.md` for full documentation.

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/models` | Model registry + availability |
| POST | `/api/packaging/recommend` | Packaging recommendation |
| POST | `/api/vision/analyze` | Full vision pipeline |
| POST | `/api/vision/material` | Material classification only |
| GET | `/api/products/search` | Search ABO catalog |
| POST | `/api/products/lookup` | Get representative product |
| POST | `/api/reviews/analyze` | Sentiment analysis |
| POST | `/api/chat` | TrashGPT chatbot |
| GET | `/api/dashboard/stats` | Real usage statistics |
| GET | `/api/ecopoints` | EcoPoints summary |
| POST | `/api/ecopoints/events` | Record EcoPoints event |
| GET | `/api/ecopoints/leaderboard` | EcoPoints leaderboard |
| GET | `/api/ecopoints/rules` | EcoPoints rules |
| GET | `/api/recycling/nearby` | Nearby recycling centers (Google Places) |
