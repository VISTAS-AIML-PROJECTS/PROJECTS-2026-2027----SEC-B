import React, { useState, useEffect, useRef } from 'react';
import { 
  Video, 
  Layers, 
  Gauge, 
  CreditCard, 
  Sparkles, 
  Route, 
  Upload, 
  Camera, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw,
  Eye,
  ShieldAlert,
  Play,
  FileCheck,
  X,
  Clock,
  Film
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveHUD({ onSelectTruck }) {
  const [telemetry, setTelemetry] = useState(null);
  const [overlays, setOverlays] = useState({
    bboxes: true,
    speed: true,
    plates: true,
    vit: true,
    trajectories: true
  });
  const [source, setSource] = useState('SIMULATED');
  const [streamKey, setStreamKey] = useState(Date.now());
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedVideoInfo, setUploadedVideoInfo] = useState(null);
  const [localVideoUrl, setLocalVideoUrl] = useState(null);
  const [viewMode, setViewMode] = useState('AI_STREAM'); // 'AI_STREAM', 'RAW_PREVIEW', 'SPLIT_SCREEN'
  const [uploadToast, setUploadToast] = useState(null);
  const fileInputRef = useRef(null);
  const videoPlayerRef = useRef(null);

  // Batch Video Analyzer Modal State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);

  // Autoplay video preview when source or viewMode updates
  useEffect(() => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.muted = true;
      const playPromise = videoPlayerRef.current.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          // Autoplay policy handled gracefully
        });
      }
    }
  }, [localVideoUrl, uploadedVideoInfo, viewMode]);

  // Poll Telemetry at 4Hz (every 250ms) without overriding active uploaded video source
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const data = await api.getTelemetry();
        setTelemetry(data);
        if (data.overlays) {
          setOverlays(data.overlays);
        }
        // Only update source if not viewing custom uploaded video and not currently uploading
        setSource(prev => {
          if (prev === 'VIDEO_FILE' || isUploading) {
            return prev;
          }
          return data.active_source || prev;
        });
      } catch (err) {
        console.error('Telemetry fetch error:', err);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 500);
    return () => clearInterval(interval);
  }, [isUploading]);

  const handleToggleOverlay = async (key) => {
    const updated = { ...overlays, [key]: !overlays[key] };
    setOverlays(updated);
    try {
      await api.toggleOverlays({ [key]: updated[key] });
    } catch (e) {
      console.error('Failed to toggle overlay:', e);
    }
  };

  const handleSourceChange = async (newSource) => {
    try {
      await api.setCameraSource(newSource);
      setSource(newSource);
      setStreamKey(Date.now()); // Reconnect video feed stream
      if (newSource === 'SIMULATED') {
        if (localVideoUrl) {
          try { URL.revokeObjectURL(localVideoUrl); } catch (_) {}
        }
        setUploadedVideoInfo(null);
        setLocalVideoUrl(null);
        setViewMode('AI_STREAM');
      }
    } catch (e) {
      console.error('Failed to change camera source:', e);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 1. Create immediate local Object URL for instant 0ms HTML5 preview
    if (localVideoUrl) {
      try { URL.revokeObjectURL(localVideoUrl); } catch (_) {}
    }
    const previewBlobUrl = URL.createObjectURL(file);
    setLocalVideoUrl(previewBlobUrl);
    setSource('VIDEO_FILE');
    setViewMode('AI_STREAM'); // Display full AI HUD stream by default (no automatic split screen)

    setIsUploading(true);
    setUploadToast(`Uploading "${file.name}" to AI surveillance pipeline...`);

    try {
      const res = await api.uploadVideo(file);
      setUploadedVideoInfo({
        filename: res.filename,
        video_url: res.video_url || previewBlobUrl,
        metadata: res.metadata
      });
      setStreamKey(Date.now()); // Force MJPEG stream reconnection immediately
      setUploadToast(`Video "${res.filename}" uploaded successfully! Real-time AI stream active.`);
      setTimeout(() => setUploadToast(null), 5000);
    } catch (err) {
      console.error('Upload error:', err);
      setUploadToast(`Video playing in local preview. Pipeline warning: ${err.message || 'Connecting...'}`);
      setTimeout(() => setUploadToast(null), 6000);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleRunFullVideoScan = async (file = null) => {
    setIsAnalyzing(true);
    setShowAnalysisModal(true);
    try {
      const target = file || (uploadedVideoInfo?.filename) || null;
      const res = await api.analyzeVideo(target);
      setAnalysisResult(res);
      setStreamKey(Date.now());
    } catch (err) {
      alert('Video analysis error: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const hasCriticalAlert = telemetry?.active_tracks?.some(
    t => t.is_blocklisted || t.is_overspeed || t.police_action_required === 'DESTROY_VEHICLE_SCRAP'
  );

  const activeRawVideoSrc = localVideoUrl || uploadedVideoInfo?.video_url;

  return (
    <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* Upload Toast Banner */}
      {uploadToast && (
        <div className="glass-panel" style={{ 
          padding: '10px 18px', 
          backgroundColor: 'rgba(6, 78, 59, 0.85)',
          border: '1px solid #10b981',
          borderRadius: '8px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          color: '#ecfdf5',
          fontSize: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CheckCircle2 size={20} color="#34d399" />
            <span><strong>Video Stream Online:</strong> {uploadToast}</span>
          </div>
          <button onClick={() => setUploadToast(null)} style={{ background: 'none', border: 'none', color: '#ecfdf5', cursor: 'pointer' }}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Critical Alert Strobe Banner */}
      {hasCriticalAlert && (
        <div className="glass-panel-danger animate-siren" style={{ 
          padding: '10px 20px', 
          borderRadius: '8px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <ShieldAlert size={24} color="#ef4444" className="animate-pulse-glow" />
            <div>
              <span style={{ fontWeight: 700, color: '#f87171', fontSize: '0.95rem' }}>
                ACTIVE SURVEILLANCE THREAT / POLICE SCRAP MANDATE / SPEED VIOLATION DETECTED
              </span>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#fca5a5' }}>
                One or more heavy vehicles currently in camera view exceed safety limits, have expired Fitness Certificates (≥15yr Scrap Order), or match security blocklists.
              </p>
            </div>
          </div>
          <span className="badge badge-danger">REAL-TIME INTERCEPTION ACTIVE</span>
        </div>
      )}

      {/* Main Grid: Video Stream (Left) + Active Telemetry & Controls (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '16px', alignItems: 'start' }}>
        
        {/* Left Column: Live Video Canvas */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          
          {/* Stream Header & Controls */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: '#10b981'
              }} className="animate-pulse-glow" />
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f8fafc' }}>
                {source === 'VIDEO_FILE' ? `VIDEO FILE AI STREAM [${uploadedVideoInfo?.filename || 'CUSTOM VIDEO'}]` : 'LIVE AI SURVEILLANCE FEED [1080p HD]'}
              </span>
              <span className="badge badge-info font-mono">
                {telemetry ? `${telemetry.fps} FPS` : 'CONNECTING...'}
              </span>
            </div>

            {/* Source Switcher Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                onClick={() => handleSourceChange('SIMULATED')}
                className={source === 'SIMULATED' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                style={{ padding: '5px 10px', fontSize: '0.76rem' }}
              >
                Highway Sim
              </button>
              <button
                onClick={() => handleSourceChange('WEBCAM')}
                className={source === 'WEBCAM' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                style={{ padding: '5px 10px', fontSize: '0.76rem' }}
              >
                <Camera size={13} /> Webcam
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className={source === 'VIDEO_FILE' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                style={{ padding: '5px 10px', fontSize: '0.76rem' }}
                disabled={isUploading}
                title="Upload MP4, AVI, MKV, MOV video for AI analysis"
              >
                <Upload size={13} /> {isUploading ? 'Uploading...' : 'Upload Video'}
              </button>
              <button
                onClick={() => handleRunFullVideoScan()}
                className="btn-cyber-outline"
                style={{ padding: '5px 10px', fontSize: '0.76rem', borderColor: '#a855f7', color: '#d8b4fe' }}
                title="Scan entire video offline and generate vehicle dossiers"
              >
                <Film size={13} /> Full Video Scan
              </button>
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept="video/mp4,video/avi,video/mkv,video/mov,video/webm,video/*"
                onChange={handleFileUpload}
              />
            </div>
          </div>

          {/* Video Preview Mode Selector (Active when a video file is loaded) */}
          {source === 'VIDEO_FILE' && activeRawVideoSrc && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '10px',
              background: 'rgba(15, 23, 42, 0.85)',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              fontSize: '0.78rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <Film size={14} color="#38bdf8" />
                <span style={{ color: '#94a3b8' }}>Preview Mode:</span>
                <button
                  onClick={() => setViewMode('AI_STREAM')}
                  className={viewMode === 'AI_STREAM' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                  style={{ padding: '3px 9px', fontSize: '0.74rem' }}
                >
                  🛰️ Full AI HUD Stream
                </button>
                <button
                  onClick={() => setViewMode('RAW_PREVIEW')}
                  className={viewMode === 'RAW_PREVIEW' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                  style={{ padding: '3px 9px', fontSize: '0.74rem' }}
                >
                  🎬 Raw Video Player
                </button>
                <button
                  onClick={() => setViewMode('SPLIT_SCREEN')}
                  className={viewMode === 'SPLIT_SCREEN' ? 'btn-cyber-primary' : 'btn-cyber-outline'}
                  style={{ padding: '3px 9px', fontSize: '0.74rem' }}
                >
                  🔲 Split Screen
                </button>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {uploadedVideoInfo?.metadata && (
                  <>
                    <span className="badge badge-info font-mono">{uploadedVideoInfo.metadata.resolution}</span>
                    <span className="badge badge-purple font-mono">{uploadedVideoInfo.metadata.fps} FPS</span>
                    <span className="badge badge-success font-mono">{uploadedVideoInfo.metadata.duration_seconds}s</span>
                  </>
                )}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="btn-cyber-outline"
                  style={{ padding: '2px 8px', fontSize: '0.72rem', borderColor: '#38bdf8', color: '#38bdf8' }}
                >
                  <Upload size={11} /> Change Video
                </button>
              </div>
            </div>
          )}

          {/* Video Display Container based on View Mode */}
          {viewMode === 'SPLIT_SCREEN' && source === 'VIDEO_FILE' && activeRawVideoSrc ? (
            /* Split-Screen: Original Video (Left) vs AI HUD Overlays (Right) */
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
              width: '100%'
            }}>
              {/* Left Half: Raw Video Player */}
              <div style={{
                position: 'relative',
                backgroundColor: '#030712',
                borderRadius: '8px',
                overflow: 'hidden',
                border: '1px solid rgba(168, 85, 247, 0.4)',
                aspectRatio: '16/9'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  left: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: '#d8b4fe',
                  zIndex: 2
                }}>
                  RAW VIDEO PREVIEW
                </div>
                <video
                  ref={videoPlayerRef}
                  src={activeRawVideoSrc}
                  controls
                  autoPlay
                  muted
                  loop
                  playsInline
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                />
              </div>

              {/* Right Half: Live AI HUD Stream */}
              <div style={{
                position: 'relative',
                backgroundColor: '#030712',
                borderRadius: '8px',
                overflow: 'hidden',
                border: '1px solid rgba(0, 242, 254, 0.4)',
                aspectRatio: '16/9'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  left: '8px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: '#38bdf8',
                  zIndex: 2
                }}>
                  AI HUD OVERLAYS
                </div>
                <img
                  key={`split-${streamKey}`}
                  src={`${api.videoFeedUrl}?t=${streamKey}`}
                  alt="AI CCTV Feed"
                  style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                  onError={() => setTimeout(() => setStreamKey(Date.now()), 1500)}
                />
              </div>
            </div>
          ) : viewMode === 'RAW_PREVIEW' && source === 'VIDEO_FILE' && activeRawVideoSrc ? (
            /* Full Raw HTML5 Video Player Preview */
            <div style={{
              position: 'relative',
              width: '100%',
              backgroundColor: '#030712',
              borderRadius: '8px',
              overflow: 'hidden',
              border: '1px solid rgba(168, 85, 247, 0.4)',
              aspectRatio: '16/9',
              boxShadow: '0 0 25px rgba(0, 0, 0, 0.7)'
            }}>
              <div style={{
                position: 'absolute',
                top: '12px',
                left: '12px',
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(8px)',
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '0.74rem',
                fontWeight: 700,
                color: '#d8b4fe',
                zIndex: 2,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <Play size={12} color="#c084fc" /> ORIGINAL VIDEO PLAYER (HIGH-DEF)
              </div>
              <video
                ref={videoPlayerRef}
                src={activeRawVideoSrc}
                controls
                autoPlay
                muted
                loop
                playsInline
                style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
              />
            </div>
          ) : source === 'VIDEO_FILE' && !activeRawVideoSrc ? (
            /* Upload Call-To-Action Dropzone when in Video File source mode without a loaded file */
            <div 
              onClick={() => fileInputRef.current?.click()}
              style={{
                width: '100%',
                aspectRatio: '16/9',
                backgroundColor: '#030712',
                borderRadius: '8px',
                border: '2px dashed rgba(56, 189, 248, 0.4)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                padding: '24px'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#00f2fe'; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)'; }}
            >
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8'
              }}>
                <Upload size={28} />
              </div>
              <div style={{ textAlign: 'center' }}>
                <h4 style={{ margin: '0 0 6px', color: '#f8fafc', fontSize: '1.05rem', fontWeight: 600 }}>
                  Upload Video for Live AI Analysis
                </h4>
                <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.85rem' }}>
                  Click to select or drop an MP4, AVI, MKV, MOV video file for automated YOLOv26 & OCR surveillance
                </p>
              </div>
              <button className="btn-cyber-primary" style={{ padding: '8px 18px', fontSize: '0.82rem' }}>
                <Upload size={14} /> Select Video File
              </button>
            </div>
          ) : (
            /* Full AI Stream with Cyber HUD Overlays */
            <div style={{
              position: 'relative',
              width: '100%',
              backgroundColor: '#030712',
              borderRadius: '8px',
              overflow: 'hidden',
              border: '1px solid rgba(0, 242, 254, 0.3)',
              aspectRatio: '16/9',
              boxShadow: '0 0 25px rgba(0, 0, 0, 0.7)'
            }}>
              <img
                key={streamKey}
                src={`${api.videoFeedUrl}?t=${streamKey}`}
                alt="Live CCTV Heavy Vehicle Stream"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  display: 'block'
                }}
                onError={() => {
                  setTimeout(() => setStreamKey(Date.now()), 1500);
                }}
              />

              {/* In-Video HUD Quick Overlay Floating Toggles */}
              <div style={{
                position: 'absolute',
                bottom: '12px',
                left: '12px',
                background: 'rgba(7, 10, 18, 0.85)',
                backdropFilter: 'blur(10px)',
                padding: '6px 12px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                border: '1px solid rgba(56, 189, 248, 0.25)'
              }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Layers size={13} color="#00f2fe" /> AI HUD:
                </span>
                
                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', cursor: 'pointer', color: overlays.bboxes ? '#38bdf8' : '#64748b' }}>
                  <input type="checkbox" checked={overlays.bboxes} onChange={() => handleToggleOverlay('bboxes')} />
                  <span>YOLOv26 Box</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', cursor: 'pointer', color: overlays.speed ? '#34d399' : '#64748b' }}>
                  <input type="checkbox" checked={overlays.speed} onChange={() => handleToggleOverlay('speed')} />
                  <span>Speed km/h</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', cursor: 'pointer', color: overlays.plates ? '#fbbf24' : '#64748b' }}>
                  <input type="checkbox" checked={overlays.plates} onChange={() => handleToggleOverlay('plates')} />
                  <span>Plate OCR</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', cursor: 'pointer', color: overlays.vit ? '#c084fc' : '#64748b' }}>
                  <input type="checkbox" checked={overlays.vit} onChange={() => handleToggleOverlay('vit')} />
                  <span>MTL-ViT</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', cursor: 'pointer', color: overlays.trajectories ? '#00f2fe' : '#64748b' }}>
                  <input type="checkbox" checked={overlays.trajectories} onChange={() => handleToggleOverlay('trajectories')} />
                  <span>Trails</span>
                </label>
              </div>
            </div>
          )}

          {/* Pipeline Workflow Banner */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            padding: '10px 14px',
            borderRadius: '6px',
            border: '1px solid rgba(56, 189, 248, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.75rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={15} color="#00f2fe" />
              <span style={{ color: '#cbd5e1' }}>
                <strong>Active Architecture:</strong> CCTV Frame &rarr; YOLOv26 (Heavy Vehicle) &rarr; ByteTrack &rarr; Parallel [Speed | PaddleOCR | MTL-ViT | FC Registry] &rarr; Alert Core
              </span>
            </div>
            <span className="badge badge-success">YOLOv26 ACTIVE</span>
          </div>

        </div>

        {/* Right Column: Active Tracked Vehicles Real-Time Inspector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Active Summary Panel */}
          <div className="glass-panel" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Gauge size={18} color="#00f2fe" />
                <h3 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700 }}>ACTIVE TRUCKS IN FRAME</h3>
              </div>
              <span className="badge badge-info font-mono">
                {telemetry?.active_tracks?.length || 0} VEHICLES
              </span>
            </div>

            {/* List of active tracked vehicles */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '490px', overflowY: 'auto', paddingRight: '4px' }}>
              {(!telemetry?.active_tracks || telemetry.active_tracks.length === 0) ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '36px 12px', 
                  color: '#64748b', 
                  fontSize: '0.82rem',
                  border: '1px dashed rgba(56, 189, 248, 0.2)',
                  borderRadius: '8px'
                }}>
                  <RefreshCw size={24} color="#38bdf8" className="animate-pulse-glow" style={{ margin: '0 auto 8px' }} />
                  <div>Scanning CCTV feed for heavy vehicles...</div>
                  <div style={{ fontSize: '0.72rem', color: '#475569', marginTop: '4px' }}>YOLO heavy vehicle filter engaged</div>
                </div>
              ) : (
                telemetry.active_tracks.map((truck) => {
                  const isBlocked = truck.is_blocklisted;
                  const isOver = truck.is_overspeed;
                  const speedPct = Math.min(100, (truck.speed / 100) * 100);

                  return (
                    <div
                      key={truck.track_id}
                      className={`glass-panel ${isBlocked ? 'glass-panel-danger' : isOver ? 'glass-panel-warning' : ''}`}
                      style={{ 
                        padding: '12px', 
                        borderRadius: '8px', 
                        cursor: 'pointer',
                        transition: 'transform 0.15s ease'
                      }}
                      onClick={() => onSelectTruck && onSelectTruck(truck)}
                    >
                      {/* Top row: Track ID + Plate chip */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span className="badge badge-info font-mono">{truck.track_id}</span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f8fafc' }}>
                            {truck.truck_type || 'Heavy Carrier'}
                          </span>
                        </div>
                        <div className="license-plate-chip">
                          <span className="ind-badge">IND</span>
                          <span>{truck.license_plate}</span>
                        </div>
                      </div>

                      {/* Speed Bar */}
                      <div style={{ marginBottom: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '3px' }}>
                          <span style={{ color: '#94a3b8' }}>Speed:</span>
                          <span className="font-mono" style={{ 
                            fontWeight: 700, 
                            color: isOver ? '#ef4444' : '#10b981' 
                          }}>
                            {truck.speed} km/h {isOver ? '(OVERSPEED ⚠️)' : '(OK)'}
                          </span>
                        </div>
                        <div style={{ width: '100%', height: '5px', backgroundColor: 'rgba(51, 65, 85, 0.5)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ 
                            width: `${speedPct}%`, 
                            height: '100%', 
                            backgroundColor: isOver ? '#ef4444' : '#10b981',
                            transition: 'width 0.2s ease'
                          }} />
                        </div>
                      </div>

                      {/* ViT Attributes & FC Status */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', fontSize: '0.72rem' }}>
                        <span className="badge badge-purple" style={{ textTransform: 'none' }}>
                          🎨 {truck.color}
                        </span>
                        <span className="badge badge-info" style={{ textTransform: 'none' }}>
                          📦 {truck.cargo_attributes}
                        </span>
                        
                        {/* FC Status Badge */}
                        {truck.police_action_required === 'DESTROY_VEHICLE_SCRAP' ? (
                          <span className="badge badge-danger font-mono" style={{ backgroundColor: '#7f1d1d', border: '1px solid #ef4444' }}>
                            🚨 POLICE: DESTROY ({truck.vehicle_age_years || '15+'}y)
                          </span>
                        ) : truck.police_action_required === 'FC_RENEWAL_PROCESS' || truck.fc_status === 'EXPIRED' ? (
                          <span className="badge badge-warning font-mono">
                            ⚠️ FC EXPIRED (₹5K FINE)
                          </span>
                        ) : truck.fc_status === 'SCRAPPED' ? (
                          <span className="badge badge-danger font-mono">
                            🚫 SCRAPPED
                          </span>
                        ) : (
                          <span className="badge badge-success font-mono">
                            ✓ FC VALID
                          </span>
                        )}

                        {isBlocked && (
                          <span className="badge badge-danger">
                            🚨 BLOCKLISTED
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

          </div>

        </div>

      </div>

      {/* Full Video Scan & Vehicle Dossier Analysis Modal */}
      {showAnalysisModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: '900px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: '12px',
            border: '1px solid rgba(0, 242, 254, 0.4)',
            overflow: 'hidden',
            boxShadow: '0 0 40px rgba(0, 242, 254, 0.2)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '16px 20px',
              borderBottom: '1px solid rgba(56, 189, 248, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'rgba(15, 23, 42, 0.8)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Film size={20} color="#00f2fe" />
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                  Full Video AI Heavy Vehicle & FC Analysis
                </h3>
              </div>
              <button
                onClick={() => setShowAnalysisModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '20px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {isAnalyzing ? (
                <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                  <RefreshCw size={40} color="#00f2fe" className="animate-spin" style={{ margin: '0 auto 16px' }} />
                  <h4 style={{ margin: '0 0 8px', color: '#f8fafc', fontSize: '1.1rem' }}>
                    Scanning Video with YOLOv26 & OCR Engines...
                  </h4>
                  <p style={{ color: '#94a3b8', fontSize: '0.85rem', maxWidth: '480px', margin: '0 auto' }}>
                    Processing video frames, tracking persistent vehicle IDs, extracting license plates, classifying cargo attributes, and verifying Fitness Certificate compliance.
                  </p>
                </div>
              ) : analysisResult ? (
                <>
                  {/* Summary KPI Cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Processed Duration</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#00f2fe' }}>
                        {analysisResult.summary?.duration_seconds || 0}s
                      </div>
                    </div>
                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Vehicles Detected</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#34d399' }}>
                        {analysisResult.summary?.unique_vehicles_detected || 0}
                      </div>
                    </div>
                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Overspeed Violations</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>
                        {analysisResult.summary?.overspeed_violations || 0}
                      </div>
                    </div>
                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Police Scrap Orders</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ef4444' }}>
                        {analysisResult.summary?.fc_scrap_orders || 0}
                      </div>
                    </div>
                  </div>

                  {/* Detected Vehicles Grid */}
                  <div>
                    <h4 style={{ margin: '0 0 12px', fontSize: '0.92rem', color: '#cbd5e1' }}>
                      Identified Vehicle Dossiers ({analysisResult.detected_vehicles?.length || 0}):
                    </h4>
                    {analysisResult.detected_vehicles && analysisResult.detected_vehicles.length > 0 ? (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
                        {analysisResult.detected_vehicles.map((v, idx) => (
                          <div
                            key={idx}
                            className="glass-panel"
                            style={{ padding: '12px', borderRadius: '8px', cursor: 'pointer' }}
                            onClick={() => {
                              setShowAnalysisModal(false);
                              if (onSelectTruck) onSelectTruck(v);
                            }}
                          >
                            <img
                              src={v.snapshot_url}
                              alt={v.license_plate}
                              style={{ width: '100%', height: '120px', objectFit: 'cover', borderRadius: '6px', marginBottom: '8px' }}
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                              <span className="badge badge-info font-mono">{v.track_id}</span>
                              <div className="license-plate-chip">
                                <span className="ind-badge">IND</span>
                                <span>{v.license_plate}</span>
                              </div>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                              Type: <strong>{v.truck_type}</strong> ({v.color})
                            </div>
                            <div style={{ fontSize: '0.75rem', color: v.is_overspeed ? '#ef4444' : '#10b981', marginBottom: '6px' }}>
                              Speed: <strong>{v.speed} km/h</strong> {v.is_overspeed && '⚠️ OVERSPEED'}
                            </div>
                            <div>
                              {v.police_action_required === 'DESTROY_VEHICLE_SCRAP' ? (
                                <span className="badge badge-danger">POLICE: SCRAP WARRANT</span>
                              ) : v.police_action_required === 'FC_RENEWAL_PROCESS' ? (
                                <span className="badge badge-warning">FC EXPIRED (₹5K)</span>
                              ) : (
                                <span className="badge badge-success">✓ FC VALID</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '24px', color: '#64748b' }}>
                        No commercial vehicles matched confidence thresholds in this segment.
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#94a3b8' }}>Select or upload a video file to scan and generate AI dossiers.</p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-cyber-primary"
                    style={{ padding: '8px 16px', margin: '0 auto' }}
                  >
                    <Upload size={16} /> Choose Video File
                  </button>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '12px 20px',
              borderTop: '1px solid rgba(56, 189, 248, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: '10px',
              background: 'rgba(15, 23, 42, 0.8)'
            }}>
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="btn-cyber-outline"
                style={{ padding: '6px 14px' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

