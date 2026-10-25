# API Reference

All endpoints are served by the Flask backend at `http://localhost:5000`.

---

## GET /api/health

Returns backend status.

**Response**
```json
{ "status": "ok", "service": "Wrapture Backend" }
```

---

## GET /api/models

Returns model registry with live availability check.

**Response**
```json
{
  "material_classifier": {
    "name": "Wrapture MobileNetV2 Material Classifier",
    "classes": 7,
    "status": "trained",
    "test_accuracy": "~86.98%",
    "model_present": true
  },
  "product_detector": {
    "name": "Wrapture YOLO11s Product Detector",
    "classes": 15,
    "status": "training_in_progress",
    "weights_present": false
  }
}
```

---

## POST /api/packaging/recommend

Run the deterministic packaging optimization engine against the real Packrift catalog.

**Request body**
```json
{
  "product_length": 11.7,
  "product_width": 8.3,
  "product_height": 0.5,
  "is_fragile": false,
  "clearance_fraction": 0.10,
  "top_n": 10
}
```
Dimensions are in **inches**.

**Response**
```json
{
  "status": "RECOMMENDED",
  "recommendations": [
    {
      "rank": 1,
      "sku": "...",
      "title": "...",
      "package_length_in": 12.0,
      "package_width_in": 9.0,
      "package_height_in": 1.0,
      "space_utilization": 0.897,
      "unused_volume": 5.4,
      "unit_price": 0.45,
      "co2e_recycling_mt": 0.000012,
      "material": "corrugated_cardboard",
      "protection_score": 2,
      "load_capacity_verified": false
    }
  ],
  "meta": {
    "totalCandidatesEvaluated": 2209,
    "totalPhysicalFits": 47,
    "load_capacity_verified": false
  }
}
```

Status values: `RECOMMENDED` | `NO_PHYSICAL_FIT` | `FIT_BUT_PROTECTION_UNVERIFIED`

`load_capacity_verified` is always `false` — the Packrift catalog does not provide load capacity data.

---

## POST /api/vision/analyze

Full vision pipeline: YOLO → ABO → Material → Packaging.

**Request**: `multipart/form-data` with field `image`.

**Response (YOLO unavailable)**
```json
{
  "status": "PRODUCT_DETECTOR_UNAVAILABLE",
  "error": "Product detection model not installed. Expected weights at: ...",
  "detection": null,
  "product": null,
  "material": null,
  "packaging": null
}
```

**Response (YOLO available)**
```json
{
  "status": "OK",
  "detection": {
    "class": "laptop",
    "confidence": 0.94,
    "bbox": { "x1": 120, "y1": 80, "x2": 640, "y2": 480 }
  },
  "product": {
    "item_id": "...",
    "product_type": "LAPTOP",
    "length_in": 14.2,
    "width_in": 9.8,
    "height_in": 0.8,
    "catalog_candidates": 312
  },
  "material": {
    "predicted_class": "plastic",
    "confidence": 0.72,
    "all_classes": [...]
  },
  "packaging": { ... }
}
```

---

## POST /api/vision/material

Material classification only (MobileNetV2). Does not require YOLO.

**Request**: `multipart/form-data` with field `image`.

**Response**
```json
{
  "predicted_class": "cardboard",
  "confidence": 0.91,
  "all_classes": [
    { "class": "cardboard", "confidence": 0.91 },
    { "class": "paper",     "confidence": 0.06 },
    ...
  ],
  "model": "Wrapture MobileNetV2 Material Classifier",
  "note": "Classifies packaging/waste material. Not a product detector."
}
```

Classes: `cardboard` | `compost` | `glass` | `metal` | `paper` | `plastic` | `trash`

---

## GET /api/products/search

Search the ABO catalog.

**Query parameters**: `q` (text), `type` (product_type), `limit` (default 20, max 100)

**Response**
```json
{
  "count": 5,
  "catalog_size": 42650,
  "products": [
    {
      "item_id": "...",
      "item_name": "...",
      "product_type": "LAPTOP",
      "length_in": 14.2,
      "width_in": 9.8,
      "height_in": 0.8
    }
  ]
}
```

---

## POST /api/products/lookup

Get the median-volume representative product for a type.

**Request body**: `{ "product_type": "LAPTOP" }`

**Response**: Single product record (same schema as search) or 404.

---

## POST /api/reviews/analyze

Sentiment analysis using DistilBERT SST-2.

**Request body**: `{ "text": "paste review text here..." }`

**Response**
```json
{
  "status": "OK",
  "reviews_analyzed": 3,
  "sentiment": { "positive": 1, "negative": 1, "neutral": 1 },
  "packaging_keywords": [
    { "finding": "Cardboard packaging mentioned", "mentions": 1 }
  ],
  "segment_results": [
    { "text": "...", "sentiment": "negative", "confidence": 0.98 }
  ],
  "model": "distilbert-base-uncased-finetuned-sst-2-english"
}
```

If the model is unavailable: `{ "status": "MODEL_UNAVAILABLE", "error": "..." }`

---

## POST /api/chat

TrashGPT — LLM-powered sustainability assistant.

TrashGPT uses a pretrained general-purpose language model via the OpenAI API.
It was **not** trained by Wrapture. It is a pretrained LLM used by Wrapture.

**Configuration** — set in `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | Provider (`openai` only currently) |
| `LLM_API_KEY` | _(empty)_ | OpenAI API key — required for chat to work |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model name |

**Request body**
```json
{
  "message": "What is the most eco-friendly packaging for fragile items?",
  "history": [
    { "role": "user",      "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```
`history` is optional. Up to the last 10 turns are sent as context.

**Response (configured)**
```json
{
  "status":   "OK",
  "response": "Corrugated cardboard with ECT-32 rating is a strong recyclable choice...",
  "model":    "gpt-4o-mini",
  "provider": "openai"
}
```

**Response (not configured — LLM_API_KEY missing)**
```json
{
  "status":   "NOT_CONFIGURED",
  "error":    "TrashGPT is not configured because no LLM API key is available. Set LLM_API_KEY in backend/.env to enable AI chat.",
  "response": null,
  "provider": "openai",
  "model":    null
}
```

**Error statuses**

| status | Cause |
|---|---|
| `NOT_CONFIGURED` | `LLM_API_KEY` is empty |
| `AUTH_ERROR` | API key is invalid or revoked |
| `RATE_LIMIT` | OpenAI rate limit reached |
| `TIMEOUT` | Request to OpenAI timed out |
| `CONNECTION_ERROR` | Network failure reaching OpenAI |
| `PROVIDER_ERROR` | OpenAI returned a non-auth HTTP error |
| `ERROR` | Unexpected error (safe message, no stack trace) |
| `UNSUPPORTED_PROVIDER` | `LLM_PROVIDER` is not `openai` |

The API key is **never** included in any response.

---

## GET /api/dashboard/stats

Real usage statistics from SQLite. All values start at zero.

**Response**
```json
{
  "total_recommendations": 12,
  "total_material_scans": 5,
  "total_review_analyses": 3,
  "material_distribution": [
    { "class": "cardboard", "count": 3 }
  ],
  "recommendation_statuses": {
    "RECOMMENDED": 10,
    "NO_PHYSICAL_FIT": 2
  },
  "note": "All statistics are derived from actual application usage. Starts at zero."
}
```
