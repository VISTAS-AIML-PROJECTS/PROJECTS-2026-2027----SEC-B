import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  CubeIcon,
  FireIcon,
  ArrowRightIcon,
  UsersIcon,
  GlobeAltIcon,
  FlagIcon,
  BoltIcon,
  SparklesIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../components/ui/Button';
import { recommendPackaging } from '../utils/packagingEngine';
import { recommendPackagingAPI } from '../utils/api';
import './PackagingRecommender.css';

// ── helpers ──────────────────────────────────────────────────────────────────

function fmtPrice(val) {
  if (val == null) return null;
  return `$${Number(val).toFixed(2)}`;
}

function fmtUtil(val) {
  if (val == null) return null;
  return `${(val * 100).toFixed(1)}%`;
}

function fmtVol(val) {
  if (val == null) return null;
  return `${Number(val).toFixed(2)} in³`;
}

function fmtCo2(val) {
  if (val == null) return null;
  return `${Number(val).toFixed(6)} mt`;
}

function protectionLabel(score, evidence) {
  if (evidence != null) {
    const s = String(evidence).trim();
    if (s) return s;
  }
  if (score == null || score === 0) return null;
  return `Score ${score}`;
}

function materialLabel(material) {
  if (!material || material.toLowerCase() === 'unknown') return null;
  return material;
}

// ── sub-components ────────────────────────────────────────────────────────────

function MetricBlock({ label, value, na }) {
  return (
    <div className="pr-metric">
      {value != null
        ? <div className="pr-metric-value">{value}</div>
        : <div className="pr-metric-na">{na || 'Not available'}</div>}
      <div className="pr-metric-label">{label}</div>
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div className="pr-detail-item">
      <div className="pr-detail-key">{label}</div>
      <div className={`pr-detail-val${value == null ? ' na' : ''}`}>
        {value ?? 'Not specified'}
      </div>
    </div>
  );
}

function BestMatch({ rec }) {
  const protection = protectionLabel(rec.protection_score, rec.protection_evidence);
  const material = materialLabel(rec.material);

  return (
    <div className="pr-best-card">
      <div className="pr-best-label">Best Match</div>
      {rec.sku && <div className="pr-best-sku">{rec.sku}</div>}
      <div className="pr-best-title">{rec.title ?? '—'}</div>
      <div className="pr-best-dims">
        Package dimensions&nbsp;
        <span>
          {rec.package_length_in} × {rec.package_width_in} × {rec.package_height_in} in
        </span>
      </div>

      <div className="pr-metrics">
        <MetricBlock label="Space Utilization" value={fmtUtil(rec.space_utilization)} />
        <MetricBlock label="Unused Volume"     value={fmtVol(rec.unused_volume_in3 ?? rec.unused_volume)} />
        <MetricBlock label="Unit Price"        value={fmtPrice(rec.unit_price)} />
        <MetricBlock label="CO₂ Recycling"     value={fmtCo2(rec.co2e_recycling_mt)} />
      </div>

      <div className="pr-detail-row">
        <DetailItem label="Material"           value={material} />
        <DetailItem label="Protection evidence" value={protection} />
        {rec.min_clearance_pct != null && (
          <DetailItem
            label="Min clearance"
            value={`${rec.min_clearance_pct.toFixed(1)}%`}
          />
        )}
      </div>

      <div className="pr-why-box">
        <strong>Why this package?</strong>
        Selected based on physical fit with 10% clearance requirement and lowest
        unused volume. Ranked by unused volume, then protection evidence, then
        material sustainability, then unit price.
      </div>
    </div>
  );
}

function OtherOptions({ recs }) {
  if (!recs || recs.length === 0) return null;
  return (
    <div>
      <div className="pr-others-heading">Other qualifying options</div>
      <div className="pr-other-list">
        {recs.map((rec) => (
          <div key={rec.sku ?? rec.rank} className="pr-other-row">
            <div className="pr-other-sku">{rec.sku ?? '—'}</div>
            <div className="pr-other-name">{rec.title ?? '—'}</div>
            <div className="pr-other-dims">
              {rec.package_length_in} × {rec.package_width_in} × {rec.package_height_in} in
            </div>
            <div className="pr-other-util">
              {rec.space_utilization != null
                ? fmtUtil(rec.space_utilization)
                : <span className="pr-other-na">—</span>}
            </div>
            <div className="pr-other-price">
              {rec.unit_price != null
                ? fmtPrice(rec.unit_price)
                : <span className="pr-other-na">—</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalysisSummary({ recommendation }) {
  const { status, meta, recommendations } = recommendation;

  const statusBadge = {
    RECOMMENDED:                 { cls: 'recommended', icon: '✓', text: 'Fit verified' },
    FIT_BUT_PROTECTION_UNVERIFIED: { cls: 'warning',   icon: '⚠', text: 'Protection unverified' },
    NO_PHYSICAL_FIT:             { cls: 'error',       icon: '✕', text: 'No physical fit' },
  }[status] ?? { cls: 'warning', icon: '?', text: status };

  return (
    <div className="pr-summary-card">
      <div className="pr-summary-label">Packaging Analysis</div>

      <span className={`pr-status-badge ${statusBadge.cls}`}>
        {statusBadge.icon} {statusBadge.text}
      </span>

      <div className="pr-summary-headline">
        {meta.totalPhysicalFits.toLocaleString()} of{' '}
        {meta.totalCandidatesEvaluated.toLocaleString()} packages physically fit
      </div>
      <div className="pr-summary-sub">10% clearance requirement applied</div>

      <div className="pr-summary-dims">
        <CubeIcon style={{ width: 14, height: 14 }} />
        Product dimensions&nbsp;
        {meta.productL.toFixed(2)} × {meta.productW.toFixed(2)} × {meta.productH.toFixed(2)} in
      </div>

      <div className="pr-info-box">
        <InformationCircleIcon style={{ width: 14, height: 14, flexShrink: 0, marginTop: 1 }} />
        Dimensional fit is verified. Load capacity is not available for every catalog item.
      </div>

      {status === 'FIT_BUT_PROTECTION_UNVERIFIED' && (
        <div className="pr-info-box" style={{ marginTop: '0.5rem', background: '#fffbeb', borderColor: '#fde68a' }}>
          <ExclamationTriangleIcon style={{ width: 14, height: 14, flexShrink: 0, marginTop: 1 }} />
          Packages physically fit but none have verified protection evidence for fragile items.
        </div>
      )}

      {status === 'NO_PHYSICAL_FIT' && recommendations.length === 0 && (
        <div className="pr-nofit" style={{ marginTop: '0.75rem' }}>
          No packaging in the catalog fits these dimensions with 10% clearance.
          Try adjusting the product dimensions.
        </div>
      )}
    </div>
  );
}

function ResultsPanel({ recommendation }) {
  const { recommendations } = recommendation;
  if (!recommendations || recommendations.length === 0) return null;

  const [best, ...rest] = recommendations;

  return (
    <>
      <AnalysisSummary recommendation={recommendation} />
      <BestMatch rec={best} />
      {rest.length > 0 && <OtherOptions recs={rest} />}
    </>
  );
}

// ── main component ────────────────────────────────────────────────────────────

const PackagingRecommender = () => {
  const navigate = useNavigate();
  const [showRecommender, setShowRecommender] = useState(false);
  const [formData, setFormData] = useState({
    productType: '',
    weight: '',
    length: '',
    width: '',
    height: '',
    fragility: 'low',
    currentPackaging: '',
  });
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [engineError, setEngineError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setRecommendation(null);
    setEngineError(null);
    try {
      const pL = Number(formData.length) / 2.54;
      const pW = Number(formData.width)  / 2.54;
      const pH = Number(formData.height) / 2.54;
      const isFragile = formData.fragility === 'high';

      let result = null;
      try {
        result = await recommendPackagingAPI({
          product_length: pL,
          product_width: pW,
          product_height: pH,
          is_fragile: isFragile,
          clearance_fraction: 0.10,
          top_n: 5,
        });
      } catch (apiErr) {
        // Fall back to client-side packagingEngine if backend is offline/unreachable
        console.warn('Backend recommendation API unavailable, using client-side engine:', apiErr.message);
        result = await recommendPackaging({
          productL: pL,
          productW: pW,
          productH: pH,
          isFragile: isFragile,
          clearanceFraction: 0.10,
          topN: 5,
        });
      }
      setRecommendation(result);
    } catch (err) {
      setEngineError(err.message || 'Failed to load packaging catalog.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // ── landing page (unchanged) ────────────────────────────────────────────────
  if (!showRecommender) {
    return (
      <div className="min-h-screen bg-eco-pattern bg-leaf-pattern" style={{ backgroundColor: 'var(--earth-gray)' }}>
        {/* Hero Section */}
        <div className="relative overflow-hidden hero-bg">
          <div className="relative max-w-7xl mx-auto px-4 py-20">
            <div className="text-center">
              <motion.div
                className="inline-flex items-center px-6 py-3 glass-effect rounded-full text-sm font-semibold mb-8 shadow-lg border"
                style={{ color: 'var(--forest-green)', borderColor: 'var(--mint-leaf)' }}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
              >
                <SparklesIcon className="w-4 h-4 mr-2" />
                AI-Powered Sustainability Platform
              </motion.div>
              <motion.h1
                className="text-5xl md:text-7xl font-bold mb-8"
                style={{ color: 'var(--charcoal-text)' }}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                Welcome to <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">Wrapture</span>
              </motion.h1>
              <motion.p
                className="text-xl mb-10 max-w-4xl mx-auto leading-relaxed font-medium"
                style={{ color: 'var(--charcoal-text)' }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                Revolutionary AI platform that optimizes packaging for environmental sustainability, cost-effectiveness, and carbon-conscious solutions. Reduce waste, save money, and create positive environmental impact through intelligent packaging decisions.
              </motion.p>
              <motion.div
                className="flex flex-col sm:flex-row gap-4 justify-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <Button
                  size="lg"
                  onClick={() => setShowRecommender(true)}
                  className="shadow-xl px-8 py-4 text-lg font-semibold"
                  style={{ backgroundColor: 'var(--eco-green)', borderColor: 'var(--forest-green)' }}
                >
                  Start Optimizing
                  <ArrowRightIcon className="ml-2 w-6 h-6" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => navigate('/simulator')}
                  className="shadow-lg px-8 py-4 text-lg font-semibold glass-effect"
                  style={{ borderColor: 'var(--sustainable-blue)', color: 'var(--sustainable-blue)' }}
                >
                  View Demo
                </Button>
              </motion.div>
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="py-12 stats-bg border-y" style={{ borderColor: 'var(--mint-leaf)' }}>
          <div className="max-w-7xl mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { val: '42,650+', label: 'ABO Products in Catalog',    color: 'var(--eco-green)' },
                { val: '2,209',   label: 'Packrift Packaging Records', color: 'var(--sustainable-blue)' },
                { val: '524',     label: 'Product Types Covered',      color: 'var(--forest-green)' },
                { val: '~87%',    label: 'Material Classifier Accuracy', color: 'var(--sustainable-blue)' },
              ].map(({ val, label, color }) => (
                <motion.div
                  key={label}
                  className="text-center p-6 rounded-xl glass-effect shadow-lg"
                  whileHover={{ scale: 1.05, y: -5 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <div className="text-3xl font-bold mb-2" style={{ color }}>{val}</div>
                  <div className="text-sm font-medium text-gray-600">{label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="py-16 bg-leaf-pattern">
          <div className="max-w-7xl mx-auto px-4">
            <div className="text-center mb-20">
              <motion.h2
                className="text-4xl font-bold mb-4 text-heading"
                style={{ color: 'var(--charcoal-text)' }}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                AI-Powered Packaging Innovation
              </motion.h2>
              <motion.p
                className="text-lg max-w-2xl mx-auto leading-relaxed text-gray-600"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                Revolutionary platform combining artificial intelligence, environmental consciousness, and cost optimization to transform e-commerce packaging decisions.
              </motion.p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { Icon: BoltIcon,      color: 'var(--eco-green)',         border: 'var(--mint-leaf)',  title: 'AI-Powered Optimization',    body: 'Advanced machine learning algorithms analyze product specifications to deliver intelligent, cost-effective packaging recommendations.' },
                { Icon: GlobeAltIcon,  color: 'var(--sustainable-blue)',  border: 'var(--sky-mist)',   title: 'Carbon Footprint Reduction',  body: 'Real-time tracking of CO₂ emissions, waste reduction metrics, and comprehensive environmental impact analytics.' },
                { Icon: UsersIcon,     color: 'var(--forest-green)',      border: 'var(--mint-leaf)',  title: 'EcoPoints Gamification',      body: 'Reward-based system with badges, leaderboards, and vendor coupons to incentivize sustainable packaging practices.' },
                { Icon: FlagIcon,      color: 'var(--sustainable-blue)',  border: 'var(--sky-mist)',   title: 'Dual Interface System',       body: 'Product-ID optimization for large sellers and Vision-based scanning for smaller artisanal businesses.' },
              ].map(({ Icon, color, border, title, body }) => (
                <motion.div
                  key={title}
                  className="glass-effect p-4 rounded-xl shadow-lg border"
                  style={{ borderColor: border }}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  whileHover={{ y: -4, scale: 1.01, transition: { duration: 0.3 } }}
                >
                  <motion.div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3 shadow-sm"
                    style={{ backgroundColor: color }}
                    whileHover={{ rotate: 10, scale: 1.1, transition: { duration: 0.2 } }}
                  >
                    <Icon className="w-4 h-4 text-white" />
                  </motion.div>
                  <h3 className="text-lg font-semibold mb-2 text-heading" style={{ color: 'var(--charcoal-text)' }}>{title}</h3>
                  <p className="text-sm leading-relaxed text-gray-600">{body}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* About Section */}
        <div className="py-20 relative">
          <div className="absolute inset-0 opacity-50">
            <div className="w-full h-full bg-gradient-to-r from-green-50 to-blue-50" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1441974231531-c6227db76b6e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80)', backgroundSize: 'cover', backgroundPosition: 'center', backgroundBlendMode: 'overlay' }}></div>
          </div>
          <div className="relative">
            <div className="max-w-7xl mx-auto px-4">
              <div className="grid lg:grid-cols-2 gap-16 items-center">
                <div>
                  <h2 className="text-4xl font-bold text-gray-900 mb-6">About Wrapture</h2>
                  <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                    Wrapture is the world's first AI-powered sustainable packaging assistant designed specifically for e-commerce sellers.
                    We combine cutting-edge artificial intelligence with environmental consciousness to help businesses make smarter packaging decisions.
                  </p>
                  <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                    Our platform offers everything from computer vision-based product scanning to 3D packaging simulation,
                    helping you visualize, optimize, and implement sustainable packaging solutions that benefit both your bottom line and the planet.
                  </p>
                  <div className="space-y-4">
                    {[
                      'Built on the real Amazon Berkeley Objects (ABO) product catalog',
                      'Uses the real Packrift packaging catalog (2,209 records)',
                      'MobileNetV2 material classifier trained on 2,616 images (~87% accuracy)',
                    ].map((t) => (
                      <div key={t} className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-4"></div>
                        <span className="text-gray-700">{t}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="relative">
                  <div className="bg-gradient-to-br from-green-400 to-emerald-600 rounded-2xl p-8 text-white">
                    <h3 className="text-2xl font-bold mb-4">Our Mission</h3>
                    <p className="text-green-100 mb-6">
                      To make sustainable packaging accessible, affordable, and intelligent for every e-commerce business,
                      creating a positive environmental impact at scale.
                    </p>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <div className="text-3xl font-bold">42,650+</div>
                        <div className="text-green-200 text-sm">ABO Products</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold">~87%</div>
                        <div className="text-green-200 text-sm">Material Classifier Accuracy</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-24 bg-gradient-to-r from-green-600 via-blue-600 to-green-700 relative overflow-hidden">
          <div className="absolute inset-0 opacity-20">
            <div className="w-full h-full bg-gradient-to-tr from-white/10 to-transparent"></div>
          </div>
          <div className="max-w-5xl mx-auto text-center px-4 relative">
            <motion.h2
              className="text-5xl md:text-6xl font-bold text-white mb-8"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              Transform E-commerce Packaging
            </motion.h2>
            <motion.p
              className="text-xl text-green-100 mb-10 max-w-3xl mx-auto leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Join the revolution in sustainable packaging. Reduce waste, optimize costs, and create positive environmental impact through intelligent AI-driven solutions.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Button
                size="lg"
                onClick={() => setShowRecommender(true)}
                className="bg-white hover:bg-gray-50 shadow-2xl px-10 py-5 text-xl font-bold"
                style={{ color: 'var(--forest-green)' }}
              >
                Begin Optimization
                <ArrowRightIcon className="ml-3 w-6 h-6" />
              </Button>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  // ── recommender tool ────────────────────────────────────────────────────────
  return (
    <div className="pr-page">
      {/* Top bar */}
      <div className="pr-topbar">
        <div className="pr-topbar-title">
          <CubeIcon style={{ width: 22, height: 22, color: 'var(--forest-green)' }} />
          <h1>Packaging Recommender</h1>
          <span>Packrift catalog · 2,209 records</span>
        </div>
        <button className="pr-back-btn" onClick={() => setShowRecommender(false)}>
          ← Back
        </button>
      </div>

      <div className="pr-layout">
        {/* ── Input card ── */}
        <div className="pr-input-card">
          <div className="pr-card-heading">
            <CubeIcon style={{ width: 18, height: 18 }} />
            Product Details
          </div>

          <form onSubmit={handleSubmit}>
            <div className="pr-form-group">
              <label className="pr-label">Product Type</label>
              <select
                name="productType"
                value={formData.productType}
                onChange={handleChange}
                className="pr-select"
                required
              >
                <option value="">Select type</option>
                <option value="electronics">Electronics</option>
                <option value="clothing">Clothing</option>
                <option value="books">Books</option>
                <option value="cosmetics">Cosmetics</option>
                <option value="food">Food Items</option>
                <option value="fragile">Fragile Items</option>
              </select>
            </div>

            <div className="pr-row-2 pr-form-group">
              <div>
                <label className="pr-label">Weight (kg)</label>
                <input
                  type="number"
                  name="weight"
                  value={formData.weight}
                  onChange={handleChange}
                  className="pr-input"
                  placeholder="0.5"
                  step="0.1"
                  required
                />
              </div>
              <div>
                <label className="pr-label">Fragility</label>
                <select
                  name="fragility"
                  value={formData.fragility}
                  onChange={handleChange}
                  className="pr-select"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div className="pr-form-group">
              <label className="pr-label">Dimensions (cm) — L × W × H</label>
              <div className="pr-dims-row">
                <input
                  type="number"
                  name="length"
                  value={formData.length}
                  onChange={handleChange}
                  className="pr-input"
                  placeholder="L"
                  required
                />
                <span className="pr-dims-sep">×</span>
                <input
                  type="number"
                  name="width"
                  value={formData.width}
                  onChange={handleChange}
                  className="pr-input"
                  placeholder="W"
                  required
                />
                <span className="pr-dims-sep">×</span>
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  className="pr-input"
                  placeholder="H"
                  required
                />
              </div>
            </div>

            <div className="pr-form-group">
              <label className="pr-label">Current Packaging</label>
              <input
                type="text"
                name="currentPackaging"
                value={formData.currentPackaging}
                onChange={handleChange}
                className="pr-input"
                placeholder="e.g. Plastic bubble wrap"
              />
            </div>

            <button type="submit" disabled={loading} className="pr-submit-btn">
              {loading
                ? <><span className="pr-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Analyzing…</>
                : <><FireIcon style={{ width: 16, height: 16 }} /> Get Recommendation</>}
            </button>
          </form>
        </div>

        {/* ── Right panel ── */}
        <div>
          {!loading && !recommendation && !engineError && (
            <div className="pr-empty-state">
              <CubeIcon style={{ width: 48, height: 48 }} />
              <p>Enter product details and click<br /><strong>Get Recommendation</strong> to begin.</p>
            </div>
          )}

          {loading && (
            <div className="pr-loading">
              <div className="pr-spinner" />
              <span>Evaluating catalog…</span>
            </div>
          )}

          {engineError && !loading && (
            <div className="pr-error">
              <strong>Error:</strong> {engineError}
            </div>
          )}

          {recommendation && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
            >
              <ResultsPanel recommendation={recommendation} />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PackagingRecommender;
