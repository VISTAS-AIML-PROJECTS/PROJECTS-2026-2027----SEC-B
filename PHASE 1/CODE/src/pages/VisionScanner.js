import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Camera,
  Package,
  Brain,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Sparkles,
  Layers,
  Scale,
} from 'lucide-react';
import { analyzeVision, analyzeMaterial, getApiBaseUrl } from '../utils/api';

/**
 * VisionScanner
 *
 * Full pipeline:
 * 1. YOLO11s detects product bounding box and category
 * 2. ABO lookup resolves representative dimensions and weight from Amazon Berkeley Objects catalog
 * 3. MobileNetV2 classifies packaging material and confidence
 * 4. Packrift packaging engine recommends best physical fit
 *
 * Direct navigation to /eco-shop?sku=XYZ highlights the exact recommended SKU.
 */

const VisionScanner = () => {
  const navigate = useNavigate();

  const [useCamera, setUseCamera] = useState(true);
  const [cameraError, setCameraError] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedDetIdx, setSelectedDetIdx] = useState(0);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const overlayRef = useRef(null);
  const previewRef = useRef(null);

  // ── Camera ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!useCamera) return;
    let stream;
    (async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error('Camera access is not supported by this browser.');
        }
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (err) {
        setCameraError('Camera could not be started: ' + err.message);
      }
    })();
    return () => {
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, [useCamera]);

  // ── Bounding box overlay ─────────────────────────────────────────────────────

  const drawBoxes = useCallback((detections, highlightIdx) => {
    const canvas = overlayRef.current;
    const img = previewRef.current;
    if (!canvas || !img || !detections?.length) return;

    const { offsetWidth: dw, offsetHeight: dh } = img;
    const { naturalWidth: nw, naturalHeight: nh } = img;
    canvas.width = dw;
    canvas.height = dh;
    const scaleX = dw / nw;
    const scaleY = dh / nh;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, dw, dh);

    detections.forEach((det, i) => {
      const { x1, y1, x2, y2 } = det.bbox;
      const sx1 = x1 * scaleX;
      const sy1 = y1 * scaleY;
      const sw = (x2 - x1) * scaleX;
      const sh = (y2 - y1) * scaleY;
      const isSelected = i === highlightIdx;

      ctx.strokeStyle = isSelected ? '#2e4a3a' : '#94a3b8';
      ctx.lineWidth = isSelected ? 3 : 1.5;
      ctx.strokeRect(sx1, sy1, sw, sh);

      const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = 'bold 11px sans-serif';
      const tw = ctx.measureText(label).width + 8;
      ctx.fillStyle = isSelected ? '#2e4a3a' : '#94a3b8';
      ctx.fillRect(sx1, sy1 - 18, tw, 18);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, sx1 + 4, sy1 - 4);
    });
  }, []);

  useEffect(() => {
    if (result?.detections?.length) {
      setTimeout(() => drawBoxes(result.detections, selectedDetIdx), 50);
    }
  }, [result, selectedDetIdx, drawBoxes, imagePreview]);

  // ── Capture ──────────────────────────────────────────────────────────────────

  const captureFromCamera = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
      setImageFile(file);
      setImagePreview(URL.createObjectURL(blob));
      setResult(null);
      setError(null);
      setSelectedDetIdx(0);
    }, 'image/jpeg', 0.92);
  };

  // ── File upload ──────────────────────────────────────────────────────────────

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setResult(null);
    setError(null);
    setSelectedDetIdx(0);
  };

  // ── Analyse ──────────────────────────────────────────────────────────────────

  const handleAnalyze = async () => {
    if (!imageFile) return;
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      const data = await analyzeVision(imageFile);
      setResult(data);
      setSelectedDetIdx(0);
    } catch (err) {
      setError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : err.message
      );
    } finally {
      setScanning(false);
    }
  };

  const handleMaterialOnly = async () => {
    if (!imageFile) return;
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      const data = await analyzeMaterial(imageFile);
      setResult({ status: 'MATERIAL_ONLY', material: data });
    } catch (err) {
      setError(
        err.message.includes('Failed to fetch')
          ? 'Cannot reach the Wrapture backend. Make sure Flask is running on port 5000.'
          : err.message
      );
    } finally {
      setScanning(false);
    }
  };

  const handleSelectDetection = async (idx) => {
    if (!imageFile || idx === selectedDetIdx) return;
    setSelectedDetIdx(idx);
    setScanning(true);
    try {
      const fd = new FormData();
      fd.append('image', imageFile);
      const BASE = getApiBaseUrl();
      const res = await fetch(`${BASE}/api/vision/analyze?detection_index=${idx}`, {
        method: 'POST',
        body: fd,
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  };

  // ── Render Results ───────────────────────────────────────────────────────────

  const renderDetection = () => {
    if (!result) return null;

    if (result.status === 'PRODUCT_DETECTOR_UNAVAILABLE') {
      return (
        <div className="p-5 bg-amber-50 border border-amber-200 rounded-2xl text-amber-800">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-serif text-[16px] font-semibold text-amber-900">Product Detector Notice</p>
              <p className="text-[13px] text-amber-800 mt-1">{result.error}</p>
            </div>
          </div>
        </div>
      );
    }

    if (result.status === 'NO_PRODUCT_DETECTED') {
      return (
        <div className="p-5 bg-surface-container-low border border-outline-variant/30 rounded-2xl text-on-surface-variant text-[13px] text-center">
          <Package className="w-10 h-10 text-on-surface-variant/40 mx-auto mb-2" />
          <p className="font-serif text-[16px] font-medium text-primary">No product detected in this image</p>
          <p className="mt-1">Try capturing or uploading a clearer image with the product centred in good lighting.</p>
        </div>
      );
    }

    const detections = result.detections || [];
    const selectedDet = detections[selectedDetIdx] || result.selected_detection;
    const prod = result.product;
    const dims = prod?.dimensions;
    const mat = result.material;
    const pack = result.packaging;
    const topRec = pack?.recommendations?.[0];

    return (
      <div className="space-y-4">
        {/* Multi-detection selector if multiple objects found */}
        {detections.length > 1 && (
          <div className="bg-surface-container-low rounded-2xl p-4 border border-outline-variant/30">
            <span className="font-label-caps text-[10px] tracking-wider uppercase text-secondary font-bold block mb-2">
              Detected Objects ({detections.length}) — Tap to select
            </span>
            <div className="flex flex-wrap gap-2">
              {detections.map((det, i) => (
                <button
                  key={i}
                  onClick={() => handleSelectDetection(i)}
                  className={`py-1.5 px-3 rounded-xl text-[12px] font-medium transition-colors border cursor-pointer ${
                    i === selectedDetIdx
                      ? 'bg-primary text-surface border-primary font-semibold shadow-xs'
                      : 'bg-surface text-primary border-outline-variant/30 hover:bg-surface-container'
                  }`}
                >
                  <span>{det.class_name}</span>
                  <span className="ml-1.5 opacity-75">{(det.confidence * 100).toFixed(0)}%</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── 1. DETECTED PRODUCT ── */}
        <div className="bg-surface-container-low rounded-2xl p-4.5 border border-outline-variant/30 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-surface flex items-center justify-center text-primary shadow-2xs border border-outline-variant/20">
                <Brain className="w-4 h-4 text-secondary" />
              </span>
              <span className="font-label-caps text-[11px] uppercase tracking-wider text-secondary font-bold">
                1. DETECTED PRODUCT
              </span>
            </div>
            <span className="font-label-mono-data text-[11px] font-bold text-secondary">
              YOLO11s Model
            </span>
          </div>

          <div className="bg-surface rounded-xl p-3.5 border border-outline-variant/20 grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Product Category</span>
              <span className="font-serif text-[17px] text-primary font-medium capitalize">
                {selectedDet?.class_name || 'Object'}
              </span>
            </div>
            <div>
              <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Detection Confidence</span>
              <span className="font-label-mono-data text-[17px] font-bold text-primary">
                {selectedDet?.confidence != null ? `${(selectedDet.confidence * 100).toFixed(1)}%` : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* ── 2. PRODUCT DETAILS (Real ABO Data) ── */}
        <div className="bg-surface-container-low rounded-2xl p-4.5 border border-outline-variant/30 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-surface flex items-center justify-center text-primary shadow-2xs border border-outline-variant/20">
                <Scale className="w-4 h-4 text-secondary" />
              </span>
              <span className="font-label-caps text-[11px] uppercase tracking-wider text-secondary font-bold">
                2. PRODUCT DETAILS
              </span>
            </div>
            <span className="font-label-mono-data text-[10px] text-on-surface-variant">
              Amazon Berkeley Objects
            </span>
          </div>

          {prod && !prod.status ? (
            <div className="space-y-3">
              <div className="bg-surface rounded-xl p-3.5 border border-outline-variant/20">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Length</span>
                    <span className="font-label-mono-data font-bold text-primary text-[14px]">
                      {dims?.length_in != null ? `${dims.length_in.toFixed(2)} in` : <span className="text-on-surface-variant/70 italic font-normal text-[11px]">Not available in ABO</span>}
                    </span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Width</span>
                    <span className="font-label-mono-data font-bold text-primary text-[14px]">
                      {dims?.width_in != null ? `${dims.width_in.toFixed(2)} in` : <span className="text-on-surface-variant/70 italic font-normal text-[11px]">Not available in ABO</span>}
                    </span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Height</span>
                    <span className="font-label-mono-data font-bold text-primary text-[14px]">
                      {dims?.height_in != null ? `${dims.height_in.toFixed(2)} in` : <span className="text-on-surface-variant/70 italic font-normal text-[11px]">Not available in ABO</span>}
                    </span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Weight</span>
                    <span className="font-label-mono-data font-bold text-primary text-[14px]">
                      {prod.weight != null ? (
                        `${Number(prod.weight).toFixed(2)} ${prod.weight_unit || 'lb'}`
                      ) : (
                        <span className="text-on-surface-variant/70 italic font-normal text-[11px]">Not available in ABO</span>
                      )}
                    </span>
                  </div>
                </div>

                {prod.item_name && (
                  <div className="mt-3 pt-2.5 border-t border-outline-variant/15 text-[11px] text-on-surface-variant flex items-center justify-between">
                    <span className="truncate max-w-[70%]">ABO Catalog: {prod.item_name}</span>
                    {prod.item_id && <span className="font-label-mono-data text-[10px] opacity-75">{prod.item_id}</span>}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-surface rounded-xl p-3.5 border border-outline-variant/20 text-xs text-on-surface-variant">
              <span>Not available in ABO for detected category "{selectedDet?.class_name}".</span>
            </div>
          )}
        </div>

        {/* ── 3. MATERIAL CLASSIFICATION ── */}
        {mat && !mat.error && (
          <div className="bg-surface-container-low rounded-2xl p-4.5 border border-outline-variant/30 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded-lg bg-surface flex items-center justify-center text-primary shadow-2xs border border-outline-variant/20">
                  <Layers className="w-4 h-4 text-secondary" />
                </span>
                <span className="font-label-caps text-[11px] uppercase tracking-wider text-secondary font-bold">
                  3. MATERIAL CLASSIFICATION
                </span>
              </div>
              <span className="font-label-mono-data text-[10px] text-on-surface-variant">
                MobileNetV2
              </span>
            </div>

            <div className="bg-surface rounded-xl p-3.5 border border-outline-variant/20">
              <div className="flex items-center justify-between mb-2">
                <span className="font-serif text-[17px] text-primary font-medium capitalize">
                  {mat.predicted_class?.replace(/_/g, ' ') || 'Unknown'}
                </span>
                <span className="font-label-mono-data text-[14px] font-bold text-secondary">
                  {mat.confidence != null ? `${(mat.confidence * 100).toFixed(1)}% confidence` : '—'}
                </span>
              </div>

              {/* Confidence bars */}
              {mat.all_classes && (
                <div className="space-y-1.5 pt-2 border-t border-outline-variant/15">
                  {mat.all_classes.slice(0, 3).map((c) => (
                    <div key={c.class} className="flex items-center gap-2 text-xs">
                      <span className="w-28 text-[11px] text-on-surface-variant truncate capitalize">
                        {c.class.replace(/_/g, ' ')}
                      </span>
                      <div className="flex-1 bg-surface-container rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-secondary h-1.5 rounded-full"
                          style={{ width: `${(c.confidence * 100).toFixed(1)}%` }}
                        />
                      </div>
                      <span className="font-label-mono-data text-[10px] text-on-surface-variant w-10 text-right">
                        {(c.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── 4. PACKAGING RECOMMENDATION ── */}
        {pack && pack.status !== 'NO_PHYSICAL_FIT' && topRec && (
          <div className="bg-surface-container-high rounded-2xl p-5 border-2 border-secondary/50 shadow-md">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-surface shadow-xs">
                  <span className="material-symbols-outlined text-[18px] text-secondary-fixed">auto_awesome</span>
                </span>
                <div>
                  <span className="font-label-caps text-[10px] tracking-wider uppercase text-secondary font-bold block">
                    4. PACKAGING RECOMMENDATION
                  </span>
                  <span className="font-serif text-[15px] font-medium text-primary">
                    Best Matching Real Packrift Package
                  </span>
                </div>
              </div>
              <span className="font-label-mono-data text-[11px] px-2 py-0.5 rounded-full bg-surface text-primary border border-outline-variant/30 font-semibold">
                SKU: {topRec.sku}
              </span>
            </div>

            {/* Recommendation card */}
            <div className="bg-surface rounded-xl p-4 border border-outline-variant/30 shadow-xs space-y-3">
              <div>
                <h4 className="font-serif text-[17px] text-primary font-semibold leading-snug">
                  {topRec.title || 'Packrift Carton'}
                </h4>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {topRec.family && (
                    <span className="font-label-caps text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-bold uppercase">
                      {topRec.family}
                    </span>
                  )}
                  {topRec.material && (
                    <span className="font-label-caps text-[10px] px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-bold uppercase">
                      {topRec.material}
                    </span>
                  )}
                  {topRec.space_utilization != null && (
                    <span className="font-label-caps text-[10px] px-2 py-0.5 rounded-full bg-surface-container text-primary font-bold">
                      {(topRec.space_utilization * 100).toFixed(1)}% space utilization
                    </span>
                  )}
                </div>
              </div>

              {/* Physical specifications */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-3 border-t border-outline-variant/20 text-xs">
                <div>
                  <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Dimensions</span>
                  <span className="font-label-mono-data font-bold text-primary">
                    {topRec.package_length_in} × {topRec.package_width_in} × {topRec.package_height_in} in
                  </span>
                </div>
                <div>
                  <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Unit Price</span>
                  <span className="font-serif text-[15px] font-bold text-primary">
                    {topRec.unit_price != null ? `$${topRec.unit_price.toFixed(2)}` : 'Price unavailable'}
                  </span>
                </div>
                <div>
                  <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Pack Quantity</span>
                  <span className="font-label-mono-data font-medium text-primary">
                    {topRec.pack_quantity ? `${topRec.pack_quantity} units` : 'Not specified'}
                  </span>
                </div>
                <div>
                  <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Recycling CO₂e</span>
                  <span className="font-label-mono-data font-semibold text-secondary truncate block">
                    {topRec.co2e_recycling_mt != null
                      ? `${(Math.abs(topRec.co2e_recycling_mt) * 1000).toFixed(4)} kg avoided`
                      : 'Not available'}
                  </span>
                </div>
              </div>

              {/* Protection */}
              <div className="pt-2 border-t border-outline-variant/15 text-xs text-on-surface-variant flex items-center justify-between">
                <span className="text-[11px] font-label-caps uppercase">Protection:</span>
                <span className="font-body-sm font-medium text-primary">
                  {topRec.protection_evidence?.length
                    ? topRec.protection_evidence.join(', ')
                    : topRec.protection_score != null
                    ? `Level ${topRec.protection_score} / 3`
                    : 'Not specified'}
                </span>
              </div>
            </div>

            {/* ── BUTTON: View Recommended Packaging (Deep Link to EcoShop) ── */}
            <div className="pt-3 flex flex-col sm:flex-row gap-2.5">
              <button
                id="view-recommended-packaging-btn"
                onClick={() => navigate(`/eco-shop?sku=${encodeURIComponent(topRec.sku)}`)}
                className="flex-1 py-3 px-4 bg-primary hover:bg-primary-container text-surface rounded-xl font-body-sm text-[13px] font-semibold flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer"
              >
                <span>View Recommended Packaging</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              {topRec.canonical_product_url && (
                <a
                  href={topRec.canonical_product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="py-3 px-4 bg-surface text-primary border border-outline-variant/30 rounded-xl font-body-sm text-[13px] font-medium flex items-center justify-center gap-1.5 hover:bg-surface-container transition-colors"
                >
                  <span>View on Packrift</span>
                  <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                </a>
              )}
            </div>
          </div>
        )}

        {pack?.status === 'NO_PHYSICAL_FIT' && (
          <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-2xl text-on-surface-variant text-sm">
            No packaging in the catalog fits these product dimensions with 10% clearance.
          </div>
        )}

        {/* Material-only view */}
        {result.status === 'MATERIAL_ONLY' && mat && !mat.error && (
          <div className="p-4 bg-surface-container-low border border-outline-variant/30 rounded-2xl">
            <h3 className="font-serif text-[17px] text-primary font-medium mb-1">
              Material Classification Result
            </h3>
            <p className="text-sm font-semibold text-secondary">
              {mat.predicted_class} ({(mat.confidence * 100).toFixed(1)}%)
            </p>
          </div>
        )}
      </div>
    );
  };

  // ── Main Layout ─────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col w-full min-h-full bg-surface pb-safe-nav">
      <div className="flex flex-col w-full px-4 md:px-6 space-y-4 pb-12">
        {/* Header */}
        <section className="pt-3 flex flex-col gap-1">
          <span className="font-label-caps text-[11px] tracking-[0.2em] text-secondary font-bold uppercase">
            ATELIER COMPUTER VISION
          </span>
          <h1 className="font-serif text-[28px] md:text-[34px] text-primary font-medium tracking-tight">
            AI Product Scanner
          </h1>
          <p className="font-body-sm text-[13px] text-on-surface-variant">
            Capture or upload a product photograph. The AI pipeline runs YOLO detection, ABO catalog sizing, MobileNetV2 material analysis, and Packrift recommendation.
          </p>
        </section>

        {/* Mode Toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => {
              setUseCamera(true);
              setImageFile(null);
              setImagePreview(null);
              setResult(null);
              setError(null);
            }}
            className={`py-2 px-4 rounded-xl text-[13px] font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
              useCamera
                ? 'bg-primary text-surface font-semibold shadow-xs'
                : 'bg-surface-container-low text-primary border border-outline-variant/30 hover:bg-surface-container'
            }`}
          >
            <Camera className="w-4 h-4" />
            <span>Camera</span>
          </button>
          <button
            onClick={() => {
              setUseCamera(false);
              setResult(null);
              setError(null);
            }}
            className={`py-2 px-4 rounded-xl text-[13px] font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
              !useCamera
                ? 'bg-primary text-surface font-semibold shadow-xs'
                : 'bg-surface-container-low text-primary border border-outline-variant/30 hover:bg-surface-container'
            }`}
          >
            <Upload className="w-4 h-4" />
            <span>Upload Photo</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* Input Card */}
          <div className="bg-surface-container-low rounded-2xl p-4.5 border border-outline-variant/30 shadow-xs">
            {useCamera ? (
              <div className="space-y-3">
                {cameraError ? (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs">
                    {cameraError}
                  </div>
                ) : (
                  <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3] w-full">
                    <video
                      ref={videoRef}
                      className="w-full h-full object-cover"
                      playsInline
                      muted
                    />
                  </div>
                )}
                <canvas ref={canvasRef} className="hidden" />
                <button
                  id="capture-photo-btn"
                  onClick={captureFromCamera}
                  disabled={!!cameraError}
                  className="w-full py-3 bg-primary text-surface rounded-xl font-body-sm text-[13px] font-medium flex items-center justify-center gap-2 hover:bg-primary-container shadow-xs cursor-pointer active:scale-[0.99]"
                >
                  <Camera className="w-4 h-4" />
                  <span>Capture Photo</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-outline-variant/50 rounded-xl p-8 text-center cursor-pointer hover:border-secondary transition-colors bg-surface"
                >
                  <Upload className="h-10 w-10 text-on-surface-variant/40 mx-auto mb-2" />
                  <p className="font-serif text-[15px] text-primary font-medium">Click to select an image</p>
                  <p className="text-[11px] text-on-surface-variant mt-1">JPG, PNG, WEBP up to 10MB</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            )}

            {/* Preview with Bounding Box Canvas */}
            {imagePreview && (
              <div className="mt-4 pt-4 border-t border-outline-variant/20">
                <span className="font-label-caps text-[10px] tracking-wider uppercase text-on-surface-variant block mb-2">
                  Captured Image &amp; Detection Overlay
                </span>
                <div className="relative rounded-xl overflow-hidden bg-surface-container aspect-[4/3] w-full border border-outline-variant/30">
                  <img
                    ref={previewRef}
                    src={imagePreview}
                    alt="Scan preview"
                    className="w-full h-full object-contain"
                    onLoad={() => {
                      if (result?.detections?.length) drawBoxes(result.detections, selectedDetIdx);
                    }}
                  />
                  <canvas
                    ref={overlayRef}
                    className="absolute inset-0 pointer-events-none"
                    style={{ width: '100%', height: '100%' }}
                  />
                </div>
              </div>
            )}

            {/* Analysis Trigger Buttons */}
            {imageFile && (
              <div className="mt-4 flex gap-2">
                <button
                  id="run-full-analysis-btn"
                  onClick={handleAnalyze}
                  disabled={scanning}
                  className="flex-1 py-3 px-4 bg-primary hover:bg-primary-container text-surface rounded-xl font-body-sm text-[13px] font-semibold flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer active:scale-[0.99] disabled:opacity-50"
                >
                  {scanning ? (
                    <>
                      <span className="material-symbols-outlined text-[18px] animate-spin">sync</span>
                      <span>Running AI Pipeline…</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-secondary-fixed" />
                      <span>Run Full Analysis</span>
                    </>
                  )}
                </button>
                <button
                  id="material-only-btn"
                  onClick={handleMaterialOnly}
                  disabled={scanning}
                  title="Classify material only with MobileNetV2"
                  className="py-3 px-4 bg-surface-container text-primary rounded-xl font-body-sm text-[13px] font-medium border border-outline-variant/30 hover:bg-surface-container-high transition-colors"
                >
                  <Brain className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Results Side Panel */}
          <div>
            {!imageFile && !scanning && !result && !error && (
              <div className="bg-surface-container-low rounded-2xl p-8 border border-outline-variant/30 text-center flex flex-col items-center justify-center min-h-[300px]">
                <div className="w-12 h-12 rounded-2xl bg-surface flex items-center justify-center text-primary shadow-xs border border-outline-variant/30 mb-3">
                  <Camera className="w-6 h-6 text-secondary" />
                </div>
                <h3 className="font-serif text-[18px] text-primary font-medium">Ready to scan</h3>
                <p className="font-body-sm text-[13px] text-on-surface-variant mt-1 max-w-xs">
                  Capture or upload a photo to identify category, ABO physical dimensions, material, and recommended packaging.
                </p>
              </div>
            )}

            {scanning && (
              <div className="bg-surface-container-low rounded-2xl p-10 border border-outline-variant/30 text-center flex flex-col items-center justify-center min-h-[300px]">
                <span className="material-symbols-outlined text-[36px] text-secondary animate-spin mb-3">
                  progress_activity
                </span>
                <h3 className="font-serif text-[18px] text-primary font-medium">Processing Image</h3>
                <p className="font-body-sm text-[12px] text-on-surface-variant mt-1">
                  Executing YOLO detection → ABO catalog lookup → MobileNetV2 material classification…
                </p>
              </div>
            )}

            {error && (
              <div className="p-5 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm">
                <strong>Error:</strong> {error}
              </div>
            )}

            {result && !scanning && renderDetection()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisionScanner;
