import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Search,
  Sparkles,
  Film,
  Layers,
  Clock,
  Cpu,
  AlertCircle,
  RefreshCw,
  Crosshair,
  Filter,
  BarChart2,
  Database,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight
} from 'lucide-react';

const PRESET_QUERIES = [
  'person',
  'person wearing blue shirt',
  'person wearing grey shirt',
  'person carrying backpack',
  'person with glasses',
  'What did he say about the bus?',
  'what was said about the library?',
  'find the person saying hello',
  'laptop',
  'tv screen',
  'handbag',
  'bottle',
  'chair',
  'cell phone'
];


const SEARCH_LOADING_STEPS = [
  'Encoding Text Query...',
  'Searching Frame FAISS Index...',
  'Searching Object FAISS Index...',
  'Filtering Similarity Threshold...',
  'Grouping Duplicate Track Trajectories...',
  'Rendering Results...'
];

export const SemanticSearch = ({ onNavigateToFrame, onNavigateToTrack }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStepIdx, setLoadingStepIdx] = useState(0);
  const [searchResults, setSearchResults] = useState(null);
  const [error, setError] = useState(null);
  const [customThreshold, setCustomThreshold] = useState(0.20);
  const stepperIntervalRef = useRef(null);

  const executeSearch = async (searchQuery, thresholdOverride) => {
    const q = searchQuery !== undefined ? searchQuery : query;
    if (!q || !q.toString().trim()) return;

    const queryClean = q.toString().trim();
    setQuery(queryClean);
    setLoading(true);
    setLoadingStepIdx(0);
    setError(null);

    // Animate progressive loading stepper
    stepperIntervalRef.current = setInterval(() => {
      setLoadingStepIdx((prev) => (prev < SEARCH_LOADING_STEPS.length - 1 ? prev + 1 : prev));
    }, 180);

    const thresh = thresholdOverride !== undefined ? thresholdOverride : customThreshold;

    try {
      const res = await axios.post('/api/search', {
        query: queryClean,
        topK: 10,
        similarityThreshold: thresh
      });

      if (stepperIntervalRef.current) clearInterval(stepperIntervalRef.current);
      setLoadingStepIdx(SEARCH_LOADING_STEPS.length - 1);

      if (res.data) {
        setSearchResults(res.data);
      }
    } catch (err) {
      if (stepperIntervalRef.current) clearInterval(stepperIntervalRef.current);
      console.error('Semantic search error:', err);
      setError(err.response?.data?.detail || 'Failed to execute semantic search.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      executeSearch();
    }
  };

  const analytics = searchResults?.analytics;
  const stats = searchResults?.statistics;

  return (
    <div className="semantic-search-container">
      {/* Hero Header */}
      <div className="search-hero-card">
        <h2 className="search-hero-title">Natural Language Video Search</h2>
        <p className="search-hero-desc">
          Search indexed video frames and object trajectories using plain English queries with similarity threshold filtering and duplicate track consolidation.
        </p>

        {/* Input & Action Bar */}
        <div className="search-input-wrapper">
          <div className="search-input-box">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              className="search-input-field"
              placeholder="Type natural language query (e.g. 'person wearing blue shirt', 'laptop', 'person with glasses')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            {query && (
              <button className="search-clear-btn" onClick={() => setQuery('')}>
                ×
              </button>
            )}
          </div>
          <button
            className="btn-search-execute"
            onClick={() => executeSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <>
                <RefreshCw className="spinning" size={16} />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Search size={16} />
                <span>Search</span>
              </>
            )}
          </button>
        </div>

        {/* Preset Query Chips */}
        <div className="query-chips-row">
          <span className="chips-label">Try Example Queries:</span>
          <div className="chips-list">
            {PRESET_QUERIES.map((preset) => (
              <button
                key={preset}
                className={`query-chip ${query === preset ? 'active' : ''}`}
                onClick={() => executeSearch(preset)}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Progressive Search Loading Stepper */}
      {loading && (
        <div className="search-loading-stepper-card">
          <div className="stepper-title">
            <RefreshCw className="spinning text-indigo-400" size={18} />
            <span>Executing Intelligent Semantic Search...</span>
          </div>
          <div className="stepper-grid">
            {SEARCH_LOADING_STEPS.map((stepName, idx) => {
              const isDone = loadingStepIdx > idx;
              const isCurrent = loadingStepIdx === idx;
              return (
                <div
                  key={idx}
                  className={`stepper-item ${isDone ? 'done' : ''} ${isCurrent ? 'active' : ''}`}
                >
                  <span className="stepper-dot"></span>
                  <span className="stepper-text">{stepName}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Redesigned Search Analytics Dashboard Cards */}
      {!loading && analytics && (
        <div className="search-analytics-dashboard-v2">
          <div className="analytics-v2-header">
            <div className="flex items-center gap-2">
              <BarChart2 size={18} className="text-sky-400" />
              <span>Search Analytics & Hybrid Retrieval Metrics</span>
            </div>
            <div className="ranking-weights-badge">
              <span>Weights: 75% Semantic • 15% YOLO • 10% Persistence</span>
            </div>
          </div>
          <div className="analytics-cards-grid">
            <div className="stat-metric-card candidates">
              <span className="metric-title">Candidates</span>
              <span className="metric-value">{analytics.candidatesRetrieved}</span>
              <span className="metric-subtitle">FAISS Vector Hits</span>
            </div>

            <div className="stat-metric-card rejected">
              <span className="metric-title">Filtered</span>
              <span className="metric-value">{analytics.resultsRejectedByThreshold}</span>
              <span className="metric-subtitle">Below Threshold</span>
            </div>

            <div className="stat-metric-card accepted">
              <span className="metric-title">Accepted</span>
              <span className="metric-value">{analytics.acceptedResults}</span>
              <span className="metric-subtitle">Passed Threshold</span>
            </div>

            <div className="stat-metric-card grouped">
              <span className="metric-title">Grouped</span>
              <span className="metric-value">{analytics.groupedTracks}</span>
              <span className="metric-subtitle">Track Trajectories</span>
            </div>

            <div className="stat-metric-card returned">
              <span className="metric-title">Returned</span>
              <span className="metric-value">{analytics.finalReturnedResults}</span>
              <span className="metric-subtitle">Result Cards</span>
            </div>

            <div className="stat-metric-card threshold">
              <span className="metric-title">Threshold</span>
              <span className="metric-value">{analytics.similarityThreshold}</span>
              <span className="metric-subtitle">Min Cosine Sim</span>
            </div>
          </div>

          {stats && (
            <div className="search-stats-bar mt-3">
              <div className="stats-item">
                <span className="stats-label">Query Text Embedding:</span>
                <span className="stats-val">{stats.queryEmbeddingTimeMs}ms</span>
              </div>
              <div className="stats-divider">•</div>
              <div className="stats-item">
                <span className="stats-label">FAISS Frame Search:</span>
                <span className="stats-val">{stats.frameSearchTimeMs}ms</span>
              </div>
              <div className="stats-divider">•</div>
              <div className="stats-item">
                <span className="stats-label">FAISS Object Search:</span>
                <span className="stats-val">{stats.objectSearchTimeMs}ms</span>
              </div>
              <div className="stats-divider">•</div>
              <div className="stats-item">
                <span className="stats-label">Hybrid Ranking:</span>
                <span className="stats-val">{analytics.rankingTimeMs || 0.0}ms</span>
              </div>
              <div className="stats-divider">•</div>
              <div className="stats-item highlight">
                <span className="stats-label">Total Retrieval Latency:</span>
                <span className="stats-val">{stats.totalSearchTimeMs}ms</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Box */}
      {error && (
        <div className="debug-card error-box my-4">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Friendly Empty State */}
      {!loading && searchResults && searchResults.analytics && searchResults.analytics.finalReturnedResults === 0 && (
        (searchResults.route === "SPEECH" || searchResults.analytics?.route === "SPEECH") ? (
          <div className="empty-results-card-v2">
            <div className="empty-header">
              <XCircle size={32} className="text-amber-400" />
              <h3>No speech matches found in indexed transcript.</h3>
            </div>
            <p className="empty-desc">
              {(searchResults.speechMode === "EXACT_PHRASE" || searchResults.analytics?.speechMode === "EXACT_PHRASE")
                ? `No exact spoken match found for phrase: "${searchResults.targetPhrase || searchResults.analytics?.targetPhrase || searchResults.query}"`
                : `No transcript matches found for query: "${searchResults.query}"`}
            </p>
            <div className="empty-suggestions-box">
              <div className="suggestions-title">
                <HelpCircle size={16} />
                <span>Helpful Suggestions for Speech Search:</span>
              </div>
              <ul className="suggestions-list">
                <li>• Verify exact words spoken in the video audio.</li>
                <li>• Ensure Whisper audio indexing has completed for the target video.</li>
                <li>• Try searching for key spoken words without quotes.</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="empty-results-card-v2">
            <div className="empty-header">
              <XCircle size={32} className="text-amber-400" />
              <h3>No semantic matches found above the current threshold.</h3>
            </div>
            <p className="empty-desc">
              All vector candidates retrieved scored below the active similarity threshold of <strong>{searchResults.similarityThreshold}</strong> for query "<strong>{searchResults.query}</strong>".
            </p>
            <div className="empty-suggestions-box">
              <div className="suggestions-title">
                <HelpCircle size={16} />
                <span>Helpful Suggestions to Find Matches:</span>
              </div>
              <ul className="suggestions-list">
                <li>• Try another description or query keyword (e.g. "person", "road", "cyclist").</li>
                <li>• Lower the similarity threshold in Developer Controls.</li>
                <li>• Increase Top-K search parameter to retrieve more candidate vectors.</li>
              </ul>
            </div>
          </div>
        )
      )}

      {/* Search Results Display */}
      {!loading && searchResults && searchResults.analytics && searchResults.analytics.finalReturnedResults > 0 && (
        <div className="search-results-section">
          {/* 1. FRAME LEVEL RESULTS */}
          {searchResults.frameResults.length > 0 && (
            <div className="results-group-card">
              <div className="results-group-header">
                <div className="group-title">
                  <Film size={20} />
                  <span>Frame Results ({searchResults.frameResults.length} matches)</span>
                </div>
                <span className="group-subtitle">Ranked by Phase 2.3 Hybrid Score & Enriched with Phase 2.4 Visual Attributes & Scene Context</span>
              </div>

              <div className="results-grid">
                {searchResults.frameResults.map((frameRes, idx) => (
                  <div key={idx} className="result-card frame-card">
                    {/* Header Row with Index Origin Badge & Rank Position */}
                    <div className="card-header-row">
                      <div className="flex items-center gap-1.5">
                        <span className="rank-position-badge">Rank #{frameRes.rankingPosition || idx + 1}</span>
                        <div className="origin-badge frame-origin-badge">
                          <Database size={10} />
                          <span>
                            {frameRes.indexOrigin?.includes("OCR")
                              ? "OCR / PaddleOCR"
                              : frameRes.indexOrigin === "SpeechTranscript/Whisper"
                              ? "SPEECH / Whisper"
                              : "FRAME FAISS"}
                          </span>
                        </div>
                      </div>
                      <span className={`confidence-badge-pill ${(frameRes.confidenceBadge || '').toLowerCase().replace(' ', '-')}`}>
                        {frameRes.confidenceBadge || 'Match'}
                      </span>
                    </div>

                    {/* Playable Trimmed Video Clip Player */}
                    {frameRes.videoClipUrl && (
                      <div className="result-video-clip-container">
                        <div className="clip-header-bar">
                          <span className="clip-title-tag">
                            <span className="live-clip-pulse"></span>
                            <Film size={13} />
                            <span>Trimmed Event Clip ({frameRes.clipStartTime ?? 0}s → {frameRes.clipEndTime ?? 0}s)</span>
                          </span>
                          <span className="clip-dur-badge">
                            <Clock size={11} />
                            <span>{frameRes.clipDuration ? `${frameRes.clipDuration}s` : '10s'}</span>
                          </span>
                        </div>
                        <div className="clip-player-wrapper">
                          <video
                            controls
                            preload="metadata"
                            src={frameRes.videoClipUrl}
                            className="result-clip-player"
                          />
                        </div>
                      </div>
                    )}

                    {/* Frame Evidence Thumbnail Section */}
                    <div className="section-label-bar">
                      <Film size={11} />
                      <span>Annotated Frame Evidence</span>
                    </div>
                    <div className="card-thumb-container">
                      <img
                        src={frameRes.thumbnail}
                        alt={`Frame ${frameRes.frameNumber}`}
                        className="result-thumb-img"
                        onError={(e) => { e.target.src = 'https://via.placeholder.com/320x180?text=Frame+Thumbnail'; }}
                      />
                      <div className="similarity-pill hybrid-score-pill">
                        Final Score: {frameRes.finalScorePercentage || frameRes.similarityPercentage}
                      </div>
                    </div>

                    <div className="result-card-body">
                      <div className="res-row main">
                        <span className="res-time-badge">
                          <Clock size={12} />
                          <span>Frame #{frameRes.frameNumber} • {frameRes.timestamp}s</span>
                        </span>
                        <span className="res-sim-sub">Sim: {frameRes.similarityPercentage}</span>
                      </div>

                      {/* Phase 2.4 Scene Context */}
                      {frameRes.sceneContext && (
                        <div className="phase24-metadata-box scene-metadata-box">
                          <div className="phase24-box-title">Phase 2.4 Scene Context</div>
                          <div className="phase24-pills-row">
                            {frameRes.sceneContext.environment && (
                              <span className="phase24-pill env-pill">
                                Environment: <strong>{frameRes.sceneContext.environment}</strong>
                              </span>
                            )}
                            {frameRes.sceneContext.locationType && (
                              <span className="phase24-pill loc-pill">
                                Scene: <strong>{frameRes.sceneContext.locationType}</strong> {frameRes.sceneContext.confidence ? `(${Math.round(frameRes.sceneContext.confidence * 100)}%)` : ''}
                              </span>
                            )}
                            {frameRes.sceneContext.crowdLevel && (
                              <span className="phase24-pill crowd-pill">
                                Crowd: <strong>{frameRes.sceneContext.crowdLevel}</strong>
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Ranking Signal Breakdown */}
                      <div className="ranking-signals-grid">
                        <div className="signal-item">
                          <span className="sig-lbl">Semantic</span>
                          <span className="sig-val">{frameRes.similarityPercentage}</span>
                        </div>
                        <div className="signal-item">
                          <span className="sig-lbl">YOLO Conf</span>
                          <span className="sig-val">{Math.round((frameRes.averageYOLOConfidence || 0) * 100)}%</span>
                        </div>
                        <div className="signal-item">
                          <span className="sig-lbl">Persistence</span>
                          <span className="sig-val">{Math.round((frameRes.trackPersistence || 0.5) * 100)}%</span>
                        </div>
                      </div>

                      {frameRes.explanation && (
                        <div className="ranking-explanation-box">
                          <span>💡 {frameRes.explanation}</span>
                        </div>
                      )}

                      <div className="res-row sub mt-2">
                        <span>Video ID: {frameRes.videoId}</span>
                      </div>
                      <button
                        className="btn-result-action"
                        onClick={() => onNavigateToFrame && onNavigateToFrame(frameRes.videoId, frameRes.frameNumber)}
                      >
                        <Cpu size={14} />
                        <span>Open in Debug Dashboard</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. OBJECT LEVEL RESULTS (Consolidated Trajectories) */}
          {searchResults.objectResults.length > 0 && (
            <div className="results-group-card mt-6">
              <div className="results-group-header">
                <div className="group-title">
                  <Layers size={20} />
                  <span>Consolidated Object Trajectories ({searchResults.objectResults.length} tracks)</span>
                </div>
                <span className="group-subtitle">Grouped by ByteTrack ID & Ranked by Phase 2.3 Hybrid Score</span>
              </div>

              <div className="results-grid">
                {searchResults.objectResults.map((objRes, idx) => (
                  <div key={idx} className="result-card object-card">
                    {/* Header Row with Index Origin Badge & Rank Position */}
                    <div className="card-header-row">
                      <div className="flex items-center gap-1.5">
                        <span className="rank-position-badge">Rank #{objRes.rankingPosition || idx + 1}</span>
                        <div className="origin-badge object-origin-badge">
                          <Database size={10} />
                          <span>OBJECT FAISS</span>
                        </div>
                        <span className="res-track-badge">Track #{objRes.trackId}</span>
                      </div>
                      <span className={`confidence-badge-pill ${(objRes.confidenceBadge || '').toLowerCase().replace(' ', '-')}`}>
                        {objRes.confidenceBadge || 'Match'}
                      </span>
                    </div>

                    {/* Playable Trimmed Video Clip Player */}
                    {objRes.videoClipUrl && (
                      <div className="result-video-clip-container">
                        <div className="clip-header-bar">
                          <span className="clip-title-tag">
                            <span className="live-clip-pulse"></span>
                            <Film size={13} />
                            <span>Trimmed Event Clip ({objRes.clipStartTime ?? 0}s → {objRes.clipEndTime ?? 0}s)</span>
                          </span>
                          <span className="clip-dur-badge">
                            <Clock size={11} />
                            <span>{objRes.clipDuration ? `${objRes.clipDuration}s` : '10s'}</span>
                          </span>
                        </div>
                        <div className="clip-player-wrapper">
                          <video
                            controls
                            preload="metadata"
                            src={objRes.videoClipUrl}
                            className="result-clip-player"
                          />
                        </div>
                      </div>
                    )}

                    {/* Track Representative Crop Section */}
                    <div className="section-label-bar">
                      <Crosshair size={11} />
                      <span>Representative Track Crop</span>
                    </div>
                    <div className="card-thumb-container crop-container">
                      <img
                        src={objRes.cropThumbnail || objRes.annotatedFrame}
                        alt={`Track ${objRes.trackId}`}
                        className="result-crop-img"
                        onError={(e) => {
                          if (objRes.annotatedFrame && e.target.src !== objRes.annotatedFrame && !e.target.src.includes(objRes.annotatedFrame)) {
                            e.target.src = objRes.annotatedFrame;
                          } else {
                            e.target.style.display = 'none';
                            const parent = e.target.parentElement;
                            if (parent) {
                              let fb = parent.querySelector('.crop-fallback-text');
                              if (!fb) {
                                fb = document.createElement('div');
                                fb.className = 'crop-fallback-text';
                                fb.innerHTML = '<span>Evidence Frame Unavailable</span>';
                                parent.insertBefore(fb, parent.firstChild);
                              }
                            }
                          }
                        }}
                      />
                      <div className="similarity-pill object-pill hybrid-score-pill">
                        Final Score: {objRes.finalScorePercentage || objRes.similarityPercentage}
                      </div>
                    </div>

                    <div className="result-card-body">
                      <div className="res-row main">
                        <span className="res-class-badge">{objRes.objectClass.toUpperCase()}</span>
                        <span className="res-sim-sub">Sim: {objRes.similarityPercentage}</span>
                      </div>

                      <div className="trajectory-stats-box">
                        <div><strong>Appearance:</strong> {objRes.appearanceCount} Frames</div>
                        <div><strong>Time Span:</strong> {objRes.firstSeen}s → {objRes.lastSeen}s ({objRes.trackDurationSec}s)</div>
                        <div><strong>Rep Frame:</strong> Frame #{objRes.frameNumber} ({objRes.timestamp}s)</div>
                      </div>

                      {/* Phase 2.4 Visual Attributes */}
                      {objRes.visualAttributes && (
                        <div className="phase24-metadata-box attr-metadata-box">
                          <div className="phase24-box-title">Phase 2.4 Visual Attributes</div>
                          <div className="phase24-pills-row">
                            {objRes.visualAttributes.upperClothingColor && objRes.visualAttributes.upperClothingColor !== 'unknown' && (
                              <span className="phase24-pill upper-pill">
                                Upper: <strong>{objRes.visualAttributes.upperClothingColor}</strong> {objRes.visualAttributes.upperClothingConfidence ? `(${Math.round(objRes.visualAttributes.upperClothingConfidence * 100)}%)` : ''}
                              </span>
                            )}
                            {objRes.visualAttributes.lowerClothingColor && objRes.visualAttributes.lowerClothingColor !== 'unknown' && (
                              <span className="phase24-pill lower-pill">
                                Lower: <strong>{objRes.visualAttributes.lowerClothingColor}</strong> {objRes.visualAttributes.lowerClothingConfidence ? `(${Math.round(objRes.visualAttributes.lowerClothingConfidence * 100)}%)` : ''}
                              </span>
                            )}
                            {objRes.visualAttributes.vehicleColor && objRes.visualAttributes.vehicleColor !== 'unknown' && (
                              <span className="phase24-pill vehicle-pill">
                                Color: <strong>{objRes.visualAttributes.vehicleColor}</strong> {objRes.visualAttributes.vehicleColorConfidence ? `(${Math.round(objRes.visualAttributes.vehicleColorConfidence * 100)}%)` : ''}
                              </span>
                            )}
                            {objRes.visualAttributes.hasBackpack !== undefined && objRes.visualAttributes.hasBackpack !== null && (
                              <span className={`phase24-pill ${objRes.visualAttributes.hasBackpack ? 'acc-yes' : 'acc-no'}`}>
                                Backpack: <strong>{objRes.visualAttributes.hasBackpack ? 'Yes' : 'No'}</strong> {objRes.visualAttributes.accessoryConfidence ? `(${Math.round(objRes.visualAttributes.accessoryConfidence * 100)}%)` : ''}
                              </span>
                            )}
                            {objRes.visualAttributes.hasHelmet !== undefined && objRes.visualAttributes.hasHelmet !== null && (
                              <span className={`phase24-pill ${objRes.visualAttributes.hasHelmet ? 'acc-yes' : 'acc-no'}`}>
                                Helmet: <strong>{objRes.visualAttributes.hasHelmet ? 'Yes' : 'No'}</strong>
                              </span>
                            )}
                            {objRes.visualAttributes.hasGlasses !== undefined && objRes.visualAttributes.hasGlasses !== null && (
                              <span className={`phase24-pill ${objRes.visualAttributes.hasGlasses ? 'acc-yes' : 'acc-no'}`}>
                                Glasses: <strong>{objRes.visualAttributes.hasGlasses ? 'Yes' : 'No'}</strong>
                              </span>
                            )}
                          </div>
                        </div>
                      )}


                      {/* Ranking Signal Breakdown */}
                      <div className="ranking-signals-grid">
                        <div className="signal-item">
                          <span className="sig-lbl">Semantic</span>
                          <span className="sig-val">{objRes.similarityPercentage}</span>
                        </div>
                        <div className="signal-item">
                          <span className="sig-lbl">YOLO Conf</span>
                          <span className="sig-val">{Math.round((objRes.averageYOLOConfidence || 0) * 100)}%</span>
                        </div>
                        <div className="signal-item">
                          <span className="sig-lbl">Persistence</span>
                          <span className="sig-val">{Math.round((objRes.trackPersistence || 0) * 100)}%</span>
                        </div>
                      </div>

                      {objRes.explanation && (
                        <div className="ranking-explanation-box">
                          <span>💡 {objRes.explanation}</span>
                        </div>
                      )}

                      <div className="res-row sub mt-2">
                        <span>Video: {objRes.videoId}</span>
                      </div>

                      <button
                        className="btn-result-action object-btn"
                        onClick={() => onNavigateToTrack && onNavigateToTrack(objRes.videoId, objRes.trackId)}
                      >
                        <Crosshair size={14} />
                        <span>Inspect Track Trajectory</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
