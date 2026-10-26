from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="English natural language query string", example="person riding bicycle")
    topK: int = Field(10, description="Top-K search results per index (default: 10)", ge=1, le=500)
    similarityThreshold: Optional[float] = Field(
        None,
        description="Optional similarity threshold override (default: 0.20)",
        ge=0.0,
        le=1.0
    )


class FrameSearchResult(BaseModel):
    videoId: str
    frameNumber: int
    timestamp: float
    thumbnail: str
    annotatedFrame: Optional[str] = None
    faissId: int
    similarityScore: float
    similarityPercentage: str
    indexOrigin: str = "Frame FAISS Index"
    # Phase 2.3 Hybrid Ranking extensions
    finalScore: float = 0.0
    finalScorePercentage: str = "0.00%"
    rankingPosition: int = 1
    confidenceBadge: str = "Possible Match"
    explanation: str = "High semantic similarity match."
    averageYOLOConfidence: float = 0.0
    trackPersistence: float = 0.0
    # Phase 2.4 Visual Attribute & Scene extensions
    sceneContext: Optional[Dict[str, Any]] = None
    # Video Clip Extension
    videoClipUrl: Optional[str] = None
    clipStartTime: Optional[float] = None
    clipEndTime: Optional[float] = None
    clipDuration: Optional[float] = None
    evidenceType: str = "frame_evidence"


class ObjectSearchResult(BaseModel):

    videoId: str
    trackId: int
    objectClass: str
    frameNumber: int
    timestamp: float
    cropThumbnail: str
    annotatedFrame: Optional[str] = None
    bbox: Optional[List[float]] = None
    evidenceType: str = "track_crop"
    faissId: int
    similarityScore: float
    similarityPercentage: str
    appearanceCount: int = 1
    firstSeen: float = 0.0
    lastSeen: float = 0.0
    trackDurationSec: float = 0.0
    indexOrigin: str = "Object FAISS Index"
    # Phase 2.3 Hybrid Ranking extensions
    finalScore: float = 0.0
    finalScorePercentage: str = "0.00%"
    rankingPosition: int = 1
    confidenceBadge: str = "Possible Match"
    explanation: str = "Strong semantic similarity with persistent track presence."
    averageYOLOConfidence: float = 0.0
    trackPersistence: float = 0.0
    bestSimilarityScore: float = 0.0
    bestSimilarityPercentage: str = "0.00%"
    # Phase 2.4 Visual Attribute & Scene extensions
    visualAttributes: Optional[Dict[str, Any]] = None
    siglipScore: Optional[float] = None
    siglipCosSim: Optional[float] = None
    # Video Clip Extension
    videoClipUrl: Optional[str] = None
    clipStartTime: Optional[float] = None
    clipEndTime: Optional[float] = None
    clipDuration: Optional[float] = None



class SearchStatistics(BaseModel):
    queryParsingTimeMs: float = 0.0
    modelInitializationTimeMs: float = 0.0
    tokenizerTimeMs: float = 0.0
    queryEmbeddingTimeMs: float = 0.0
    gpuSynchronizationTimeMs: float = 0.0
    frameSearchTimeMs: float = 0.0
    objectSearchTimeMs: float = 0.0
    thresholdFilteringTimeMs: float = 0.0
    metadataLookupTimeMs: float = 0.0
    trackGroupingTimeMs: float = 0.0
    attributeVerificationTimeMs: float = 0.0
    relationalVerificationTimeMs: float = 0.0
    resultEnrichmentTimeMs: float = 0.0
    serializationTimeMs: float = 0.0
    otherUnaccountedTimeMs: float = 0.0
    totalSearchTimeMs: float = 0.0


class SearchAnalytics(BaseModel):
    candidatesRetrieved: int
    resultsRejectedByThreshold: int
    acceptedResults: int
    groupedTracks: int
    finalReturnedResults: int
    similarityThreshold: float
    filteringTimeMs: float
    groupingTimeMs: float
    rankingTimeMs: float = 0.0
    weightSemantic: float = 0.75
    weightYOLO: float = 0.15
    weightPersistence: float = 0.10
    totalRetrievalTimeMs: float

    # Phase 1 High-Resolution Stage Breakdown Extensions
    queryParsingTimeMs: float = 0.0
    modelInitializationTimeMs: float = 0.0
    tokenizerTimeMs: float = 0.0
    queryEmbeddingTimeMs: float = 0.0
    gpuSynchronizationTimeMs: float = 0.0
    frameSearchTimeMs: float = 0.0
    objectSearchTimeMs: float = 0.0
    thresholdFilteringTimeMs: float = 0.0
    metadataLookupTimeMs: float = 0.0
    trackGroupingTimeMs: float = 0.0
    attributeVerificationTimeMs: float = 0.0
    relationalVerificationTimeMs: float = 0.0
    resultEnrichmentTimeMs: float = 0.0
    serializationTimeMs: float = 0.0
    otherUnaccountedTimeMs: float = 0.0

    route: Optional[str] = "GENERIC_SEMANTIC"
    speechMode: Optional[str] = None
    targetPhrase: Optional[str] = None
    matchingMethod: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    topK: int
    similarityThreshold: float
    frameResults: List[FrameSearchResult]
    objectResults: List[ObjectSearchResult]
    statistics: SearchStatistics
    analytics: SearchAnalytics
    route: Optional[str] = "GENERIC_SEMANTIC"
    speechMode: Optional[str] = None
    targetPhrase: Optional[str] = None
    matchingMethod: Optional[str] = None

