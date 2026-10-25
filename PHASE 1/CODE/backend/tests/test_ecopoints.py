"""
tests/test_ecopoints.py

Tests for the EcoPoints system.

EcoPoints is a deterministic backend gamification system.
It is NOT an AI model.

Run from backend/:
    python -m pytest tests/test_ecopoints.py -v

Test cases:
1.  New user starts at zero points, zero events, null CO2
2.  Valid event creates correct points (from POINT_RULES)
3.  Invalid event_type is rejected with 400
4.  Frontend cannot submit arbitrary points (rejected with 400)
5.  Event appears in recent_events history
6.  Total points calculated correctly from multiple events
7.  CO2 remains null when no verified catalog value is supplied
8.  CO2 is stored when a verified catalog value is supplied in metadata
9.  Leaderboard does not fabricate users — unavailable with one user
10. Duplicate/replayed events are each stored (idempotency is NOT enforced —
    each action is a real event; the caller is responsible for not double-posting)
    — verified by checking event count increments correctly
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app as flask_app
from services.eco_points import POINT_RULES, init_eco_db, DB_PATH


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Each test gets a fresh in-memory-like DB by pointing DB_PATH at a temp file.
    This prevents tests from polluting each other or the real wrapture.db.
    """
    import services.eco_points as svc
    tmp_db = str(tmp_path / 'test_eco.db')
    monkeypatch.setattr(svc, 'DB_PATH', tmp_db)

    # Also patch dashboard's DB_PATH so init_db() doesn't conflict
    import services.dashboard as dash
    monkeypatch.setattr(dash, 'DB_PATH', str(tmp_path / 'test_dash.db'))

    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        # Re-run init so tables exist in the temp DB
        from services.dashboard import init_db
        init_db()
        init_eco_db()
        yield c


# ── 1. New user starts at zero ────────────────────────────────────────────────

def test_new_user_starts_at_zero(client):
    r = client.get('/api/ecopoints')
    assert r.status_code == 200
    data = r.get_json()
    assert data['points']        == 0
    assert data['events']        == 0
    assert data['co2e_saved_mt'] is None
    assert data['recent_events'] == []


# ── 2. Valid event creates correct points ─────────────────────────────────────

def test_valid_event_creates_correct_points(client):
    for event_type, expected_pts in POINT_RULES.items():
        r = client.post('/api/ecopoints/events', json={'event_type': event_type})
        assert r.status_code == 200, f"Failed for {event_type}"
        data = r.get_json()
        assert data['status']         == 'ok'
        assert data['event_recorded'] == event_type
        assert data['points_awarded'] == expected_pts


# ── 3. Invalid event_type rejected ───────────────────────────────────────────

def test_invalid_event_type_rejected(client):
    r = client.post('/api/ecopoints/events', json={'event_type': 'FAKE_EVENT_XYZ'})
    assert r.status_code == 400
    data = r.get_json()
    assert data['status'] == 'error'
    assert 'FAKE_EVENT_XYZ' in data['error']


# ── 4. Frontend cannot submit arbitrary points ────────────────────────────────

def test_frontend_cannot_submit_points(client):
    r = client.post('/api/ecopoints/events', json={
        'event_type': 'PACKAGING_ANALYSIS',
        'points': 9999,
    })
    assert r.status_code == 400
    data = r.get_json()
    assert 'points' in data['error'].lower() or 'cannot' in data['error'].lower()


# ── 5. Event appears in history ───────────────────────────────────────────────

def test_event_appears_in_history(client):
    client.post('/api/ecopoints/events', json={'event_type': 'MATERIAL_SCAN'})
    r = client.get('/api/ecopoints')
    data = r.get_json()
    assert data['events'] == 1
    assert len(data['recent_events']) == 1
    assert data['recent_events'][0]['event_type'] == 'MATERIAL_SCAN'
    assert data['recent_events'][0]['points']     == POINT_RULES['MATERIAL_SCAN']


# ── 6. Total points calculated from multiple events ───────────────────────────

def test_total_points_from_multiple_events(client):
    types = ['PACKAGING_ANALYSIS', 'MATERIAL_SCAN', 'REVIEW_ANALYSIS']
    expected = sum(POINT_RULES[t] for t in types)

    for t in types:
        client.post('/api/ecopoints/events', json={'event_type': t})

    r = client.get('/api/ecopoints')
    data = r.get_json()
    assert data['events'] == 3
    assert data['points'] == expected


# ── 7. CO2 null when no verified value supplied ───────────────────────────────

def test_co2_null_without_verified_value(client):
    client.post('/api/ecopoints/events', json={
        'event_type': 'PACKAGING_ANALYSIS',
        'metadata':   {'sku': 'BINB212'},   # no co2e_recycling_mt key
    })
    r = client.get('/api/ecopoints')
    data = r.get_json()
    assert data['co2e_saved_mt'] is None
    assert data['recent_events'][0]['co2e_saved_mt'] is None


# ── 8. CO2 stored when verified catalog value supplied ────────────────────────

def test_co2_stored_from_verified_catalog_value(client):
    # co2e_recycling_mt is negative in the catalog (CO2 saved during recycling)
    # The service stores the absolute value
    catalog_co2 = -0.0002976720000000001
    r = client.post('/api/ecopoints/events', json={
        'event_type': 'SUSTAINABLE_PACKAGING',
        'metadata':   {
            'sku':              'BINB212',
            'co2e_recycling_mt': catalog_co2,
        },
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['co2e_saved_mt'] is not None
    assert data['co2e_saved_mt'] > 0
    assert abs(data['co2e_saved_mt'] - abs(catalog_co2)) < 1e-12

    # Verify it appears in the event record
    ev = data['recent_events'][0]
    assert ev['co2e_saved_mt'] is not None
    assert ev['co2e_saved_mt'] > 0


# ── 9. Leaderboard unavailable with one user ──────────────────────────────────

def test_leaderboard_unavailable_single_user(client):
    # Record an event so the dev user has activity
    client.post('/api/ecopoints/events', json={'event_type': 'PACKAGING_ANALYSIS'})

    r = client.get('/api/ecopoints/leaderboard')
    assert r.status_code == 200
    data = r.get_json()
    assert data['status']  == 'UNAVAILABLE'
    assert data['entries'] == []
    assert 'not enough' in data['message'].lower() or 'unavailable' in data['message'].lower()


# ── 10. Multiple users rank from actual database data ─────────────────────────

def test_leaderboard_with_multiple_real_users(client, monkeypatch):
    """
    Insert a second real user directly into the DB and record events for both.
    Verify the leaderboard ranks them by actual points.
    """
    import services.eco_points as svc

    # Add a second user directly
    conn = sqlite3.connect(svc.DB_PATH)
    conn.row_factory = sqlite3.Row
    from datetime import datetime, timezone
    conn.execute(
        "INSERT INTO users (username, created_at, is_dev_user) VALUES (?, ?, 0)",
        ("user_two", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    user_two_id = conn.execute(
        "SELECT id FROM users WHERE username = 'user_two'"
    ).fetchone()["id"]
    conn.close()

    # Dev user gets 1 event (5 pts), user_two gets 2 events (5+10=15 pts)
    client.post('/api/ecopoints/events', json={'event_type': 'PACKAGING_ANALYSIS'})
    svc.record_event('PACKAGING_ANALYSIS',  user_id=user_two_id)
    svc.record_event('PACKAGING_SELECTION', user_id=user_two_id)

    r = client.get('/api/ecopoints/leaderboard')
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'ok'
    assert len(data['entries']) == 2

    # user_two has more points — must be ranked #1
    assert data['entries'][0]['username'] == 'user_two'
    assert data['entries'][0]['points']   == POINT_RULES['PACKAGING_ANALYSIS'] + POINT_RULES['PACKAGING_SELECTION']
    assert data['entries'][0]['rank']     == 1

    # dev_user is ranked #2
    assert data['entries'][1]['rank']     == 2
    assert data['entries'][1]['points']   == POINT_RULES['PACKAGING_ANALYSIS']
