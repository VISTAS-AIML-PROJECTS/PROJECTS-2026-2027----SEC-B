import React from 'react';
import { NavLink } from 'react-router-dom';

export default function WraptureBottomNav() {
  const navItems = [
    { to: '/', label: 'Home', icon: 'eco', end: true },
    { to: '/scanner', label: 'Scan', icon: 'qr_code_scanner' },
    { to: '/packaging', label: 'Packages', icon: 'inventory_2' },
    { to: '/simulator', label: 'Simulator', icon: 'view_in_ar' },
    { to: '/profile', label: 'More', icon: 'grid_view' },
  ];

  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 pb-safe bg-surface/90 backdrop-blur-xl shadow-[0_-2px_12px_rgba(43,43,40,0.04)] border-t border-outline-variant/20">
      <div className="flex items-center justify-around h-16 max-w-lg mx-auto px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center min-w-[56px] h-12 transition-colors duration-150 relative ${
                isActive
                  ? 'text-primary font-semibold'
                  : 'text-on-surface-variant hover:text-primary font-normal'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span className="material-symbols-outlined text-[22px] leading-none">
                  {item.icon}
                </span>
                <span className="font-label-caps text-[10px] tracking-wider uppercase mt-1 leading-none">
                  {item.label}
                </span>
                {isActive && (
                  <span className="w-1 h-1 rounded-full bg-primary mt-1 absolute bottom-1" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
