"""
tests/test_recycling.py — Backend tests for GET /api/recycling/nearby

Google HTTP requests are mocked inside tests only.
No mocked data is used in production code.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


# ── Helper: build a fake Places API response ─────────────────────────────────

def _places_response(places):
    """Return a mock requests.Response with the given places list."""
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'places': places}
    return mock_resp


def _empty_response():
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    return mock_resp


def _error_response(status=500):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = status
    mock_resp.json.return_value = {'error': {'message': 'API error'}}
    return mock_resp


SAMPLE_PLACE = {
    'id': 'ChIJtest123',
    'displayName': {'text': 'Green Recycling Co.'},
    'formattedAddress': '1 Eco Street, Test City',
    'location': {'latitude': 13.01, 'longitude': 80.01},
    'googleMapsUri': 'https://maps.google.com/?cid=123',
    'primaryType': 'recycling_center',
    'types': ['recycling_center'],
    'nationalPhoneNumber': '+91 99999 00000',
    'websiteUri': 'https://example.com',
    'rating': 4.2,
    'userRatingCount': 38,
    'currentOpeningHours': {'openNow': True},
}


# ── 1. Missing coordinates ────────────────────────────────────────────────────

def test_missing_coordinates(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    r = client.get('/api/recycling/nearby')
    assert r.status_code == 400
    assert r.get_json()['error'] == 'MISSING_COORDINATES'


# ── 2. Invalid coordinates ────────────────────────────────────────────────────

def test_invalid_coordinates_non_numeric(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    r = client.get('/api/recycling/nearby?lat=abc&lng=xyz')
    assert r.status_code == 400
    assert r.get_json()['error'] == 'INVALID_COORDINATES'


def test_invalid_coordinates_out_of_range(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    r = client.get('/api/recycling/nearby?lat=999&lng=0')
    assert r.status_code == 400
    assert r.get_json()['error'] == 'INVALID_COORDINATES'


# ── 3. Invalid radius ─────────────────────────────────────────────────────────

def test_invalid_radius_zero(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0&radius=0')
    assert r.status_code == 400
    assert r.get_json()['error'] == 'INVALID_RADIUS'


def test_invalid_radius_too_large(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0&radius=999999')
    assert r.status_code == 400
    assert r.get_json()['error'] == 'INVALID_RADIUS'


# ── 4. Missing API key ────────────────────────────────────────────────────────

def test_missing_api_key(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', '')
    r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 503
    assert r.get_json()['error'] == 'MAPS_NOT_CONFIGURED'


# ── 5. Successful provider response ──────────────────────────────────────────

def test_successful_response(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    with patch('routes.recycling.requests.post', return_value=_places_response([SAMPLE_PLACE])):
        r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 200
    data = r.get_json()
    assert data['count'] == 1
    assert data['results'][0]['name'] == 'Green Recycling Co.'
    assert data['results'][0]['place_id'] == 'ChIJtest123'


# ── 6. Provider error ─────────────────────────────────────────────────────────

def test_provider_error(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    with patch('routes.recycling.requests.post', return_value=_error_response(500)):
        r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 503
    assert r.get_json()['error'] == 'PROVIDER_ERROR'


# ── 7. Zero results ───────────────────────────────────────────────────────────

def test_zero_results(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    # Both nearby and text search return empty
    with patch('routes.recycling.requests.post', return_value=_empty_response()):
        r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 200
    data = r.get_json()
    assert data['count'] == 0
    assert data['results'] == []


# ── 8. Missing optional place fields ─────────────────────────────────────────

def test_missing_optional_fields(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    minimal_place = {
        'id': 'ChIJminimal',
        'displayName': {'text': 'Minimal Recycler'},
        'location': {'latitude': 13.02, 'longitude': 80.02},
        # No phone, website, rating, hours, address
    }
    with patch('routes.recycling.requests.post', return_value=_places_response([minimal_place])):
        r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 200
    result = r.get_json()['results'][0]
    assert result['name'] == 'Minimal Recycler'
    # Optional fields must not be fabricated
    assert 'phone' not in result
    assert 'website' not in result
    assert 'rating' not in result
    assert 'open_now' not in result


# ── 9. Correct response normalization ────────────────────────────────────────

def test_response_normalization(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', 'test-key')
    with patch('routes.recycling.requests.post', return_value=_places_response([SAMPLE_PLACE])):
        r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    result = r.get_json()['results'][0]
    # Distance is calculated, not fabricated
    assert result['distance_km'] is not None
    assert isinstance(result['distance_km'], float)
    # Accepted materials must always say not verified
    assert result['accepted_materials'] == 'Accepted materials not verified'
    # Distance note must clarify it is straight-line
    assert 'Haversine' in result['distance_note']


# ── 10. No fabricated fallback locations ─────────────────────────────────────

def test_no_fabricated_fallback(client, monkeypatch):
    """When the API key is missing, the response must contain zero results — never fake data."""
    monkeypatch.setenv('GOOGLE_MAPS_API_KEY', '')
    r = client.get('/api/recycling/nearby?lat=13.0&lng=80.0')
    assert r.status_code == 503
    data = r.get_json()
    assert 'results' not in data   # no results key at all when not configured
    assert data['error'] == 'MAPS_NOT_CONFIGURED'
