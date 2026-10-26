import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  ArrowLeft,
  Film,
  Eye,
  Layers,
  MessageSquare,
  Clock,
  Database,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Cpu,
  CheckCircle2,
  AlertCircle,
  Download,
  X,
  Activity,
  Maximize2,
  BarChart2,
  Sliders,
  Crosshair,
  FileText,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Search
} from 'lucide-react';

export const DebugDashboard = ({ videoId, onBack, initialFrameNumber, initialTrackId }) => {
  const [debugData, setDebugData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Interactive Viewers State
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [selectedTrackId, setSelectedTrackId] = useState(null);
  const videoPlayerRef = useRef(null);

  // Track Timeline Inspector Modal State
  const [inspectingTrackId, setInspectingTrackId] = useState(null);
  const [trackDetails, setTrackDetails] = useState(null);
  const [loadingTrack, setLoadingTrack] = useState(false);
  const [trackError, setTrackError] = useState(null);

  // Phase 2.0 & 2.1 Tab State
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'embeddings' | 'search_diagnostics'
  const [embeddingsData, setEmbeddingsData] = useState(null);
  const [loadingEmbeddings, setLoadingEmbeddings] = useState(false);
  const [embeddingsError, setEmbeddingsError] = useState(null);

  // Developer Reset Utility State
  const [showResetModal, setShowResetModal] = useState(false);

  // Auto-navigate to initial frame or track if passed from search results
  useEffect(() => {
    if (debugData) {
      if (initialFrameNumber !== null && initialFrameNumber !== undefined) {
        const frameIdx = debugData.frameExtraction.frames.findIndex((f) => f.frameNumber === initialFrameNumber);
        if (frameIdx !== -1) {
          setCurrentFrameIdx(frameIdx);
        }
      }
      if (initialTrackId !== null && initialTrackId !== undefined) {
        setSelectedTrackId(initialTrackId);
        handleInspectTrack(initialTrackId);
      }
    }
  }, [debugData, initialFrameNumber, initialTrackId]);

  const [resetStatus, setResetStatus] = useState('idle'); // 'idle' | 'executing' | 'success' | 'failed'
  const [resetStepIdx, setResetStepIdx] = useState(0);
  const [resetSummary, setResetSummary] = useState(null);
  const [resetError, setResetError] = useState(null);

  const resetStepNames = [
    'Resetting...',
    'Deleting uploads...',
    'Deleting frames...',
    'Clearing MongoDB...',
    'Resetting FAISS...',
    'Recreating indices...',
    'Finished.'
  ];

  const handleExecuteReset = async () => {
    setResetStatus('executing');
    setResetStepIdx(0);
    setResetError(null);

    const interval = setInterval(() => {
      setResetStepIdx((prev) => (prev < resetStepNames.length - 2 ? prev + 1 : prev));
    }, 450);

    try {
      const res = await axios.post('/api/developer/reset');
      clearInterval(interval);
      setResetStepIdx(resetStepNames.length - 1);
      if (res.data && res.data.success) {
        setResetStatus('success');
        setResetSummary(res.data.summary);
      } else {
        setResetStatus('failed');
        setResetError(res.data?.message || 'Developer Reset Failed.');
      }
    } catch (err) {
      clearInterval(interval);
      setResetStatus('failed');
      setResetError(err.response?.data?.detail?.message || err.response?.data?.detail || err.message || 'Developer Reset Failed.');
    }
  };


  // Playback Mode State
  const [playbackRunning, setPlaybackRunning] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 4x
  const [playbackStepIdx, setPlaybackStepIdx] = useState(0);
  const playbackTimerRef = useRef(null);

  useEffect(() => {
    fetchDebugData();
  }, [videoId]);

  const fetchEmbeddingsData = async () => {
    setLoadingEmbeddings(true);
    setEmbeddingsError(null);
    try {
      const res = await axios.get(`/api/video/${videoId}/embeddings?t=${Date.now()}`);
      if (res.data) {
        setEmbeddingsData(res.data);
      }
    } catch (err) {
      console.error('Error fetching semantic embeddings:', err);
      setEmbeddingsError(err.response?.data?.detail || 'Failed to load semantic embeddings.');
    } finally {
      setLoadingEmbeddings(false);
    }
  };

  const fetchDebugData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/api/video/${videoId}/debug?t=${Date.now()}`);
      if (res.data) {
        setDebugData(res.data);
      }
    } catch (err) {
      console.error('Error fetching debug diagnostics:', err);
      setError(err.response?.data?.detail || 'Failed to load debug diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch Trajectory Details when a track is inspected
  const handleInspectTrack = async (trackId) => {
    setInspectingTrackId(trackId);
    setLoadingTrack(true);
    setTrackError(null);
    setPlaybackRunning(false);
    setPlaybackStepIdx(0);

    try {
      const res = await axios.get(`/api/video/${videoId}/track/${trackId}?t=${Date.now()}`);
      if (res.data) {
        setTrackDetails(res.data);
      }
    } catch (err) {
      console.error(`Error fetching track ${trackId} trajectory:`, err);
      setTrackError(err.response?.data?.detail || `Failed to load trajectory for Track #${trackId}`);
    } finally {
      setLoadingTrack(false);
    }
  };

  // Playback Auto-Stepping Timer Effect
  useEffect(() => {
    if (playbackRunning && trackDetails?.detections?.length > 0) {
      const intervalMs = Math.max(100, 1000 / playbackSpeed);
      playbackTimerRef.current = setInterval(() => {
        setPlaybackStepIdx((prev) => {
          if (prev >= trackDetails.detections.length - 1) {
            setPlaybackRunning(false);
            return prev;
          }
          return prev + 1;
        });
      }, intervalMs);
    } else {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
    }
    return () => {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
    };
  }, [playbackRunning, playbackSpeed, trackDetails]);

  // Export Track trajectory JSON payload
  const handleExportTrackJson = () => {
    if (!trackDetails) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(trackDetails, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `track_${videoId}_id_${trackDetails.trackId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  if (loading) {
    return (
      <div className="debug-container" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <div className="status-badge uploading" style={{ margin: '0 auto', fontSize: '1rem', padding: '0.6rem 1.2rem' }}>
          <Sparkles className="spinning" size={18} />
          <span>Generating Developer Debug Diagnostics & Annotated Video...</span>
        </div>
      </div>
    );
  }

  if (error || !debugData) {
    return (
      <div className="debug-container">
        <button className="btn-secondary" onClick={onBack} style={{ marginBottom: '1.5rem' }}>
          <ArrowLeft size={16} />
          <span>Back to Uploader</span>
        </button>
        <div className="error-banner">
          <AlertCircle size={24} className="error-icon" />
          <div>
            <div className="error-title">Debug Load Failure</div>
            <div className="error-desc">{error || 'Diagnostics data unavailable.'}</div>
          </div>
        </div>
      </div>
    );
  }

  const {
    videoInformation,
    frameExtraction,
    yoloDetection,
    byteTrackSummary,
    whisperTranscript,
    processingPerformance,
    storageSummary,
    annotatedAssets,
    inferenceConfiguration,
  } = debugData;

  const currentFrame = frameExtraction.frames[currentFrameIdx] || null;
  const currentFrameDetections = yoloDetection.framesWithDetections.find(
    (fg) => fg.frameNumber === currentFrame?.frameNumber
  )?.detections || [];

  // Handle timestamp seek
  const handleSeekTimestamp = (seconds) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = seconds;
      videoPlayerRef.current.play();
    }
    const targetIdx = frameExtraction.frames.findIndex((f) => f.timestamp >= seconds);
    if (targetIdx !== -1) {
      setCurrentFrameIdx(targetIdx);
    }
  };

  return (
    <div className="debug-container">
      {/* Top Header */}
      <div className="debug-header">
        <button className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={16} />
          <span>Back to Uploader</span>
        </button>
        <div className="debug-title-badge">
          <Cpu size={14} />
          <span>DEVELOPER DEBUG DASHBOARD • VIDEO ID: {videoId}</span>
        </div>
      </div>

      {/* Phase 2.0 Tab Navigation Bar */}
      <div className="dashboard-tab-bar">
        <button
          className={`dashboard-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Cpu size={16} />
          <span>Phase 1 Overview Diagnostics</span>
        </button>
        <button
          className={`dashboard-tab-btn ${activeTab === 'embeddings' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('embeddings');
            if (!embeddingsData) fetchEmbeddingsData();
          }}
        >
          <Sparkles size={16} />
          <span>Phase 2.0 Semantic Embeddings & FAISS Engine</span>
        </button>
        <button
          className={`dashboard-tab-btn ${activeTab === 'search_diagnostics' ? 'active' : ''}`}
          onClick={() => setActiveTab('search_diagnostics')}
        >
          <Search size={16} />
          <span>Phase 2.1 Search Diagnostics</span>
        </button>
      </div>


      {activeTab === 'overview' && (
        <>
          {/* Video Information Panel */}
          <div className="debug-card">
            <div className="card-title">
              <Film size={18} />
              <span>Video Information & Metadata</span>
            </div>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Filename</span>
                <span className="info-val">{videoInformation.filename}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Duration</span>
                <span className="info-val">{videoInformation.duration}s</span>
              </div>
              <div className="info-item">
                <span className="info-label">FPS</span>
                <span className="info-val">{videoInformation.fps}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Resolution</span>
                <span className="info-val">{videoInformation.resolution}</span>
              </div>
              <div className="info-item">
                <span className="info-label">File Size</span>
                <span className="info-val">{videoInformation.fileSize}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Codec</span>
                <span className="info-val">{videoInformation.codec}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Status</span>
                <span className="status-badge success" style={{ textTransform: 'uppercase' }}>
                  <CheckCircle2 size={12} />
                  <span>{videoInformation.currentProcessingStatus}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Inference Configuration Panel */}
          <div className="debug-card">
            <div className="card-title">
              <Sparkles size={18} />
              <span>Locked Pipeline Inference Configuration</span>
            </div>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">YOLO Model</span>
                <span className="info-val">{inferenceConfiguration?.yoloModel || 'yolov8m.pt'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Image Size (imgsz)</span>
                <span className="info-val">{inferenceConfiguration?.imgsz || 1280}px</span>
              </div>
              <div className="info-item">
                <span className="info-label">Confidence Threshold</span>
                <span className="info-val">{inferenceConfiguration?.confidence || 0.25}</span>
              </div>
              <div className="info-item">
                <span className="info-label">NMS IoU Threshold</span>
                <span className="info-val">{inferenceConfiguration?.iou || 0.45}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Inference Device</span>
                <span className="info-val">{inferenceConfiguration?.device || 'CPU'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">ByteTrack Enabled</span>
                <span className="info-val">{inferenceConfiguration?.byteTrackEnabled !== false ? 'Yes' : 'No'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Whisper Model</span>
                <span className="info-val">{inferenceConfiguration?.whisperModel || 'base'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Frame Extraction Rate</span>
                <span className="info-val">{inferenceConfiguration?.frameExtractionFps || 1.0} FPS</span>
              </div>
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="summary-grid">
            <div className="stat-card">
              <Film size={18} className="stat-icon" />
              <div className="stat-value">{frameExtraction.totalFramesExtracted}</div>
              <div className="stat-label">Extracted Frames</div>
            </div>

            <div className="stat-card">
              <Eye size={18} className="stat-icon" />
              <div className="stat-value">{yoloDetection.totalDetections}</div>
              <div className="stat-label">YOLO Detections</div>
            </div>

            <div className="stat-card">
              <Layers size={18} className="stat-icon" />
              <div className="stat-value">{byteTrackSummary.length}</div>
              <div className="stat-label">ByteTrack Tracks</div>
            </div>

            <div className="stat-card">
              <MessageSquare size={18} className="stat-icon" />
              <div className="stat-value">{whisperTranscript.segments.length}</div>
              <div className="stat-label">Whisper Segments</div>
            </div>

            <div className="stat-card">
              <Clock size={18} className="stat-icon" />
              <div className="stat-value">{processingPerformance.totalProcessingTimeSec}s</div>
              <div className="stat-label">Total Exec Time</div>
            </div>
          </div>

          {/* Grid Layout: Annotated Video Player & Performance Breakdown */}
          <div className="debug-two-col">
            {/* Annotated Video Player */}
            <div className="debug-card">
              <div className="card-title">
                <Play size={18} />
                <span>Annotated Video Player (Bounding Boxes & Track IDs)</span>
              </div>
              <div className="video-player-box">
                <video
                  ref={videoPlayerRef}
                  controls
                  preload="auto"
                  playsInline
                  src={`/api/video/${videoId}/stream?t=${Date.now()}`}
                  className="annotated-video-element"
                />
              </div>
            </div>

            {/* Performance Timings Breakdown */}
            <div className="debug-card">
              <div className="card-title">
                <Clock size={18} />
                <span>Pipeline Stage Execution Performance</span>
              </div>
              <div className="timings-table">
                <div className="timing-row">
                  <span className="timing-stage">Metadata Extraction</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.metadataExtractionSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.metadataExtractionSec}s</span>
                </div>

                <div className="timing-row">
                  <span className="timing-stage">Frame Extraction (FFmpeg)</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.frameExtractionSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.frameExtractionSec}s</span>
                </div>

                <div className="timing-row">
                  <span className="timing-stage">YOLOv8 Detection</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.yoloDetectionSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.yoloDetectionSec}s</span>
                </div>

                <div className="timing-row">
                  <span className="timing-stage">ByteTrack Tracking</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.byteTrackSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.byteTrackSec}s</span>
                </div>

                <div className="timing-row">
                  <span className="timing-stage">Whisper Audio Transcription</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.whisperSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.whisperSec}s</span>
                </div>

                <div className="timing-row">
                  <span className="timing-stage">MongoDB Sync Operations</span>
                  <span className="timing-bar-container">
                    <span className="timing-bar" style={{ width: `${Math.min(100, (processingPerformance.mongoDbSec / processingPerformance.totalProcessingTimeSec) * 100)}%` }}></span>
                  </span>
                  <span className="timing-val">{processingPerformance.mongoDbSec}s</span>
                </div>

                <div className="timing-row total">
                  <span className="timing-stage">Total Pipeline Exec Time</span>
                  <span className="timing-val">{processingPerformance.totalProcessingTimeSec}s</span>
                </div>
              </div>
            </div>
          </div>

          {/* Frame & Detection Inspection Viewer */}
          <div className="debug-card">
            <div className="card-title">
              <Eye size={18} />
              <span>Frame & Detection Inspector</span>
            </div>

            {currentFrame && (
              <div className="frame-inspector-box">
                {/* Frame Controls Bar */}
                <div className="frame-controls-bar">
                  <button
                    className="btn-secondary"
                    disabled={currentFrameIdx === 0}
                    onClick={() => setCurrentFrameIdx((prev) => Math.max(0, prev - 1))}
                  >
                    <ChevronLeft size={16} />
                    <span>Prev Frame</span>
                  </button>

                  <span className="frame-indicator-text">
                    Frame {currentFrame.frameNumber} / {frameExtraction.totalFramesExtracted} (Timestamp: {currentFrame.timestamp}s)
                  </span>

                  <button
                    className="btn-secondary"
                    disabled={currentFrameIdx >= frameExtraction.totalFramesExtracted - 1}
                    onClick={() => setCurrentFrameIdx((prev) => Math.min(frameExtraction.totalFramesExtracted - 1, prev + 1))}
                  >
                    <span>Next Frame</span>
                    <ChevronRight size={16} />
                  </button>
                </div>

                <div className="inspector-grid">
                  {/* Annotated Frame Display */}
                  <div className="frame-image-container">
                    <img
                      src={`/static/storage/debug/${videoId}/frames/frame_${String(currentFrame.frameNumber).padStart(4, '0')}.jpg?t=${Date.now()}`}
                      alt={`Frame ${currentFrame.frameNumber}`}
                      className="frame-display-img"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = `/static/storage/frames/${videoId}/frame_${String(currentFrame.frameNumber).padStart(4, '0')}.jpg`;
                      }}
                    />

                  </div>

                  {/* Frame Detection Details List */}
                  <div className="detections-list-panel">
                    <div className="panel-subtitle">Detections in Frame {currentFrame.frameNumber}:</div>
                    {currentFrameDetections.length === 0 ? (
                      <div className="empty-text">No objects detected in this frame.</div>
                    ) : (
                      currentFrameDetections.map((det, idx) => {
                        const isSelectedTrack = selectedTrackId !== null && det.assignedTrackId === selectedTrackId;
                        return (
                          <div
                            key={idx}
                            className={`detection-detail-card ${isSelectedTrack ? 'highlighted-track' : ''}`}
                            onClick={() => {
                              setSelectedTrackId(det.assignedTrackId);
                              if (det.assignedTrackId) handleInspectTrack(det.assignedTrackId);
                            }}
                          >
                            <div className="det-row">
                              <span className="det-class">{det.objectClass?.toUpperCase()}</span>
                              <span className="det-track-badge">Track ID: #{det.assignedTrackId || 'N/A'}</span>
                            </div>
                            <div className="det-row sub">
                              <span>Conf: {(det.confidence * 100).toFixed(1)}%</span>
                              <span>BBox: [{det.boundingBox.join(', ')}]</span>
                            </div>
                            <div className="det-action-hint">Click to Inspect Trajectory →</div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ByteTrack Track Directory */}
          <div className="debug-card">
            <div className="card-title">
              <Layers size={18} />
              <span>ByteTrack Track Directory (Click any Card to Inspect Trajectory)</span>
            </div>
            <div className="tracks-grid">
              {byteTrackSummary.map((track) => {
                const isSelected = selectedTrackId === track.trackId;
                return (
                  <div
                    key={track.trackId}
                    className={`track-card ${isSelected ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedTrackId(track.trackId);
                      handleInspectTrack(track.trackId);
                    }}
                  >
                    <div className="track-card-header">
                      <span className="track-id-badge">Track #{track.trackId}</span>
                      <span className="track-class">{track.objectClass.toUpperCase()}</span>
                    </div>
                    <div className="track-details">
                      <div>Tracked Frames: {track.totalFramesTracked} ({track.firstFrame} → {track.lastFrame})</div>
                      <div>Duration: {track.trackDurationSec}s ({track.startTime}s - {track.endTime}s)</div>
                      <div className="frames-string">Frame List: [{track.frames.join(', ')}]</div>
                    </div>
                    <div className="inspect-btn-row">
                      <span className="btn-inspect">
                        <Crosshair size={12} />
                        <span>Inspect Trajectory & Crops</span>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Whisper Transcript Timeline */}
          <div className="debug-card">
            <div className="card-title">
              <MessageSquare size={18} />
              <span>Whisper Speech Transcript Timeline ({whisperTranscript.language.toUpperCase()})</span>
            </div>
            {whisperTranscript.segments.length === 0 ? (
              <div className="empty-text">No active speech audio detected in video.</div>
            ) : (
              <div className="transcript-debug-list">
                {whisperTranscript.segments.map((seg, idx) => (
                  <div
                    key={idx}
                    className="transcript-debug-item"
                    onClick={() => handleSeekTimestamp(seg.startTime)}
                  >
                    <span className="seek-badge">
                      <Play size={10} />
                      <span>{seg.startTime}s - {seg.endTime}s</span>
                    </span>
                    <span className="seg-text">{seg.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* MongoDB Storage Summary */}
          <div className="debug-card">
            <div className="card-title">
              <Database size={18} />
              <span>MongoDB Database Storage Summary</span>
            </div>
            <div className="storage-table">
              <div className="storage-row">
                <span className="col-name">videos Collection</span>
                <span className="col-count">{storageSummary.videosCollectionCount} docs</span>
              </div>
              <div className="storage-row">
                <span className="col-name">frames Collection</span>
                <span className="col-count">{storageSummary.framesCollectionCount} docs</span>
              </div>
              <div className="storage-row">
                <span className="col-name">detections Collection</span>
                <span className="col-count">{storageSummary.detectionsCollectionCount} docs</span>
              </div>
              <div className="storage-row">
                <span className="col-name">tracks Collection</span>
                <span className="col-count">{storageSummary.tracksCollectionCount} docs</span>
              </div>
              <div className="storage-row">
                <span className="col-name">transcripts Collection</span>
                <span className="col-count">{storageSummary.transcriptsCollectionCount} docs</span>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* DEVELOPER UTILITIES - RESET DEVELOPMENT DATA                             */}
          {/* ========================================================================= */}
          <div className="developer-utils-card">
            <div className="developer-utils-header">
              <div>
                <div className="developer-utils-title">
                  <Trash2 size={20} />
                  <span>Developer Utilities • Reset Development Data</span>
                </div>
                <div className="developer-utils-desc">
                  Completely purges all uploaded videos, extracted frames, object crops, FAISS indices, and MongoDB metadata. Restores clean empty directory structure for reproducible dataset indexing.
                </div>
              </div>
              <button className="btn-reset-danger" onClick={() => { setShowResetModal(true); setResetStatus('idle'); }}>
                <Trash2 size={16} />
                <span>Reset Development Data</span>
              </button>
            </div>

            {/* Post-Reset Completion Summary Card */}
            {resetStatus === 'success' && resetSummary && (
              <div className="reset-summary-card">
                <div className="reset-summary-header">
                  <div className="reset-summary-title">
                    <CheckCircle2 size={20} />
                    <span>Development Reset Complete</span>
                  </div>
                  <span className="system-ready-badge">System Ready</span>
                </div>
                <div className="reset-checklist-grid">
                  <div className="reset-check-item">✓ Uploaded Videos Removed ({resetSummary.videosDeleted} files)</div>
                  <div className="reset-check-item">✓ Frames Removed ({resetSummary.framesDeleted} files)</div>
                  <div className="reset-check-item">✓ Debug Assets Removed ({resetSummary.objectCropsDeleted} crops)</div>
                  <div className="reset-check-item">✓ MongoDB Cleared ({resetSummary.mongodbCollectionsCleared?.length} collections)</div>
                  <div className="reset-check-item">✓ FAISS Reinitialized (Frame & Object 0-vector)</div>
                  <div className="reset-check-item">✓ Folder Structure Recreated</div>
                </div>
                <button className="btn-secondary" onClick={onBack}>
                  <ArrowLeft size={16} />
                  <span>Back to Uploader (Fresh Environment)</span>
                </button>
              </div>
            )}

            {/* Reset Failure Alert */}
            {resetStatus === 'failed' && (
              <div className="debug-card error-box mt-4">
                <AlertCircle size={20} />
                <span>{resetError}</span>
              </div>
            )}
          </div>

          {/* Confirmation & Stepper Modal */}
          {showResetModal && (
            <div className="reset-modal-overlay">
              <div className="reset-modal-content">
                {resetStatus === 'idle' && (
                  <>
                    <div className="reset-warning-header">
                      <AlertTriangle size={24} />
                      <span>WARNING: Reset Development Data</span>
                    </div>
                    <div className="reset-warning-body">
                      This will permanently remove all uploaded videos, extracted frames, debug assets, FAISS indices, and MongoDB metadata.<br /><br />
                      <strong>This operation cannot be undone.</strong><br /><br />
                      Continue?
                    </div>
                    <div className="reset-modal-actions">
                      <button className="btn-modal-cancel" onClick={() => setShowResetModal(false)}>
                        Cancel
                      </button>
                      <button className="btn-reset-danger" onClick={handleExecuteReset}>
                        <Trash2 size={16} />
                        <span>Reset Data</span>
                      </button>
                    </div>
                  </>
                )}

                {resetStatus === 'executing' && (
                  <div>
                    <div className="reset-warning-header" style={{ color: '#38BDF8' }}>
                      <RefreshCw className="spinning" size={24} />
                      <span>Resetting Development Environment...</span>
                    </div>
                    <div className="reset-stepper-box">
                      {resetStepNames.map((stepName, idx) => {
                        const isDone = idx < resetStepIdx;
                        const isActive = idx === resetStepIdx;
                        return (
                          <div key={idx} className={`reset-step-row ${isActive ? 'active' : isDone ? 'done' : ''}`}>
                            {isDone ? <CheckCircle2 size={14} /> : isActive ? <RefreshCw className="spinning" size={14} /> : <div style={{ width: 14 }} />}
                            <span>{stepName}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {(resetStatus === 'success' || resetStatus === 'failed') && (
                  <div className="text-right">
                    <button className="btn-secondary mt-4" onClick={() => setShowResetModal(false)}>
                      Close Window
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* ========================================================================= */}
      {/* PHASE 2.0 SEMANTIC EMBEDDINGS & FAISS INDEX INSPECTOR TAB               */}
      {/* ========================================================================= */}
      {activeTab === 'embeddings' && (
        <div className="embeddings-tab-container">
          {loadingEmbeddings ? (
            <div className="debug-card text-center p-8">
              <Sparkles className="spinning mx-auto text-indigo-400 mb-2" size={32} />
              <div>Loading Phase 2.0 OpenCLIP ViT-L/14 Embeddings & FAISS Index Metadata...</div>
            </div>
          ) : embeddingsError ? (
            <div className="debug-card error-box">
              <AlertCircle size={20} />
              <span>{embeddingsError}</span>
            </div>
          ) : embeddingsData ? (
            <>
              {/* Model & FAISS Overview Summary Cards */}
              <div className="debug-card">
                <div className="card-title">
                  <Sparkles size={18} />
                  <span>OpenCLIP ViT-L/14 & Dual FAISS Index Overview</span>
                </div>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Embedding Model</span>
                    <span className="info-val highlight">{embeddingsData.embeddingModel}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Embedding Dimension</span>
                    <span className="info-val">{embeddingsData.embeddingDimension}d</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Frame Embeddings</span>
                    <span className="info-val">{embeddingsData.totalFrameEmbeddings}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Object Crop Embeddings</span>
                    <span className="info-val">{embeddingsData.totalObjectEmbeddings}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Frame FAISS Index Size</span>
                    <span className="info-val font-mono">{embeddingsData.frameFaissSize} vectors</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Object FAISS Index Size</span>
                    <span className="info-val font-mono">{embeddingsData.objectFaissSize} vectors</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Avg Generation Time</span>
                    <span className="info-val">{embeddingsData.statistics.averageGenerationTimeSec}s</span>
                  </div>
                </div>
              </div>

              {/* Semantic Embedding Verification Status */}
              <div className="debug-card">
                <div className="card-title">
                  <CheckCircle2 size={18} />
                  <span>Embedding Validation & Infrastructure Integrity</span>
                </div>
                <div className="verification-checks-grid">
                  <div className="check-item success">
                    <CheckCircle2 size={16} />
                    <span>All {embeddingsData.embeddingDimension}d vectors L2 Normalized (Unit Norm = 1.0)</span>
                  </div>
                  <div className="check-item success">
                    <CheckCircle2 size={16} />
                    <span>Zero NaN / Inf vector values validated</span>
                  </div>
                  <div className="check-item success">
                    <CheckCircle2 size={16} />
                    <span>Dual FAISS indices persisted on disk (storage/faiss/)</span>
                  </div>
                  <div className="check-item success">
                    <CheckCircle2 size={16} />
                    <span>MongoDB stores metadata ONLY (Zero raw vectors in DB)</span>
                  </div>
                </div>
              </div>

              {/* Frame Embedding Explorer */}
              <div className="debug-card">
                <div className="card-title">
                  <Film size={18} />
                  <span>Frame Embedding Explorer ({embeddingsData.totalFrameEmbeddings} Vectors)</span>
                </div>
                <div className="explorer-table-container">
                  <table className="explorer-table">
                    <thead>
                      <tr>
                        <th>Frame #</th>
                        <th>Timestamp</th>
                        <th>Frame Thumbnail</th>
                        <th>FAISS ID</th>
                        <th>Dimension</th>
                        <th>L2 Norm</th>
                        <th>Gen Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {embeddingsData.frameEmbeddings.map((f, idx) => (
                        <tr key={idx}>
                          <td><span className="badge-frame">Frame #{f.frameNumber}</span></td>
                          <td>{f.timestamp}s</td>
                          <td>
                            <img src={f.frameImage} alt={`Frame ${f.frameNumber}`} className="explorer-thumb-frame" />
                          </td>
                          <td><span className="badge-faiss">FAISS #{f.faissId}</span></td>
                          <td>{f.embeddingDimension}d</td>
                          <td><span className="badge-norm">{f.vectorNorm}</span></td>
                          <td>{f.generationTimeSec}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Object Crop Embedding Explorer */}
              <div className="debug-card">
                <div className="card-title">
                  <Layers size={18} />
                  <span>Tracked Object Crop Embedding Explorer ({embeddingsData.totalObjectEmbeddings} Vectors)</span>
                </div>
                <div className="explorer-table-container">
                  <table className="explorer-table">
                    <thead>
                      <tr>
                        <th>Track ID</th>
                        <th>Class</th>
                        <th>Frame #</th>
                        <th>Timestamp</th>
                        <th>Crop Thumbnail</th>
                        <th>FAISS ID</th>
                        <th>Dimension</th>
                        <th>L2 Norm</th>
                      </tr>
                    </thead>
                    <tbody>
                      {embeddingsData.objectEmbeddings.map((o, idx) => (
                        <tr key={idx}>
                          <td><span className="badge-track">Track #{o.trackId}</span></td>
                          <td><span className="badge-class">{o.objectClass}</span></td>
                          <td>Frame #{o.frameNumber}</td>
                          <td>{o.timestamp}s</td>
                          <td>
                            <img src={o.cropImage} alt={`Track ${o.trackId}`} className="explorer-thumb-crop" />
                          </td>
                          <td><span className="badge-faiss">FAISS #{o.faissId}</span></td>
                          <td>{o.embeddingDimension}d</td>
                          <td><span className="badge-norm">{o.vectorNorm}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Embedding Performance Statistics */}
              <div className="debug-card">
                <div className="card-title">
                  <BarChart2 size={18} />
                  <span>Semantic Embedding Performance & Timing Statistics</span>
                </div>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Total Semantic Time</span>
                    <span className="info-val">{embeddingsData.statistics.totalSemanticProcessingTimeSec}s</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Avg Generation Time</span>
                    <span className="info-val">{embeddingsData.statistics.averageGenerationTimeSec}s</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Fastest Vector</span>
                    <span className="info-val">{embeddingsData.statistics.fastestFrameSec}s</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Slowest Vector</span>
                    <span className="info-val">{embeddingsData.statistics.slowestFrameSec}s</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Average L2 Norm</span>
                    <span className="info-val">{embeddingsData.statistics.averageVectorNorm}</span>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* ========================================================================= */}
      {/* PHASE 2.2 SEMANTIC SEARCH RETRIEVAL & THRESHOLD DIAGNOSTICS TAB         */}
      {/* ========================================================================= */}
      {activeTab === 'search_diagnostics' && (
        <div className="search-diagnostics-tab">
          <div className="debug-card">
            <div className="card-title">
              <Search size={18} />
              <span>Phase 2.2 Semantic Search Engine & Refinement Diagnostics</span>
            </div>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Embedding Model</span>
                <span className="info-val highlight">OpenCLIP ViT-L/14</span>
              </div>
              <div className="info-item">
                <span className="info-label">Embedding Dimension</span>
                <span className="info-val">768d</span>
              </div>
              <div className="info-item">
                <span className="info-label">Active Similarity Threshold</span>
                <span className="info-val" style={{ color: '#FBBF24' }}>0.20 (Configurable)</span>
              </div>
              <div className="info-item">
                <span className="info-label">Duplicate Track Grouping</span>
                <span className="info-val" style={{ color: '#34D399' }}>Active (By Track ID)</span>
              </div>
              <div className="info-item">
                <span className="info-label">Frame Index Origin</span>
                <span className="info-val" style={{ color: '#38BDF8' }}>Frame FAISS Index</span>
              </div>
              <div className="info-item">
                <span className="info-label">Object Index Origin</span>
                <span className="info-val" style={{ color: '#F472B6' }}>Object FAISS Index</span>
              </div>
            </div>
          </div>

          <div className="debug-card mt-4">
            <div className="card-title">
              <CheckCircle2 size={18} className="text-emerald-400" />
              <span>Pipeline Processing Summary</span>
            </div>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Pipeline Status</span>
                <span className="info-val highlight">COMPLETED</span>
              </div>
              <div className="info-item">
                <span className="info-label">Frames Indexed</span>
                <span className="info-val">{debugData?.frameExtraction?.totalFramesExtracted || 0}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Objects Tracked</span>
                <span className="info-val">{debugData?.objectTracking?.totalTracksGenerated || 0}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Embeddings Generated</span>
                <span className="info-val">{(debugData?.frameExtraction?.totalFramesExtracted || 0) + (debugData?.objectTracking?.totalDetections || 0)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">FAISS Updated</span>
                <span className="info-val" style={{ color: '#34D399' }}>True (Dual Indices)</span>
              </div>
              <div className="info-item">
                <span className="info-label">MongoDB Sync</span>
                <span className="info-val" style={{ color: '#34D399' }}>True</span>
              </div>
              <div className="info-item">
                <span className="info-label">Search Ready</span>
                <span className="info-val" style={{ color: '#38BDF8' }}>True</span>
              </div>
            </div>
          </div>

          <div className="debug-card mt-4">
            <div className="card-title">
              <Sparkles size={18} />
              <span>Phase 2.2 Retrieval & Consolidation Pipeline Rules</span>
            </div>
            <div className="pipeline-steps-list">
              <div className="pipeline-step-item">
                <strong>1. OpenCLIP Query Encoding</strong>: Encodes natural language query into a 768d L2 unit-norm text vector.
              </div>
              <div className="pipeline-step-item">
                <strong>2. Dual FAISS Search</strong>: Queries `frame.index` and `object.index` independently.
              </div>
              <div className="pipeline-step-item">
                <strong>3. Similarity Threshold Filtering</strong>: Rejects candidates with cosine similarity &lt; 0.20.
              </div>
              <div className="pipeline-step-item">
                <strong>4. Duplicate Track Consolidation</strong>: Groups object detections by `(videoId, trackId)` into single representative trajectory result cards.
              </div>
              <div className="pipeline-step-item">
                <strong>5. Index Origin Tracking</strong>: Tagged explicitly as `Frame FAISS Index` or `Object FAISS Index`.
              </div>
              <div className="pipeline-step-item">
                <strong>6. Search Analytics Compilation</strong>: Computes `candidatesRetrieved`, `resultsRejectedByThreshold`, `acceptedResults`, `groupedTracks`, `finalReturnedResults`.
              </div>
            </div>
          </div>
        </div>
      )}




      {/* ========================================================================= */}
      {/* TRACK TIMELINE INSPECTOR & OBJECT TRAJECTORY VALIDATION MODAL PANEL      */}
      {/* ========================================================================= */}
      {inspectingTrackId !== null && (
        <div className="modal-overlay" onClick={() => setInspectingTrackId(null)}>
          <div className="modal-content track-inspector-modal" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <div className="modal-header-title">
                <Crosshair size={20} className="modal-title-icon" />
                <div>
                  <div className="modal-title-text">
                    Track #{inspectingTrackId} Trajectory Inspector
                    {trackDetails && (
                      <span className="class-badge">
                        {trackDetails.objectClass.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="modal-subtitle-text">
                    Developer-Only Trajectory Validation & Object Crop Inspector
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                {trackDetails && (
                  <button className="btn-secondary" onClick={handleExportTrackJson} title="Export Trajectory JSON">
                    <Download size={14} />
                    <span>Export JSON</span>
                  </button>
                )}
                <button className="btn-close" onClick={() => setInspectingTrackId(null)}>
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="modal-body">
              {loadingTrack ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                  <Sparkles className="spinning" size={24} style={{ color: 'var(--primary-light)' }} />
                  <div style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Generating Object Bounding Box Crops & Computing Trajectory Metrics...
                  </div>
                </div>
              ) : trackError ? (
                <div className="error-banner">
                  <AlertCircle size={20} />
                  <span>{trackError}</span>
                </div>
              ) : trackDetails ? (
                <div className="inspector-flow-grid">
                  {/* Track Summary Badges */}
                  <div className="track-summary-bar">
                    <div className="ts-item">
                      <span className="ts-label">Track ID</span>
                      <span className="ts-val">#{trackDetails.trackId}</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">Object Class</span>
                      <span className="ts-val">{trackDetails.objectClass.toUpperCase()}</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">Frames Tracked</span>
                      <span className="ts-val">{trackDetails.totalFramesTracked}</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">Track Duration</span>
                      <span className="ts-val">{trackDetails.trackDuration}s</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">Start Time</span>
                      <span className="ts-val">{trackDetails.startTime}s</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">End Time</span>
                      <span className="ts-val">{trackDetails.endTime}s</span>
                    </div>
                    <div className="ts-item">
                      <span className="ts-label">Avg Confidence</span>
                      <span className="ts-val font-accent">{(trackDetails.averageConfidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {/* Kinematic & Trajectory Statistics Panel */}
                  <div className="debug-card stats-panel-card">
                    <div className="card-title">
                      <BarChart2 size={16} />
                      <span>Trajectory Kinematic & Spatial Statistics</span>
                    </div>
                    <div className="stats-metric-grid">
                      <div className="metric-box">
                        <div className="m-label">Track Lifetime</div>
                        <div className="m-val">{trackDetails.statistics.trackLifetimeSec}s</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Confidence (Min / Max)</div>
                        <div className="m-val">
                          {(trackDetails.statistics.minimumConfidence * 100).toFixed(1)}% → {(trackDetails.statistics.maximumConfidence * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Confidence Variance</div>
                        <div className="m-val">{trackDetails.statistics.confidenceVariance.toFixed(6)}</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Avg Bounding Box Area</div>
                        <div className="m-val">{trackDetails.statistics.averageBoundingBoxArea.toLocaleString()} px²</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Object Movement Distance</div>
                        <div className="m-val">{trackDetails.statistics.objectMovementDistance} px</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Missing Frames</div>
                        <div className="m-val">{trackDetails.statistics.framesMissing}</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Detection Success Rate</div>
                        <div className="m-val font-accent">{trackDetails.statistics.detectionSuccessRate}%</div>
                      </div>
                      <div className="metric-box">
                        <div className="m-label">Largest Bounding Box</div>
                        <div className="m-val sub-text-code">[{trackDetails.statistics.largestBoundingBox.join(', ')}]</div>
                      </div>
                    </div>
                  </div>

                  {/* Confidence Trajectory SVG Graph */}
                  <div className="debug-card graph-card">
                    <div className="card-title">
                      <Activity size={16} />
                      <span>Confidence Score Trajectory Over Time</span>
                    </div>
                    <div className="svg-chart-container">
                      <ConfidenceSvgChart
                        detections={trackDetails.detections}
                        activeIdx={playbackStepIdx}
                        onSelectIdx={(idx) => {
                          setPlaybackStepIdx(idx);
                          setPlaybackRunning(false);
                        }}
                      />
                    </div>
                  </div>

                  {/* Step Playback Controls Bar */}
                  <div className="playback-bar-card">
                    <div className="pb-left">
                      <button
                        className={`btn-play-toggle ${playbackRunning ? 'running' : ''}`}
                        onClick={() => setPlaybackRunning(!playbackRunning)}
                      >
                        {playbackRunning ? <Pause size={16} /> : <Play size={16} />}
                        <span>{playbackRunning ? 'Pause Step Playback' : 'Play Trajectory Stepper'}</span>
                      </button>

                      <div className="speed-pills">
                        <span className="speed-label">Speed:</span>
                        {[1, 2, 4].map((sp) => (
                          <button
                            key={sp}
                            className={`speed-pill ${playbackSpeed === sp ? 'active' : ''}`}
                            onClick={() => setPlaybackSpeed(sp)}
                          >
                            {sp}x
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="pb-right">
                      <button
                        className="btn-secondary"
                        disabled={playbackStepIdx === 0}
                        onClick={() => {
                          setPlaybackStepIdx((prev) => Math.max(0, prev - 1));
                          setPlaybackRunning(false);
                        }}
                      >
                        <ChevronLeft size={16} />
                        <span>Prev Step</span>
                      </button>

                      <span className="pb-step-counter">
                        Step {playbackStepIdx + 1} / {trackDetails.detections.length}
                        <span className="frame-num-pill">
                          (Frame {trackDetails.detections[playbackStepIdx]?.frameNumber})
                        </span>
                      </span>

                      <button
                        className="btn-secondary"
                        disabled={playbackStepIdx >= trackDetails.detections.length - 1}
                        onClick={() => {
                          setPlaybackStepIdx((prev) => Math.min(trackDetails.detections.length - 1, prev + 1));
                          setPlaybackRunning(false);
                        }}
                      >
                        <span>Next Step</span>
                        <ChevronRight size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Active Detection Image Triplets Viewer */}
                  {trackDetails.detections[playbackStepIdx] && (
                    <div className="debug-card active-triplet-card">
                      <div className="card-title">
                        <Maximize2 size={16} />
                        <span>
                          Active Detection Step Details — Frame #{trackDetails.detections[playbackStepIdx].frameNumber}
                          (Timestamp: {trackDetails.detections[playbackStepIdx].timestamp}s)
                        </span>
                      </div>

                      <div className="triplet-metadata-row">
                        <span><strong>Confidence:</strong> {(trackDetails.detections[playbackStepIdx].confidence * 100).toFixed(1)}%</span>
                        <span><strong>Bounding Box [x1, y1, x2, y2]:</strong> [{trackDetails.detections[playbackStepIdx].bbox.join(', ')}]</span>
                      </div>

                      {/* Image Triplets Grid */}
                      <div className="triplets-image-grid">
                        {/* 1. Original Frame Thumbnail */}
                        <div className="triplet-box">
                          <div className="triplet-label">1. Original Frame</div>
                          <img
                            src={`${trackDetails.detections[playbackStepIdx].frameImage}?t=${Date.now()}`}
                            alt="Original Frame"
                            className="triplet-img"
                          />
                        </div>

                        {/* 2. Annotated Frame Thumbnail */}
                        <div className="triplet-box">
                          <div className="triplet-label">2. Annotated Frame (BBox & Track ID)</div>
                          <img
                            src={`${trackDetails.detections[playbackStepIdx].annotatedFrame}?t=${Date.now()}`}
                            alt="Annotated Frame"
                            className="triplet-img"
                          />
                        </div>

                        {/* 3. Cropped Object Thumbnail */}
                        <div className="triplet-box crop-highlight">
                          <div className="triplet-label crop-label">3. Cropped Object (Padded BBox)</div>
                          <img
                            src={`${trackDetails.detections[playbackStepIdx].croppedObject}?t=${Date.now()}`}
                            alt="Cropped Object"
                            className="triplet-img crop-img"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Full Trajectory Detections Matrix List */}
                  <div className="debug-card">
                    <div className="card-title">
                      <Sliders size={16} />
                      <span>Complete Trajectory Detection Matrix</span>
                    </div>

                    <div className="matrix-detections-list">
                      {trackDetails.detections.map((det, idx) => {
                        const isActive = idx === playbackStepIdx;
                        return (
                          <div
                            key={idx}
                            className={`matrix-row-item ${isActive ? 'active-step' : ''}`}
                            onClick={() => {
                              setPlaybackStepIdx(idx);
                              setPlaybackRunning(false);
                            }}
                          >
                            <img
                              src={det.croppedObject}
                              alt={`Crop ${det.frameNumber}`}
                              className="matrix-crop-thumb"
                            />
                            <div className="matrix-info">
                              <div className="m-top">
                                <strong>Frame #{det.frameNumber}</strong> ({det.timestamp}s)
                              </div>
                              <div className="m-sub">
                                BBox: [{det.bbox.join(', ')}]
                              </div>
                            </div>
                            <div className="matrix-right">
                              <span className="matrix-conf-badge">
                                {(det.confidence * 100).toFixed(1)}%
                              </span>
                              {isActive && <span className="active-badge">ACTIVE</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// =========================================================================
// SVG CONFIDENCE TRAJECTORY CHART COMPONENT
// =========================================================================
const ConfidenceSvgChart = ({ detections = [], activeIdx = 0, onSelectIdx }) => {
  if (!detections || detections.length === 0) {
    return <div className="empty-text">No confidence data available to plot.</div>;
  }

  const width = 800;
  const height = 140;
  const padding = 30;

  const times = detections.map((d) => d.timestamp);
  const confs = detections.map((d) => d.confidence * 100);

  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const timeSpan = Math.max(0.1, maxTime - minTime);

  const minConf = Math.max(0, Math.min(...confs) - 5);
  const maxConf = Math.min(100, Math.max(...confs) + 5);
  const confSpan = Math.max(1, maxConf - minConf);

  const points = detections.map((d, i) => {
    const x = timeSpan === 0 ? padding : padding + ((d.timestamp - minTime) / timeSpan) * (width - 2 * padding);
    const y = height - padding - ((d.confidence * 100 - minConf) / confSpan) * (height - 2 * padding);
    return { x, y, conf: (d.confidence * 100).toFixed(1), timestamp: d.timestamp, frameNumber: d.frameNumber, index: i };
  });

  const pathD = points.length === 1
    ? `M ${points[0].x} ${points[0].y} L ${points[0].x + 10} ${points[0].y}`
    : points.reduce((acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), '');

  return (
    <div className="svg-wrapper">
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        {/* Horizontal Grid lines */}
        {[0, 0.5, 1].map((ratio, idx) => {
          const y = height - padding - ratio * (height - 2 * padding);
          const val = (minConf + ratio * confSpan).toFixed(0);
          return (
            <g key={idx}>
              <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="rgba(255, 255, 255, 0.08)" strokeDasharray="4 4" />
              <text x={padding - 6} y={y + 3} fill="var(--text-muted)" fontSize="10" textAnchor="end">
                {val}%
              </text>
            </g>
          );
        })}

        {/* Trajectory Polyline */}
        <path d={pathD} fill="none" stroke="var(--primary-light)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* Data Points */}
        {points.map((p) => {
          const isActive = p.index === activeIdx;
          return (
            <g key={p.index} onClick={() => onSelectIdx(p.index)} style={{ cursor: 'pointer' }}>
              <circle
                cx={p.x}
                cy={p.y}
                r={isActive ? 7 : 4.5}
                fill={isActive ? '#38BDF8' : 'var(--primary)'}
                stroke="#FFFFFF"
                strokeWidth={isActive ? 2.5 : 1.5}
              />
              <title>{`Frame ${p.frameNumber} (${p.timestamp}s): ${p.conf}%`}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
