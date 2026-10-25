import React, { useState, useEffect, useCallback } from 'react';
import { simulatePackaging, getCatalogMaterials, getApiBaseUrl } from '../utils/api';

/**
 * SustainabilityInsights
 *
 * Follows Stitch wrapture_09_sustainability_insights design spec.
 * Connects to real backend:
 *   POST /api/sustainability/simulate  — returns { status, packaging, metrics, … }
 *   GET  /api/sustainability/materials — list biomaterial catalog
 *
 * REAL DATA ONLY — no hardcoded numbers.
 * Backend response shape (services/sustainability.py):
 *   result.packaging.{ sku, title, material, length_in, width_in, height_in }
 *   result.metrics.{ co2e_recycling_mt, packaging_weight_kg, cost_per_unit_usd }
 *   result.data_availability.{ co2_recycling, packaging_weight, cost_per_unit }
 */

// ── helpers ────────────────────────────────────────────────────────────────────

function fmt(val, decimals = 2) {
  if (val == null) return null;
  return Number(val).toFixed(decimals);
}

function fmtDims(pkg) {
  if (!pkg) return null;
  const { length_in, width_in, height_in } = pkg;
  if (length_in == null && width_in == null && height_in == null) return null;
  return [length_in, width_in, height_in]
    .map((v) => (v != null ? Number(v).toFixed(2) : '?'))
    .join(' × ') + ' in';
}

/** co2e_recycling_mt is negative (CO₂ saved). Show absolute value in readable units. */
function fmtCo2Display(val) {
  if (val == null) return null;
  const mt = Math.abs(val);
  const kg = mt * 1000;
  if (kg >= 1) return `${kg.toFixed(3)} kg CO₂e`;
  return `${(mt * 1e6).toFixed(2)} g CO₂e`;
}

// ── sub-components ─────────────────────────────────────────────────────────────

function MetricCard({ value, suffix, label, na }) {
  return (
    <div className="bg-white/80 p-3.5 rounded-2xl border border-outline-variant/40 text-center shadow-sm">
      {value != null ? (
        <span className="block font-serif text-[28px] font-normal text-primary-container leading-tight">
          {value}
          {suffix && <span className="text-[18px]">{suffix}</span>}
        </span>
      ) : (
        <span className="block text-[12px] text-tertiary leading-tight mt-2 mb-1 italic">{na || 'Not available'}</span>
      )}
      <span className="text-[11px] text-tertiary font-medium leading-tight block mt-1">{label}</span>
    </div>
  );
}

function DataRow({ label, value, note }) {
  return (
    <div className="py-2 border-b border-sand/50 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <span className="text-[12px] text-tertiary flex-shrink-0">{label}</span>
        <span className={`text-[12px] font-medium text-right ${value == null ? 'text-on-surface-variant/60 italic' : 'text-on-surface'}`}>
          {value ?? 'Not available'}
        </span>
      </div>
      {note && (
        <p className="text-[10px] text-tertiary/70 text-right mt-0.5">{note}</p>
      )}
    </div>
  );
}

// ── real PDF export ────────────────────────────────────────────────────────────

async function exportPdf(simResult, apiUrl) {
  let jsPDF;
  try {
    const mod = await import('jspdf');
    jsPDF = mod.default || mod.jsPDF;
  } catch {
    alert('PDF export requires jsPDF.\nRun: npm install jspdf');
    return;
  }

  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const pkg   = simResult?.packaging || {};
  const met   = simResult?.metrics   || {};
  const avail = simResult?.data_availability || {};
  const now   = new Date().toLocaleString();

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.text('Wrapture Sustainability Report', 20, 20);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.text(`Generated: ${now}`, 20, 28);
  doc.text(`Backend: ${apiUrl}`, 20, 33);
  doc.text('Data source: Packrift catalog — real records only, nothing fabricated.', 20, 38);

  doc.setFontSize(13);
  doc.setFont('helvetica', 'bold');
  doc.text('Best-Fit Packaging', 20, 50);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  const rows = [
    ['SKU',            pkg.sku    || 'Not available'],
    ['Title',          pkg.title  || 'Not available'],
    ['Material',       pkg.material || 'Not specified'],
    ['Dimensions',     fmtDims(pkg) || 'Not available'],
    ['CO₂e recycling', avail.co2_recycling && met.co2e_recycling_mt != null
      ? `${fmtCo2Display(met.co2e_recycling_mt)} (${Number(met.co2e_recycling_mt).toFixed(6)} mt)`
      : 'Not available'],
    ['Package weight',  avail.packaging_weight && met.packaging_weight_kg != null
      ? `${Number(met.packaging_weight_kg).toFixed(5)} kg`
      : 'Not available'],
    ['Unit price',      avail.cost_per_unit && met.cost_per_unit_usd != null
      ? `$${Number(met.cost_per_unit_usd).toFixed(4)}`
      : 'Not available'],
  ];

  let y = 58;
  rows.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(`${label}:`, 20, y);
    doc.setFont('helvetica', 'normal');
    doc.text(String(value), 68, y);
    y += 7;
  });

  y += 5;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.text('Data Integrity Notes', 20, y);
  y += 6;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  const notes = [
    '• CO₂e values from Packrift catalog field co2e_recycling_mt (EPA-based modeling).',
    '• Negative CO₂e = CO₂ avoided during recycling (not a full lifecycle value).',
    '• Package weight derived from package_weight_lb / pack_quantity.',
    '• Fields showing "Not available" are genuinely absent from the catalog record.',
    '• No values in this report are fabricated, estimated, or interpolated.',
  ];
  notes.forEach((n) => { doc.text(n, 20, y); y += 5; });

  doc.save(`wrapture-sustainability-${Date.now()}.pdf`);
}

// ── main component ─────────────────────────────────────────────────────────────

export default function SustainabilityInsights() {
  const [materials, setMaterials] = useState([]);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError]   = useState(null);
  const [exportState, setExportState] = useState('idle'); // idle | loading | done | error

  const runSimulation = useCallback(async () => {
    setSimLoading(true);
    setSimError(null);
    try {
      // Representative mid-size product; backend picks the best real catalog package.
      const payload = {
        length_cm: 20,
        width_cm: 15,
        height_cm: 10,
        weight_kg: 0.5,
        product_type: 'box',
        packaging_material: 'corrugated_cardboard',
      };
      const result = await simulatePackaging(payload);
      setSimResult(result);
    } catch (err) {
      setSimError(err.message || 'Simulation failed');
    } finally {
      setSimLoading(false);
    }
  }, []);

  useEffect(() => {
    getCatalogMaterials()
      .then((data) => setMaterials(Array.isArray(data) ? data : data?.materials || []))
      .catch(() => {});
    runSimulation();
  }, [runSimulation]);

  const handleExport = async () => {
    if (!simResult) {
      alert('Run the simulation first before exporting a report.');
      return;
    }
    setExportState('loading');
    try {
      await exportPdf(simResult, getApiBaseUrl());
      setExportState('done');
      setTimeout(() => setExportState('idle'), 2500);
    } catch (err) {
      console.error('[Export PDF]', err);
      setExportState('error');
      setTimeout(() => setExportState('idle'), 3000);
    }
  };

  // ── Derive display values from REAL backend response ─────────────────────────
  // Backend shape:
  //   { status, packaging: { sku, title, material, length_in, width_in, height_in, … },
  //     metrics: { co2e_recycling_mt, packaging_weight_kg, cost_per_unit_usd },
  //     data_availability: { co2_recycling, packaging_weight, cost_per_unit } }
  //
  // No fallback numbers — null means the field is absent from the catalog record.

  const isOk  = simResult?.status === 'ok';
  const pkg   = isOk ? (simResult.packaging          || {}) : {};
  const met   = isOk ? (simResult.metrics            || {}) : {};
  const avail = isOk ? (simResult.data_availability  || {}) : {};

  const co2DisplayStr    = avail.co2_recycling    ? fmtCo2Display(met.co2e_recycling_mt) : null;
  const weightDisplayStr = avail.packaging_weight ? `${fmt(met.packaging_weight_kg, 5)} kg` : null;
  const priceDisplayStr  = avail.cost_per_unit    ? `$${fmt(met.cost_per_unit_usd, 4)}` : null;
  const dimsStr          = fmtDims(pkg);

  return (
    <div className="flex flex-col w-full min-h-full bg-surface pb-safe-nav">
      <div className="flex flex-col w-full">

        {/* Section header */}
        <div className="px-5 pt-3 pb-3">
          <span className="text-[11px] font-semibold tracking-[0.2em] text-secondary uppercase block mb-1">
            SUSTAINABILITY INSIGHT
          </span>
          <h1 className="font-serif text-[30px] font-normal tracking-tight text-on-surface leading-tight mb-1">
            Packaging Impact
          </h1>
          <p className="text-[13px] text-tertiary leading-relaxed">
            Real catalog data — best-fit package for a 20 × 15 × 10 cm product.
          </p>
        </div>

        {/* Hero image */}
        <div className="px-5 mb-5">
          <div className="relative w-full rounded-2xl overflow-hidden shadow-sm bg-sand aspect-[16/9]">
            <img
              src="/assets/cardboard-macro.png"
              alt="Optimized sustainable packaging material — recycled corrugated cardboard"
              className="w-full h-full object-cover object-center"
              onError={(e) => { e.target.src = '/assets/hero-kraft-packaging.png'; }}
            />
            <div className="absolute bottom-3 left-3 right-3 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-xl flex items-center justify-between border border-sand/60">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary-container" />
                <span className="text-[12px] font-medium text-on-surface">
                  {pkg.title ? pkg.title : 'Best-Fit Package'}
                </span>
              </div>
              <span className="text-[11px] font-semibold text-primary-container tracking-wider uppercase">
                {pkg.material || 'Packrift catalog'}
              </span>
            </div>
          </div>
        </div>

        {/* Key Metrics Grid — REAL values only, no invented fallbacks */}
        <div className="grid grid-cols-3 gap-2.5 px-5 mb-5">
          <MetricCard
            value={co2DisplayStr}
            label="CO₂e (recycling)"
            na="No CO₂ data"
          />
          <MetricCard
            value={weightDisplayStr}
            label="Package Weight"
            na="No weight data"
          />
          <MetricCard
            value={priceDisplayStr}
            label="Unit Price"
            na="No price data"
          />
        </div>

        {/* Simulation result card */}
        <div className="px-5 mb-5">
          <div className="bg-white/85 p-5 rounded-2xl border border-sand/80 shadow-sm">
            <h2 className="font-serif text-[18px] font-medium text-on-surface mb-4">
              Best-Fit Catalog Package
            </h2>

            {simLoading ? (
              <div className="flex items-center justify-center py-6">
                <span className="material-symbols-outlined text-secondary animate-spin text-[28px]">sync</span>
                <span className="ml-2 text-[13px] text-on-surface-variant">Running simulation…</span>
              </div>
            ) : simError ? (
              <div className="flex flex-col items-center py-4 text-center gap-2">
                <span className="material-symbols-outlined text-error text-[24px]">error</span>
                <p className="text-[12px] text-on-surface-variant">{simError}</p>
                <button
                  onClick={runSimulation}
                  className="mt-2 py-1.5 px-4 bg-primary text-surface rounded-lg text-[12px] font-medium cursor-pointer"
                >
                  Retry
                </button>
              </div>
            ) : isOk ? (
              <div className="space-y-0">
                <DataRow label="SKU"            value={pkg.sku    || null} />
                <DataRow label="Title"          value={pkg.title  || null} />
                <DataRow label="Material"       value={pkg.material || null} />
                <DataRow label="Family"         value={pkg.family  || null} />
                <DataRow label="Dimensions"     value={dimsStr} />
                <DataRow
                  label="CO₂e recycling"
                  value={co2DisplayStr}
                  note={co2DisplayStr
                    ? 'Source: Packrift co2e_recycling_mt (negative = CO₂ avoided during recycling)'
                    : null}
                />
                <DataRow label="Package weight" value={weightDisplayStr} />
                <DataRow label="Unit price"     value={priceDisplayStr} />
              </div>
            ) : simResult?.status === 'no_fit' ? (
              <p className="text-[13px] text-tertiary py-4 text-center">
                No packaging in the catalog fits these dimensions with 10% clearance.
              </p>
            ) : null}
          </div>
        </div>

        {/* Material catalog preview */}
        {materials.length > 0 && (
          <div className="px-5 mb-5">
            <div className="bg-white/85 p-4 rounded-2xl border border-sand/80 shadow-sm">
              <h3 className="font-serif text-[16px] font-medium text-on-surface mb-3">Material Catalog</h3>
              <div className="space-y-2">
                {materials.slice(0, 4).map((mat, i) => {
                  const label = typeof mat === 'string' ? mat : (mat?.label || mat?.name || mat?.id || JSON.stringify(mat));
                  const count = typeof mat === 'object' ? mat?.count : null;
                  return (
                    <div key={i} className="flex items-center gap-3 p-2 rounded-xl bg-surface border border-outline-variant/20">
                      <div className="w-8 h-8 rounded-lg bg-secondary-container flex items-center justify-center shrink-0">
                        <span className="material-symbols-outlined text-[16px] text-secondary">compost</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-body-sm text-[13px] font-semibold text-primary truncate block">
                          {label}
                        </span>
                        {count != null && (
                          <span className="text-[11px] text-tertiary">{count.toLocaleString()} records</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              <p className="text-[10px] text-tertiary mt-3">
                Source: Packrift catalog — real product records only.
              </p>
            </div>
          </div>
        )}

        {/* Export Button — generates real PDF from live simulation data */}
        <div className="px-5 mb-6">
          <button
            id="export-sustainability-report-btn"
            onClick={handleExport}
            disabled={exportState === 'loading' || simLoading || !simResult}
            className="w-full py-3.5 px-4 bg-primary-container hover:bg-primary text-surface rounded-xl font-medium text-[14px] flex items-center justify-center gap-2 shadow-sm transition-colors cursor-pointer active:scale-[0.99] disabled:opacity-70"
          >
            {exportState === 'loading' ? (
              <>
                <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
                <span>Generating PDF…</span>
              </>
            ) : exportState === 'done' ? (
              <>
                <span className="material-symbols-outlined text-[18px]">check_circle</span>
                <span>Report Downloaded</span>
              </>
            ) : exportState === 'error' ? (
              <>
                <span className="material-symbols-outlined text-[18px]">error</span>
                <span>Export failed — see console</span>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">download</span>
                <span>Download Sustainability Report (PDF)</span>
              </>
            )}
          </button>
          {!simResult && !simLoading && (
            <p className="text-[11px] text-tertiary text-center mt-2">
              Simulation must succeed before exporting.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
