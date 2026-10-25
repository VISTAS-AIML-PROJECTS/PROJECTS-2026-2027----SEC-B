import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getDashboardStats } from '../utils/api';

/**
 * HomeDashboard — Wrapture mobile home screen
 * Follows Stitch wrapture_home_dashboard design spec.
 * Fetches real stats from /api/dashboard/stats and displays
 * live insight metrics.
 */
export default function HomeDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(() => {}); // silently fail — stats are supplemental
  }, []);

  const quickActions = [
    {
      id: 'find-packaging',
      label: 'Find Packaging',
      icon: 'package_2',
      to: '/packaging',
    },
    {
      id: 'view-impact',
      label: 'View Impact',
      icon: 'eco',
      to: '/sustainability',
    },
    {
      id: '3d-simulator',
      label: '3D Simulator',
      icon: 'view_in_ar',
      to: '/simulator',
    },
  ];

  const featureGrid = [
    {
      id: 'eco-shop',
      icon: 'storefront',
      label: 'EcoShop',
      sub: 'Eco-certified products',
      to: '/shop',
      color: 'text-secondary',
    },
    {
      id: 'trashgpt',
      icon: 'smart_toy',
      label: 'TrashGPT',
      sub: 'AI packaging chat',
      to: '/chatbot',
      color: 'text-tertiary',
    },
    {
      id: 'ecopoints',
      icon: 'workspace_premium',
      label: 'EcoPoints',
      sub: 'Your impact rewards',
      to: '/dashboard',
      color: 'text-secondary',
    },
    {
      id: 'reverse-logistics',
      icon: 'sync_alt',
      label: 'Returns',
      sub: 'Reverse logistics',
      to: '/logistics',
      color: 'text-primary',
    },
    {
      id: 'analyzer',
      icon: 'analytics',
      label: 'Reviews',
      sub: 'Packaging sentiment',
      to: '/analyzer',
      color: 'text-primary',
    },
    {
      id: 'admin',
      icon: 'admin_panel_settings',
      label: 'Admin',
      sub: 'System dashboard',
      to: '/admin',
      color: 'text-on-surface-variant',
    },
  ];

  return (
    <div className="flex flex-col w-full min-h-full bg-surface pb-safe-nav">
      {/* Scrollable content */}
      <div className="flex flex-col w-full px-5 pb-6 space-y-5">

        {/* Editorial Header */}
        <section className="flex flex-col pt-3 pb-1">
          <span className="font-label-caps text-[11px] text-on-surface-variant tracking-[0.18em] uppercase font-semibold mb-2 opacity-75">
            Welcome back,
          </span>
          <h1 className="font-serif text-[34px] text-primary font-normal tracking-[-0.02em] leading-[1.12] mb-2">
            What are you<br />
            <span className="italic">packaging?</span>
          </h1>
          <p className="font-body-md text-[14px] text-on-surface-variant font-normal opacity-80 leading-relaxed">
            Find the right packaging with AI.
          </p>
        </section>

        {/* Hero Scanner Card */}
        <section className="relative w-full rounded-2xl overflow-hidden shadow-md bg-surface-container-high transition-transform duration-300 active:scale-[0.99]">
          <div className="w-full aspect-[4/3] min-h-[280px] overflow-hidden relative rounded-2xl">
            <img
              alt="Premium sustainable packaging studio photograph — molded fiber tray product photography"
              className="w-full h-full object-cover object-center"
              src="/assets/hero-kraft-packaging.png"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-primary/80 via-primary/15 to-transparent pointer-events-none" />
            <div className="absolute bottom-4 inset-x-4 flex justify-center">
              <button
                id="scan-product-hero-btn"
                aria-label="Scan a product with AI"
                onClick={() => navigate('/scanner')}
                className="w-full max-w-xs bg-primary hover:bg-primary-container active:scale-[0.98] text-surface py-4 px-6 rounded-xl shadow-xl backdrop-blur-sm flex items-center justify-center gap-2.5 font-body-md text-[14px] font-medium tracking-wide transition-all duration-200 border border-white/10 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[20px]">qr_code_scanner</span>
                <span className="tracking-wide">Scan a product</span>
                <span className="material-symbols-outlined text-[20px] transition-transform group-hover:translate-x-0.5">arrow_forward</span>
              </button>
            </div>
          </div>
        </section>

        {/* Quick Actions Grid */}
        <section className="w-full pt-1">
          <div className="grid grid-cols-3 gap-3">
            {quickActions.map((action) => (
              <Link
                key={action.id}
                to={action.to}
                id={`quick-action-${action.id}`}
                className="flex flex-col items-center justify-center py-5 px-2 rounded-xl bg-surface-container-low shadow-sm hover:bg-surface-container active:bg-surface-variant/60 transition-all duration-150 text-center gap-2.5 min-h-[108px] border border-outline-variant/30"
              >
                <div className="w-11 h-11 rounded-full bg-surface-container flex items-center justify-center text-primary shadow-xs">
                  <span className="material-symbols-outlined text-[22px]">{action.icon}</span>
                </div>
                <span className="font-label-mono-data text-[11px] text-primary font-medium tracking-tight leading-tight">
                  {action.label}
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Daily Insight Card */}
        <section className="w-full">
          <div className="relative overflow-hidden rounded-2xl bg-surface-container-low p-5 shadow-sm border border-outline-variant/30">
            <div className="flex items-center justify-between relative z-10">
              {/* Text cluster */}
              <div className="flex flex-col max-w-[65%]">
                <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-widest mb-2 opacity-80 font-semibold">
                  Packaging Activity
                </span>
                <div className="flex flex-col mb-1.5">
                  <span className="font-serif text-[28px] text-primary font-medium tracking-tight leading-none">
                    {stats != null ? (stats.total_recommendations ?? 0) : '…'}
                  </span>
                  <span className="font-serif text-[18px] text-primary font-normal tracking-tight mt-1">
                    recommendations generated
                  </span>
                </div>
                <p className="font-body-sm text-[12px] text-on-surface-variant leading-snug mt-1 opacity-90">
                  {stats?.total_material_scans != null && stats.total_material_scans > 0
                    ? `${stats.total_material_scans} material scan${stats.total_material_scans !== 1 ? 's' : ''} completed.`
                    : 'Real Packrift catalog & EPA WARM data.'}
                </p>
              </div>

              {/* Abstract box motif */}
              <div className="w-24 h-24 flex items-center justify-end text-secondary pointer-events-none select-none">
                <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 100 100">
                  <path className="opacity-60" d="M25 35 L50 20 L75 35 L50 50 Z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.2" />
                  <path className="opacity-60" d="M25 35 L25 65 L50 80 L50 50 Z" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.2" />
                  <path className="opacity-60" d="M75 35 L75 65 L50 80" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.2" />
                  <path d="M50 72 C48 50, 68 45, 78 30 C72 45, 58 55, 50 72 Z" fill="currentColor" fillOpacity="0.15" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.4" />
                  <path d="M50 72 C42 60, 30 54, 22 48 C32 52, 42 62, 50 72 Z" fill="currentColor" fillOpacity="0.1" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.2" />
                  <circle className="opacity-80" cx="50" cy="20" fill="currentColor" r="1.5" />
                  <circle className="opacity-80" cx="75" cy="35" fill="currentColor" r="1.5" />
                  <circle className="opacity-80" cx="25" cy="35" fill="currentColor" r="1.5" />
                </svg>
              </div>
            </div>
          </div>
        </section>

        {/* Material Scan CTA */}
        <section className="w-full">
          <div className="rounded-2xl overflow-hidden relative bg-primary-container shadow-md">
            <div className="px-5 py-5 flex items-center justify-between">
              <div className="flex-1 min-w-0 pr-4">
                <span className="font-label-caps text-[10px] tracking-[0.2em] text-on-primary-container uppercase font-bold mb-1 block">
                  MATERIAL ANALYSIS
                </span>
                <h2 className="font-serif text-[20px] text-on-primary-container font-medium leading-tight mb-1">
                  Classify packaging<br />material instantly
                </h2>
                <p className="font-body-sm text-[12px] text-on-primary-container/80 leading-relaxed">
                  MobileNetV2 · 7 material classes
                </p>
              </div>
              <div className="shrink-0">
                <Link
                  to="/scanner"
                  id="material-scan-cta-btn"
                  className="w-12 h-12 rounded-full bg-surface/90 flex items-center justify-center text-primary shadow-md hover:bg-surface transition-all active:scale-95"
                >
                  <span className="material-symbols-outlined text-[22px]">photo_camera</span>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* More Tools Grid */}
        <section className="w-full">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-serif text-[18px] text-primary font-medium tracking-tight">More Tools</h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {featureGrid.map((item) => (
              <Link
                key={item.id}
                to={item.to}
                id={`feature-${item.id}`}
                className="flex flex-col p-4 rounded-2xl bg-surface-container-low border border-outline-variant/30 shadow-xs hover:bg-surface-container active:bg-surface-container-high transition-all duration-150"
              >
                <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center shadow-xs mb-3 border border-outline-variant/20">
                  <span className={`material-symbols-outlined text-[20px] ${item.color}`}>{item.icon}</span>
                </div>
                <span className="font-body-md text-[13px] font-semibold text-primary leading-tight">
                  {item.label}
                </span>
                <span className="font-body-sm text-[11px] text-on-surface-variant mt-0.5 leading-snug">
                  {item.sub}
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Stats Strip (if available) */}
        {stats && (
          <section className="w-full">
            <div className="rounded-2xl bg-surface-container-low border border-outline-variant/30 divide-y divide-outline-variant/20 overflow-hidden shadow-xs">
              <div className="px-4 py-3 flex items-center justify-between">
                <span className="font-label-caps text-[10px] tracking-widest uppercase text-on-surface-variant font-semibold">System Status</span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
                  <span className="font-label-mono-data text-[11px] text-secondary font-medium">Live</span>
                </span>
              </div>
              {stats.total_analyses != null && (
                <div className="px-4 py-3 flex items-center justify-between">
                  <span className="font-body-sm text-[13px] text-on-surface-variant">Total Analyses</span>
                  <span className="font-label-mono-data text-[13px] text-primary font-semibold">{stats.total_analyses}</span>
                </div>
              )}
              {stats.catalog_size != null && (
                <div className="px-4 py-3 flex items-center justify-between">
                  <span className="font-body-sm text-[13px] text-on-surface-variant">Catalog Records</span>
                  <span className="font-label-mono-data text-[13px] text-primary font-semibold">{stats.catalog_size.toLocaleString()}</span>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
