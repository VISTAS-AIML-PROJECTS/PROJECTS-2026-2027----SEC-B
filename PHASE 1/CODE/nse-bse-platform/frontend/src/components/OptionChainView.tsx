import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  TrendingUp,
  BarChart2,
  Calendar,
  Search,
  Activity,
  Layers,
  Info
} from 'lucide-react';
import { api } from '../api/client';
import { OptionChainResponse, OptionChainStrikeRow } from '../types';

interface OptionChainViewProps {
  initialSymbol?: string;
  onOpenFutures: (symbol: string) => void;
}

const QUICK_UNDERLYINGS = [
  'NIFTY',
  'BANKNIFTY',
  'FINNIFTY',
  'SENSEX',
  'RELIANCE',
  'TCS',
  'HDFCBANK',
  'INFY',
  'TATAMOTORS',
  'ICICIBANK'
];

export const OptionChainView: React.FC<OptionChainViewProps> = ({
  initialSymbol = 'NIFTY',
  onOpenFutures
}) => {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [searchInput, setSearchInput] = useState('');
  const [selectedExpiry, setSelectedExpiry] = useState<string>('');
  const [strikeRange, setStrikeRange] = useState<string>('20');
  const [chainData, setChainData] = useState<OptionChainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flashingTokens, setFlashingTokens] = useState<Record<string, 'up' | 'down'>>({});

  const fetchOptionChain = async (targetSymbol: string, expiry?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getOptionChain(targetSymbol, expiry);
      setChainData(data);
      if (data.selected_expiry) {
        setSelectedExpiry(data.selected_expiry);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load option chain');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptionChain(symbol);
  }, [symbol]);

  const handleExpiryChange = (newExpiry: string) => {
    setSelectedExpiry(newExpiry);
    fetchOptionChain(symbol, newExpiry);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSymbol(searchInput.trim().toUpperCase());
      setSearchInput('');
    }
  };

  const analytics = chainData?.analytics;
  const spotPrice = chainData?.spot_price;
  const hasDerivatives = chainData?.has_derivatives ?? true;

  const strikes = chainData?.strikes || [];
  let displayedStrikes = strikes;
  if (strikeRange !== 'all' && strikes.length > 0) {
    const count = parseInt(strikeRange, 10);
    const half = Math.floor(count / 2);
    let atmIndex = strikes.findIndex((s) => s.is_atm);
    if (atmIndex === -1 && spotPrice) {
      atmIndex = strikes.reduce((closest, curr, idx) => {
        return Math.abs(curr.strike - spotPrice) < Math.abs(strikes[closest].strike - spotPrice) ? idx : closest;
      }, 0);
    }
    if (atmIndex === -1) atmIndex = Math.floor(strikes.length / 2);
    const start = Math.max(0, atmIndex - half);
    const end = Math.min(strikes.length, start + count);
    displayedStrikes = strikes.slice(start, end);
  }

  // Live 1.0s WebSocket Tick Engine for displayed Option Chain strikes
  useEffect(() => {
    if (!displayedStrikes || displayedStrikes.length === 0) return;
    const tokens: string[] = [];
    displayedStrikes.forEach((s) => {
      if (s.call?.instrument_token) tokens.push(s.call.instrument_token);
      if (s.put?.instrument_token) tokens.push(s.put.instrument_token);
    });

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

            setChainData((prev) => {
              if (!prev) return prev;
              const updatedStrikes = prev.strikes.map((row) => {
                let callUpdated = row.call;
                let putUpdated = row.put;

                if (row.call?.instrument_token && tickMap.has(row.call.instrument_token)) {
                  const tick = tickMap.get(row.call.instrument_token);
                  if (tick.direction > 0) newFlashes[row.call.instrument_token] = 'up';
                  else if (tick.direction < 0) newFlashes[row.call.instrument_token] = 'down';
                  callUpdated = {
                    ...row.call,
                    ltp: tick.ltp,
                    change: tick.change,
                    change_percent: tick.change_percent,
                    volume: tick.volume
                  };
                }

                if (row.put?.instrument_token && tickMap.has(row.put.instrument_token)) {
                  const tick = tickMap.get(row.put.instrument_token);
                  if (tick.direction > 0) newFlashes[row.put.instrument_token] = 'up';
                  else if (tick.direction < 0) newFlashes[row.put.instrument_token] = 'down';
                  putUpdated = {
                    ...row.put,
                    ltp: tick.ltp,
                    change: tick.change,
                    change_percent: tick.change_percent,
                    volume: tick.volume
                  };
                }

                return {
                  ...row,
                  call: callUpdated,
                  put: putUpdated
                };
              });

              return {
                ...prev,
                strikes: updatedStrikes
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
      console.error('WebSocket error in OptionChainView:', err);
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
  }, [displayedStrikes.length, symbol, selectedExpiry]);


  return (
    <div className="space-y-4">
      {/* Top Header & Selector */}
      <div className="bg-[#111827] p-4 rounded-xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Underlying & Spot */}
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center font-bold text-lg text-blue-400 font-mono">
              {symbol.slice(0, 3)}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-extrabold text-white tracking-tight">{symbol}</h1>
                <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                  Option Chain
                </span>
                {hasDerivatives && (
                  <button
                    onClick={() => onOpenFutures(symbol)}
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 underline ml-2"
                  >
                    View Futures →
                  </button>
                )}
              </div>
              <div className="flex items-center space-x-3 text-xs mt-1">
                <span className="text-slate-400">Spot Price:</span>
                <span className="font-mono font-bold text-white text-base">
                  {spotPrice ? `₹${spotPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                </span>
                {chainData?.atm_strike && (
                  <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.5 rounded text-[11px] font-mono">
                    ATM: {chainData.atm_strike}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick Select Buttons & Expiry Dropdown */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Quick Underlyings */}
            <div className="flex items-center space-x-1 overflow-x-auto no-scrollbar py-1">
              {QUICK_UNDERLYINGS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSymbol(s)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-all ${
                    symbol === s
                      ? 'bg-blue-600 text-white font-bold'
                      : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-700/80'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Custom Search Box */}
            <form onSubmit={handleSearchSubmit} className="relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Lookup underlying..."
                className="pl-7 pr-3 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 w-36"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2" />
            </form>

            {/* Expiry Selector */}
            {chainData?.available_expiries && chainData.available_expiries.length > 0 && (
              <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-400 text-[11px]">Expiry:</span>
                <select
                  value={selectedExpiry}
                  onChange={(e) => handleExpiryChange(e.target.value)}
                  className="bg-transparent text-white font-mono font-medium focus:outline-none cursor-pointer"
                >
                  {chainData.available_expiries.map((exp) => (
                    <option key={exp} value={exp} className="bg-slate-900 text-white">
                      {exp}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Strike Range Filter */}
            <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs">
              <span className="text-slate-400 text-[11px]">Strikes:</span>
              <select
                value={strikeRange}
                onChange={(e) => setStrikeRange(e.target.value)}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                <option value="20" className="bg-slate-900 text-white">±10 Strikes (ATM)</option>
                <option value="40" className="bg-slate-900 text-white">±20 Strikes</option>
                <option value="all" className="bg-slate-900 text-white">All Strikes ({chainData?.strikes?.length || 0})</option>
              </select>
            </div>
          </div>
        </div>

        {/* Analytics Cards (PCR, Max Pain, Concentration, Straddle) */}
        {hasDerivatives && analytics && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-800">
            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">PCR (by OI)</span>
              <span className="text-base font-bold font-mono text-emerald-400">
                {analytics.pcr_oi !== null && analytics.pcr_oi !== undefined ? analytics.pcr_oi : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Total Put OI / Call OI</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">PCR (Volume)</span>
              <span className="text-base font-bold font-mono text-blue-400">
                {analytics.pcr_volume !== null && analytics.pcr_volume !== undefined ? analytics.pcr_volume : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Total Put Vol / Call Vol</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Max Pain</span>
              <span className="text-base font-bold font-mono text-amber-400">
                {analytics.max_pain_strike ? `₹${analytics.max_pain_strike}` : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Min Writer Loss Strike</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Call OI Wall</span>
              <span className="text-base font-bold font-mono text-rose-400">
                {analytics.call_oi_concentration_strike ? `₹${analytics.call_oi_concentration_strike}` : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Major Resistance</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Put OI Wall</span>
              <span className="text-base font-bold font-mono text-emerald-400">
                {analytics.put_oi_concentration_strike ? `₹${analytics.put_oi_concentration_strike}` : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Major Support</span>
            </div>

            <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">ATM Straddle</span>
              <span className="text-base font-bold font-mono text-cyan-400">
                {analytics.atm_straddle_price ? `₹${analytics.atm_straddle_price}` : '—'}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">ATM Call + Put Price</span>
            </div>
          </div>
        )}
      </div>

      {/* Main Condition Check: If no derivatives exist */}
      {!hasDerivatives ? (
        <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-8 text-center space-y-3 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            Futures/Options are not available for this instrument.
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            <span className="font-mono text-amber-300 font-semibold">{symbol}</span> is listed in the cash equity segment, but the exchange and configured market-data provider do not list any active derivatives contracts for this underlying.
          </p>
          <div className="pt-2">
            <button
              onClick={() => setSymbol('NIFTY')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition-all"
            >
              Switch to NIFTY 50 Option Chain
            </button>
          </div>
        </div>
      ) : (
        /* Real NSE Option Chain Table */
        <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
          {/* Header Row Explaining Call vs Put sides */}
          <div className="grid grid-cols-2 divide-x divide-slate-800 bg-[#0b0f19] border-b border-slate-800 text-center py-2 text-xs font-bold uppercase tracking-wider">
            <div className="text-emerald-400">CALL OPTIONS (CE)</div>
            <div className="text-rose-400">PUT OPTIONS (PE)</div>
          </div>

          <div className="overflow-x-auto max-h-[70vh]">
            <table className="w-full text-center text-[11px] font-mono border-collapse">
              <thead className="sticky top-0 bg-[#0d1322] border-b border-slate-800 text-slate-400 uppercase font-sans text-[10px] tracking-wider z-10">
                <tr>
                  {/* Call Columns */}
                  <th className="py-2.5 px-2 bg-slate-900/60">OI</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Chg OI</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Volume</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">IV %</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Delta</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Bid</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Ask</th>
                  <th className="py-2.5 px-2.5 bg-emerald-950/40 text-emerald-300 font-bold border-r border-slate-800">LTP</th>

                  {/* Strike Center */}
                  <th className="py-2.5 px-3 bg-slate-800 text-white font-bold text-xs border-x border-slate-700">Strike</th>

                  {/* Put Columns */}
                  <th className="py-2.5 px-2.5 bg-rose-950/40 text-rose-300 font-bold border-l border-slate-800">LTP</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Bid</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Ask</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Delta</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">IV %</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Volume</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">Chg OI</th>
                  <th className="py-2.5 px-2 bg-slate-900/60">OI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={17} className="py-16 text-center text-slate-400">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-xs">Loading genuine option chain contracts...</span>
                      </div>
                    </td>
                  </tr>
                ) : displayedStrikes && displayedStrikes.length > 0 ? (
                  displayedStrikes.map((row) => {
                    const isAtm = row.is_atm;
                    const call = row.call;
                    const put = row.put;
                    const callItm = call?.is_itm;
                    const putItm = put?.is_itm;

                    return (
                      <tr
                        key={row.strike}
                        className={`transition-colors font-mono ${
                          isAtm
                            ? 'bg-amber-500/15 border-y-2 border-amber-500/60 font-bold'
                            : 'hover:bg-slate-800/40'
                        }`}
                      >
                        {/* Call Side */}
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-slate-300' : 'text-slate-400'}`}>
                          {call?.oi ? call.oi.toLocaleString() : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15' : ''} ${call?.oi_change && call.oi_change > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                          {call?.oi_change ? `${call.oi_change > 0 ? '+' : ''}${call.oi_change.toLocaleString()}` : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {call?.volume ? call.volume.toLocaleString() : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {call?.iv ? `${call.iv}%` : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-blue-300' : 'text-slate-400'}`}>
                          {call?.delta !== null && call?.delta !== undefined ? call.delta : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {call?.bid ? call.bid.toFixed(2) : '—'}
                        </td>
                        <td className={`py-2 px-2 text-right ${callItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {call?.ask ? call.ask.toFixed(2) : '—'}
                        </td>
                        <td className={`py-2 px-2.5 text-right font-bold border-r border-slate-800 transition-colors ${
                          flashingTokens[call?.instrument_token || ''] === 'up'
                            ? 'bg-emerald-500/50 text-emerald-100'
                            : flashingTokens[call?.instrument_token || ''] === 'down'
                            ? 'bg-rose-500/50 text-rose-100'
                            : callItm ? 'bg-amber-500/20 text-emerald-300' : 'text-emerald-400'
                        }`}>
                          {call?.ltp ? `₹${call.ltp.toFixed(2)}` : '—'}
                        </td>

                        {/* Center Strike */}
                        <td className={`py-2 px-3 font-bold text-xs border-x border-slate-700 ${
                          isAtm ? 'bg-amber-500 text-slate-950 font-black' : 'bg-slate-900 text-white'
                        }`}>
                          {row.strike.toFixed(2)}
                        </td>

                        {/* Put Side */}
                        <td className={`py-2 px-2.5 text-left font-bold border-l border-slate-800 transition-colors ${
                          flashingTokens[put?.instrument_token || ''] === 'up'
                            ? 'bg-emerald-500/50 text-emerald-100'
                            : flashingTokens[put?.instrument_token || ''] === 'down'
                            ? 'bg-rose-500/50 text-rose-100'
                            : putItm ? 'bg-amber-500/20 text-rose-300' : 'text-rose-400'
                        }`}>
                          {put?.ltp ? `₹${put.ltp.toFixed(2)}` : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {put?.bid ? put.bid.toFixed(2) : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {put?.ask ? put.ask.toFixed(2) : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-blue-300' : 'text-slate-400'}`}>
                          {put?.delta !== null && put?.delta !== undefined ? put.delta : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {put?.iv ? `${put.iv}%` : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-slate-400' : 'text-slate-500'}`}>
                          {put?.volume ? put.volume.toLocaleString() : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15' : ''} ${put?.oi_change && put.oi_change > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                          {put?.oi_change ? `${put.oi_change > 0 ? '+' : ''}${put.oi_change.toLocaleString()}` : '—'}
                        </td>
                        <td className={`py-2 px-2 text-left ${putItm ? 'bg-amber-950/15 text-slate-300' : 'text-slate-400'}`}>
                          {put?.oi ? put.oi.toLocaleString() : '—'}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={17} className="py-12 text-center text-slate-400">
                      No contracts found for the selected expiry.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Legend Footer */}
          <div className="px-4 py-2.5 bg-[#0d1322] border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-3">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-amber-500 inline-block"></span>
                <span className="text-[11px]">ATM Strike (At The Money)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-amber-900/40 border border-amber-600/30 inline-block"></span>
                <span className="text-[11px]">ITM (In The Money)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded bg-slate-900 border border-slate-800 inline-block"></span>
                <span className="text-[11px]">OTM (Out of The Money)</span>
              </span>
            </div>
            <div className="text-[11px] text-slate-500 italic">
              European Greeks computed via Black-Scholes (1973) benchmark model.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
