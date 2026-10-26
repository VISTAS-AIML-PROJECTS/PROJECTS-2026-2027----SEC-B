import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  UploadCloud,
  FileVideo,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  Layers,
  Sparkles,
  Eye,
  Film,
  MessageSquare,
  Activity,
  Cpu,
  Trash2,
  AlertTriangle,
  Clock
} from 'lucide-react';

const ALLOWED_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv'];
const MAX_SIZE_BYTES = 2 * 1024 * 1024 * 1024; // 2 GB

const STAGES_ORDER = [
  'UPLOADED',
  'METADATA_EXTRACTION',
  'FRAME_EXTRACTION',
  'OBJECT_DETECTION',
  'OBJECT_TRACKING',
  'AUDIO_TRANSCRIPTION',
  'DATABASE_SYNC',
  'COMPLETED'
];

export const VideoUploader = ({ onOpenDebug, onOpenSearch }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Pipeline tracking
  const [activeVideoId, setActiveVideoId] = useState(null);
  const [currentStage, setCurrentStage] = useState('');
  const [stageMessage, setStageMessage] = useState('');
  const [summaryData, setSummaryData] = useState(null);

  // Pipeline Completion Timeline State
  const [uploadStartTime, setUploadStartTime] = useState('');
  const [backendStartTime, setBackendStartTime] = useState('');
  const [backendCompletedTime, setBackendCompletedTime] = useState('');
  const [frontendUpdatedTime, setFrontendUpdatedTime] = useState('');
  const [totalProcessingTimeStr, setTotalProcessingTimeStr] = useState('');
  const [liveTimerSec, setLiveTimerSec] = useState(0);
  const startTimestampRef = useRef(null);

  // Live stopwatch timer ticker effect during uploading and pipeline processing
  useEffect(() => {
    let timerInterval = null;
    if ((uploadStatus === 'uploading' || uploadStatus === 'processing') && startTimestampRef.current) {
      timerInterval = setInterval(() => {
        const elapsed = (Date.now() - startTimestampRef.current) / 1000;
        setLiveTimerSec(elapsed);
      }, 100);
    } else {
      if (timerInterval) clearInterval(timerInterval);
    }
    return () => {
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [uploadStatus]);

  // Developer Reset Utility State
  const [showResetModal, setShowResetModal] = useState(false);
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
    }, 100);

    try {
      const res = await axios.post('/api/developer/reset');
      clearInterval(interval);
      setResetStepIdx(resetStepNames.length - 1);
      if (res.data && res.data.success) {
        setResetStatus('success');
        setResetSummary(res.data.summary);
        resetUploader(); // Reset uploader state after successful environment reset
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


  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const formatBytes = (bytes) => {
    if (!bytes || bytes <= 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    if (!file) return false;
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
      setErrorMessage('Unsupported file type.');
      setUploadStatus('error');
      return false;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setErrorMessage('Large file.');
      setUploadStatus('error');
      return false;
    }
    return true;
  };

  // Poll processing status every 2 seconds
  useEffect(() => {
    if (uploadStatus === 'processing' && activeVideoId) {
      const pollStatus = async () => {
        try {
          const res = await axios.get(`/api/video/${activeVideoId}/status`);
          if (res.data) {
            const { status, currentStage: stageName, message, error } = res.data;
            setCurrentStage(status);
            setStageMessage(message || stageName);

            const statusUpper = (status || '').toUpperCase();
            if (statusUpper === 'COMPLETED') {
              const compTime = new Date().toLocaleTimeString();
              setBackendCompletedTime(compTime);
              setFrontendUpdatedTime(compTime);
              if (startTimestampRef.current) {
                const totalSec = ((Date.now() - startTimestampRef.current) / 1000).toFixed(1);
                setTotalProcessingTimeStr(`${totalSec}s`);
              }
              setUploadStatus('completed');
              setProgress(100);
              fetchSummary(activeVideoId);
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            } else if (statusUpper === 'FAILED') {
              setUploadStatus('error');
              setErrorMessage(error || message || 'Processing failed.');
              if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
            }
          }
        } catch (err) {
          console.error('Error polling status:', err);
        }
      };

      pollStatus(); // initial check
      pollIntervalRef.current = setInterval(pollStatus, 2000);
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [uploadStatus, activeVideoId]);

  const fetchSummary = async (videoId) => {
    try {
      const res = await axios.get(`/api/video/${videoId}/summary`);
      if (res.data) {
        setSummaryData(res.data);
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    }
  };

  const handleUpload = async (fileToUpload) => {
    setErrorMessage('');
    setSummaryData(null);
    setActiveVideoId(null);

    if (!validateFile(fileToUpload)) return;

    const uploadStart = new Date().toLocaleTimeString();
    setUploadStartTime(uploadStart);
    startTimestampRef.current = Date.now();

    setSelectedFile(fileToUpload);
    setUploadStatus('uploading');
    setProgress(0);

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percentCompleted);
          }
        },
      });

      if (response.data && response.data.video_id) {
        const vid = response.data.video_id;
        setActiveVideoId(vid);
        setBackendStartTime(new Date().toLocaleTimeString());
        setUploadStatus('processing');
        setCurrentStage('UPLOADED');
        setStageMessage('Video uploaded successfully. Processing started.');
      } else {
        setUploadStatus('error');
        setErrorMessage('Upload failed.');
      }
    } catch (err) {
      setUploadStatus('error');
      if (!err.response) {
        setErrorMessage('Network error.');
      } else if (err.response.status === 400) {
        setErrorMessage('Unsupported file type.');
      } else if (err.response.status === 413) {
        setErrorMessage('Large file.');
      } else {
        setErrorMessage(err.response.data?.detail || 'Upload failed.');
      }
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const resetUploader = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setSelectedFile(null);
    setUploadStatus('idle');
    setProgress(0);
    setErrorMessage('');
    setActiveVideoId(null);
    setCurrentStage('');
    setStageMessage('');
    setSummaryData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const getStageIndex = (stage) => STAGES_ORDER.indexOf(stage);

  return (
    <div className="upload-card">
      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.avi,.mov,.mkv"
        className="file-input-hidden"
        onChange={handleFileChange}
      />

      {/* Drag & Drop Zone */}
      {(uploadStatus === 'idle' || uploadStatus === 'error') && (
        <div
          className={`dropzone ${dragActive ? 'dragging' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="icon-container">
            <UploadCloud size={32} />
          </div>

          <div className="dropzone-prompt">
            <span className="main-text">Drag and drop your video here</span>
            <span className="sub-text">or click to choose a file from your device</span>
          </div>

          <div className="format-tags">
            {ALLOWED_EXTENSIONS.map((ext) => (
              <span key={ext} className="format-tag">
                .{ext.toUpperCase()}
              </span>
            ))}
            <span className="format-tag">MAX 2GB</span>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Browse File
          </button>
        </div>
      )}

      {/* Error Alert */}
      {uploadStatus === 'error' && (
        <div className="error-banner">
          <AlertCircle size={20} className="error-icon" />
          <div>
            <div className="error-title">{errorMessage}</div>
            <div className="error-desc">
              Please select a valid video file (.mp4, .avi, .mov, .mkv) under 2GB.
            </div>
          </div>
        </div>
      )}

      {/* Uploading Progress */}
      {uploadStatus === 'uploading' && selectedFile && (
        <div className="upload-status-box">
          <div className="file-info-header">
            <div className="file-meta">
              <div className="file-icon">
                <FileVideo size={20} />
              </div>
              <div className="file-details">
                <span className="filename-text">{selectedFile.name}</span>
                <span className="filesize-text">{formatBytes(selectedFile.size)}</span>
              </div>
            </div>
            <div className="status-badge uploading">
              <Loader2 size={12} className="spinning" />
              <span>Uploading</span>
            </div>
          </div>

          <div className="progress-container">
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div className="progress-metrics">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Processing Pipeline Stepper */}
      {uploadStatus === 'processing' && (
        <div className="upload-status-box">
          <div className="file-info-header">
            <div className="file-meta">
              <div className="file-icon">
                <Activity size={20} />
              </div>
              <div className="file-details">
                <span className="filename-text">{selectedFile?.name || 'Processing Video...'}</span>
                <span className="filesize-text">Video ID: {activeVideoId}</span>
              </div>
            </div>
            <div className="status-badge uploading" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818CF8', borderColor: 'rgba(99, 102, 241, 0.4)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Clock size={13} className="spinning" />
              <span>Elapsed: {liveTimerSec.toFixed(1)}s</span>
            </div>
          </div>

          {/* Pipeline Stage Indicators */}
          <div className="pipeline-stepper">
            <div className="stage-message">{stageMessage}</div>

            <div className="stages-bar">
              {STAGES_ORDER.slice(1, -1).map((stage, idx) => {
                const currentIdx = getStageIndex(currentStage);
                const thisIdx = getStageIndex(stage);
                const isPassed = currentIdx > thisIdx;
                const isCurrent = currentIdx === thisIdx;

                return (
                  <div
                    key={stage}
                    className={`stage-pill ${isPassed ? 'completed' : ''} ${isCurrent ? 'active' : ''}`}
                  >
                    <span className="pill-dot"></span>
                    <span className="pill-name">{stage.replace('_', ' ')}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Completed Summary Card */}
      {uploadStatus === 'completed' && (
        <div className="upload-status-box">
          <div className="file-info-header">
            <div className="file-meta">
              <div className="file-icon" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>
                <CheckCircle2 size={20} />
              </div>
              <div className="file-details">
                <span className="filename-text">{summaryData?.videoMetadata?.filename || selectedFile?.name || 'Processed Video'}</span>
                <span className="filesize-text">Duration: {summaryData?.videoMetadata?.duration || 0}s | ID: {activeVideoId}</span>
              </div>
            </div>
            <div className="status-badge success">
              <CheckCircle2 size={12} />
              <span>Completed</span>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="summary-grid">
            <div className="stat-card">
              <Film size={18} className="stat-icon" />
              <div className="stat-value">{summaryData?.frameCount ?? '...'}</div>
              <div className="stat-label">Frames Extracted</div>
            </div>

            <div className="stat-card">
              <Eye size={18} className="stat-icon" />
              <div className="stat-value">{summaryData?.objectsDetected ?? '...'}</div>
              <div className="stat-label">Objects Detected</div>
            </div>

            <div className="stat-card">
              <Layers size={18} className="stat-icon" />
              <div className="stat-value">{summaryData?.trackCount ?? '...'}</div>
              <div className="stat-label">Tracks Generated</div>
            </div>

            <div className="stat-card">
              <MessageSquare size={18} className="stat-icon" />
              <div className="stat-value">{summaryData?.transcriptLength ?? '...'}</div>
              <div className="stat-label">Transcripts</div>
            </div>

            <div className="stat-card" style={{ borderColor: 'rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.06)' }}>
              <Clock size={18} className="stat-icon" style={{ color: '#10B981' }} />
              <div className="stat-value" style={{ color: '#10B981' }}>{summaryData?.processingTime || totalProcessingTimeStr || `${liveTimerSec.toFixed(1)}s`}</div>
              <div className="stat-label">Total Exec Time</div>
            </div>
          </div>

          {/* Developer Diagnostics • Pipeline Completion Timeline Card */}
          <div className="timeline-card-container mt-4">
            <div className="timeline-card-header">
              <Activity size={16} className="text-emerald-400" />
              <span>Developer Diagnostics • Pipeline Completion Timeline</span>
            </div>
            <div className="timeline-grid">
              <div className="timeline-item">
                <span className="timeline-label">Upload Started</span>
                <span className="timeline-val">{uploadStartTime || 'N/A'}</span>
              </div>
              <div className="timeline-item">
                <span className="timeline-label">Backend Processing Started</span>
                <span className="timeline-val">{backendStartTime || 'N/A'}</span>
              </div>
              <div className="timeline-item">
                <span className="timeline-label">Backend Processing Completed</span>
                <span className="timeline-val">{backendCompletedTime || 'N/A'}</span>
              </div>
              <div className="timeline-item">
                <span className="timeline-label">Frontend Updated</span>
                <span className="timeline-val">{frontendUpdatedTime || 'N/A'}</span>
              </div>
              <div className="timeline-item highlight">
                <span className="timeline-label">Total Processing Time</span>
                <span className="timeline-val">{totalProcessingTimeStr || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Quick Navigation Buttons Bar */}
          <div className="upload-actions-row mt-4">
            {onOpenDebug && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onOpenDebug(activeVideoId)}
                style={{ background: '#6366F1' }}
              >
                <Cpu size={16} />
                <span>View Debug Dashboard</span>
              </button>
            )}

            {onOpenSearch && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onOpenSearch()}
                style={{ background: '#38BDF8', color: '#0F172A' }}
              >
                <Search size={16} />
                <span>Open Semantic Search</span>
              </button>
            )}

            <button className="btn-secondary" onClick={resetUploader}>
              <RefreshCw size={14} />
              <span>Upload Another Video</span>
            </button>
          </div>
        </div>
      )}


      {/* ========================================================================= */}
      {/* DEVELOPER UTILITIES - RESET DEVELOPMENT DATA CARD                        */}
      {/* ========================================================================= */}
      <div className="developer-utils-card" style={{ marginTop: '2rem' }}>
        <div className="developer-utils-header">
          <div>
            <div className="developer-utils-title">
              <Trash2 size={20} />
              <span>Developer Utilities • Reset Development Data</span>
            </div>
            <div className="developer-utils-desc">
              Completely purges all uploaded videos, extracted frames, object crops, FAISS indices, and MongoDB metadata. Restores a clean empty development environment.
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
    </div>
  );
};

