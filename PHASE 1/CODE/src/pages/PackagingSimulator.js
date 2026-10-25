import React, { useState, Suspense, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import {
  OrbitControls, Box, Environment, ContactShadows, Float,
  Sparkles, Cylinder, RoundedBox,
} from '@react-three/drei';
import { RotateCcw, Play, Pause, Info } from 'lucide-react';
import * as THREE from 'three';
import { simulatePackaging } from '../utils/api';

// ── Visual-only material definitions ─────────────────────────────────────────
// These control the 3-D appearance only.
// CO₂, cost, and weight come exclusively from the backend catalog response.

const VISUAL_MATERIALS = [
  { id: 'corrugated_cardboard', label: 'Corrugated Cardboard', color: '#8b5a3c', roughness: 0.9, metalness: 0.0, pattern: 'corrugated' },
  { id: 'kraft_paper',          label: 'Kraft Paper',          color: '#c8a96e', roughness: 0.85, metalness: 0.0, pattern: 'corrugated' },
  { id: 'plastic',              label: 'Plastic / Poly',       color: '#3b82f6', roughness: 0.05, metalness: 0.0, pattern: 'bubbles' },
  { id: 'any',                  label: 'Any (best fit)',        color: '#6b7280', roughness: 0.7,  metalness: 0.0, pattern: 'none' },
];

const PRODUCT_PRESETS = {
  smartphone:  { dims: { w: 7,  h: 15, d: 1  }, shape: 'rounded-box', color: '#1f2937', metalness: 0.9, roughness: 0.1, emoji: '📱' },
  book:        { dims: { w: 15, h: 23, d: 2  }, shape: 'box',         color: '#7c2d12', metalness: 0.0, roughness: 0.8, emoji: '📚' },
  bottle:      { dims: { w: 8,  h: 25, d: 8  }, shape: 'cylinder',    color: '#059669', metalness: 0.1, roughness: 0.2, emoji: '🍶' },
  electronics: { dims: { w: 20, h: 15, d: 10 }, shape: 'box',         color: '#374151', metalness: 0.7, roughness: 0.3, emoji: '📺' },
};

// ── 3-D helpers ───────────────────────────────────────────────────────────────

function ProductMesh({ preset, dims, isAnimating }) {
  const ref = useRef();
  useFrame((state) => {
    if (!ref.current || !isAnimating) return;
    ref.current.rotation.y += 0.01;
    ref.current.position.y = Math.sin(state.clock.elapsedTime * 2) * 0.1;
  });
  const mat = (
    <meshPhysicalMaterial
      color={preset.color} metalness={preset.metalness} roughness={preset.roughness}
      clearcoat={preset.metalness > 0.5 ? 1 : 0} clearcoatRoughness={0.1}
    />
  );
  const args = [dims.w, dims.h, dims.d];
  if (preset.shape === 'rounded-box')
    return <RoundedBox ref={ref} args={args} radius={0.1} smoothness={4} castShadow>{mat}</RoundedBox>;
  if (preset.shape === 'cylinder')
    return <Cylinder ref={ref} args={[dims.w / 2, dims.w / 2, dims.h, 16]} castShadow>{mat}</Cylinder>;
  return <Box ref={ref} args={args} castShadow>{mat}</Box>;
}

function PackagingMesh({ vismat, dims, isAnimating }) {
  const ref = useRef();
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 256;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = vismat.color;
    ctx.fillRect(0, 0, 256, 256);
    if (vismat.pattern === 'corrugated') {
      ctx.strokeStyle = 'rgba(0,0,0,0.15)'; ctx.lineWidth = 2;
      for (let i = 0; i < 256; i += 8) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 256); ctx.stroke(); }
    } else if (vismat.pattern === 'bubbles') {
      ctx.fillStyle = 'rgba(255,255,255,0.25)';
      for (let x = 0; x < 256; x += 20)
        for (let y = 0; y < 256; y += 20) { ctx.beginPath(); ctx.arc(x + 10, y + 10, 8, 0, Math.PI * 2); ctx.fill(); }
    }
    const t = new THREE.CanvasTexture(canvas);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(2, 2);
    return t;
  }, [vismat]);

  useFrame(() => { if (ref.current && isAnimating) ref.current.rotation.y += 0.005; });

  return (
    <Box ref={ref} args={[dims.w + 0.6, dims.h + 0.6, dims.d + 0.6]} castShadow>
      <meshPhysicalMaterial
        map={texture} color={vismat.color}
        opacity={vismat.id === 'plastic' ? 0.65 : 0.45} transparent
        roughness={vismat.roughness} metalness={vismat.metalness}
        transmission={vismat.id === 'plastic' ? 0.8 : 0} thickness={0.5}
      />
    </Box>
  );
}

// ── Metric display helper ─────────────────────────────────────────────────────

function Metric({ label, value, unit, available, note }) {
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      {available ? (
        <div className="text-lg font-bold text-gray-800">
          {value} <span className="text-sm font-normal text-gray-500">{unit}</span>
        </div>
      ) : (
        <div className="text-sm text-gray-400 italic">Not available</div>
      )}
      {note && <div className="text-xs text-gray-400 mt-1">{note}</div>}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const PackagingSimulator = () => {
  const [productType, setProductType] = useState('smartphone');
  const [dims, setDims]               = useState({ w: 7, h: 15, d: 1 });
  const [weight, setWeight]           = useState(0.2);
  const [materialId, setMaterialId]   = useState('corrugated_cardboard');
  const [isAnimating, setIsAnimating] = useState(true);

  const [simResult, setSimResult]     = useState(null);
  const [simLoading, setSimLoading]   = useState(false);
  const [simError, setSimError]       = useState(null);

  const preset = PRODUCT_PRESETS[productType];
  const vismat = VISUAL_MATERIALS.find((m) => m.id === materialId);
  const scaledDims = { w: dims.w / 10, h: dims.h / 10, d: dims.d / 10 };

  const handlePresetChange = (type) => {
    setProductType(type);
    setDims({ ...PRODUCT_PRESETS[type].dims });
    setSimResult(null);
    setSimError(null);
  };

  const handleSimulate = async () => {
    setSimLoading(true);
    setSimResult(null);
    setSimError(null);
    try {
      const result = await simulatePackaging({
        product_type:       productType,
        length_cm:          dims.w,
        width_cm:           dims.h,
        height_cm:          dims.d,
        weight_kg:          weight,
        packaging_material: materialId === 'any' ? null : materialId,
      });
      setSimResult(result);
    } catch (err) {
      setSimError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : (err.data?.error || err.message),
      );
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">📦 Packaging Simulator</h1>
        <p className="text-gray-600">
          3-D preview + real catalog metrics from the Packrift database.
          All values come from actual catalog records — nothing is invented.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

        {/* 3-D canvas — visualization only */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Material Preview <span className="text-xs text-gray-400 font-normal">(visualization only)</span></h2>
            <div className="flex gap-2">
              <button onClick={() => setIsAnimating((v) => !v)} className="btn btn-secondary text-sm">
                {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <button
                onClick={() => { handlePresetChange('smartphone'); setMaterialId('corrugated_cardboard'); setSimResult(null); }}
                className="btn btn-secondary text-sm"
              >
                <RotateCcw className="w-4 h-4 mr-1" /> Reset
              </button>
            </div>
          </div>

          <div className="h-72 bg-gradient-to-br from-gray-900 to-gray-700 rounded-lg overflow-hidden">
            <Canvas camera={{ position: [6, 6, 6], fov: 45 }} shadows>
              <Suspense fallback={null}>
                <Environment preset="studio" />
                <ambientLight intensity={0.4} />
                <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
                <OrbitControls enablePan enableZoom enableRotate autoRotate={isAnimating} autoRotateSpeed={2} />
                <ContactShadows position={[0, -2, 0]} opacity={0.4} scale={10} blur={2} far={4} />
                <Float speed={isAnimating ? 2 : 0} floatIntensity={isAnimating ? 0.2 : 0}>
                  <ProductMesh preset={preset} dims={scaledDims} isAnimating={isAnimating} />
                </Float>
                <Float speed={isAnimating ? 1.5 : 0} floatIntensity={isAnimating ? 0.1 : 0}>
                  <PackagingMesh vismat={vismat} dims={scaledDims} isAnimating={isAnimating} />
                </Float>
                {materialId === 'corrugated_cardboard' && isAnimating && (
                  <Sparkles count={20} scale={4} size={3} speed={0.3} color="#22c55e" />
                )}
              </Suspense>
            </Canvas>
          </div>
        </div>

        {/* Configuration */}
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-xl font-semibold mb-4">Product Configuration</h2>
          <div className="space-y-4">

            <div>
              <label className="block text-sm font-medium mb-2">Product Type</label>
              <select value={productType} onChange={(e) => handlePresetChange(e.target.value)} className="input">
                {Object.entries(PRODUCT_PRESETS).map(([k, v]) => (
                  <option key={k} value={k}>{v.emoji} {k.charAt(0).toUpperCase() + k.slice(1)}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Dimensions (cm) — W × H × D</label>
              <div className="grid grid-cols-3 gap-2">
                {['w', 'h', 'd'].map((axis) => (
                  <input
                    key={axis} type="number" value={dims[axis]}
                    onChange={(e) => setDims((p) => ({ ...p, [axis]: parseFloat(e.target.value) || 0 }))}
                    className="input text-sm" placeholder={axis.toUpperCase()}
                  />
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Weight (kg)</label>
              <input
                type="number" step="0.1" value={weight}
                onChange={(e) => setWeight(parseFloat(e.target.value) || 0)}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Packaging Material</label>
              <div className="space-y-2">
                {VISUAL_MATERIALS.map((m) => (
                  <button
                    key={m.id} onClick={() => setMaterialId(m.id)}
                    className={`w-full p-3 text-left rounded-lg border-2 transition-all ${
                      materialId === m.id ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ backgroundColor: m.color }} />
                      <span className="text-sm font-medium">{m.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleSimulate}
              disabled={simLoading || dims.w <= 0 || dims.h <= 0 || dims.d <= 0}
              className="btn btn-primary w-full"
            >
              {simLoading ? 'Querying catalog…' : 'Simulate with Real Catalog Data'}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {simError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Error:</strong> {simError}
        </div>
      )}

      {/* Results */}
      {simResult && simResult.status === 'ok' && (
        <div className="space-y-6">

          {/* Matched package */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
            <h2 className="text-xl font-semibold mb-1">Matched Catalog Package</h2>
            <p className="text-xs text-gray-400 mb-4">
              Source: Packrift catalog · SKU: {simResult.packaging.sku ?? '—'}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div><span className="text-gray-500">Title:</span> <span className="font-medium">{simResult.packaging.title ?? '—'}</span></div>
              <div><span className="text-gray-500">Family:</span> <span className="font-medium">{simResult.packaging.family ?? '—'}</span></div>
              <div>
                <span className="text-gray-500">Dimensions:</span>{' '}
                <span className="font-medium">
                  {simResult.packaging.length_in} × {simResult.packaging.width_in} × {simResult.packaging.height_in} in
                </span>
              </div>
              <div>
                <span className="text-gray-500">Material:</span>{' '}
                <span className="font-medium">{simResult.packaging.material ?? 'Not specified'}</span>
              </div>
              <div>
                <span className="text-gray-500">Protection score:</span>{' '}
                <span className="font-medium">{simResult.packaging.protection_score ?? '—'}</span>
              </div>
              <div>
                <span className="text-gray-500">Protection evidence:</span>{' '}
                <span className="font-medium">
                  {Array.isArray(simResult.packaging.protection_evidence) && simResult.packaging.protection_evidence.length > 0
                    ? simResult.packaging.protection_evidence.join(', ')
                    : '—'}
                </span>
              </div>
            </div>
            {simResult.packaging.canonical_product_url && (
              <a
                href={simResult.packaging.canonical_product_url}
                target="_blank" rel="noopener noreferrer"
                className="text-xs text-blue-600 underline mt-3 inline-block"
              >
                View on Packrift ↗
              </a>
            )}
          </div>

          {/* Metrics */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
            <h2 className="text-xl font-semibold mb-1">Catalog Metrics</h2>
            <p className="text-xs text-gray-400 mb-4">
              All values are read directly from the catalog record. "Not available" means the field
              is absent in the source data — no value has been estimated or invented.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Metric
                label="Cost per Unit"
                value={simResult.metrics.cost_per_unit_usd != null ? `$${simResult.metrics.cost_per_unit_usd.toFixed(4)}` : null}
                available={simResult.data_availability.cost_per_unit}
                note="Source: unit_price field (= snapshot_price / pack_quantity)"
              />
              <Metric
                label="Packaging Weight"
                value={simResult.metrics.packaging_weight_kg != null ? simResult.metrics.packaging_weight_kg.toFixed(4) : null}
                unit="kg"
                available={simResult.data_availability.packaging_weight}
                note="Source: package_weight_lb × 0.453592 (per-unit physical weight)"
              />
              <Metric
                label="CO₂ Recycling"
                value={simResult.metrics.co2e_recycling_mt != null ? simResult.metrics.co2e_recycling_mt.toFixed(7) : null}
                unit="mt CO₂e"
                available={simResult.data_availability.co2_recycling}
                note={simResult.metrics.co2e_recycling_mt != null && simResult.metrics.co2e_recycling_mt < 0
                  ? 'Negative = CO₂ saved during recycling. Source: co2e_recycling_mt field.'
                  : 'Source: co2e_recycling_mt field.'}
              />
            </div>

            {/* Sustainability score — intentionally null */}
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
              <Info className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-semibold text-yellow-800">Sustainability Score: Not calculated</div>
                <div className="text-xs text-yellow-700 mt-1">{simResult.metrics.sustainability_score_note}</div>
              </div>
            </div>

            {/* CO2 sign convention note */}
            {simResult.data_availability.co2_recycling && (
              <p className="text-xs text-gray-400 mt-3">{simResult.co2_sign_convention}</p>
            )}
          </div>

        </div>
      )}

      {/* No fit */}
      {simResult && simResult.status === 'no_fit' && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-gray-600 text-sm">
          No packaging in the catalog fits these dimensions with 10% clearance.
          Try increasing the dimensions or selecting "Any (best fit)" material.
        </div>
      )}
    </div>
  );
};

export default PackagingSimulator;
