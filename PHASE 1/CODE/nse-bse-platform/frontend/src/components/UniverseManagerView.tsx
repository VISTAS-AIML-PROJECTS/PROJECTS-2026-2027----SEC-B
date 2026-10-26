import React, { useState, useEffect } from 'react';
import { Layers, Bookmark, CheckCircle, ExternalLink, ChevronRight, TrendingUp } from 'lucide-react';
import { api } from '../api/client';
import { Universe, Instrument } from '../types';

interface UniverseManagerViewProps {
  onSelectInstrument: (inst: Instrument) => void;
  onOpenOptionChain: (symbol: string) => void;
  onOpenFutures: (symbol: string) => void;
}

export const UniverseManagerView: React.FC<UniverseManagerViewProps> = ({
  onSelectInstrument,
  onOpenOptionChain,
  onOpenFutures
}) => {
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverseId, setSelectedUniverseId] = useState<string>('NIFTY_50');
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalMembers, setTotalMembers] = useState(0);

  useEffect(() => {
    api.getUniverses().then((data) => {
      setUniverses(data);
    });
  }, []);

  useEffect(() => {
    if (!selectedUniverseId) return;
    setLoading(true);
    api.getUniverseMembers(selectedUniverseId, 50, 0)
      .then((data) => {
        setMembers(data.members || []);
        setTotalMembers(data.total || 0);
      })
      .finally(() => setLoading(false));
  }, [selectedUniverseId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-2">
          <Layers className="w-5 h-5 text-blue-400" />
          <h1 className="text-xl font-extrabold text-white tracking-tight">Stock Universe Management</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl">
          Configurable universes isolate standard market sub-segments (e.g. NIFTY 50, F&O underlyings, or custom watchlists) for focused algorithmic modeling, backtesting, and monitoring, while the platform maintains the complete NSE & BSE market coverage.
        </p>
      </div>

      {/* Universe Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {universes.map((u) => {
          const isSelected = selectedUniverseId === u.id;
          return (
            <div
              key={u.id}
              onClick={() => setSelectedUniverseId(u.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-blue-600/15 border-blue-500 shadow-lg shadow-blue-500/10'
                  : 'bg-[#111827] border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] font-bold text-slate-400 uppercase tracking-wider">{u.id}</span>
                <span className="font-mono text-sm font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
                  {u.member_count.toLocaleString()}
                </span>
              </div>
              <h3 className="font-bold text-white text-sm mt-1">{u.name}</h3>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{u.description}</p>
            </div>
          );
        })}
      </div>

      {/* Selected Universe Members Table */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 bg-[#0d1322] border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Universe Constituents: <span className="text-blue-400 font-mono">{selectedUniverseId}</span>
            </h2>
            <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
              {totalMembers} stocks
            </span>
          </div>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Symbol</th>
                <th className="py-2.5 px-4">Company Name</th>
                <th className="py-2.5 px-3">Exchange</th>
                <th className="py-2.5 px-3 text-right">Price</th>
                <th className="py-2.5 px-3 text-right">Change %</th>
                <th className="py-2.5 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs">Loading universe constituents...</span>
                    </div>
                  </td>
                </tr>
              ) : members.length > 0 ? (
                members.map((m) => {
                  const isPositive = (m.change_percent ?? 0) >= 0;
                  return (
                    <tr key={m.instrument_token} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-4 font-mono font-bold text-white">{m.trading_symbol}</td>
                      <td className="py-2.5 px-4 text-slate-300 truncate max-w-xs">{m.name}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-300">
                          {m.exchange}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-medium text-white">
                        {m.last_price ? `₹${m.last_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold">
                        {m.change_percent ? (
                          <span className={isPositive ? 'text-emerald-400' : 'text-rose-400'}>
                            {isPositive ? '+' : ''}{m.change_percent.toFixed(2)}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <div className="flex items-center justify-center space-x-1.5">
                          <button
                            onClick={() => onOpenOptionChain(m.trading_symbol)}
                            className="px-2 py-0.5 text-[11px] rounded bg-blue-600/20 text-blue-400 hover:bg-blue-600 hover:text-white transition-colors"
                          >
                            Options
                          </button>
                          <button
                            onClick={() => onOpenFutures(m.trading_symbol)}
                            className="px-2 py-0.5 text-[11px] rounded bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white transition-colors"
                          >
                            Futures
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No members found in this universe.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
