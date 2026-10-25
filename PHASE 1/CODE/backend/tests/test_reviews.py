"""
tests/test_reviews.py

Tests for POST /api/reviews/analyze

Model: distilbert-base-uncased-finetuned-sst-2-english (HuggingFace)
Source: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
Trained by: HuggingFace / Stanford (SST-2 fine-tune). NOT trained by Wrapture.
Purpose: General binary sentiment classification (POSITIVE / NEGATIVE).

Run from backend/:
    python -m pytest tests/test_reviews.py -v

Test cases:
1.  Positive review — model returns POSITIVE with real confidence
2.  Negative review — model returns NEGATIVE with real confidence
3.  Empty text — 400 response
4.  Missing text field — 400 response
5.  Batch reviews (blank-line separated) — aggregate counts calculated from inference
6.  MODEL_UNAVAILABLE — handled gracefully when model cannot load
7.  Actual confidence returned — confidence is a float in [0, 1]
8.  Aggregate percentages calculated correctly from real inference results
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def _model_available(data):
    """Return False if the model is not installed — skip the test."""
    return data.get('status') != 'MODEL_UNAVAILABLE'


# ── 1. Positive review ────────────────────────────────────────────────────────

def test_positive_review(client):
    r = client.post('/api/reviews/analyze', json={
        'text': 'Great packaging, arrived perfectly intact in eco-friendly cardboard!'
    })
    assert r.status_code == 200
    data = r.get_json()
    if not _model_available(data):
        pytest.skip('Sentiment model not installed')

    assert data['status'] == 'OK'
    assert data['reviews_analyzed'] == 1
    assert data['sentiment']['positive'] == 1
    assert data['sentiment']['negative'] == 0

    seg = data['segment_results'][0]
    assert seg['sentiment'] == 'positive'
    assert 0.0 <= seg['confidence'] <= 1.0


# ── 2. Negative review ────────────────────────────────────────────────────────

def test_negative_review(client):
    r = client.post('/api/reviews/analyze', json={
        'text': 'The box was completely crushed and the product arrived broken.'
    })
    assert r.status_code == 200
    data = r.get_json()
    if not _model_available(data):
        pytest.skip('Sentiment model not installed')

    assert data['status'] == 'OK'
    assert data['reviews_analyzed'] == 1
    assert data['sentiment']['negative'] == 1
    assert data['sentiment']['positive'] == 0

    seg = data['segment_results'][0]
    assert seg['sentiment'] == 'negative'
    assert 0.0 <= seg['confidence'] <= 1.0


# ── 3. Empty text — 400 ───────────────────────────────────────────────────────

def test_empty_text(client):
    r = client.post('/api/reviews/analyze', json={'text': ''})
    assert r.status_code == 400


# ── 4. Missing text field — 400 ───────────────────────────────────────────────

def test_missing_text_field(client):
    r = client.post('/api/reviews/analyze', json={})
    assert r.status_code == 400


# ── 5. Batch reviews — aggregate counts from real inference ──────────────────

def test_batch_reviews_aggregate(client):
    r = client.post('/api/reviews/analyze', json={
        'text': (
            'The packaging was completely crushed when it arrived.\n\n'
            'Great product, arrived in eco-friendly cardboard — very impressed!\n\n'
            'Way too much plastic bubble wrap, very wasteful.'
        )
    })
    assert r.status_code == 200
    data = r.get_json()
    if not _model_available(data):
        pytest.skip('Sentiment model not installed')

    assert data['status'] == 'OK'
    # Three blank-line-separated segments
    assert data['reviews_analyzed'] == 3
    # Aggregate counts must sum to total
    total = (data['sentiment']['positive'] +
             data['sentiment']['negative'] +
             data['sentiment']['neutral'])
    assert total == data['reviews_analyzed']
    # Each segment must have a result
    assert len(data['segment_results']) == 3


# ── 6. MODEL_UNAVAILABLE — graceful handling ──────────────────────────────────

def test_model_unavailable_handling(client, monkeypatch):
    """
    Simulate the model failing to load.
    The endpoint must return a structured error, not a 500.
    """
    import services.review_analyzer as svc
    original_pipeline = svc._pipeline
    original_error    = svc._pipeline_error

    svc._pipeline       = None
    svc._pipeline_error = 'Simulated load failure'

    try:
        r = client.post('/api/reviews/analyze', json={
            'text': 'Some review text.'
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data['status'] == 'MODEL_UNAVAILABLE'
        assert 'error' in data
        assert len(data['error']) > 0
    finally:
        svc._pipeline       = original_pipeline
        svc._pipeline_error = original_error


# ── 7. Actual confidence returned — float in [0, 1] ──────────────────────────

def test_confidence_is_real_float(client):
    r = client.post('/api/reviews/analyze', json={
        'text': 'Excellent packaging, very well protected.'
    })
    assert r.status_code == 200
    data = r.get_json()
    if not _model_available(data):
        pytest.skip('Sentiment model not installed')

    assert data['status'] == 'OK'
    seg = data['segment_results'][0]
    conf = seg['confidence']
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    # Confidence must be the actual model probability, not a hardcoded value
    # A real model output is never exactly 0.5 for a clear sentiment statement
    assert conf != 0.5


# ── 8. Aggregate percentages calculated from real inference ───────────────────

def test_aggregate_percentages_from_inference(client):
    """
    Verify that positive/negative/neutral counts are derived from
    actual per-segment inference, not hardcoded.
    """
    r = client.post('/api/reviews/analyze', json={
        'text': (
            'Packaging was perfect, no damage at all.\n\n'
            'Arrived completely destroyed, terrible experience.\n\n'
            'Packaging was fine, nothing special.\n\n'
            'Love the recyclable materials used here!'
        )
    })
    assert r.status_code == 200
    data = r.get_json()
    if not _model_available(data):
        pytest.skip('Sentiment model not installed')

    assert data['status'] == 'OK'
    assert data['reviews_analyzed'] == 4

    pos = data['sentiment']['positive']
    neg = data['sentiment']['negative']
    neu = data['sentiment']['neutral']

    # Counts must sum to total
    assert pos + neg + neu == 4

    # Each segment_result sentiment must match the aggregate
    seg_pos = sum(1 for s in data['segment_results'] if s['sentiment'] == 'positive')
    seg_neg = sum(1 for s in data['segment_results'] if s['sentiment'] == 'negative')
    seg_neu = sum(1 for s in data['segment_results'] if s['sentiment'] == 'neutral')

    assert seg_pos == pos
    assert seg_neg == neg
    assert seg_neu == neu

    # Model name must be the real pretrained model, not a Wrapture-trained one
    assert data['model'] == 'distilbert-base-uncased-finetuned-sst-2-english'
