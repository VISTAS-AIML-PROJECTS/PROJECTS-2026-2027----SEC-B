import React, { useState, useEffect, useCallback } from 'react';
import { Trophy, Leaf, Zap, Clock, AlertCircle, RefreshCw } from 'lucide-react';
import { getEcoPoints, getEcoLeaderboard, getEcoRules, recordEcoEvent } from '../utils/api';

// ── Helpers ───────────────────────────────────────────────────────────────────

const EVENT_LABELS = {
  PACKAGING_ANALYSIS:    'Packaging Analysis',
  PACKAGING_SELECTION:   'Packaging Selection',
  SUSTAINABLE_PACKAGING: 'Sustainable Packaging Choice',
  MATERIAL_SCAN:         'Material Scan',
  REVIEW_ANALYSIS:       'Review Analysis',
};

function fmt(val, decimals = 4) {
  if (val == null) return null;
  return Number(val).toFixed(decimals);
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, color, value, label, sub }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
      <Icon className={`h-8 w-8 ${color} mx-auto mb-3`} />
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="text-sm text-gray-600 mt-1">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const EcoPointsDashboard = () => {
  const [summary,     setSummary]     = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [rules,       setRules]       = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);

  // Demo event recording state
  const [demoType,    setDemoType]    = useState('PACKAGING_ANALYSIS');
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoMsg,     setDemoMsg]     = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, l, r] = await Promise.all([
        getEcoPoints(),
        getEcoLeaderboard(),
        getEcoRules(),
      ]);
      setSummary(s);
      setLeaderboard(l);
      setRules(r);
    } catch (err) {
      setError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : err.message,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDemoEvent = async () => {
    setDemoLoading(true);
    setDemoMsg(null);
    try {
      const result = await recordEcoEvent(demoType, null);
      if (result.status === 'ok') {
        setDemoMsg(`+${result.points_awarded} pts for ${EVENT_LABELS[demoType] ?? demoType}`);
        await load();
      } else {
        setDemoMsg(`Error: ${result.error}`);
      }
    } catch (err) {
      setDemoMsg(`Error: ${err.message}`);
    } finally {
      setDemoLoading(false);
    }
  };

  // ── Loading / error states ────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 gap-2">
        <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
        Loading EcoPoints…
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <strong>Dashboard unavailable:</strong> {error}
      </div>
    );
  }

  const co2Display = summary?.co2e_saved_mt != null
    ? `${fmt(summary.co2e_saved_mt, 6)} mt CO₂e`
    : null;

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-8 mb-8 text-white">
        <h1 className="text-4xl font-bold mb-2">🌿 EcoPoints</h1>
        <p className="text-green-100">
          Deterministic backend gamification — points are awarded for real Wrapture actions.
          All values come from the database.
        </p>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon={Zap}
          color="text-green-600"
          value={summary?.points ?? 0}
          label="Total EcoPoints"
          sub={summary?.events === 0 ? 'No eco activity recorded yet.' : `from ${summary.events} event${summary.events !== 1 ? 's' : ''}`}
        />
        <StatCard
          icon={Leaf}
          color="text-emerald-600"
          value={co2Display ?? 'N/A'}
          label="CO₂e Saved"
          sub={co2Display ? 'Source: Packrift catalog co2e_recycling_mt' : 'No verified CO₂ data yet'}
        />
        <StatCard
          icon={Trophy}
          color="text-yellow-500"
          value={leaderboard?.status === 'ok' ? `#${(leaderboard.entries.findIndex(e => e.is_dev_user) + 1) || '—'}` : '—'}
          label="Leaderboard Rank"
          sub={leaderboard?.status !== 'ok' ? 'Not enough users' : null}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

        {/* Recent events */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Clock className="h-5 w-5 text-gray-400" /> Recent Activity
            </h2>
            <button onClick={load} className="text-gray-400 hover:text-gray-600">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          {summary?.recent_events?.length === 0 ? (
            <div className="text-center text-gray-400 text-sm py-8">
              No eco activity recorded yet.
            </div>
          ) : (
            <div className="space-y-2">
              {summary.recent_events.map((ev, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-gray-800">
                      {EVENT_LABELS[ev.event_type] ?? ev.event_type}
                    </div>
                    <div className="text-xs text-gray-400">{timeAgo(ev.created_at)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-green-600">+{ev.points} pts</div>
                    {ev.co2e_saved_mt != null && (
                      <div className="text-xs text-emerald-600">
                        {fmt(ev.co2e_saved_mt, 6)} mt CO₂e
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Point rules */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Point Rules</h2>
          <p className="text-xs text-gray-400 mb-3">
            All rules are deterministic and set by the backend. The frontend cannot submit
            arbitrary point values.
          </p>
          {rules?.rules?.length > 0 ? (
            <div className="space-y-2">
              {rules.rules.map(({ event_type, points }) => (
                <div key={event_type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700">
                    {EVENT_LABELS[event_type] ?? event_type}
                  </span>
                  <span className="text-sm font-bold text-green-600">{points} pts</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-400 text-sm">Rules unavailable.</div>
          )}
        </div>
      </div>

      {/* Leaderboard */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-500" /> Leaderboard
        </h2>
        {leaderboard?.status !== 'ok' ? (
          <div className="flex items-center gap-2 text-gray-500 text-sm py-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            {leaderboard?.message ?? 'Leaderboard unavailable — more user data is required.'}
          </div>
        ) : (
          <div className="space-y-2">
            {leaderboard.entries.map((entry) => (
              <div key={entry.rank} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <span className="text-lg font-bold text-gray-400 w-6">#{entry.rank}</span>
                <span className="flex-1 text-sm font-medium text-gray-800">
                  {entry.username}
                  {entry.is_dev_user && (
                    <span className="ml-2 text-xs text-gray-400">(dev)</span>
                  )}
                </span>
                <span className="text-sm font-bold text-green-600">{entry.points} pts</span>
                <span className="text-xs text-gray-400">{entry.events} events</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dev event recorder */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold mb-1">Record a Test Event</h2>
        <p className="text-xs text-gray-400 mb-4">
          Development tool — records a real event in the database using the dev user.
          Points are determined by the backend rule for the selected event type.
        </p>
        <div className="flex gap-3 items-center flex-wrap">
          <select
            value={demoType}
            onChange={(e) => setDemoType(e.target.value)}
            className="input text-sm"
          >
            {rules?.rules?.map(({ event_type }) => (
              <option key={event_type} value={event_type}>
                {EVENT_LABELS[event_type] ?? event_type}
              </option>
            ))}
          </select>
          <button
            onClick={handleDemoEvent}
            disabled={demoLoading}
            className="btn btn-primary text-sm"
          >
            {demoLoading ? 'Recording…' : 'Record Event'}
          </button>
          {demoMsg && (
            <span className="text-sm text-green-700 font-medium">{demoMsg}</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default EcoPointsDashboard;
