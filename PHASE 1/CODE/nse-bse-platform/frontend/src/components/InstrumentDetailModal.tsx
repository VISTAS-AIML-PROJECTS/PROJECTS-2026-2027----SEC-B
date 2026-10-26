import React, { useState, useEffect } from 'react';
import { X, Layers, ExternalLink, Calendar, AlertCircle, CheckCircle, TrendingUp, Sparkles } from 'lucide-react';
import { Instrument } from '../types';

interface InstrumentDetailModalProps {
  instrument: Instrument | null;
  onClose: () => void;
  onOpenOptionChain: (symbol: string) => void;
  onOpenFutures: (symbol: string) => void;
  onOpenPrediction?: (symbol: string) => void;
  onOpenAiCopilot?: (symbol: string) => void;
}

export const InstrumentDetailModal: React.FC<InstrumentDetailModalProps> = ({
  instrument,
  onClose,
  onOpenOptionChain,
  onOpenFutures,
  onOpenPrediction,
  onOpenAiCopilot
}) => {
  const [livePrice, setLivePrice] = useState<number | undefined>(instrument?.last_price);
  const [liveChange, setLiveChange] = useState<number | undefined>(instrument?.change);
  const [liveChangePct, setLiveChangePct] = useState<number | undefined>(instrument?.change_percent);
  const [flash, setFlash] = useState<'up' | 'down' | null>(null);

  useEffect(() => {
    setLivePrice(instrument?.last_price);
    setLiveChange(instrument?.change);
    setLiveChangePct(instrument?.change_percent);
  }, [instrument]);

  useEffect(() => {
    if (!instrument?.instrument_token) return;
    const token = instrument.instrument_token;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/api/market-data/ws/stream`;

    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        ws?.send(JSON.stringify({ action: 'subscribe', tokens: [token] }));
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'TICKS' && Array.isArray(msg.data)) {
            const tick = msg.data.find((t: any) => t.token === token);
            if (tick) {
              if (tick.direction > 0) setFlash('up');
              else if (tick.direction < 0) setFlash('down');

              setLivePrice(tick.ltp);
              setLiveChange(tick.change);
              setLiveChangePct(tick.change_percent);

              setTimeout(() => setFlash(null), 600);
            }
          }
        } catch (e) {
          // ignore parsing error
        }
      };
    } catch (err) {
      console.error('WebSocket error in InstrumentDetailModal:', err);
    }

    return () => {
      if (ws) {
        try {
          ws.send(JSON.stringify({ action: 'unsubscribe', tokens: [token] }));
          ws.close();
        } catch (e) {
          // ignore
        }
      }
    };
  }, [instrument?.instrument_token]);

  if (!instrument) return null;

  const hasFno = instrument.has_derivatives === 1;
  const isIndex = instrument.instrument_type === 'INDEX';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg bg-[#111827] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-[#0d1322]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center font-bold text-sm text-blue-400 font-mono">
              {instrument.exchange}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight font-mono">{instrument.trading_symbol}</h2>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                  {instrument.segment}
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate max-w-xs">{instrument.name || instrument.trading_symbol}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 text-xs">
          {/* Price & Change Banner */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Last Traded Price</span>
              <span className={`text-xl font-bold font-mono transition-colors ${
                flash === 'up'
                  ? 'text-emerald-400 bg-emerald-500/20 px-1.5 rounded'
                  : flash === 'down'
                  ? 'text-rose-400 bg-rose-500/20 px-1.5 rounded'
                  : 'text-white'
              }`}>
                {livePrice ? `₹${livePrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">24h Change</span>
              <span className={`text-sm font-bold font-mono ${
                (liveChangePct ?? 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {liveChangePct ? `${liveChangePct > 0 ? '+' : ''}${liveChangePct.toFixed(2)}%` : '—'}
              </span>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Instrument Token</span>
              <span className="font-mono text-slate-200 font-semibold truncate block">{instrument.instrument_token}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Exchange Token</span>
              <span className="font-mono text-slate-200 font-semibold">{instrument.exchange_token}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Instrument Type</span>
              <span className="font-mono text-slate-200 font-semibold">{instrument.instrument_type}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Series</span>
              <span className="font-mono text-slate-200 font-semibold">{instrument.series || 'EQ'}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Lot Size</span>
              <span className="font-mono text-slate-200 font-semibold">{instrument.lot_size}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Tick Size</span>
              <span className="font-mono text-slate-200 font-semibold">₹{instrument.tick_size}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Listing Status</span>
              <span className="font-mono text-emerald-400 font-semibold">{instrument.listing_status}</span>
            </div>

            <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/80">
              <span className="text-[10px] uppercase text-slate-500 block">Provider</span>
              <span className="font-mono text-blue-400 font-semibold uppercase">{instrument.provider}</span>
            </div>
          </div>

          {/* Derivatives Status Indicator */}
          <div className={`p-3 rounded-xl border flex items-center space-x-3 ${
            hasFno ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-300' : 'bg-slate-900 border-slate-800 text-slate-400'
          }`}>
            {hasFno ? <CheckCircle className="w-5 h-5 text-cyan-400 shrink-0" /> : <AlertCircle className="w-5 h-5 text-slate-500 shrink-0" />}
            <div>
              <span className="font-bold block text-xs">
                {hasFno ? 'Active F&O Derivatives Available' : 'Cash Equity Only (No F&O Available)'}
              </span>
              <span className="text-[11px] text-slate-400 block">
                {hasFno
                  ? 'Active Index/Stock futures and option contracts are available on NSE/BSE.'
                  : 'Futures/Options are not available for this instrument.'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-4 bg-[#0d1322] border-t border-slate-800 flex items-center justify-end space-x-2">
          {onOpenAiCopilot && (
            <button
              onClick={() => {
                onClose();
                onOpenAiCopilot(instrument.trading_symbol);
              }}
              className="px-3.5 py-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-lg text-xs transition-all shadow-lg shadow-blue-600/30 flex items-center space-x-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
              <span>Ask AI Copilot</span>
            </button>
          )}
          {onOpenPrediction && (
            <button
              onClick={() => {
                onClose();
                onOpenPrediction(instrument.trading_symbol);
              }}
              className="px-3.5 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg text-xs transition-colors shadow-lg shadow-purple-600/30 flex items-center space-x-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Predict</span>
            </button>
          )}
          {hasFno && (
            <>
              <button
                onClick={() => {
                  onClose();
                  onOpenOptionChain(instrument.trading_symbol);
                }}
                className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg text-xs transition-colors shadow-lg shadow-blue-600/30"
              >
                Option Chain
              </button>
              <button
                onClick={() => {
                  onClose();
                  onOpenFutures(instrument.trading_symbol);
                }}
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg text-xs transition-colors"
              >
                Futures Curve
              </button>
            </>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
