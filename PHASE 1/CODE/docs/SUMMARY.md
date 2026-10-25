# Wrapture — Project Summary

## Overview

Wrapture is an AI-powered sustainable packaging recommendation platform built as a cross-platform mobile and web application. It helps businesses and individuals make environmentally responsible packaging decisions by combining computer vision, machine learning, real product catalog data, and an LLM-powered sustainability assistant.

The platform is available as a React Progressive Web App (PWA) and as a native Android application built with Capacitor.

---

## Problem Statement

Packaging waste is one of the largest contributors to global CO₂ emissions and landfill volume. Businesses often select packaging based on cost alone, without visibility into environmental impact, fit efficiency, or material sustainability. Wrapture solves this by providing data-driven, AI-assisted packaging recommendations that balance cost, protection, fit, and environmental impact.

---

## Key Features

| Feature | Description |
|---|---|
| AI Vision Scanner | Camera-based product detection using YOLO11s + MobileNetV2 material classifier |
| Packaging Recommender | Deterministic engine matching product dimensions to 2,209 real Packrift catalog items |
| 3D Packaging Simulator | Interactive three.js visualizer for packaging fit and space utilization |
| Sustainability Insights | Real CO₂e recycling data from catalog, material distribution analytics |
| TrashGPT Chatbot | OpenAI GPT-4o-mini powered sustainability assistant |
| Review Analyzer | DistilBERT SST-2 sentiment analysis on packaging-related reviews |
| EcoPoints System | Gamified reward system for sustainable packaging choices |
| EcoShop | Browse and filter 2,209 real packaging products with dimensions and pricing |
| Recycling Locator | Google Maps Places API integration to find nearby recycling centers |
| Admin Dashboard | Real usage statistics from SQLite — all values start at zero, no fabricated data |

---

## System Architecture

```
React Frontend (port 3000)
        ↓  REST API (HTTP/JSON)
Flask Backend (port 5000)
        ↓
┌──────────────────────────────────────────┐
│  AI / ML Services                        │
│  ├── MobileNetV2 Material Classifier     │
│  │     Accuracy: ~86.98% (645 test imgs) │
│  ├── YOLO11s Product Detector            │
│  │     Status: Training in progress      │
│  └── DistilBERT Review Sentiment         │
│        Model: SST-2 (HuggingFace)        │
│                                          │
│  Data Services                           │
│  ├── ABO Product Catalog (42,650 items)  │
│  ├── Packrift Packaging Catalog (2,209)  │
│  ├── Deterministic Packaging Engine      │
│  ├── OpenAI LLM (TrashGPT)              │
│  └── SQLite Usage Database               │
└──────────────────────────────────────────┘
        ↓
Android APK (Capacitor 8)
```

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.3 | UI framework |
| React Router | v6 | Client-side routing |
| Tailwind CSS | v3 | Utility-first styling |
| Framer Motion | v12 | Animations and micro-interactions |
| React Three Fiber | v8 | 3D packaging simulator |
| TensorFlow.js | — | Browser-side material classification |
| Capacitor | v8 | Android native bridge |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| Flask | 3.0 | REST API framework |
| TensorFlow | 2.16 | MobileNetV2 inference |
| Ultralytics | 8.3+ | YOLO11s product detection |
| HuggingFace Transformers | 4.44+ | DistilBERT sentiment analysis |
| OpenAI SDK | 1.40 | TrashGPT LLM integration |
| SQLite | — | Usage statistics persistence |

---

## Data Sources

| Dataset | Records | Purpose |
|---|---|---|
| Amazon Berkeley Objects (ABO) | 42,650 products | Product dimension lookup |
| Packrift Packaging Catalog | 2,209 items | Packaging recommendations and EcoShop |
| Rootstrap Waste Dataset | 3,261 images | MobileNetV2 training (2,616 train / 645 test) |
| COCO 2017 (15-class subset) | — | YOLO11s training (in progress) |

---

## AI Models

### 1. Wrapture MobileNetV2 Material Classifier
- Architecture: MobileNetV2 + GlobalAveragePooling + Dense(7, softmax)
- Classes: cardboard, compost, glass, metal, paper, plastic, trash
- Test Accuracy: ~86.98% on 645 unseen images
- Status: Trained and deployed

### 2. Wrapture YOLO11s Product Detector
- Architecture: YOLO11s (Ultralytics / PyTorch)
- Classes: 15 common product types
- Status: Training in progress (Google Colab)

### 3. DistilBERT Sentiment Analyzer
- Model: distilbert-base-uncased-finetuned-sst-2-english (HuggingFace)
- Task: Binary sentiment classification on packaging reviews
- Note: Pretrained third-party model, not trained by Wrapture

---

## API Surface

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/models` | Model registry and live availability |
| POST | `/api/packaging/recommend` | Packaging recommendation engine |
| POST | `/api/vision/analyze` | Full vision pipeline |
| POST | `/api/vision/material` | Material classification only |
| GET | `/api/products/search` | Search ABO product catalog |
| POST | `/api/products/lookup` | Get representative product by type |
| POST | `/api/reviews/analyze` | Packaging sentiment analysis |
| POST | `/api/chat` | TrashGPT sustainability chatbot |
| GET | `/api/dashboard/stats` | Real usage statistics |
| GET | `/api/ecopoints` | EcoPoints summary |
| POST | `/api/ecopoints/events` | Record EcoPoints event |
| GET | `/api/ecopoints/leaderboard` | EcoPoints leaderboard |
| GET | `/api/recycling/nearby` | Nearby recycling centers |

---

## Standards Compliance

Wrapture was developed in alignment with the following internationally recognised standards:

| Standard | Full Name | Application in Wrapture |
|---|---|---|
| **ISO/IEC 25010** | Systems and Software Quality Requirements and Evaluation | Functional suitability, reliability, security, maintainability, usability, and portability addressed across all layers of the application |
| **ISO/IEC 27001** | Information Security Management | No credentials in source control, `.env` excluded via `.gitignore`, API keys never returned in responses, CORS locked to configured origins, Google Maps keys split by scope |
| **ISO/IEC 42001** | Artificial Intelligence Management System | Real measured model accuracy reported (86.98%), third-party models clearly attributed, no fabricated AI outputs, live model availability exposed via `/api/models` |
| **ISO 14001** | Environmental Management Systems | CO₂e data sourced exclusively from real catalog fields, sustainability score left null with documented justification, material ranking prioritises corrugated cardboard and kraft paper over plastic |
| **ISO/IEC 29119** | Software Testing | Pytest suite covering all backend routes, React Testing Library configured for frontend, test and production environments separated via `.env` and `FLASK_DEBUG` |
| **ISO 9241-11** | Ergonomics of Human-System Interaction | Mobile-first responsive design, `focus-visible` accessibility on all interactive elements, disabled states enforced, dark mode support, bottom navigation following mobile UX conventions |
| **ISO/IEC 9126** | Software Product Quality — Interface Design | Consistent JSON response envelopes across all endpoints, structured error status codes (no raw stack traces), full API documented with request and response schemas in `docs/API.md` |
| **ISO/IEC 12207** | Software Life Cycle Processes | Defined layered architecture (frontend → backend → services), version control via Git, documented setup, build, test, and deployment process in `README.md` |
| **ISO/IEC 5055** | Software Quality Measurement (CISQ) | Strict service layer separation (routes vs services), no hardcoded URLs anywhere, centralised configuration via `config.py` and `api.js`, reusable UI component library |
| **ISO 31000** | Risk Management | Graceful degradation on every failure path, structured fallback responses when models are unavailable, no fake data returned under any failure condition |

---

## Project Repository

GitHub: [https://github.com/Reyshmashri/wrapture](https://github.com/Reyshmashri/wrapture)

---

## Document References

- `README.md` — Setup and configuration guide
- `docs/API.md` — Full API reference
- `docs/MODELS.md` — AI model documentation
- `docs/DATA_SOURCES.md` — Data source attribution
