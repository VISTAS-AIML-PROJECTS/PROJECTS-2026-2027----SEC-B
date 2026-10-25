import React from 'react';
import { useLocation, NavLink } from 'react-router-dom';
import WraptureHeader from './WraptureHeader';
import WraptureBottomNav from './WraptureBottomNav';

/**
 * Layout — Wrapture application shell
 *
 * Provides:
 *   - Fixed top header (WraptureHeader)
 *   - Desktop sidebar navigation (lg+ screens)
 *   - Mobile bottom navigation (WraptureBottomNav)
 *   - Clean full-bleed area for splash / onboarding screens
 */
export default function Layout({ children }) {
  const location = useLocation();

  // Splash and onboarding use their own full-screen layout — no chrome
  const isFullScreen =
    location.pathname === '/splash' || location.pathname === '/onboarding';

  if (isFullScreen) {
    return (
      <main className="w-full min-h-screen bg-surface">
        {children}
      </main>
    );
  }

  const desktopNavItems = [
    { to: '/',              label: 'Home',              icon: 'eco',                   end: true },
    { to: '/scanner',       label: 'AI Scanner',        icon: 'qr_code_scanner' },
    { to: '/packaging',     label: 'Packaging',         icon: 'inventory_2' },
    { to: '/simulator',     label: '3D Simulator',      icon: 'view_in_ar' },
    { to: '/sustainability',label: 'Sustainability',     icon: 'compost' },
    { to: '/shop',          label: 'EcoShop',           icon: 'storefront' },
    { to: '/logistics',     label: 'Reverse Logistics',  icon: 'sync_alt' },
    { to: '/dashboard',     label: 'EcoPoints',         icon: 'workspace_premium' },
    { to: '/analyzer',      label: 'Review Analyzer',   icon: 'analytics' },
    { to: '/chatbot',       label: 'TrashGPT',          icon: 'smart_toy' },
    { to: '/admin',         label: 'Admin',             icon: 'admin_panel_settings' },
    { to: '/profile',       label: 'Profile & Settings',icon: 'settings' },
  ];

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col antialiased">
      {/* Fixed Top Header */}
      <WraptureHeader />

      <div className="flex-1 flex w-full max-w-7xl mx-auto pt-14 pb-20 md:pb-8">

        {/* Desktop Sidebar Navigation — only visible on lg+ screens */}
        <aside className="hidden lg:flex flex-col w-64 shrink-0 p-4 border-r border-outline-variant/30 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
          <div className="mb-4 px-3 py-2 bg-surface-container-low rounded-xl border border-outline-variant/30">
            <span className="font-label-caps text-[9px] uppercase tracking-wider text-secondary font-bold block mb-1">
              Atelier Intelligence
            </span>
            <p className="font-serif text-sm font-medium text-primary">
              Wrapture Engine v1.0
            </p>
          </div>

          <nav className="flex flex-col space-y-1">
            {desktopNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl font-body-sm text-[13px] transition-colors ${
                    isActive
                      ? 'bg-primary text-surface font-semibold shadow-xs'
                      : 'text-on-surface-variant hover:bg-surface-container hover:text-primary font-medium'
                  }`
                }
              >
                <span className="material-symbols-outlined text-[19px]">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 w-full overflow-x-hidden">
          {children}
        </main>
      </div>

      {/* Mobile / Tablet Bottom Navigation — hidden on lg+ screens */}
      <div className="lg:hidden">
        <WraptureBottomNav />
      </div>
    </div>
  );
}