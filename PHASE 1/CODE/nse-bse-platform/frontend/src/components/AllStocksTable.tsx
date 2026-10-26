import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  TrendingUp,
  Bookmark,
  CheckCircle,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Info
} from 'lucide-react';
import { api } from '../api/client';
import { Instrument, InstrumentSearchParams } from '../types';

interface AllStocksTableProps {
  initialExchange?: string;
  initialSegment?: string;
  initialHasFno?: boolean;
  initialUniverseId?: string;
  onSelectInstrument: (inst: Instrument) => void;
  onOpenOptionChain: (symbol: string) => void;
  onOpenFutures: (symbol: string) => void;
  onOpenPrediction?: (symbol: string) => void;
}

export const AllStocksTable: React.FC<AllStocksTableProps> = ({
  initialExchange,
  initialSegment,
  initialHasFno,
  initialUniverseId,
  onSelectInstrument,
  onOpenOptionChain,
  onOpenFutures,
  onOpenPrediction
}) => {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [exchangeFilter, setExchangeFilter] = useState<string>(initialExchange || '');
  const [instrumentTypeFilter, setInstrumentTypeFilter] = useState<string>(initialSegment || 'EQ');
  const [fnoOnlyFilter, setFnoOnlyFilter] = useState<boolean | undefined>(initialHasFno);
  const [universeFilter, setUniverseFilter] = useState<string>(initialUniverseId || '');
  const [sortBy, setSortBy] = useState('trading_symbol');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Debounce search input by 250ms to prevent rapid query bursts
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 250);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  // Watchlist tracker
  const [watchlistTokens, setWatchlistTokens] = useState<Set<string>>(new Set());
  // Price flash tracker for 1-second live ticks
  const [flashingTokens, setFlashingTokens] = useState<Record<string, 'up' | 'down'>>({});

  const fetchStocks = async () => {
    setLoading(true);
    try {
      const params: InstrumentSearchParams = {
        q: debouncedSearchQuery,
        exchange: exchangeFilter || undefined,
        instrument_type: instrumentTypeFilter || undefined,
        universe_id: universeFilter || undefined,
        has_fno: fnoOnlyFilter,
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      const res = await api.searchInstruments(params);
      setInstruments(res.instruments);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load stocks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [debouncedSearchQuery, exchangeFilter, instrumentTypeFilter, fnoOnlyFilter, universeFilter, sortBy, sortOrder, pageSize]);

  useEffect(() => {
    fetchStocks();
  }, [page, pageSize, debouncedSearchQuery, exchangeFilter, instrumentTypeFilter, fnoOnlyFilter, universeFilter, sortBy, sortOrder]);

  // Live WebSocket Tick Stream for currently viewed table page
  useEffect(() => {
    if (!instruments.length) return;
    const tokens = instruments.map((i) => i.instrument_token);
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

            setInstruments((prev) =>
              prev.map((inst) => {
                const tick = tickMap.get(inst.instrument_token);
                if (tick) {
                  if (tick.direction > 0) newFlashes[inst.instrument_token] = 'up';
                  else if (tick.direction < 0) newFlashes[inst.instrument_token] = 'down';
                  return {
                    ...inst,
                    last_price: tick.ltp,
                    change: tick.change,
                    change_percent: tick.change_percent,
                    volume: tick.volume
                  };
                }
                return inst;
              })
            );

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
    } catch (e) {
      console.warn('WS error:', e);
    }

    return () => {
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) {
          try {
            ws.send(JSON.stringify({ action: 'unsubscribe', tokens }));
          } catch (_) {}
        }
        try {
          ws.close();
        } catch (_) {}
      }
    };
  }, [instruments.map((i) => i.instrument_token).join(',')]);

  const toggleWatchlist = async (inst: Instrument) => {
    const isAdded = watchlistTokens.has(inst.instrument_token);
    try {
      if (isAdded) {
        await api.removeFromWatchlist(inst.instrument_token);
        setWatchlistTokens((prev) => {
          const next = new Set(prev);
          next.delete(inst.instrument_token);
          return next;
        });
      } else {
        await api.addToWatchlist(inst.instrument_token);
        setWatchlistTokens((prev) => new Set(prev).add(inst.instrument_token));
      }
    } catch (err) {
      console.error('Watchlist toggle error:', err);
    }
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  return (
    <div className="space-y-4">
      {/* Control Bar: Filters & Search */}
      <div className="bg-[#111827] p-4 rounded-xl border border-slate-800 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by symbol, company, ISIN (e.g. RELIANCE, TCS)..."
            className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700/80 rounded-lg text-xs text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Exchange Filter */}
          <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-700/80 text-xs">
            <button
              onClick={() => setExchangeFilter('')}
              className={`px-2.5 py-1 rounded-md transition-all ${!exchangeFilter ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              All Exchanges
            </button>
            <button
              onClick={() => setExchangeFilter('NSE')}
              className={`px-2.5 py-1 rounded-md transition-all ${exchangeFilter === 'NSE' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              NSE
            </button>
            <button
              onClick={() => setExchangeFilter('BSE')}
              className={`px-2.5 py-1 rounded-md transition-all ${exchangeFilter === 'BSE' ? 'bg-purple-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              BSE
            </button>
          </div>

          {/* Instrument Type Filter */}
          <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-700/80 text-xs">
            <button
              onClick={() => setInstrumentTypeFilter('EQ')}
              className={`px-2.5 py-1 rounded-md transition-all ${instrumentTypeFilter === 'EQ' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              Equities
            </button>
            <button
              onClick={() => setInstrumentTypeFilter('INDEX')}
              className={`px-2.5 py-1 rounded-md transition-all ${instrumentTypeFilter === 'INDEX' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              Indices
            </button>
            <button
              onClick={() => setInstrumentTypeFilter('')}
              className={`px-2.5 py-1 rounded-md transition-all ${instrumentTypeFilter === '' ? 'bg-blue-600 text-white font-medium' : 'text-slate-400 hover:text-white'}`}
            >
              All Types
            </button>
          </div>

          {/* F&O Toggle */}
          <button
            onClick={() => setFnoOnlyFilter(fnoOnlyFilter ? undefined : true)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all flex items-center space-x-1.5 ${
              fnoOnlyFilter
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm'
                : 'bg-slate-900 text-slate-400 border-slate-700/80 hover:text-white'
            }`}
          >
            <CheckCircle className={`w-3.5 h-3.5 ${fnoOnlyFilter ? 'text-cyan-400' : 'text-slate-500'}`} />
            <span>F&O Only</span>
          </button>
        </div>
      </div>

      {/* Main Stock Table */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden relative">
        {loading && (
          <div className="w-full h-1 bg-slate-800 overflow-hidden">
            <div className="w-full h-full bg-blue-500 animate-pulse"></div>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0d1322] border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider">
              <tr>
                <th className="py-3 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('trading_symbol')}>
                  <div className="flex items-center space-x-1">
                    <span>Symbol</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="py-3 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('name')}>
                  <div className="flex items-center space-x-1">
                    <span>Company / Security</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="py-3 px-3 cursor-pointer hover:text-white" onClick={() => handleSort('exchange')}>
                  <div className="flex items-center space-x-1">
                    <span>Exchange</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="py-3 px-3 text-right">Price</th>
                <th className="py-3 px-3 text-right">Change %</th>
                <th className="py-3 px-3 text-right">Volume</th>
                <th className="py-3 px-3 text-center">F&O Eligible</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className={`divide-y divide-slate-800/60 font-sans ${loading && instruments.length > 0 ? 'opacity-70 transition-opacity' : 'transition-opacity'}`}>
              {loading && instruments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs">Scanning complete market universe...</span>
                    </div>
                  </td>
                </tr>
              ) : instruments.length > 0 ? (
                instruments.map((inst) => {
                  const hasFno = inst.has_derivatives === 1;
                  const price = inst.last_price;
                  const chgPct = inst.change_percent;
                  const isPositive = chgPct !== undefined && chgPct >= 0;

                  return (
                    <tr
                      key={inst.instrument_token}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                      onClick={() => onSelectInstrument(inst)}
                    >
                      {/* Symbol */}
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-white group-hover:text-blue-400 transition-colors font-mono">
                            {inst.trading_symbol}
                          </span>
                          {inst.series && inst.series !== 'EQ' && (
                            <span className="text-[10px] bg-slate-800 text-slate-400 px-1 py-0.2 rounded font-mono">
                              {inst.series}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Company Name */}
                      <td className="py-3 px-4 max-w-xs truncate text-slate-300">
                        {inst.name || inst.trading_symbol}
                      </td>

                      {/* Exchange */}
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                            inst.exchange === 'NSE'
                              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                              : 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                          }`}
                        >
                          {inst.exchange}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="py-3 px-3 text-right font-mono font-medium">
                        {price !== undefined && price !== null ? (
                          <span className="text-slate-100">₹{price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                        ) : (
                          <span className="text-[10px] text-slate-500 italic">Data unavailable</span>
                        )}
                      </td>

                      {/* Change % */}
                      <td className="py-3 px-3 text-right font-mono">
                        {chgPct !== undefined && chgPct !== null ? (
                          <span className={`font-semibold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isPositive ? '+' : ''}{chgPct.toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>

                      {/* Volume */}
                      <td className="py-3 px-3 text-right font-mono text-slate-400">
                        {inst.volume ? inst.volume.toLocaleString('en-IN') : '—'}
                      </td>

                      {/* F&O Available */}
                      <td className="py-3 px-3 text-center">
                        {hasFno ? (
                          <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full">
                            Available
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-600 font-medium">
                            Equity Only
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center space-x-1.5" onClick={(e) => e.stopPropagation()}>
                          {hasFno && (
                            <>
                              <button
                                onClick={() => onOpenOptionChain(inst.trading_symbol)}
                                className="px-2 py-1 text-[11px] rounded bg-blue-600/20 text-blue-400 hover:bg-blue-600 hover:text-white border border-blue-500/30 transition-all font-semibold"
                                title="View Option Chain"
                              >
                                Options
                              </button>
                              <button
                                onClick={() => onOpenFutures(inst.trading_symbol)}
                                className="px-2 py-1 text-[11px] rounded bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 transition-all font-semibold"
                                title="View Futures"
                              >
                                Futures
                              </button>
                            </>
                          )}
                          {onOpenPrediction && (
                            <button
                              onClick={() => onOpenPrediction(inst.trading_symbol)}
                              className="px-2 py-1 text-[11px] rounded bg-purple-600/20 text-purple-400 hover:bg-purple-600 hover:text-white border border-purple-500/30 transition-all font-semibold"
                              title="Predict Future Movement"
                            >
                              Predict
                            </button>
                          )}
                          <button
                            onClick={() => toggleWatchlist(inst)}
                            className="p-1 rounded text-slate-400 hover:text-amber-400 transition-colors"
                            title="Add to Watchlist"
                          >
                            <Bookmark className={`w-3.5 h-3.5 ${watchlistTokens.has(inst.instrument_token) ? 'fill-amber-400 text-amber-400' : ''}`} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No securities found matching your current filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 bg-[#0d1322] border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div>
            Showing <span className="font-semibold text-white">{instruments.length ? (page - 1) * pageSize + 1 : 0}</span> to{' '}
            <span className="font-semibold text-white">{Math.min(page * pageSize, total)}</span> of{' '}
            <span className="font-semibold text-white font-mono">{total.toLocaleString()}</span> instruments
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <span>Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded bg-slate-900 border border-slate-700 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded bg-slate-900 border border-slate-700 disabled:opacity-40 hover:bg-slate-800 text-slate-300"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
