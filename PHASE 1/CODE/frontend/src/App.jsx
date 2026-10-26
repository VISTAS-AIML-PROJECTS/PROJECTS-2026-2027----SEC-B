import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { VideoUploader } from './components/VideoUploader';
import { DebugDashboard } from './components/DebugDashboard';
import { SemanticSearch } from './components/SemanticSearch';
import { Search, UploadCloud, Cpu, Trash2, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

export function App() {
  const [view, setView] = useState('search'); // 'search' | 'uploader' | 'debug'
  const [debugVideoId, setDebugVideoId] = useState(null);
  const [initialFrameNumber, setInitialFrameNumber] = useState(null);
  const [initialTrackId, setInitialTrackId] = useState(null);

  // Global Reset State
  const [showResetModal, setShowResetModal] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [resetNotification, setResetNotification] = useState('');
  const [resetKey, setResetKey] = useState(0);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#/debug/')) {
        const parts = hash.replace('#/debug/', '').split('?');
        const videoId = parts[0];
        if (videoId) {
          setDebugVideoId(videoId);
          setView('debug');

          if (parts[1]) {
            const searchParams = new URLSearchParams(parts[1]);
            const frame = searchParams.get('frame');
            const track = searchParams.get('track');
            if (frame) setInitialFrameNumber(parseInt(frame, 10));
            if (track) setInitialTrackId(parseInt(track, 10));
          }
        }
      } else if (hash === '#/uploader') {
        setView('uploader');
      } else if (hash === '#/search') {
        setView('search');
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const openDebugView = (videoId, frameNum = null, trackId = null) => {
    setDebugVideoId(videoId);
    setInitialFrameNumber(frameNum);
    setInitialTrackId(trackId);
    setView('debug');
    let hashStr = `#/debug/${videoId}`;
    const params = [];
    if (frameNum !== null) params.push(`frame=${frameNum}`);
    if (trackId !== null) params.push(`track=${trackId}`);
    if (params.length > 0) hashStr += `?${params.join('&')}`;
    window.location.hash = hashStr;
  };

  const navigateToSearch = () => {
    setView('search');
    window.location.hash = '#/search';
  };

  const navigateToUploader = () => {
    setView('uploader');
    window.location.hash = '#/uploader';
  };

  const handleNavigateToFrame = (videoId, frameNumber) => {
    openDebugView(videoId, frameNumber, null);
  };

  const handleNavigateToTrack = (videoId, trackId) => {
    openDebugView(videoId, null, trackId);
  };

  const handleConfirmReset = async () => {
    setIsResetting(true);
    try {
      await axios.post('/api/developer/reset');
      setDebugVideoId(null);
      setInitialFrameNumber(null);
      setInitialTrackId(null);
      setResetKey((prev) => prev + 1);
      setResetNotification('All ChronoLens data has been reset.');
      setShowResetModal(false);
      setView('search');
      window.location.hash = '#/search';
      setTimeout(() => setResetNotification(''), 6000);
    } catch (err) {
      console.error('Reset error:', err);
      alert('Failed to reset data. Please try again.');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="app-container" style={{ maxWidth: view === 'debug' ? '1360px' : view === 'search' ? '1360px' : '900px' }}>
      {/* Top Header Bar */}
      <header className="app-header-bar">
        <div className="header-brand">
          <div className="brand-title-row">
            <span className="live-status-dot"></span>
            <h1 className="app-title-compact">ChronoLens</h1>
          </div>
          <span className="app-subtitle-compact">AI Powered Video Intelligence Framework</span>
        </div>

        {/* Global Reset Notification Banner */}
        {resetNotification && (
          <div style={{
            padding: '6px 14px',
            backgroundColor: 'rgba(34, 197, 94, 0.15)',
            border: '1px solid rgba(34, 197, 94, 0.4)',
            borderRadius: '8px',
            color: '#4ADE80',
            fontSize: '0.85rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <CheckCircle2 size={16} />
            <span>{resetNotification}</span>
          </div>
        )}

        {/* Global Navigation Bar */}
        <nav className="main-nav-bar">
          <div className="nav-tabs-group">
            <button
              className={`nav-tab-btn ${view === 'search' ? 'active' : ''}`}
              onClick={navigateToSearch}
            >
              <Search size={16} />
              <span>Semantic Search</span>
            </button>
            <button
              className={`nav-tab-btn ${view === 'uploader' ? 'active' : ''}`}
              onClick={navigateToUploader}
            >
              <UploadCloud size={16} />
              <span>Video Uploader</span>
            </button>
            <button
              className={`nav-tab-btn ${view === 'debug' ? 'active' : ''}`}
              onClick={() => debugVideoId && setView('debug')}
              disabled={!debugVideoId}
            >
              <Cpu size={16} />
              <span>Developer Debug</span>
            </button>
          </div>

          {/* Reset Data Button */}
          <button
            className="nav-tab-btn btn-reset-nav"
            onClick={() => setShowResetModal(true)}
          >
            <Trash2 size={16} />
            <span>Reset Data</span>
          </button>
        </nav>
      </header>

      {/* Main Content Router */}
      <main style={{ width: '100%' }}>
        {view === 'search' && (
          <SemanticSearch
            key={`search-${resetKey}`}
            onNavigateToFrame={handleNavigateToFrame}
            onNavigateToTrack={handleNavigateToTrack}
          />
        )}

        {view === 'uploader' && (
          <VideoUploader
            key={`uploader-${resetKey}`}
            onOpenDebug={openDebugView}
            onOpenSearch={navigateToSearch}
          />
        )}

        {view === 'debug' && debugVideoId && (
          <DebugDashboard
            key={`debug-${resetKey}-${debugVideoId}`}
            videoId={debugVideoId}
            onBack={navigateToSearch}
            initialFrameNumber={initialFrameNumber}
            initialTrackId={initialTrackId}
          />
        )}
      </main>

      {/* Confirmation Modal */}
      {showResetModal && (
        <div className="reset-modal-overlay" style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999
        }}>
          <div className="reset-modal-content" style={{
            backgroundColor: '#1E293B',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '480px',
            width: '90%',
            color: '#F8FAFC'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#F87171', fontSize: '1.2rem', fontWeight: 600, marginBottom: '16px' }}>
              <AlertTriangle size={26} />
              <span>Reset all data?</span>
            </div>
            <p style={{ color: '#94A3B8', fontSize: '0.95rem', lineHeight: '1.5', marginBottom: '24px' }}>
              This will permanently remove all uploaded videos, indexed embeddings, tracks, metadata, and generated artifacts.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                className="btn-modal-cancel"
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  background: 'transparent',
                  border: '1px solid #475569',
                  color: '#CBD5E1',
                  cursor: 'pointer'
                }}
                onClick={() => setShowResetModal(false)}
                disabled={isResetting}
              >
                Cancel
              </button>
              <button
                className="btn-reset-danger"
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  background: '#DC2626',
                  border: 'none',
                  color: '#FFFFFF',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                onClick={handleConfirmReset}
                disabled={isResetting}
              >
                {isResetting ? <RefreshCw className="spinning" size={16} /> : <Trash2 size={16} />}
                <span>{isResetting ? 'Resetting...' : 'Reset Data'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>ChronoLens Video Intelligence Framework</p>
      </footer>
    </div>
  );
}

export default App;

