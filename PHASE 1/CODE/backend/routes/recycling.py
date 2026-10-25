"""
routes/recycling.py — Recycling center locator via Google Places API (New).

Endpoint:
  GET /api/recycling/nearby?lat=&lng=&radius=&query=

The backend holds GOOGLE_MAPS_API_KEY so it is never exposed to the browser.
All place data is returned verbatim from the Google API — nothing is fabricated.
"""
import math
import os

import requests
from flask import Blueprint, jsonify, request

recycling_bp = Blueprint('recycling', __name__)

# ── Constants ─────────────────────────────────────────────────────────────────

PLACES_NEARBY_URL = 'https://places.googleapis.com/v1/places:searchNearby'
PLACES_TEXT_URL   = 'https://places.googleapis.com/v1/places:searchText'

# Fields requested from the API — only what the UI actually uses.
# Wildcard (*) is intentionally avoided to control cost.
FIELD_MASK = (
    'places.id,'
    'places.displayName,'
    'places.formattedAddress,'
    'places.location,'
    'places.googleMapsUri,'
    'places.primaryType,'
    'places.types,'
    'places.currentOpeningHours,'
    'places.nationalPhoneNumber,'
    'places.websiteUri,'
    'places.rating,'
    'places.userRatingCount'
)

DEFAULT_RADIUS_M = 10000   # 10 km
MAX_RADIUS_M     = 50000   # 50 km
MAX_RESULTS      = 20

RECYCLING_QUERIES = [
    'recycling center',
    'recycling facility',
    'e-waste recycling',
    'electronic waste recycling',
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _haversine_km(lat1, lng1, lat2, lng2):
    """Straight-line distance between two lat/lng points in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _normalize_place(place, user_lat, user_lng):
    """Return only verified fields from a Places API place object."""
    loc  = place.get('location') or {}
    plat = loc.get('latitude')
    plng = loc.get('longitude')

    distance_km = None
    if plat is not None and plng is not None:
        distance_km = round(_haversine_km(user_lat, user_lng, plat, plng), 2)

    name_obj = place.get('displayName') or {}
    name     = name_obj.get('text') if isinstance(name_obj, dict) else name_obj

    hours_obj = place.get('currentOpeningHours') or {}
    open_now  = hours_obj.get('openNow')          # bool or None

    result = {
        'place_id':          place.get('id'),
        'name':              name,
        'address':           place.get('formattedAddress'),
        'latitude':          plat,
        'longitude':         plng,
        'distance_km':       distance_km,
        'distance_note':     'Approx. straight-line distance (Haversine)',
        'google_maps_uri':   place.get('googleMapsUri'),
        'primary_type':      place.get('primaryType'),
        'types':             place.get('types'),
        'phone':             place.get('nationalPhoneNumber'),
        'website':           place.get('websiteUri'),
        'rating':            place.get('rating'),
        'user_rating_count': place.get('userRatingCount'),
        'open_now':          open_now,
        'accepted_materials': 'Accepted materials not verified',
    }
    # Strip keys whose value is None to keep the payload clean
    return {k: v for k, v in result.items() if v is not None or k in ('distance_km', 'accepted_materials', 'distance_note')}


def _api_key():
    return os.getenv('GOOGLE_MAPS_API_KEY', '')


# ── Route ─────────────────────────────────────────────────────────────────────

@recycling_bp.route('/nearby', methods=['GET'])
def nearby():
    api_key = _api_key()
    if not api_key:
        return jsonify({
            'error': 'MAPS_NOT_CONFIGURED',
            'message': 'Recycling locator requires Google Maps configuration.',
        }), 503

    # ── Validate coordinates ──────────────────────────────────────────────────
    lat_str = request.args.get('lat', '').strip()
    lng_str = request.args.get('lng', '').strip()

    if not lat_str or not lng_str:
        return jsonify({'error': 'MISSING_COORDINATES', 'message': 'lat and lng are required.'}), 400

    try:
        lat = float(lat_str)
        lng = float(lng_str)
    except ValueError:
        return jsonify({'error': 'INVALID_COORDINATES', 'message': 'lat and lng must be numeric.'}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return jsonify({'error': 'INVALID_COORDINATES', 'message': 'lat must be −90…90, lng must be −180…180.'}), 400

    # ── Validate radius ───────────────────────────────────────────────────────
    radius_str = request.args.get('radius', str(DEFAULT_RADIUS_M)).strip()
    try:
        radius = int(float(radius_str))
    except ValueError:
        return jsonify({'error': 'INVALID_RADIUS', 'message': 'radius must be a number (metres).'}), 400

    if radius <= 0 or radius > MAX_RADIUS_M:
        return jsonify({
            'error': 'INVALID_RADIUS',
            'message': f'radius must be between 1 and {MAX_RADIUS_M} metres.',
        }), 400

    # ── Call Places API (New) — Nearby Search ─────────────────────────────────
    headers = {
        'Content-Type':  'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': FIELD_MASK,
    }

    payload = {
        'locationRestriction': {
            'circle': {
                'center': {'latitude': lat, 'longitude': lng},
                'radius': float(radius),
            }
        },
        'includedTypes': ['recycling_center'],
        'maxResultCount': MAX_RESULTS,
        'languageCode': 'en',
    }

    try:
        resp = requests.post(PLACES_NEARBY_URL, json=payload, headers=headers, timeout=10)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'PROVIDER_TIMEOUT', 'message': 'Recycling location service is temporarily unavailable.'}), 503
    except requests.exceptions.RequestException as exc:
        return jsonify({'error': 'PROVIDER_ERROR', 'message': 'Recycling location service is temporarily unavailable.'}), 503

    if resp.status_code == 429:
        return jsonify({'error': 'QUOTA_EXCEEDED', 'message': 'Recycling location service is temporarily unavailable.'}), 503

    if not resp.ok:
        return jsonify({'error': 'PROVIDER_ERROR', 'message': 'Recycling location service is temporarily unavailable.'}), 503

    data   = resp.json()
    places = data.get('places') or []

    # If nearby search returns nothing, fall back to text search
    if not places:
        query = request.args.get('query', 'recycling center').strip() or 'recycling center'
        text_payload = {
            'textQuery': f'{query} near me',
            'locationBias': {
                'circle': {
                    'center': {'latitude': lat, 'longitude': lng},
                    'radius': float(radius),
                }
            },
            'maxResultCount': MAX_RESULTS,
            'languageCode': 'en',
        }
        text_headers = {
            'Content-Type':  'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': FIELD_MASK,
        }
        try:
            text_resp = requests.post(PLACES_TEXT_URL, json=text_payload, headers=text_headers, timeout=10)
            if text_resp.ok:
                places = text_resp.json().get('places') or []
        except requests.exceptions.RequestException:
            pass  # return zero results rather than error

    normalized = [_normalize_place(p, lat, lng) for p in places]
    normalized.sort(key=lambda x: x.get('distance_km') or float('inf'))

    return jsonify({
        'results':      normalized,
        'count':        len(normalized),
        'search_lat':   lat,
        'search_lng':   lng,
        'radius_m':     radius,
        'data_source':  'Google Maps Platform — Places API (New)',
    })
