import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MapPin, Search, Recycle, ExternalLink, Phone, Globe, Clock, AlertCircle, Navigation } from 'lucide-react';
import { getNearbyRecycling } from '../utils/api';

/**
 * ReverseLogistics — Real recycling center locator.
 *
 * Map:    Google Maps JavaScript API
 * Places: Google Places API (New) — proxied through Flask backend
 *         so GOOGLE_MAPS_API_KEY is never exposed to the browser.
 *
 * Frontend key (REACT_APP_GOOGLE_MAPS_API_KEY) is used only to load
 * the Maps JavaScript API for the interactive map tile rendering.
 * All Places API calls go through /api/recycling/nearby.
 *
 * No recycling center data is fabricated. All results come from Google.
 */

const MAPS_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '';

// ── Disposal guidance (general best-practice text, not location data) ─────────
const DISPOSAL_GUIDANCE = [
  {
    material: 'Corrugated Cardboard',
    color: 'yellow',
    steps: [
      'Remove all tape, labels, and staples.',
      'Flatten boxes before placing in the recycling bin.',
      'Keep dry — wet cardboard is often rejected.',
    ],
  },
  {
    material: 'Kraft Paper / Paper Mailers',
    color: 'yellow',
    steps: [
      'Remove plastic windows or bubble-lined inserts.',
      'Place clean, dry paper in the paper recycling stream.',
    ],
  },
  {
    material: 'Plastic Poly Bags / Mailers',
    color: 'blue',
    steps: [
      'Most curbside programs do NOT accept plastic film.',
      'Return to a store drop-off point (many supermarkets accept plastic film).',
      'Check the How2Recycle label on the packaging.',
    ],
  },
  {
    material: 'Bubble Wrap (plastic)',
    color: 'blue',
    steps: [
      'Not accepted in most curbside recycling.',
      'Return to a store plastic film drop-off.',
      'Consider reusing before recycling.',
    ],
  },
  {
    material: 'Styrofoam / EPS Foam',
    color: 'red',
    steps: [
      'Not accepted in most curbside programs.',
      'Search for a local EPS drop-off via the AFPR locator (epspackaging.org).',
      'Avoid where possible — low recyclability.',
    ],
  },
];

const colorMap = {
  yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', title: 'text-yellow-800', text: 'text-yellow-700' },
  blue:   { bg: 'bg-blue-50',   border: 'border-blue-200',   title: 'text-blue-800',   text: 'text-blue-700'   },
  red:    { bg: 'bg-red-50',    border: 'border-red-200',    title: 'text-red-800',    text: 'text-red-700'    },
};

// ── Google Maps loader (idempotent) ───────────────────────────────────────────
let _mapsPromise = null;
function loadGoogleMaps(apiKey) {
  if (!apiKey) return Promise.reject(new Error('NO_KEY'));
  if (window.google?.maps) return Promise.resolve(window.google.maps);
  if (_mapsPromise) return _mapsPromise;
  _mapsPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&loading=async`;
    script.async = true;
    script.onload  = () => resolve(window.google.maps);
    script.onerror = () => reject(new Error('MAPS_LOAD_FAILED'));
    document.head.appendChild(script);
  });
  return _mapsPromise;
}

// ── Geocode a text query using the Maps Geocoding API ────────────────────────
function geocodeAddress(mapsApi, address) {
  return new Promise((resolve, reject) => {
    const geocoder = new mapsApi.Geocoder();
    geocoder.geocode({ address }, (results, status) => {
      if (status === 'OK' && results.length > 0) {
        const loc = results[0].geometry.location;
        resolve({ lat: loc.lat(), lng: loc.lng(), formatted: results[0].formatted_address });
      } else {
        reject(new Error(`Geocoding failed: ${status}`));
      }
    });
  });
}

// ── Component ─────────────────────────────────────────────────────────────────
const ReverseLogistics = () => {
  const mapRef      = useRef(null);
  const mapInstance = useRef(null);
  const markersRef  = useRef([]);

  const [mapsApi,       setMapsApi]       = useState(null);
  const [mapsError,     setMapsError]     = useState(null);
  const [userLocation,  setUserLocation]  = useState(null);   // { lat, lng, label }
  const [locationInput, setLocationInput] = useState('');
  const [geoState,      setGeoState]      = useState('idle'); // idle | requesting | denied | manual
  const [results,       setResults]       = useState(null);   // null = not searched yet
  const [searching,     setSearching]     = useState(false);
  const [searchError,   setSearchError]   = useState(null);
  const [sortBy,        setSortBy]        = useState('distance');
  const [radiusKm,      setRadiusKm]      = useState(10);
  const [geocoding,     setGeocoding]     = useState(false);

  // ── Load Google Maps JS ───────────────────────────────────────────────────
  useEffect(() => {
    if (!MAPS_KEY) {
      setMapsError('NO_KEY');
      return;
    }
    loadGoogleMaps(MAPS_KEY)
      .then((api) => setMapsApi(api))
      .catch(() => setMapsError('MAPS_LOAD_FAILED'));
  }, []);

  // ── Initialise map once API is ready and div is mounted ───────────────────
  useEffect(() => {
    if (!mapsApi || !mapRef.current || mapInstance.current) return;
    mapInstance.current = new mapsApi.Map(mapRef.current, {
      zoom: 12,
      center: { lat: 20, lng: 0 },
      mapTypeControl: false,
      streetViewControl: false,
    });
  }, [mapsApi]);

  // ── Update map center + markers when results change ───────────────────────
  const updateMap = useCallback((lat, lng, places) => {
    if (!mapInstance.current) return;
    mapInstance.current.setCenter({ lat, lng });
    mapInstance.current.setZoom(12);

    // Clear old markers
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    // User location marker
    const userMarker = new mapsApi.Marker({
      position: { lat, lng },
      map: mapInstance.current,
      title: 'Your location',
      icon: {
        path: mapsApi.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: '#3b82f6',
        fillOpacity: 1,
        strokeColor: '#fff',
        strokeWeight: 2,
      },
    });
    markersRef.current.push(userMarker);

    // Result markers
    places.forEach((place, i) => {
      if (place.latitude == null || place.longitude == null) return;
      const marker = new mapsApi.Marker({
        position: { lat: place.latitude, lng: place.longitude },
        map: mapInstance.current,
        title: place.name || `Result ${i + 1}`,
        label: { text: String(i + 1), color: '#fff', fontSize: '11px', fontWeight: 'bold' },
      });
      markersRef.current.push(marker);
    });
  }, [mapsApi]);

  // ── Request browser geolocation ───────────────────────────────────────────
  const requestGeolocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoState('manual');
      return;
    }
    setGeoState('requesting');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude, label: 'Your location' };
        setUserLocation(loc);
        setGeoState('granted');
      },
      () => {
        setGeoState('denied');
      },
      { timeout: 10000 }
    );
  }, []);

  // ── Geocode manual input ──────────────────────────────────────────────────
  const handleGeocode = useCallback(async () => {
    if (!locationInput.trim() || !mapsApi) return;
    setGeocoding(true);
    setSearchError(null);
    try {
      const { lat, lng, formatted } = await geocodeAddress(mapsApi, locationInput.trim());
      setUserLocation({ lat, lng, label: formatted });
      setGeoState('manual_resolved');
    } catch {
      setSearchError('Could not find that location. Try a different address or city name.');
    } finally {
      setGeocoding(false);
    }
  }, [locationInput, mapsApi]);

  // ── Search for recycling centers ──────────────────────────────────────────
  const handleSearch = useCallback(async () => {
    if (!userLocation) return;
    setSearching(true);
    setSearchError(null);
    setResults(null);
    try {
      const data = await getNearbyRecycling({
        lat: userLocation.lat,
        lng: userLocation.lng,
        radius: radiusKm * 1000,
      });
      setResults(data.results || []);
      updateMap(userLocation.lat, userLocation.lng, data.results || []);
    } catch (err) {
      const code = err?.data?.error;
      if (code === 'MAPS_NOT_CONFIGURED') {
        setSearchError('Recycling locator requires Google Maps configuration.');
      } else if (code === 'QUOTA_EXCEEDED') {
        setSearchError('Recycling location service is temporarily unavailable.');
      } else {
        setSearchError(err.message || 'Recycling location service is temporarily unavailable.');
      }
    } finally {
      setSearching(false);
    }
  }, [userLocation, radiusKm, updateMap]);

  // ── Sort results ──────────────────────────────────────────────────────────
  const sortedResults = results
    ? [...results].sort((a, b) => {
        if (sortBy === 'distance') return (a.distance_km ?? Infinity) - (b.distance_km ?? Infinity);
        if (sortBy === 'name')     return (a.name || '').localeCompare(b.name || '');
        return 0;
      })
    : [];

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">🗺️ Reverse Logistics</h1>
        <p className="text-gray-600">Find real recycling centers near you</p>
        <p className="text-xs text-gray-400 mt-1">Location data provided by Google Maps Platform.</p>
      </div>

      {/* ── Maps not configured ─────────────────────────────────────────── */}
      {mapsError === 'NO_KEY' && (
        <div className="card mb-6 bg-yellow-50 border border-yellow-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="font-semibold text-yellow-800 mb-1">Recycling locator requires Google Maps configuration.</h2>
              <p className="text-sm text-yellow-700">
                Set <code className="bg-yellow-100 px-1 rounded">REACT_APP_GOOGLE_MAPS_API_KEY</code> in{' '}
                <code className="bg-yellow-100 px-1 rounded">.env</code> and{' '}
                <code className="bg-yellow-100 px-1 rounded">GOOGLE_MAPS_API_KEY</code> in{' '}
                <code className="bg-yellow-100 px-1 rounded">backend/.env</code>.
                See README for setup instructions.
              </p>
            </div>
          </div>
        </div>
      )}

      {mapsError === 'MAPS_LOAD_FAILED' && (
        <div className="card mb-6 bg-red-50 border border-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">
              Recycling location service is temporarily unavailable. Could not load Google Maps.
            </p>
          </div>
        </div>
      )}

      {/* ── Location selection ──────────────────────────────────────────── */}
      {!mapsError && (
        <div className="card mb-6">
          <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Navigation className="h-4 w-4 text-green-600" />
            Your Location
          </h2>

          {(geoState === 'idle' || geoState === 'requesting') && (
            <div className="flex flex-col sm:flex-row gap-3 items-start">
              <button
                className="btn btn-primary flex items-center gap-2"
                onClick={requestGeolocation}
                disabled={geoState === 'requesting'}
              >
                <MapPin className="w-4 h-4" />
                {geoState === 'requesting' ? 'Requesting…' : 'Use my location'}
              </button>
              <button
                className="btn btn-secondary text-sm"
                onClick={() => setGeoState('manual')}
              >
                Enter location manually
              </button>
            </div>
          )}

          {(geoState === 'denied' || geoState === 'manual') && (
            <div>
              <p className="text-sm text-gray-600 mb-3">
                {geoState === 'denied'
                  ? 'Location permission was denied. Enter a location to search.'
                  : 'Enter a city, address, or PIN code.'}
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input flex-1 text-sm"
                  placeholder="e.g. Mumbai, 400001 or 123 Main St"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGeocode()}
                />
                <button
                  className="btn btn-primary flex items-center gap-2"
                  onClick={handleGeocode}
                  disabled={geocoding || !locationInput.trim() || !mapsApi}
                >
                  <Search className="w-4 h-4" />
                  {geocoding ? 'Finding…' : 'Find'}
                </button>
              </div>
            </div>
          )}

          {(geoState === 'granted' || geoState === 'manual_resolved') && userLocation && (
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg flex-1">
                <MapPin className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{userLocation.label}</span>
              </div>
              <button
                className="btn btn-secondary text-sm"
                onClick={() => { setGeoState('manual'); setUserLocation(null); setResults(null); }}
              >
                Change location
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── Search controls ─────────────────────────────────────────────── */}
      {userLocation && (
        <div className="card mb-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Search radius</label>
              <select
                className="input text-sm"
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
              >
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={20}>20 km</option>
                <option value={50}>50 km</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Sort results by</label>
              <select
                className="input text-sm"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="distance">Distance</option>
                <option value="name">Name</option>
              </select>
            </div>
            <button
              className="btn btn-primary flex items-center gap-2"
              onClick={handleSearch}
              disabled={searching}
            >
              <Search className="w-4 h-4" />
              {searching ? 'Searching…' : 'Find recycling centers'}
            </button>
          </div>
        </div>
      )}

      {/* ── Search error ────────────────────────────────────────────────── */}
      {searchError && (
        <div className="card mb-6 bg-red-50 border border-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{searchError}</p>
          </div>
        </div>
      )}

      {/* ── Map ─────────────────────────────────────────────────────────── */}
      {!mapsError && (
        <div
          ref={mapRef}
          className="w-full rounded-xl border border-gray-200 mb-6"
          style={{ height: '400px', background: '#e5e7eb' }}
        >
          {!mapsApi && !mapsError && (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              Loading map…
            </div>
          )}
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {results !== null && (
        <div className="mb-8">
          {sortedResults.length === 0 ? (
            <div className="card text-center py-10 text-gray-500">
              No verified recycling locations found in this search area.
            </div>
          ) : (
            <>
              <h2 className="font-semibold text-gray-800 mb-4">
                {sortedResults.length} recycling location{sortedResults.length !== 1 ? 's' : ''} found
              </h2>
              <div className="space-y-4">
                {sortedResults.map((place, i) => (
                  <div key={place.place_id || i} className="card hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-green-500 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-800">{place.name || 'Unnamed location'}</h3>

                        {place.address && (
                          <p className="text-sm text-gray-600 mt-0.5 flex items-start gap-1">
                            <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-400" />
                            {place.address}
                          </p>
                        )}

                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
                          {place.distance_km != null && (
                            <span title={place.distance_note}>
                              📍 Approx. {place.distance_km} km away
                            </span>
                          )}
                          {place.rating != null && (
                            <span>⭐ {place.rating}{place.user_rating_count != null ? ` (${place.user_rating_count} reviews)` : ''}</span>
                          )}
                          {place.open_now != null && (
                            <span className={place.open_now ? 'text-green-600' : 'text-red-500'}>
                              <Clock className="w-3 h-3 inline mr-0.5" />
                              {place.open_now ? 'Open now' : 'Closed now'}
                            </span>
                          )}
                        </div>

                        {place.primary_type && (
                          <p className="text-xs text-gray-400 mt-1">Type: {place.primary_type.replace(/_/g, ' ')}</p>
                        )}

                        <p className="text-xs text-gray-400 mt-1 italic">{place.accepted_materials}</p>

                        <div className="flex flex-wrap gap-3 mt-3">
                          {place.google_maps_uri && (
                            <a
                              href={place.google_maps_uri}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-xs text-green-600 hover:text-green-800 font-medium"
                            >
                              <ExternalLink className="w-3 h-3" />
                              View on Google Maps
                            </a>
                          )}
                          {place.phone && (
                            <a
                              href={`tel:${place.phone}`}
                              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                            >
                              <Phone className="w-3 h-3" />
                              {place.phone}
                            </a>
                          )}
                          {place.website && (
                            <a
                              href={place.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                            >
                              <Globe className="w-3 h-3" />
                              Website
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Disposal guidance ───────────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-6">
          <Recycle className="h-5 w-5 text-green-600" />
          <h2 className="text-xl font-semibold">General Disposal Guidance</h2>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          The following guidance is based on general recycling best practices.
          Always check your local authority's specific rules, as accepted materials vary by region.
        </p>
        <div className="space-y-4">
          {DISPOSAL_GUIDANCE.map(({ material, color, steps }) => {
            const c = colorMap[color];
            return (
              <div key={material} className={`p-4 rounded-lg border ${c.bg} ${c.border}`}>
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className={`h-4 w-4 ${c.title}`} />
                  <h3 className={`font-semibold ${c.title}`}>{material}</h3>
                </div>
                <ul className="space-y-1">
                  {steps.map((step) => (
                    <li key={step} className={`text-sm ${c.text} flex items-start gap-2`}>
                      <span className="mt-1">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ReverseLogistics;
