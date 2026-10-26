import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Database,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  FileText,
  Calendar
} from 'lucide-react';
import { api } from '../api/client';
import { SyncStatus, SyncChangeItem } from '../types';

export const SyncManagerView: React.FC = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [changes, setChanges] = useState<SyncChangeItem[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('kite');
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [changeTypeFilter, setChangeTypeFilter] = useState('');

  const loadData = async () => {
    try {
      const [statusRes, histRes, changesRes] = await Promise.all([
        api.getSyncStatus(),
        api.getSyncHistory(),
        api.getSyncChanges({ change_type: changeTypeFilter || undefined })
      ]);
      setSyncStatus(statusRes);
      setHistory(histRes);
      setChanges(changesRes);
      setSyncing(statusRes.is_syncing);
    } catch (err) {
      console.error('Failed to load sync data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [changeTypeFilter]);

  const handleTriggerSync = async () => {
    setSyncing(true);
    setMessage(null);
    try {
      const res = await api.triggerSync(selectedProvider);
      setMessage(`Sync initiated with ${selectedProvider.toUpperCase()}. Tracking progress...`);
      setTimeout(loadData, 1000);
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
      setSyncing(false);
    }
  };

  const lastSync = syncStatus?.last_sync;

  return (
    <div className="space-y-6">
      {/* Top Banner / Sync Trigger */}
      <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <Database className="w-5 h-5 text-blue-400" />
              <h1 className="text-xl font-extrabold text-white tracking-tight">
                Instrument Master Synchronization
              </h1>
              <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                syncStatus?.is_syncing ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}>
                {syncStatus?.is_syncing ? 'SYNC IN PROGRESS' : 'ACTIVE & SYNCHRONIZED'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Downloads the complete instrument master directly from the legitimate provider (Zerodha Kite / Upstox), validates schemas, normalizes exchange tokens, runs change detection (new listings, delistings, expiries, lot changes), and indexes SQLite FTS5.
            </p>
          </div>

          {/* Trigger Form */}
          <div className="flex items-center space-x-3 bg-slate-900 p-2 rounded-xl border border-slate-700/80">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={syncing}
              className="bg-[#111827] text-white border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none"
            >
              <option value="kite">Zerodha Kite Master (~100k+)</option>
              <option value="upstox">Upstox Public Dump</option>
            </select>

            <button
              onClick={handleTriggerSync}
              disabled={syncing}
              className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center space-x-2 transition-all ${
                syncing
                  ? 'bg-blue-600/50 text-slate-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              <span>{syncing ? 'Synchronizing...' : 'Run Sync Now'}</span>
            </button>
          </div>
        </div>

        {message && (
          <div className="p-2.5 bg-blue-950/40 border border-blue-500/30 rounded-lg text-xs text-blue-300">
            {message}
          </div>
        )}

        {/* Change Detection Summary Cards */}
        {lastSync && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-800">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Total Downloaded</span>
              <span className="text-lg font-bold font-mono text-white">
                {lastSync.total_downloaded.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Raw Master Records</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Active Instruments</span>
              <span className="text-lg font-bold font-mono text-blue-400">
                {(syncStatus?.total_active_instruments || 0).toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">NSE + BSE Universe</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Newly Listed</span>
              <span className="text-lg font-bold font-mono text-emerald-400">
                +{lastSync.newly_listed_count.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Discovered Equities</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Delisted / Inactive</span>
              <span className="text-lg font-bold font-mono text-rose-400">
                {lastSync.delisted_count}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Suspended / Removed</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Expired Derivatives</span>
              <span className="text-lg font-bold font-mono text-amber-400">
                {lastSync.expired_count}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Marked Inactive</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Lot-Size Changes</span>
              <span className="text-lg font-bold font-mono text-cyan-400">
                {lastSync.lot_size_changed_count}
              </span>
              <span className="text-[10px] text-slate-500 block truncate">Contract Revisions</span>
            </div>
          </div>
        )}
      </div>

      {/* Exchange Coverage Breakdown */}
      {syncStatus?.exchange_breakdown && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(syncStatus.exchange_breakdown).map(([exch, count]) => (
            <div key={exch} className="bg-[#111827] p-4 rounded-xl border border-slate-800 shadow-md">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-slate-200">{exch} Segment</span>
                <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                  {exch === 'NSE' ? 'Cash Equities' : exch === 'BSE' ? 'Cash Equities' : exch === 'NFO' ? 'NSE F&O' : 'BSE F&O'}
                </span>
              </div>
              <div className="text-2xl font-bold font-mono text-white mt-2">
                {count.toLocaleString()}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Real, normalized active instruments</div>
            </div>
          ))}
        </div>
      )}

      {/* Change Detection Audit Log */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-[#0d1322] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Change Detection Audit Log
            </h2>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400">Filter Event:</span>
            <select
              value={changeTypeFilter}
              onChange={(e) => setChangeTypeFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs focus:outline-none"
            >
              <option value="">All Change Events</option>
              <option value="NEW_LISTING">New Listings</option>
              <option value="NEW_DERIVATIVE_CONTRACT">New Derivatives</option>
              <option value="DELISTED">Delisted Securities</option>
              <option value="EXPIRED">Expired Contracts</option>
              <option value="LOT_SIZE_CHANGE">Lot Size Changes</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-4">Event Type</th>
                <th className="py-2.5 px-4">Symbol</th>
                <th className="py-2.5 px-3">Exchange</th>
                <th className="py-2.5 px-4">Instrument Token</th>
                <th className="py-2.5 px-4">Previous Value</th>
                <th className="py-2.5 px-4">New Value / Details</th>
                <th className="py-2.5 px-4">Detected At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {changes.length > 0 ? (
                changes.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        c.change_type === 'NEW_LISTING' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        c.change_type === 'DELISTED' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                        c.change_type === 'LOT_SIZE_CHANGE' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {c.change_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2 px-4 font-mono font-bold text-white">{c.trading_symbol}</td>
                    <td className="py-2 px-3 font-mono text-slate-300">{c.exchange}</td>
                    <td className="py-2 px-4 font-mono text-slate-500">{c.instrument_token}</td>
                    <td className="py-2 px-4 text-slate-400 font-mono">{c.old_value || '—'}</td>
                    <td className="py-2 px-4 text-slate-200 font-medium truncate max-w-xs">{c.new_value || '—'}</td>
                    <td className="py-2 px-4 text-slate-400 font-mono text-[11px]">{new Date(c.detected_at).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No change events matching criteria.
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
