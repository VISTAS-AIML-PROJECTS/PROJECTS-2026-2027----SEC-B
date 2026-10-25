import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { getHealth, getApiBaseUrl } from '../utils/api';

export default function WraptureHeader({ title, showBack = false, onBack }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [serverUrl, setServerUrl] = useState('');

  const isHome = location.pathname === '/';
  const shouldShowBack = showBack || (!isHome && location.pathname !== '/splash' && location.pathname !== '/onboarding');

  useEffect(() => {
    let mounted = true;
    setServerUrl(getApiBaseUrl());

    const check = async () => {
      try {
        await getHealth();
        if (mounted) setBackendStatus('online');
      } catch (e) {
        if (mounted) setBackendStatus('offline');
      }
    };

    check();
    const interval = setInterval(check, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-surface/90 backdrop-blur-xl pt-safe shadow-[0_1px_8px_rgba(43,43,40,0.03)] border-b border-outline-variant/20">
      <div className="h-14 px-4 sm:px-6 flex items-center justify-between gap-3 max-w-7xl mx-auto">
        <div className="flex items-center gap-2.5 min-w-0">
          {shouldShowBack && (
            <button
              onClick={handleBack}
              aria-label="Go back"
              className="w-9 h-9 rounded-full bg-surface-container flex items-center justify-center text-primary hover:bg-surface-container-high transition-colors -ml-1 shrink-0 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">arrow_back</span>
            </button>
          )}

          {/* Origami Vessel Leaf Brandmark */}
          <Link to="/" className="flex items-center gap-2 shrink-0 group">
            <svg 
              className="w-6 h-6 text-primary flex-shrink-0 transition-transform group-hover:scale-105" 
              fill="none" 
              viewBox="0 0 28 28" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M14 2L24 7.5V20.5L14 26L4 20.5V7.5L14 2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.6"></path>
              <path d="M14 2V26" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
              <path d="M14 8L20 12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
              <path d="M14 14L22 18" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
              <path d="M14 8L8 12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
              <path d="M14 14L6 18" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
            </svg>
            <div className="flex flex-col">
              <span className="font-serif tracking-[0.18em] font-semibold text-primary text-[14px] leading-none uppercase">
                WRAPTURE
              </span>
              <span className="font-label-caps tracking-[0.24em] font-semibold text-primary/60 text-[8px] uppercase mt-0.5">
                INTELLIGENT PACKAGING
              </span>
            </div>
          </Link>

          {title && (
            <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-outline-variant/30 min-w-0">
              <h1 className="font-serif text-sm font-medium text-primary truncate">
                {title}
              </h1>
            </div>
          )}
        </div>

        {/* Right Section: Real Backend Status Indicator & Profile Link */}
        <div className="flex items-center gap-2 shrink-0">
          <Link
            to="/profile"
            title={`Backend: ${backendStatus} (${serverUrl})`}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-xs font-label-mono-data text-on-surface-variant hover:bg-surface-container-high transition-colors"
          >
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                backendStatus === 'online'
                  ? 'bg-secondary animate-pulse'
                  : backendStatus === 'checking'
                  ? 'bg-amber-500 animate-ping'
                  : 'bg-error'
              }`}
            />
            <span className="hidden sm:inline text-[11px] font-medium text-primary">
              {backendStatus === 'online' ? 'Flask Live' : backendStatus === 'checking' ? 'Connecting...' : 'Offline'}
            </span>
          </Link>

          <Link
            to="/profile"
            aria-label="Profile and Workspace Settings"
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-surface hover:bg-primary-container transition-colors shadow-xs"
          >
            <span className="material-symbols-outlined text-surface text-[18px]">person</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
