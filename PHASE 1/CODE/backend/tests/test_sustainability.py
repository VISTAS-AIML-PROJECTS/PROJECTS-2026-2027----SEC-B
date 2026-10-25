"""
tests/test_sustainability.py

Tests for POST /api/sustainability/simulate

Run from backend/:
    python -m pytest tests/test_sustainability.py -v

Test cases:
1.  Valid dimensions — returns ok status
2.  Valid SKU — returns correct catalog record
3.  Unit price present — cost_per_unit is a positive float
4.  Unit price absent — cost_per_unit is null
5.  CO2 present — co2e_recycling_mt is a float (negative = CO2 saved)
6.  CO2 absent — co2e_recycling_mt is null
7.  Packaging weight present — packaging_weight_kg is a positive float
8.  Packaging weight absent — packaging_weight_kg is null
9.  Invalid SKU — 404 response
10. Missing required dimensions — 400 response
11. Zero dimensions — 400 response
12. Sustainability score is always null
13. load_capacity_verified is always false in packaging recommender
14. Material filter respected
15. data_availability flags match actual metric presence
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app as flask_app

# Load catalog once for test assertions
_CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'public', 'data', 'wrapture_packaging_catalog.json'
)
with open(_CATALOG_PATH) as f:
    _CATALOG = json.load(f)

# Build index
_INDEX = {r['sku']: r for r in _CATALOG if r.get('sku')}

# Find a SKU that has unit_price, package_weight_lb, and co2e_recycling_mt
_SKU_FULL = next(
    r['sku'] for r in _CATALOG
    if r.get('unit_price') and r.get('package_weight_lb') and r.get('co2e_recycling_mt') is not None
)

# Find a SKU that is missing unit_price (null)
_SKU_NO_PRICE = next(
    (r['sku'] for r in _CATALOG if r.get('unit_price') is None and r.get('sku')),
    None
)

# Find a SKU that is missing co2e_recycling_mt (null)
_SKU_NO_CO2 = next(
    (r['sku'] for r in _CATALOG if r.get('co2e_recycling_mt') is None and r.get('sku')),
    None
)

# Find a SKU that is missing package_weight_lb (null)
_SKU_NO_WEIGHT = next(
    (r['sku'] for r in _CATALOG if r.get('package_weight_lb') is None and r.get('sku')),
    None
)


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


# ── 1. Valid dimensions — returns ok ─────────────────────────────────────────

def test_simulate_valid_dimensions(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm': 30.0,
        'width_cm':  20.0,
        'height_cm': 10.0,
        'weight_kg': 0.5,
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] in ('ok', 'no_fit')


# ── 2. Valid SKU — returns correct catalog record ─────────────────────────────

def test_simulate_valid_sku(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['packaging']['sku'] == _SKU_FULL
    # Verify dimensions match catalog
    cat = _INDEX[_SKU_FULL]
    assert data['packaging']['length_in'] == cat['length_in']
    assert data['packaging']['width_in']  == cat['width_in']
    assert data['packaging']['height_in'] == cat['height_in']


# ── 3. Unit price present — positive float ────────────────────────────────────

def test_unit_price_present(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['cost_per_unit'] is True
    assert data['metrics']['cost_per_unit_usd'] is not None
    assert data['metrics']['cost_per_unit_usd'] > 0
    # Must match catalog value
    cat = _INDEX[_SKU_FULL]
    assert abs(data['metrics']['cost_per_unit_usd'] - cat['unit_price']) < 0.0001


# ── 4. Unit price absent — null ───────────────────────────────────────────────

@pytest.mark.skipif(_SKU_NO_PRICE is None, reason='No SKU without unit_price in catalog')
def test_unit_price_absent(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_NO_PRICE,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['cost_per_unit'] is False
    assert data['metrics']['cost_per_unit_usd'] is None


# ── 5. CO2 present — negative float (CO2 saved) ───────────────────────────────

def test_co2_present(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['co2_recycling'] is True
    co2 = data['metrics']['co2e_recycling_mt']
    assert co2 is not None
    # All co2e_recycling_mt values in this catalog are negative (CO2 saved)
    assert co2 < 0, f'Expected negative CO2 (saved), got {co2}'
    # Must match catalog value
    cat = _INDEX[_SKU_FULL]
    assert abs(co2 - cat['co2e_recycling_mt']) < 1e-10


# ── 6. CO2 absent — null ──────────────────────────────────────────────────────

@pytest.mark.skipif(_SKU_NO_CO2 is None, reason='No SKU without co2e_recycling_mt in catalog')
def test_co2_absent(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_NO_CO2,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['co2_recycling'] is False
    assert data['metrics']['co2e_recycling_mt'] is None


# ── 7. Packaging weight present — positive float ──────────────────────────────

def test_packaging_weight_present(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['packaging_weight'] is True
    wt = data['metrics']['packaging_weight_kg']
    assert wt is not None and wt > 0
    # Verify conversion: package_weight_lb * 0.453592
    cat = _INDEX[_SKU_FULL]
    expected_kg = cat['package_weight_lb'] * 0.453592
    assert abs(wt - expected_kg) < 0.00001


# ── 8. Packaging weight absent — null ────────────────────────────────────────

@pytest.mark.skipif(_SKU_NO_WEIGHT is None, reason='No SKU without package_weight_lb in catalog')
def test_packaging_weight_absent(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_NO_WEIGHT,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['data_availability']['packaging_weight'] is False
    assert data['metrics']['packaging_weight_kg'] is None


# ── 9. Invalid SKU — 404 ──────────────────────────────────────────────────────

def test_invalid_sku(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': 'NONEXISTENT_SKU_XYZ_999',
    })
    assert r.status_code == 404
    data = r.get_json()
    assert data['status'] == 'error'
    assert 'not found' in data['error'].lower()


# ── 10. Missing required dimensions — 400 ────────────────────────────────────

def test_missing_dimensions(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm': 20.0,
        'width_cm':  15.0,
        # height_cm missing
    })
    assert r.status_code == 400


# ── 11. Zero dimensions — 400 ────────────────────────────────────────────────

def test_zero_dimensions(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm': 0.0,
        'width_cm':  15.0,
        'height_cm': 10.0,
    })
    assert r.status_code == 400


# ── 12. Sustainability score is always null ───────────────────────────────────

def test_sustainability_score_always_null(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    assert data['metrics']['sustainability_score'] is None
    assert 'sustainability_score_note' in data['metrics']
    assert len(data['metrics']['sustainability_score_note']) > 10


# ── 13. data_availability flags match actual metric presence ─────────────────

def test_data_availability_flags_consistent(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':    20.0,
        'width_cm':     15.0,
        'height_cm':    10.0,
        'packaging_sku': _SKU_FULL,
    })
    data = r.get_json()
    assert data['status'] == 'ok'
    m  = data['metrics']
    da = data['data_availability']
    assert da['cost_per_unit']    == (m['cost_per_unit_usd']   is not None)
    assert da['packaging_weight'] == (m['packaging_weight_kg'] is not None)
    assert da['co2_recycling']    == (m['co2e_recycling_mt']   is not None)


# ── 14. Material filter — corrugated_cardboard ───────────────────────────────

def test_material_filter_corrugated(client):
    r = client.post('/api/sustainability/simulate', json={
        'length_cm':          30.0,
        'width_cm':           20.0,
        'height_cm':          10.0,
        'packaging_material': 'corrugated_cardboard',
    })
    assert r.status_code == 200
    data = r.get_json()
    if data['status'] == 'ok':
        # Material should be corrugated_cardboard when available
        mat = data['packaging'].get('material')
        assert mat in ('corrugated_cardboard', None), f'Unexpected material: {mat}'


# ── 15. Materials endpoint ────────────────────────────────────────────────────

def test_materials_endpoint(client):
    r = client.get('/api/sustainability/materials')
    assert r.status_code == 200
    data = r.get_json()
    assert 'materials' in data
    ids = [m['id'] for m in data['materials']]
    assert 'corrugated_cardboard' in ids
    assert 'plastic' in ids
