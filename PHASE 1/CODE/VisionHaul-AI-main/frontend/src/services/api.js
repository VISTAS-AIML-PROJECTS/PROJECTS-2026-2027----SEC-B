const API_BASE = '/api';

export const api = {
  // Authentication
  login: async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Authentication failed');
    return data;
  },

  register: async (userData) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Profile registration failed');
    return data;
  },

  verifyAuth: async (token) => {
    const res = await fetch(`${API_BASE}/auth/verify`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('Invalid token');
    return res.json();
  },

  // Stream & Telemetry
  getTelemetry: async () => {
    const res = await fetch(`${API_BASE}/stream/telemetry`);
    if (!res.ok) throw new Error('Failed to fetch telemetry');
    return res.json();
  },

  setCameraSource: async (source, video_path = null) => {
    const res = await fetch(`${API_BASE}/stream/source`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source, video_path })
    });
    return res.json();
  },

  toggleOverlays: async (overlays) => {
    const res = await fetch(`${API_BASE}/stream/overlays`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(overlays)
    });
    return res.json();
  },

  uploadVideo: async (file) => {
    const formData = new FormData();
    formData.append('video', file);
    const res = await fetch(`${API_BASE}/stream/upload_video`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Video upload failed');
    return data;
  },

  analyzeVideo: async (fileOrFilename) => {
    let res;
    if (fileOrFilename instanceof File) {
      const formData = new FormData();
      formData.append('video', fileOrFilename);
      res = await fetch(`${API_BASE}/stream/analyze_video`, {
        method: 'POST',
        body: formData
      });
    } else {
      res = await fetch(`${API_BASE}/stream/analyze_video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: fileOrFilename })
      });
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Video analysis failed');
    return data;
  },

  // Truck Logs & Statistics
  getTruckLogs: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/trucks/logs?${qs}`);
    if (!res.ok) throw new Error('Failed to fetch truck logs');
    return res.json();
  },

  getTruckStats: async () => {
    const res = await fetch(`${API_BASE}/trucks/stats`);
    if (!res.ok) throw new Error('Failed to fetch statistics');
    return res.json();
  },

  getTruckDetail: async (id) => {
    const res = await fetch(`${API_BASE}/trucks/${id}`);
    if (!res.ok) throw new Error('Failed to fetch truck details');
    return res.json();
  },

  // Alerts
  getAlerts: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/alerts?${qs}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  getRecentAlerts: async () => {
    const res = await fetch(`${API_BASE}/alerts/recent`);
    if (!res.ok) throw new Error('Failed to fetch recent alerts');
    return res.json();
  },

  acknowledgeAlert: async (alertId) => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/ack`, {
      method: 'POST'
    });
    return res.json();
  },

  testEmailAlert: async (data = {}) => {
    const res = await fetch(`${API_BASE}/alerts/test-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  // Blocklist
  getBlocklist: async (search = '') => {
    const res = await fetch(`${API_BASE}/blocklist?search=${encodeURIComponent(search)}`);
    if (!res.ok) throw new Error('Failed to fetch blocklist');
    return res.json();
  },

  addBlocklist: async (entry) => {
    const res = await fetch(`${API_BASE}/blocklist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    });
    return res.json();
  },

  updateBlocklist: async (id, entry) => {
    const res = await fetch(`${API_BASE}/blocklist/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    });
    return res.json();
  },

  deleteBlocklist: async (id) => {
    const res = await fetch(`${API_BASE}/blocklist/${id}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  // Configuration
  getConfig: async () => {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch config');
    return res.json();
  },

  updateConfig: async (config) => {
    const res = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  },

  // Image Dataset & AI Training
  getDatasetGallery: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/dataset/gallery?${qs}`);
    if (!res.ok) throw new Error('Failed to fetch dataset gallery');
    return res.json();
  },

  getDatasetStats: async () => {
    const res = await fetch(`${API_BASE}/dataset/stats`);
    if (!res.ok) throw new Error('Failed to fetch dataset statistics');
    return res.json();
  },

  startModelTraining: async (config = {}) => {
    const res = await fetch(`${API_BASE}/dataset/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to start model training');
    return data;
  },

  getTrainingStatus: async () => {
    const res = await fetch(`${API_BASE}/dataset/training_status`);
    if (!res.ok) throw new Error('Failed to fetch training status');
    return res.json();
  },

  generateMoreImages: async (count = 50) => {
    const res = await fetch(`${API_BASE}/dataset/generate_batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to generate additional dataset images');
    return data;
  },

  // Fitness Certificate (FC) & Police Enforcement
  getFCRecords: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/fc/records?${qs}`);
    if (!res.ok) throw new Error('Failed to fetch FC records');
    return res.json();
  },

  verifyPlateFC: async (plate) => {
    const res = await fetch(`${API_BASE}/fc/verify/${encodeURIComponent(plate)}`);
    if (!res.ok) throw new Error('Failed to verify plate FC');
    return res.json();
  },

  getFCStats: async () => {
    const res = await fetch(`${API_BASE}/fc/stats`);
    if (!res.ok) throw new Error('Failed to fetch FC statistics');
    return res.json();
  },

  processFCRenewal: async (plate, test_metrics = null) => {
    const res = await fetch(`${API_BASE}/fc/renew`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_plate: plate, test_metrics })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to process FC renewal');
    return data;
  },

  issueDestructionOrder: async (plate, reason = '') => {
    const res = await fetch(`${API_BASE}/fc/destruction-order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_plate: plate, reason })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to issue destruction order');
    return data;
  },

  confirmScrapping: async (plate, scrapping_facility = '', officer_badge = 'SEC-CMD-01') => {
    const res = await fetch(`${API_BASE}/fc/confirm-scrapping`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_plate: plate, scrapping_facility, officer_badge })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to confirm vehicle destruction');
    return data;
  },

  payFCFine: async (plate, amount = null, payment_ref = null) => {
    const res = await fetch(`${API_BASE}/fc/pay-fine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_plate: plate, amount, payment_ref })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to pay FC fine');
    return data;
  },

  getPoliceNotice: async (plate) => {
    const res = await fetch(`${API_BASE}/fc/police-notice/${encodeURIComponent(plate)}`);
    if (!res.ok) throw new Error('Failed to fetch police notice');
    return res.json();
  },

  // Exports & URLs
  datasetExportUrl: `${API_BASE}/dataset/export`,
  csvDownloadUrl: `${API_BASE}/export/csv`,
  pdfDownloadUrl: `${API_BASE}/export/pdf`,
  videoFeedUrl: `${API_BASE}/stream/video_feed`,
  getSnapshotUrl: (filename) => filename ? `${API_BASE}/trucks/snapshots/${filename}` : null
};

