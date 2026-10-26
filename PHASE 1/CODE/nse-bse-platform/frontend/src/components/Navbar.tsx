import React from 'react';
import {
  TrendingUp,
  Search,
  Database,
  Layers,
  LineChart,
  BarChart2,
  Bookmark,
  Cpu,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { SyncStatus } from '../types';

export type NavTab = 
  | 'ALL_STOCKS' 
  | 'NSE' 
  | 'BSE' 
  | 'FNO' 
  | 'FUTURES' 
  | 'OPTIONS' 
  | 'INDICES' 
  | 'WATCHLIST' 
  | 'PREDICTION'
  | 'SYNC' 
  | 'MODEL_LAB';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  onOpenSearch: () => void;
  onOpenBrokerSettings: () => void;
  syncStatus?: SyncStatus | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenSearch,
  onOpenBrokerSettings,
  syncStatus
}) => {
  const totalCount = syncStatus?.total_active_instruments || 62798;
  const isSyncing = syncStatus?.is_syncing || false;

  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'ALL_STOCKS', label: 'ALL STOCKS', icon: <Layers className="w-4 h-4" /> },
    { id: 'PREDICTION', label: 'AI PREDICTIONS', icon: <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" /> },
    { id: 'NSE', label: 'NSE', icon: <span className="font-bold text-xs bg-blue-500/20 text-blue-400 px-1 rounded">NSE</span> },
    { id: 'BSE', label: 'BSE', icon: <span className="font-bold text-xs bg-purple-500/20 text-purple-400 px-1 rounded">BSE</span> },
    { id: 'FNO', label: 'F&O', icon: <LineChart className="w-4 h-4" /> },
    { id: 'FUTURES', label: 'FUTURES', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'OPTIONS', label: 'OPTIONS', icon: <BarChart2 className="w-4 h-4" /> },
    { id: 'INDICES', label: 'INDICES', icon: <span className="font-bold text-xs text-amber-400">IDX</span> },
    { id: 'WATCHLIST', label: 'WATCHLIST', icon: <Bookmark className="w-4 h-4" /> },
    { id: 'SYNC', label: 'SYNC MANAGER', icon: <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-blue-400' : ''}`} /> },
    { id: 'MODEL_LAB', label: 'MODEL LAB', icon: <Cpu className="w-4 h-4 text-emerald-400" /> },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#0d1322]/95 backdrop-blur border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Terminal Info */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('ALL_STOCKS')}>
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-white">NSE + BSE</span>
                <span className="text-[10px] uppercase font-bold tracking-widest bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/30">
                  Full Universe
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs text-slate-400">
                <span className="flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="font-mono text-[11px] text-slate-300">{totalCount.toLocaleString()} instruments</span>
                </span>
                <span>•</span>
                <span className="text-[11px] text-slate-400">Cash + F&O</span>
              </div>
            </div>
          </div>

          {/* Right Header Controls: Search & Live Feed Status */}
          <div className="flex items-center space-x-2.5">
            {/* Live Feed Status Button */}
            <button
              onClick={onOpenBrokerSettings}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-500/40 text-emerald-400 hover:bg-emerald-900/40 transition-colors text-xs font-mono font-semibold"
              title="Click to configure live broker API feed"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>1s LIVE: KOTAK NEO</span>
            </button>

            {/* Global Quick Search Button */}
            <button
              onClick={onOpenSearch}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 hover:border-blue-500/50 text-slate-400 hover:text-slate-200 transition-all text-xs w-60 shadow-inner"
            >
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span className="flex-1 text-left truncate">Search RELIANCE, TCS...</span>
              <kbd className="px-1.5 py-0.5 text-[10px] bg-slate-800 text-slate-300 rounded border border-slate-700">Ctrl+K</kbd>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 overflow-x-auto no-scrollbar border-t border-slate-800/60 py-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-semibold rounded-md transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
