/**
 * api.js — Wrapture frontend API client
 *
 * All calls go to the Flask backend.
 * Configure the base URL via REACT_APP_API_URL (defaults to localhost:5000).
 * Never hardcodes localhost throughout the application.
 */

export function getApiBaseUrl() {
  const custom = typeof window !== 'undefined' ? localStorage.getItem('wrapture_custom_api_url') : null;
  if (custom && custom.trim()) {
    return custom.trim().replace(/\/$/, '');
  }
  return (process.env.REACT_APP_API_URL || 'http://localhost:5000').replace(/\/$/, '');
}

export function setApiBaseUrl(url) {
  if (typeof window !== 'undefined') {
    if (url && url.trim()) {
      localStorage.setItem('wrapture_custom_api_url', url.trim().replace(/\/$/, ''));
    } else {
      localStorage.removeItem('wrapture_custom_api_url');
    }
  }
}

export function resetApiBaseUrl() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('wrapture_custom_api_url');
  }
}

async function request(path, options = {}) {
  const base = getApiBaseUrl();
  try {
    const res = await fetch(`${base}${path}`, options);
    const json = await res.json();
    if (!res.ok) {
      const msg = json?.error || `HTTP ${res.status}`;
      throw Object.assign(new Error(msg), { status: res.status, data: json });
    }
    return json;
  } catch (err) {
    console.error(`[Wrapture API Error] ${options.method || 'GET'} ${base}${path}:`, err);
    if (err.name === 'TypeError' && (err.message.includes('fetch') || err.message.includes('NetworkError'))) {
      throw Object.assign(
        new Error(`Wrapture server unavailable at ${base}. Check your network connection or API URL in Profile / Settings.`),
        { isNetworkError: true, base, originalError: err }
      );
    }
    throw err;
  }
}

// ── Health ────────────────────────────────────────────────────────────────────

export function getHealth() {
  return request('/api/health');
}

export function getModels() {
  return request('/api/models');
}

// ── Packaging ─────────────────────────────────────────────────────────────────

export function recommendPackagingAPI(payload) {
  return request('/api/packaging/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

// ── Vision ────────────────────────────────────────────────────────────────────

export function analyzeMaterial(imageFile) {
  const fd = new FormData();
  fd.append('image', imageFile);
  return request('/api/vision/material', { method: 'POST', body: fd });
}

export function analyzeVision(imageFile) {
  const fd = new FormData();
  fd.append('image', imageFile);
  return request('/api/vision/analyze', { method: 'POST', body: fd });
}

// ── Products ──────────────────────────────────────────────────────────────────

export function searchProducts(q = '', type = '', limit = 20) {
  const params = new URLSearchParams();
  if (q)     params.set('q', q);
  if (type)  params.set('type', type);
  if (limit) params.set('limit', limit);
  return request(`/api/products/search?${params}`);
}

export function lookupProduct(productType) {
  return request('/api/products/lookup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_type: productType }),
  });
}

// ── Reviews ───────────────────────────────────────────────────────────────────

export function analyzeReviews(text) {
  return request('/api/reviews/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export function sendChat(message, history = []) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export function getDashboardStats() {
  return request('/api/dashboard/stats');
}

// ── EcoPoints ────────────────────────────────────────────────────────────────

export function getEcoPoints() {
  return request('/api/ecopoints');
}

export function recordEcoEvent(event_type, metadata = null) {
  return request('/api/ecopoints/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_type, metadata }),
  });
}

export function getEcoLeaderboard() {
  return request('/api/ecopoints/leaderboard');
}

export function getEcoRules() {
  return request('/api/ecopoints/rules');
}


export function simulatePackaging(payload) {
  return request('/api/sustainability/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export function getCatalogMaterials() {
  return request('/api/sustainability/materials');
}

// ── Recycling Locator ─────────────────────────────────────────────────────────────────────

export function getNearbyRecycling({ lat, lng, radius = 10000, query = '' } = {}) {
  const params = new URLSearchParams({ lat, lng, radius });
  if (query) params.set('query', query);
  return request(`/api/recycling/nearby?${params}`);
}
