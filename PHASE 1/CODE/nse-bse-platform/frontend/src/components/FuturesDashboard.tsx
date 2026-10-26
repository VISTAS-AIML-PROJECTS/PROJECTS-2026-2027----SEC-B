import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertCircle,
  Search,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Calendar
} from 'lucide-react';
import { api } from '../api/client';
import { FuturesDashboardResponse, FuturesContractRow } from '../types';

interface FuturesDashboardProps {
  initialSymbol?: string;
  onOpenOptionChain: (symbol: string) => void;
}

const QUICK_FUTURES_SYMBOLS = [
  'NIFTY',
  'BANKNIFTY',
  'FINNIFTY',
  'RELIANCE',
  'TCS',
  'HDFCBANK',
  'INFY',
  'TATAMOTORS',
  'SBIN',
  'BHARTIARTL'
];

export const FuturesDashboard: React.FC<FuturesDashboardProps> = ({
  initialSymbol = 'NIFTY',
  onOpenOptionChain
}) => {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [searchInput, setSearchInput] = useState('');
  const [dashboardData, setDashboardData] = useState<FuturesDashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flashingTokens, setFlashingTokens] = useState<Record<string, 'up' | 'down'>>({});

  const fetchFutures = async (targetSymbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFutures(targetSymbol);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load futures dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFutures(symbol);
  }, [symbol]);

  // Live 1.0s WebSocket Tick Engine for active Futures contracts
  useEffect(() => {
    if (!dashboardData?.contracts || dashboardData.contracts.length === 0) return;
    const tokens = dashboardData.contracts.map((c) => c.instrument_token).filter(Boolean);
    if (tokens.length === 0) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/api/market-data/ws/stream`;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        ws?.send(JSON.stringify({ action: 'subscribe', tokens }));
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'TICKS' && Array.isArray(msg.data)) {
            const tickMap = new Map<string, any>(msg.data.map((t: any) => [t.token, t]));
            const newFlashes: Record<string, 'up' | 'down'> = {};

            setDashboardData((prev) => {
              if (!prev) return prev;
              const updatedContracts = prev.contracts.map((contract) => {
                if (tickMap.has(contract.instrument_token)) {
                  const tick = tickMap.get(contract.instrument_token);
                  if (tick.direction > 0) newFlashes[contract.instrument_token] = 'up';
                  else if (tick.direction < 0) newFlashes[contract.instrument_token] = 'down';

                  const newFutPrice = tick.ltp;
                  const spot = contract.spot_price || prev.spot_price || 0;
                  const newBasis = spot > 0 ? Number((newFutPrice - spot).toFixed(2)) : contract.basis;
                  const newBasisPct = spot > 0 ? Number(((newBasis / spot) * 100).toFixed(2)) : contract.basis_percent;

                  return {
                    ...contract,
                    futures_price: newFutPrice,
                    basis: newBasis,
                    basis_percent: newBasisPct,
                    volume: tick.volume,
                    oi: tick.oi || contract.oi
                  };
                }
                return contract;
              });

              return {
                ...prev,
                contracts: updatedContracts
              };
            });

            if (Object.keys(newFlashes).length > 0) {
              setFlashingTokens((f) => ({ ...f, ...newFlashes }));
              setTimeout(() => {
                setFlashingTokens((f) => {
                  const copy = { ...f };
                  Object.keys(newFlashes).forEach((k) => delete copy[k]);
                  return copy;
                });
              }, 600);
            }
          }
        } catch (e) {
          // ignore parsing error
        }
      };
    } catch (err) {
      console.error('WebSocket error in FuturesDashboard:', err);
    }

    return () => {
      if (ws) {
        try {
          ws.send(JSON.stringify({ action: 'unsubscribe', tokens }));
          ws.close();
        } catch (e) {
          // ignore
        }
      }
    };
  }, [dashboardData?.contracts?.length, symbol]);


  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSymbol(searchInput.trim().toUpperCase());
      setSearchInput('');
    }
  };

  const getInterpretationBadge = (interp: string) => {
    switch (interp) {
      case 'Potential Long Buildup':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <ArrowUpRight className="w-3.5 h-3.5 mr-1" />
            Long Buildup
          </span>
        );
      case 'Potential Short Buildup':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <ArrowDownRight className="w-3.5 h-3.5 mr-1" />
            Short Buildup
          </span>
        );
      case 'Potential Short Covering':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
            <ArrowUpRight className="w-3.5 h-3.5 mr-1" />
            Short Covering
          </span>
        );
      case 'Potential Long Unwinding':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <ArrowDownRight className="w-3.5 h-3.5 mr-1" />
            Long Unwinding
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400">
            Neutral / Consolidating
          </span>
        );
    }
  };

  const spot = dashboardData?.spot_price;
  const hasDerivatives = dashboardData?.has_derivatives ?? true;

  return (
    <div className="space-y-4">
      {/* Top Header Card */}
      <div className="bg-[#111827] p-4 rounded-xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-lg text-indigo-400 font-mono">
              FUT
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-extrabold text-white tracking-tight">{symbol}</h1>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                  Futures Curve & Buildup
                </span>
                {hasDerivatives && (
                  <button
                    onClick={() => onOpenOptionChain(symbol)}
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 underline ml-2"
                  >
                    View Option Chain →
                  </button>
                )}
              </div>
              <div className="flex items-center space-x-3 text-xs mt-1">
                <span className="text-slate-400">Cash Spot Price:</span>
                <span className="font-mono font-bold text-white text-base">
                  {spot ? `₹${spot.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Select Buttons & Search */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
              {QUICK_FUTURES_SYMBOLS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSymbol(s)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-all ${
                    symbol === s
                      ? 'bg-indigo-600 text-white font-bold'
                      : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-700/80'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            <form onSubmit={handleSearchSubmit} className="relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Symbol..."
                className="pl-7 pr-3 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-32"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2" />
            </form>
          </div>
        </div>
      </div>

      {/* Main Derivatives Availability Verification */}
      {!hasDerivatives ? (
        <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-8 text-center space-y-3 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            Futures/Options are not available for this instrument.
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            <span className="font-mono text-amber-300 font-semibold">{symbol}</span> is listed in the cash equity segment, but there are no futures contracts available from the exchange or provider.
          </p>
        </div>
      ) : (
        /* Futures Contracts Table */
        <div className="space-y-3">
          <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0d1322] border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Contract Expiry</th>
                    <th className="py-3 px-4">Trading Symbol</th>
                    <th className="py-3 px-3">Exchange</th>
                    <th className="py-3 px-3 text-right">Futures LTP</th>
                    <th className="py-3 px-3 text-right">Spot Price</th>
                    <th className="py-3 px-3 text-right">Basis (Spread)</th>
                    <th className="py-3 px-3 text-right">Basis %</th>
                    <th className="py-3 px-3 text-right">Open Interest</th>
                    <th className="py-3 px-3 text-right">Change in OI</th>
                    <th className="py-3 px-3 text-right">Volume</th>
                    <th className="py-3 px-4 text-center">Market Analysis Label</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {loading ? (
                    <tr>
                      <td colSpan={11} className="py-16 text-center text-slate-400">
                        <div className="flex flex-col items-center justify-center space-y-2">
                          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                          <span className="text-xs">Loading futures contracts across expiries...</span>
                        </div>
                      </td>
                    </tr>
                  ) : dashboardData?.contracts && dashboardData.contracts.length > 0 ? (
                    dashboardData.contracts.map((contract) => {
                      const basis = contract.basis;
                      const basisPct = contract.basis_percent;
                      const isPremium = basis !== undefined && basis !== null && basis >= 0;

                      return (
                        <tr key={contract.instrument_token} className="hover:bg-slate-800/40 transition-colors">
                          {/* Expiry */}
                          <td className="py-3 px-4 font-mono font-semibold text-white">
                            <div className="flex items-center space-x-1.5">
                              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                              <span>{contract.expiry}</span>
                            </div>
                          </td>

                          {/* Trading Symbol */}
                          <td className="py-3 px-4 font-mono font-bold text-slate-200">
                            {contract.trading_symbol}
                          </td>

                          {/* Exchange */}
                          <td className="py-3 px-3">
                            <span className="px-1.5 py-0.5 text-[10px] font-bold bg-slate-800 text-slate-300 rounded font-mono">
                              {contract.exchange}
                            </span>
                          </td>

                          {/* Futures Price */}
                          <td className={`py-3 px-3 text-right font-mono font-bold transition-colors ${
                            flashingTokens[contract.instrument_token] === 'up'
                              ? 'bg-emerald-500/40 text-emerald-200'
                              : flashingTokens[contract.instrument_token] === 'down'
                              ? 'bg-rose-500/40 text-rose-200'
                              : 'text-white'
                          }`}>
                            {contract.futures_price ? `₹${contract.futures_price.toFixed(2)}` : '—'}
                          </td>

                          {/* Spot Price */}
                          <td className="py-3 px-3 text-right font-mono text-slate-400">
                            {contract.spot_price ? `₹${contract.spot_price.toFixed(2)}` : '—'}
                          </td>

                          {/* Basis */}
                          <td className="py-3 px-3 text-right font-mono font-semibold">
                            {basis !== undefined && basis !== null ? (
                              <span className={isPremium ? 'text-emerald-400' : 'text-rose-400'}>
                                {isPremium ? '+' : ''}{basis.toFixed(2)}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>

                          {/* Basis % */}
                          <td className="py-3 px-3 text-right font-mono">
                            {basisPct !== undefined && basisPct !== null ? (
                              <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                                isPremium ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'
                              }`}>
                                {isPremium ? '+' : ''}{basisPct.toFixed(2)}%
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>

                          {/* OI */}
                          <td className="py-3 px-3 text-right font-mono text-slate-300">
                            {contract.oi ? contract.oi.toLocaleString() : '—'}
                          </td>

                          {/* Change in OI */}
                          <td className="py-3 px-3 text-right font-mono font-semibold">
                            {contract.oi_change ? (
                              <span className={contract.oi_change > 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                {contract.oi_change > 0 ? '+' : ''}{contract.oi_change.toLocaleString()}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>

                          {/* Volume */}
                          <td className="py-3 px-3 text-right font-mono text-slate-400">
                            {contract.volume ? contract.volume.toLocaleString() : '—'}
                          </td>

                          {/* Interpretation Badge */}
                          <td className="py-3 px-4 text-center">
                            {getInterpretationBadge(contract.interpretation)}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={11} className="py-12 text-center text-slate-400">
                        No active futures contracts found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Disclaimer Banner */}
            <div className="p-3 bg-[#0d1322] border-t border-slate-800 flex items-center space-x-2 text-[11px] text-slate-400">
              <Info className="w-4 h-4 text-slate-500 shrink-0" />
              <span>
                {dashboardData?.interpretation_disclaimer ||
                  'Market-analysis labels are quantitative classifications, not guaranteed predictions.'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
