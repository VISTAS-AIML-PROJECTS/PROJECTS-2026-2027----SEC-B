import React, { useState, useEffect, useRef } from 'react';
import { Search, X, TrendingUp, Layers, ExternalLink, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import { Instrument } from '../types';

interface SearchBarModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectInstrument: (inst: Instrument) => void;
  onOpenOptionChain: (symbol: string) => void;
  onOpenFutures: (symbol: string) => void;
}

export const SearchBarModal: React.FC<SearchBarModalProps> = ({
  isOpen,
  onClose,
  onSelectInstrument,
  onOpenOptionChain,
  onOpenFutures
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setResults([]);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open handled by parent, or toggle
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.searchInstruments({ q: query, page_size: 20 });
        setResults(res.instruments);
        setSelectedIndex(0);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const getBadge = (inst: Instrument) => {
    const { exchange, instrument_type, option_type } = inst;
    if (instrument_type === 'INDEX') {
      return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded">Index</span>;
    }
    if (instrument_type === 'EQ') {
      if (exchange === 'NSE') {
        return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded">NSE Equity</span>;
      }
      return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded">BSE Equity</span>;
    }
    if (instrument_type === 'FUTSTK' || instrument_type === 'FUTIDX') {
      return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded">{exchange} Future</span>;
    }
    if (option_type === 'CE') {
      return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">{exchange} Call Option</span>;
    }
    if (option_type === 'PE') {
      return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded">{exchange} Put Option</span>;
    }
    return <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-slate-700 text-slate-300 rounded">{exchange} {instrument_type}</span>;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl bg-[#111827] border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-800 bg-[#0d1322]">
          <Search className="w-5 h-5 text-slate-400 mr-3" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search full NSE & BSE universe (e.g. RELIANCE, TCS, NIFTY 24000 CE, smallcaps)..."
            className="w-full bg-transparent text-sm text-white placeholder-slate-400 focus:outline-none"
          />
          {loading && <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>}
          <button onClick={onClose} className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-2">
          {results.length > 0 ? (
            results.map((inst, idx) => (
              <div
                key={inst.instrument_token}
                onClick={() => {
                  onSelectInstrument(inst);
                  onClose();
                }}
                className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                  idx === selectedIndex ? 'bg-blue-600/15 border border-blue-500/30' : 'hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center font-mono font-bold text-xs text-slate-300">
                    {inst.exchange}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white text-sm group-hover:text-blue-400 transition-colors">
                        {inst.trading_symbol}
                      </span>
                      {getBadge(inst)}
                      {inst.has_derivatives === 1 && (
                        <span className="text-[9px] font-bold bg-cyan-500/20 text-cyan-300 px-1 py-0.2 rounded border border-cyan-500/30">
                          F&O Active
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 truncate max-w-md">
                      {inst.name || inst.trading_symbol} • Token: <span className="font-mono text-slate-500">{inst.instrument_token}</span>
                      {inst.expiry && ` • Expiry: ${inst.expiry}`}
                      {inst.strike > 0 && ` • Strike: ${inst.strike}`}
                    </div>
                  </div>
                </div>

                {/* Quick actions for F&O eligible underlyings */}
                <div className="flex items-center space-x-2">
                  {inst.has_derivatives === 1 && (
                    <>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenOptionChain(inst.trading_symbol);
                          onClose();
                        }}
                        className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white transition-colors flex items-center space-x-1"
                        title="View Option Chain"
                      >
                        <span>Chain</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenFutures(inst.trading_symbol);
                          onClose();
                        }}
                        className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors"
                        title="View Futures Board"
                      >
                        <span>Futures</span>
                      </button>
                    </>
                  )}
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            ))
          ) : query.trim() ? (
            <div className="text-center py-10 text-slate-500">
              No instruments found matching "{query}" across NSE and BSE.
            </div>
          ) : (
            <div className="text-center py-10 text-slate-500 text-xs">
              Type any stock symbol (e.g. <span className="text-blue-400 font-mono">RELIANCE</span>, <span className="text-blue-400 font-mono">TCS</span>, <span className="text-blue-400 font-mono">NIFTY</span>), BSE scrip code, or small-cap stock.
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 bg-[#0d1322] border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Search covers 62,000+ official NSE, BSE, NFO, and BFO instruments</span>
          <div className="flex items-center space-x-2">
            <span>Navigate <kbd className="px-1 bg-slate-800 rounded">↑↓</kbd></span>
            <span>Select <kbd className="px-1 bg-slate-800 rounded">Enter</kbd></span>
            <span>Close <kbd className="px-1 bg-slate-800 rounded">Esc</kbd></span>
          </div>
        </div>
      </div>
    </div>
  );
};
