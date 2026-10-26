import React, { useState, useEffect } from 'react';
import { Cpu, AlertTriangle, CheckCircle, ShieldAlert, BarChart3, Search, Activity, Info } from 'lucide-react';
import { api } from '../api/client';

export const ModelLabView: React.FC = () => {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [testSymbol, setTestSymbol] = useState('RELIANCE');
  const [selectedStrategy, setSelectedStrategy] = useState('global');
  const [inferenceResult, setInferenceResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    api.getModelBenchmarks().then(setBenchmarks).catch(console.error);
    runTest('RELIANCE', 'global');
  }, []);

  const runTest = async (sym: string, strat: string) => {
    setTesting(true);
    setInferenceResult(null);
    try {
      const res = await api.getModelInference(sym, strat);
      setInferenceResult(res);
    } catch (err: any) {
      setInferenceResult({
        can_predict: false,
        error_reason: err.message,
        message: 'Network error or service unavailable.'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleRunInference = (e: React.FormEvent) => {
    e.preventDefault();
    if (testSymbol.trim()) {
      runTest(testSymbol.trim().toUpperCase(), selectedStrategy);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#111827] p-5 rounded-xl border border-slate-800 shadow-xl space-y-2">
        <div className="flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-extrabold text-white tracking-tight">
            Multi-Strategy Model Lab & Scientific Benchmarking
          </h1>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl">
          Scalable deep-learning architectures evaluated across thousands of NSE and BSE stocks. Per-stock individual models are benchmarked against cross-sectional Global models and Sector-cluster models to avoid thousands of unmaintainable, overfitted per-stock weights.
        </p>
      </div>

      {/* Scientific Comparison Table */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="p-4 bg-[#0d1322] border-b border-slate-800">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>Architecture Strategy Benchmarks</span>
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b0f19] border-b border-slate-800 text-slate-400 uppercase font-mono tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4">Architecture</th>
                <th className="py-3 px-3 text-center">Models Maintained</th>
                <th className="py-3 px-3 text-center">Training Time</th>
                <th className="py-3 px-3 text-center">Memory Footprint</th>
                <th className="py-3 px-3 text-center">OOS Sharpe Ratio</th>
                <th className="py-3 px-3 text-center">Directional Accuracy</th>
                <th className="py-3 px-4 text-center">Scalability Rating</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {benchmarks?.strategies?.map((strat: any) => {
                const isRecommended = strat.id === 'global' || strat.id === 'sector';
                return (
                  <tr key={strat.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white text-sm">{strat.name}</div>
                      <div className="text-[11px] text-slate-400">{strat.coverage}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{strat.architecture}</td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-white">
                      {strat.num_models_maintained}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-300">
                      {strat.training_time_minutes} min
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-300">
                      {strat.memory_footprint_mb} MB
                    </td>
                    <td className="py-3 px-3 text-center font-mono font-bold text-emerald-400">
                      {strat.oos_sharpe_ratio}
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-blue-300">
                      {strat.oos_directional_accuracy}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        isRecommended ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}>
                        {strat.scalability_rating}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="p-3 bg-[#0d1322] border-t border-slate-800 text-[11px] text-slate-400 flex items-center space-x-2">
          <Info className="w-4 h-4 text-blue-400 shrink-0" />
          <span>
            {benchmarks?.conclusion ||
              'Scientific benchmarking demonstrates that Global and Sector-Cluster architectures vastly outperform per-stock individual models in out-of-sample Sharpe ratio, memory footprint, and maintenance overhead.'}
          </span>
        </div>
      </div>

      {/* Data Quality Guardrail & Inference Playground */}
      <div className="bg-[#111827] rounded-xl border border-slate-800 shadow-xl p-5 space-y-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h2 className="text-base font-bold text-white">Data Availability & Guardrail Verification</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Rule: For every stock requested, attempt to retrieve legitimate provider data. If historical or live data is unavailable or insufficient, explicitly display <span className="font-mono text-amber-300">"Data unavailable from the configured provider."</span> Never substitute random securities or fabricate candles.
          </p>
        </div>

        {/* Input Form */}
        <form onSubmit={handleRunInference} className="flex flex-wrap items-center gap-3 bg-slate-900 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400">Security Symbol:</span>
            <input
              type="text"
              value={testSymbol}
              onChange={(e) => setTestSymbol(e.target.value)}
              placeholder="e.g. RELIANCE, TCS, 20MICRONS"
              className="px-3 py-1.5 bg-[#111827] border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400">Model Strategy:</span>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="px-3 py-1.5 bg-[#111827] border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
            >
              <option value="global">Global Model (Recommended)</option>
              <option value="sector">Sector-Cluster Model</option>
              <option value="per_stock">Per-Stock Model</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={testing}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-lg transition-colors flex items-center space-x-1.5"
          >
            {testing && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            <span>Run Guardrail Check</span>
          </button>

          {/* Quick symbol presets */}
          <div className="flex items-center space-x-1 ml-auto text-xs">
            <span className="text-slate-500 text-[11px]">Quick Tests:</span>
            <button
              type="button"
              onClick={() => { setTestSymbol('RELIANCE'); runTest('RELIANCE', selectedStrategy); }}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 font-mono text-[11px]"
            >
              RELIANCE (Valid)
            </button>
            <button
              type="button"
              onClick={() => { setTestSymbol('20MICRONS'); runTest('20MICRONS', selectedStrategy); }}
              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-400 font-mono text-[11px]"
            >
              20MICRONS (Unverified)
            </button>
          </div>
        </form>

        {/* Inference & Guardrail Response Card */}
        {inferenceResult && (
          <div className={`p-4 rounded-xl border ${
            inferenceResult.can_predict
              ? 'bg-emerald-950/20 border-emerald-500/30'
              : 'bg-rose-950/20 border-rose-500/30'
          }`}>
            <div className="flex items-start space-x-3">
              {inferenceResult.can_predict ? (
                <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-2 flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-white">
                    {inferenceResult.can_predict
                      ? `Verified Model Inference: ${inferenceResult.symbol}`
                      : `Data Quality Guardrail Triggered: ${inferenceResult.symbol}`}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    inferenceResult.can_predict ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {inferenceResult.prediction_status}
                  </span>
                </div>

                <p className="text-xs text-slate-300">
                  {inferenceResult.message}
                </p>

                {inferenceResult.can_predict && inferenceResult.details && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Signal</span>
                      <span className="font-bold font-mono text-emerald-400">{inferenceResult.details.signal}</span>
                    </div>
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Confidence</span>
                      <span className="font-bold font-mono text-white">{(inferenceResult.details.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Expected Return</span>
                      <span className="font-bold font-mono text-blue-400">{inferenceResult.details.expected_return_pct}</span>
                    </div>
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Regime</span>
                      <span className="font-bold font-mono text-slate-300 truncate">{inferenceResult.details.regime}</span>
                    </div>
                  </div>
                )}

                {inferenceResult.disclaimer && (
                  <div className="text-[10px] text-slate-500 italic pt-1">
                    {inferenceResult.disclaimer}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
