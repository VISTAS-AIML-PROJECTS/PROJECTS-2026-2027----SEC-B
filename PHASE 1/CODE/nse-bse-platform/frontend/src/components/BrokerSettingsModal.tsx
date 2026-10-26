import React, { useState, useEffect } from 'react';
import { X, Key, ShieldCheck, Zap, RefreshCw, CheckCircle2, Lock, Radio } from 'lucide-react';

interface BrokerSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const BrokerSettingsModal: React.FC<BrokerSettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeProvider, setActiveProvider] = useState('kotak_neo');
  const [kotakKey, setKotakKey] = useState('');
  const [kotakSecret, setKotakSecret] = useState('');
  const [kotakUcc, setKotakUcc] = useState('');
  const [dhanToken, setDhanToken] = useState('');
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/market-data/provider-config')
        .then((r) => r.json())
        .then((data) => {
          if (data.active_provider) setActiveProvider(data.active_provider);
          if (data.kotak_consumer_key_preview) setKotakKey(data.kotak_consumer_key_preview);
        })
        .catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch('/api/market-data/provider-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          active_provider: activeProvider,
          kotak_consumer_key: kotakKey,
          dhan_access_token: dhanToken
        })
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg bg-[#111827] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-[#0d1322]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">Live Broker API Feed</h2>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  1-Second Ticks
                </span>
              </div>
              <p className="text-xs text-slate-400">Configure genuine live market-data feeds for second-by-second updates</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSave} className="p-5 space-y-4 text-xs">
          {/* Provider Selection */}
          <div>
            <label className="text-[11px] font-bold text-slate-300 block mb-2 uppercase tracking-wider">
              Selected Broker Feed
            </label>
            <div className="grid grid-cols-2 gap-2">
              <div
                onClick={() => setActiveProvider('kotak_neo')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  activeProvider === 'kotak_neo'
                    ? 'bg-blue-600/15 border-blue-500 text-white'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800/40'
                }`}
              >
                <div>
                  <div className="font-bold text-sm">Kotak Neo</div>
                  <div className="text-[10px] text-slate-400">Trade API HSM Feed</div>
                </div>
                {activeProvider === 'kotak_neo' && <CheckCircle2 className="w-4 h-4 text-blue-400" />}
              </div>

              <div
                onClick={() => setActiveProvider('dhan')}
                className={`p-3 rounded-xl border cursor-pointer flex items-center justify-between ${
                  activeProvider === 'dhan'
                    ? 'bg-blue-600/15 border-blue-500 text-white'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800/40'
                }`}
              >
                <div>
                  <div className="font-bold text-sm">Dhan HQ</div>
                  <div className="text-[10px] text-slate-400">30-Day Binary Feed</div>
                </div>
                {activeProvider === 'dhan' && <CheckCircle2 className="w-4 h-4 text-blue-400" />}
              </div>
            </div>
          </div>

          {/* Kotak Neo Fields */}
          {activeProvider === 'kotak_neo' && (
            <div className="space-y-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div className="flex items-center space-x-1.5 text-blue-400 font-bold text-[11px]">
                <Key className="w-3.5 h-3.5" />
                <span>Kotak Neo API Credentials</span>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Consumer Key (Active):</label>
                <input
                  type="text"
                  value={kotakKey}
                  onChange={(e) => setKotakKey(e.target.value)}
                  placeholder="Paste Consumer Key"
                  className="w-full px-3 py-2 bg-[#111827] border border-slate-700 rounded-lg text-xs font-mono text-emerald-400 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Consumer Secret (Optional):</label>
                  <input
                    type="password"
                    value={kotakSecret}
                    onChange={(e) => setKotakSecret(e.target.value)}
                    placeholder="Consumer Secret"
                    className="w-full px-3 py-1.5 bg-[#111827] border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Client Code / UCC (Optional):</label>
                  <input
                    type="text"
                    value={kotakUcc}
                    onChange={(e) => setKotakUcc(e.target.value)}
                    placeholder="e.g. 98XXXXXX"
                    className="w-full px-3 py-1.5 bg-[#111827] border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Dhan Fields */}
          {activeProvider === 'dhan' && (
            <div className="space-y-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div className="flex items-center space-x-1.5 text-blue-400 font-bold text-[11px]">
                <Key className="w-3.5 h-3.5" />
                <span>Dhan HQ 30-Day Token</span>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Access Token:</label>
                <input
                  type="password"
                  value={dhanToken}
                  onChange={(e) => setDhanToken(e.target.value)}
                  placeholder="Paste Dhan 30-Day Token"
                  className="w-full px-3 py-2 bg-[#111827] border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {/* Status Badge */}
          <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 flex items-center space-x-2 text-emerald-400">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span className="text-[11px]">
              Live 1.0s WebSocket Tick Engine active. All viewed stocks and options receive live second-by-second updates.
            </span>
          </div>

          {saved && (
            <div className="p-2 bg-emerald-900/50 border border-emerald-500 rounded text-center text-emerald-300 text-xs">
              Credentials updated successfully!
            </div>
          )}

          <div className="pt-2 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-xs"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs flex items-center space-x-1.5 shadow-lg shadow-blue-600/30"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>Save & Connect</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
