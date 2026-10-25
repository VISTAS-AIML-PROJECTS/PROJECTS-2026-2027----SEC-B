import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getApiBaseUrl, setApiBaseUrl, resetApiBaseUrl, getHealth, getModels } from '../utils/api';

/**
 * ProfilePage — Wrapture workspace & profile screen
 *
 * Follows Stitch wrapture_10_profile_history design spec.
 * Provides:
 *   - Workspace overview with hero image
 *   - Quick navigation to all app sections (acts as "More" hub)
 *   - Backend server configuration (URL override for mobile APK)
 *   - Model info pulled from /api/models
 *   - Health check status
 *   - Onboarding reset
 */
export default function ProfilePage() {
  const navigate = useNavigate();
  const [apiUrl, setApiUrlState] = useState('');
  const [savedUrl, setSavedUrl] = useState('');
  const [healthStatus, setHealthStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [models, setModels] = useState(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  useEffect(() => {
    const current = getApiBaseUrl();
    setSavedUrl(current);
    setApiUrlState(current);
  }, []);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        await getHealth();
        if (mounted) setHealthStatus('online');
      } catch {
        if (mounted) setHealthStatus('offline');
      }
    };
    check();
    const iv = setInterval(check, 15000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  const loadModels = async () => {
    setModelsLoading(true);
    try {
      const data = await getModels();
      setModels(data);
    } catch {
      setModels({ error: 'Could not load models' });
    } finally {
      setModelsLoading(false);
    }
  };

  const handleSaveUrl = () => {
    setApiBaseUrl(apiUrl);
    setSavedUrl(apiUrl);
    setSaveMsg('Saved! Reconnecting…');
    setTimeout(() => setSaveMsg(''), 2500);
    setHealthStatus('checking');
    getHealth()
      .then(() => setHealthStatus('online'))
      .catch(() => setHealthStatus('offline'));
  };

  const handleResetUrl = () => {
    resetApiBaseUrl();
    const def = (process.env.REACT_APP_API_URL || 'http://localhost:5000').replace(/\/$/, '');
    setApiUrlState(def);
    setSavedUrl(def);
    setSaveMsg('Reset to default');
    setTimeout(() => setSaveMsg(''), 2000);
  };

  const handleResetOnboarding = () => {
    localStorage.removeItem('wrapture_onboarding_completed');
    navigate('/splash');
  };

  const sections = [
    { id: 'packaging', label: 'Packaging Recommender', sub: 'AI-powered sizing engine', icon: 'inventory_2', to: '/' },
    { id: 'scanner', label: 'AI Product Scanner', sub: 'YOLO11s product detection', icon: 'qr_code_scanner', to: '/scanner' },
    { id: 'simulator', label: '3D Packaging Simulator', sub: 'Interactive three.js model', icon: 'view_in_ar', to: '/simulator' },
    { id: 'sustainability', label: 'Sustainability Insights', sub: 'Volume & CO₂ analysis', icon: 'compost', to: '/sustainability' },
    { id: 'shop', label: 'EcoShop', sub: 'Certified eco products', icon: 'storefront', to: '/shop' },
    { id: 'logistics', label: 'Reverse Logistics', sub: 'Return & recycle routing', icon: 'sync_alt', to: '/logistics' },
    { id: 'dashboard', label: 'EcoPoints', sub: 'Your impact rewards', icon: 'workspace_premium', to: '/dashboard' },
    { id: 'chatbot', label: 'TrashGPT', sub: 'AI packaging assistant', icon: 'smart_toy', to: '/chatbot' },
    { id: 'analyzer', label: 'Review Analyzer', sub: 'NLP sentiment analysis', icon: 'analytics', to: '/analyzer' },
    { id: 'admin', label: 'Admin Dashboard', sub: 'System management', icon: 'admin_panel_settings', to: '/admin' },
  ];

  return (
    <div className="flex flex-col w-full min-h-full bg-surface pb-safe-nav">
      <div className="flex flex-col w-full px-5 space-y-5 pb-8">

        {/* Hero Section */}
        <section className="pt-3 flex flex-col gap-3">
          <div className="flex flex-col">
            <h1 className="font-serif text-[26px] text-primary font-medium tracking-tight">Your Wrapture</h1>
            <p className="font-body-sm text-[13px] text-on-surface-variant">Your packaging workspace.</p>
          </div>

          {/* Hero image card */}
          <div className="relative rounded-2xl overflow-hidden shadow-xs border border-outline-variant/30 bg-surface-container-low">
            <div className="aspect-[16/9] w-full overflow-hidden">
              <img
                src="/assets/hero-kraft-packaging.png"
                alt="WRAPTURE sustainable bespoke packaging workspace overview"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
              <div className="bg-surface/90 backdrop-blur-md px-3 py-1.5 rounded-full border border-outline-variant/40 shadow-xs flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    healthStatus === 'online' ? 'bg-secondary animate-pulse' :
                    healthStatus === 'checking' ? 'bg-amber-500' : 'bg-error'
                  }`}
                />
                <span className="font-label-caps text-[11px] font-semibold text-primary tracking-wide uppercase">
                  Flask Backend · {healthStatus === 'online' ? 'Live' : healthStatus === 'checking' ? 'Connecting…' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* All Sections — Navigation Hub */}
        <section className="flex flex-col space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <h2 className="font-serif text-[17px] text-primary font-medium">All Tools</h2>
          </div>
          <div className="bg-surface-container-low rounded-2xl divide-y divide-outline-variant/20 overflow-hidden shadow-xs border border-outline-variant/30">
            {sections.map((s) => (
              <Link
                key={s.id}
                to={s.to}
                id={`profile-nav-${s.id}`}
                className="p-3.5 flex items-center gap-3.5 hover:bg-surface-container/60 transition-colors"
              >
                <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-primary shadow-xs border border-outline-variant/20 shrink-0">
                  <span className="material-symbols-outlined text-[20px]">{s.icon}</span>
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="font-body-md text-[13px] font-semibold text-primary truncate">{s.label}</span>
                  <span className="font-body-sm text-[11px] text-on-surface-variant">{s.sub}</span>
                </div>
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant/60 shrink-0">chevron_right</span>
              </Link>
            ))}
          </div>
        </section>

        {/* Backend Config */}
        <section className="flex flex-col space-y-3">
          <h2 className="font-serif text-[17px] text-primary font-medium px-1">Server Configuration</h2>
          <div className="bg-surface-container-low rounded-2xl border border-outline-variant/30 shadow-xs overflow-hidden">
            <div className="p-4">
              <label className="font-label-caps text-[10px] tracking-widest uppercase text-secondary font-semibold block mb-2">
                Flask API URL
              </label>
              <input
                id="api-url-input"
                type="url"
                value={apiUrl}
                onChange={(e) => setApiUrlState(e.target.value)}
                placeholder="http://192.168.x.x:5000"
                className="w-full bg-surface border border-outline-variant/40 rounded-xl px-4 py-3 text-[13px] font-label-mono-data text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-secondary transition-colors"
              />
              <p className="font-body-sm text-[11px] text-on-surface-variant mt-2 leading-relaxed">
                On Android APK: set to your computer's LAN IP (e.g. http://192.168.1.5:5000). Both devices must be on the same Wi-Fi.
              </p>
              {saveMsg && (
                <p className="font-label-mono-data text-[11px] text-secondary mt-1 font-medium">{saveMsg}</p>
              )}
            </div>
            <div className="px-4 pb-4 flex gap-2">
              <button
                id="save-api-url-btn"
                onClick={handleSaveUrl}
                className="flex-1 py-2.5 bg-primary text-surface rounded-xl text-[13px] font-medium font-label-caps tracking-wide hover:bg-primary-container transition-colors cursor-pointer"
              >
                Save URL
              </button>
              <button
                id="reset-api-url-btn"
                onClick={handleResetUrl}
                className="py-2.5 px-4 bg-surface-container text-on-surface-variant rounded-xl text-[13px] font-medium font-label-caps tracking-wide hover:bg-surface-container-high transition-colors cursor-pointer"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Current saved URL display */}
          <div className="bg-surface-container-low rounded-xl border border-outline-variant/20 px-4 py-3">
            <span className="font-label-caps text-[10px] text-on-surface-variant tracking-wider uppercase block mb-1">
              Active Server
            </span>
            <span className="font-label-mono-data text-[12px] text-primary break-all">{savedUrl}</span>
          </div>
        </section>

        {/* AI Models Info */}
        <section className="flex flex-col space-y-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="font-serif text-[17px] text-primary font-medium">AI Models</h2>
            <button
              id="load-models-btn"
              onClick={loadModels}
              disabled={modelsLoading}
              className="font-label-caps text-[11px] text-secondary tracking-wider uppercase font-bold hover:underline flex items-center gap-1 cursor-pointer"
            >
              {modelsLoading ? (
                <span className="material-symbols-outlined text-[14px] animate-spin">sync</span>
              ) : (
                <span className="material-symbols-outlined text-[14px]">refresh</span>
              )}
              {modelsLoading ? 'Loading…' : 'Load'}
            </button>
          </div>

          {models ? (
            <div className="bg-surface-container-low rounded-2xl border border-outline-variant/30 shadow-xs overflow-hidden divide-y divide-outline-variant/20">
              {models.error ? (
                <div className="p-4 text-[13px] text-error">{models.error}</div>
              ) : (
                Object.entries(models).map(([key, val]) => (
                  <div key={key} className="p-3.5 flex items-start gap-3">
                    <span className="material-symbols-outlined text-[18px] text-secondary mt-0.5 shrink-0">smart_toy</span>
                    <div className="flex-1 min-w-0">
                      <span className="font-label-caps text-[10px] tracking-wider uppercase text-on-surface-variant block">{key}</span>
                      <span className="font-label-mono-data text-[12px] text-primary break-all">
                        {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="bg-surface-container-low rounded-2xl border border-outline-variant/30 p-4 text-center">
              <span className="material-symbols-outlined text-[28px] text-on-surface-variant/40">smart_toy</span>
              <p className="font-body-sm text-[12px] text-on-surface-variant mt-2">Tap Load to view registered AI models</p>
            </div>
          )}
        </section>

        {/* Misc Actions */}
        <section className="flex flex-col space-y-3">
          <h2 className="font-serif text-[17px] text-primary font-medium px-1">Settings</h2>
          <div className="bg-surface-container-low rounded-2xl border border-outline-variant/30 shadow-xs overflow-hidden divide-y divide-outline-variant/20">

            <button
              id="reset-onboarding-btn"
              onClick={handleResetOnboarding}
              className="w-full p-3.5 flex items-center gap-3.5 hover:bg-surface-container/60 transition-colors cursor-pointer text-left"
            >
              <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-primary shadow-xs border border-outline-variant/20 shrink-0">
                <span className="material-symbols-outlined text-[20px]">restart_alt</span>
              </div>
              <div className="flex flex-col min-w-0 flex-1">
                <span className="font-body-md text-[13px] font-semibold text-primary">Reset Onboarding</span>
                <span className="font-body-sm text-[11px] text-on-surface-variant">View intro tutorial again</span>
              </div>
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant/60 shrink-0">chevron_right</span>
            </button>

            <Link
              to="/admin"
              id="profile-admin-link"
              className="p-3.5 flex items-center gap-3.5 hover:bg-surface-container/60 transition-colors"
            >
              <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center text-primary shadow-xs border border-outline-variant/20 shrink-0">
                <span className="material-symbols-outlined text-[20px]">admin_panel_settings</span>
              </div>
              <div className="flex flex-col min-w-0 flex-1">
                <span className="font-body-md text-[13px] font-semibold text-primary">Admin Dashboard</span>
                <span className="font-body-sm text-[11px] text-on-surface-variant">System management</span>
              </div>
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant/60 shrink-0">chevron_right</span>
            </Link>
          </div>
        </section>

        {/* App Version */}
        <div className="flex items-center justify-center pt-2 pb-4">
          <span className="font-label-caps text-[10px] tracking-widest uppercase text-on-surface-variant/60">
            WRAPTURE v1.0 · INTELLIGENT PACKAGING
          </span>
        </div>
      </div>
    </div>
  );
}
