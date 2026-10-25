"""
tests/test_backend.py

Backend tests for Wrapture.
Run from the backend/ directory:
    python -m pytest tests/ -v

Tests cover:
1.  Health endpoint
2.  Product lookup (real ABO data)
3.  Packaging fit calculation
4.  Packaging recommendation (real Packrift catalog)
5.  YOLO model file exists
6.  YOLO model loads successfully
7.  Missing model error path
8.  Invalid image handling
9.  Valid image → real YOLO inference
10. Detection response structure
11. ABO lookup from detected category
12. Material classifier endpoint
13. Vision endpoint (missing image)
14. Dashboard stats structure
15. Review analyzer (real text input)
16. Chatbot not-configured behavior
17. Model registry endpoint
18. No fake fallback — response never contains Math.random artefacts
"""
import sys
import os
import io
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import config
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── helpers ───────────────────────────────────────────────────────────────────

def _minimal_jpeg():
    """Return a minimal valid 1×1 white JPEG as bytes."""
    return bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00,
        0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB,
        0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07,
        0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B,
        0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E,
        0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C,
        0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34,
        0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
        0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01,
        0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05,
        0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01,
        0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00,
        0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21,
        0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
        0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1,
        0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18,
        0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36,
        0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
        0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64,
        0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77,
        0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A,
        0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5,
        0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7,
        0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9,
        0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
        0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF,
        0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD2,
        0x8A, 0x28, 0x03, 0xFF, 0xD9,
    ])


# ── 1. Health ─────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


# ── 2. Product search — real ABO data ─────────────────────────────────────────

def test_product_search_returns_results(client):
    r = client.get("/api/products/search?type=LAPTOP&limit=5")
    assert r.status_code == 200
    data = r.get_json()
    assert "products" in data
    assert data["catalog_size"] > 0


def test_product_search_all_have_positive_dimensions(client):
    r = client.get("/api/products/search?type=LAPTOP&limit=20")
    data = r.get_json()
    for p in data["products"]:
        assert p["length_in"] > 0
        assert p["width_in"] > 0
        assert p["height_in"] > 0


def test_product_lookup_valid_type(client):
    r = client.post("/api/products/lookup", json={"product_type": "DRINKING_CUP"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["length_in"] > 0


def test_product_lookup_missing_type(client):
    r = client.post("/api/products/lookup", json={})
    assert r.status_code == 400


def test_product_lookup_unknown_type(client):
    r = client.post("/api/products/lookup",
                    json={"product_type": "NONEXISTENT_TYPE_XYZ_999"})
    assert r.status_code == 404


# ── 3. Packaging recommendation — real Packrift catalog ───────────────────────

def test_packaging_recommend_valid(client):
    r = client.post("/api/packaging/recommend", json={
        "product_length": 11.7,
        "product_width": 8.3,
        "product_height": 0.5,
    })
    assert r.status_code == 200
    data = r.get_json()
    assert "status" in data
    assert "meta" in data
    assert data["meta"]["totalCandidatesEvaluated"] > 0


def test_packaging_recommend_load_capacity_always_false(client):
    r = client.post("/api/packaging/recommend", json={
        "product_length": 8.0,
        "product_width": 5.0,
        "product_height": 2.0,
    })
    data = r.get_json()
    assert data["meta"]["load_capacity_verified"] is False


def test_packaging_recommend_real_dimensions_in_result(client):
    r = client.post("/api/packaging/recommend", json={
        "product_length": 8.0,
        "product_width": 5.0,
        "product_height": 2.0,
    })
    data = r.get_json()
    if data["status"] == "RECOMMENDED":
        rec = data["recommendations"][0]
        assert rec["package_length_in"] > 0
        assert rec["package_width_in"] > 0
        assert rec["package_height_in"] > 0


def test_packaging_recommend_no_fit(client):
    r = client.post("/api/packaging/recommend", json={
        "product_length": 9999.0,
        "product_width": 9999.0,
        "product_height": 9999.0,
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "NO_PHYSICAL_FIT"
    assert data["recommendations"] == []


def test_packaging_recommend_missing_dimensions(client):
    r = client.post("/api/packaging/recommend",
                    json={"product_length": 5.0})
    assert r.status_code == 400


def test_packaging_recommend_invalid_dimensions(client):
    r = client.post("/api/packaging/recommend",
                    json={"product_length": "abc", "product_width": 5.0, "product_height": 2.0})
    assert r.status_code == 400


# ── 4. YOLO model file exists ─────────────────────────────────────────────────

def test_yolo_weights_file_exists():
    assert os.path.isfile(config.YOLO_WEIGHTS_PATH), (
        f"best.pt not found at {config.YOLO_WEIGHTS_PATH}"
    )


# ── 5. YOLO model loads ───────────────────────────────────────────────────────

def test_yolo_model_loads():
    """Verify the model module loaded without error at import time."""
    from services import product_detector as pd
    assert pd._model_loaded, (
        f"YOLO model failed to load: {pd._load_error}"
    )
    assert pd._model is not None
    assert pd._class_names is not None
    assert len(pd._class_names) == 15


# ── 6. Missing model error path ───────────────────────────────────────────────

def test_missing_model_returns_error(tmp_path, monkeypatch):
    """When best.pt is absent, detect_products must return MODEL_NOT_INSTALLED."""
    import services.product_detector as pd
    monkeypatch.setattr(pd, '_model_loaded', False)
    monkeypatch.setattr(pd, '_load_error', 'PRODUCT_DETECTOR_UNAVAILABLE: test')
    result = pd.detect_products(_minimal_jpeg())
    assert result['status'] == 'MODEL_NOT_INSTALLED'
    assert result['detections'] == []
    assert 'PRODUCT_DETECTOR_UNAVAILABLE' in result['error']


# ── 7. Invalid image handling ─────────────────────────────────────────────────

def test_detect_products_invalid_image():
    from services.product_detector import detect_products, _model_loaded
    if not _model_loaded:
        pytest.skip("YOLO model not loaded")
    result = detect_products(b"not an image")
    assert result['status'] == 'INVALID_IMAGE'
    assert result['detections'] == []


# ── 8. Real YOLO inference on a valid image ───────────────────────────────────

def test_yolo_real_inference_returns_valid_structure():
    """
    Run actual YOLO11s inference on a real image (1×1 JPEG).
    A 1×1 pixel image is unlikely to trigger detections, but the pipeline
    must complete without error and return the correct response shape.
    For a genuine detection test, use a real product photograph.
    """
    from services.product_detector import detect_products, _model_loaded
    if not _model_loaded:
        pytest.skip("YOLO model not loaded")

    result = detect_products(_minimal_jpeg())
    assert result['status'] in ('OK', 'INVALID_IMAGE')
    assert 'detections' in result
    assert isinstance(result['detections'], list)


def test_yolo_inference_detection_structure():
    """Each detection must have class_id, class_name, confidence, bbox."""
    from services.product_detector import detect_products, _model_loaded
    if not _model_loaded:
        pytest.skip("YOLO model not loaded")

    result = detect_products(_minimal_jpeg())
    for det in result.get('detections', []):
        assert 'class_id' in det
        assert 'class_name' in det
        assert 'confidence' in det
        assert 'bbox' in det
        assert all(k in det['bbox'] for k in ('x1', 'y1', 'x2', 'y2'))
        assert 0.0 <= det['confidence'] <= 1.0
        assert isinstance(det['class_id'], int)


# ── 9. /api/vision/analyze endpoint ──────────────────────────────────────────

def test_vision_analyze_no_image(client):
    r = client.post("/api/vision/analyze")
    assert r.status_code == 400


def test_vision_analyze_with_image(client):
    img = _minimal_jpeg()
    r = client.post(
        "/api/vision/analyze",
        data={"image": (io.BytesIO(img), "test.jpg")},
        content_type="multipart/form-data",
    )
    assert r.status_code in (200, 400, 503)
    data = r.get_json()
    assert "status" in data
    assert "detections" in data
    assert isinstance(data["detections"], list)


def test_vision_analyze_response_shape(client):
    """Response must always contain the required top-level keys."""
    img = _minimal_jpeg()
    r = client.post(
        "/api/vision/analyze",
        data={"image": (io.BytesIO(img), "test.jpg")},
        content_type="multipart/form-data",
    )
    data = r.get_json()
    for key in ("status", "detections", "selected_detection", "product", "material", "packaging"):
        assert key in data, f"Missing key: {key}"


def test_vision_analyze_no_fake_fallback(client):
    """
    The response must never contain fabricated numeric values.
    We verify that confidence values (when present) are real floats in [0,1]
    and that no field is labelled 'mock', 'fake', or 'dummy'.
    """
    img = _minimal_jpeg()
    r = client.post(
        "/api/vision/analyze",
        data={"image": (io.BytesIO(img), "test.jpg")},
        content_type="multipart/form-data",
    )
    raw = r.get_data(as_text=True).lower()
    for forbidden in ("mock", "dummy", "fake", "placeholder", "hardcoded"):
        assert forbidden not in raw, f"Response contains forbidden word: {forbidden}"

    data = r.get_json()
    for det in data.get("detections", []):
        assert 0.0 <= det["confidence"] <= 1.0


# ── 10. ABO lookup from detected category ────────────────────────────────────

def test_abo_lookup_laptop():
    from services.product_catalog import get_representative_product
    result = get_representative_product("LAPTOP")
    if result is None:
        pytest.skip("No LAPTOP entries in ABO catalog")
    assert result["length_in"] > 0
    assert result["width_in"] > 0
    assert result["height_in"] > 0
    assert result["item_id"] is not None


def test_abo_lookup_unknown_returns_none():
    from services.product_catalog import get_representative_product
    result = get_representative_product("NONEXISTENT_CATEGORY_XYZ")
    assert result is None


# ── 11. Material classifier ───────────────────────────────────────────────────

def test_vision_material_no_image(client):
    r = client.post("/api/vision/material")
    assert r.status_code == 400


def test_vision_material_with_image(client):
    img = _minimal_jpeg()
    r = client.post(
        "/api/vision/material",
        data={"image": (io.BytesIO(img), "test.jpg")},
        content_type="multipart/form-data",
    )
    assert r.status_code in (200, 500, 503)
    data = r.get_json()
    if r.status_code == 200:
        assert "predicted_class" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["predicted_class"] in [
            "cardboard", "compost", "glass", "metal", "paper", "plastic", "trash"
        ]
    else:
        assert "error" in data


# ── 12. Dashboard stats ───────────────────────────────────────────────────────

def test_dashboard_stats_structure(client):
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.get_json()
    assert "total_recommendations" in data
    assert "total_material_scans" in data
    assert "total_review_analyses" in data
    assert isinstance(data["total_recommendations"], int)
    assert isinstance(data["total_material_scans"], int)
    assert isinstance(data["total_review_analyses"], int)
    assert "material_distribution" in data
    assert "recommendation_statuses" in data


# ── 13. Review analyzer ───────────────────────────────────────────────────────

def test_review_analyze_real_text(client):
    r = client.post("/api/reviews/analyze", json={
        "text": (
            "The packaging was completely crushed when it arrived.\n\n"
            "Great product, arrived in eco-friendly cardboard — very impressed!\n\n"
            "Way too much plastic bubble wrap, very wasteful."
        )
    })
    assert r.status_code == 200
    data = r.get_json()
    if data.get("status") == "MODEL_UNAVAILABLE":
        pytest.skip("Sentiment model not installed in this environment")
    assert data["status"] == "OK"
    assert data["reviews_analyzed"] >= 1
    total = (data["sentiment"]["positive"] +
             data["sentiment"]["negative"] +
             data["sentiment"]["neutral"])
    assert total == data["reviews_analyzed"]


def test_review_analyze_empty_text(client):
    r = client.post("/api/reviews/analyze", json={"text": ""})
    assert r.status_code == 400


def test_review_analyze_keyword_extraction(client):
    r = client.post("/api/reviews/analyze", json={
        "text": "The cardboard box was recyclable and eco-friendly. Great sustainable packaging!"
    })
    data = r.get_json()
    if data.get("status") == "MODEL_UNAVAILABLE":
        pytest.skip("Sentiment model not installed")
    keywords = [k["finding"] for k in data.get("packaging_keywords", [])]
    assert any("Cardboard" in k or "Recyclability" in k or "Sustainability" in k
               for k in keywords)


# ── 14. Chatbot — not configured ──────────────────────────────────────────────

def test_chatbot_not_configured(client):
    original = config.LLM_API_KEY
    config.LLM_API_KEY = ""
    try:
        r = client.post("/api/chat", json={"message": "Hello"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "NOT_CONFIGURED"
        assert data["response"] is None
    finally:
        config.LLM_API_KEY = original


def test_chatbot_empty_message(client):
    r = client.post("/api/chat", json={"message": ""})
    assert r.status_code == 400


# ── 15. Model registry ────────────────────────────────────────────────────────

def test_models_endpoint_structure(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.get_json()
    assert "material_classifier" in data
    assert "product_detector" in data


def test_yolo_weights_present_in_registry(client):
    """best.pt is now trained and present — registry must reflect this."""
    r = client.get("/api/models")
    data = r.get_json()
    assert data["product_detector"]["weights_present"] is True


def test_model_registry_metrics_present(client):
    """Registry must contain real held-out test metrics, not placeholders."""
    r = client.get("/api/models")
    data = r.get_json()
    pd = data["product_detector"]
    assert pd["status"] == "trained"
    assert "metrics" in pd
    metrics = pd["metrics"]
    assert metrics["precision"] == pytest.approx(0.6220, abs=1e-4)
    assert metrics["recall"] == pytest.approx(0.5097, abs=1e-4)
    assert metrics["mAP50"] == pytest.approx(0.5409, abs=1e-4)
    assert metrics["mAP50_95"] == pytest.approx(0.3716, abs=1e-4)
