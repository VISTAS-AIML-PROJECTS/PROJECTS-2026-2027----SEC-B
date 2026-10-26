from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ProcessingStatusEnum(str, Enum):
    UPLOADED = "UPLOADED"
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    FRAME_EXTRACTION = "FRAME_EXTRACTION"
    OBJECT_DETECTION = "OBJECT_DETECTION"
    OBJECT_TRACKING = "OBJECT_TRACKING"
    AUDIO_TRANSCRIPTION = "AUDIO_TRANSCRIPTION"
    SEMANTIC_EMBEDDING = "SEMANTIC_EMBEDDING"
    DATABASE_SYNC = "DATABASE_SYNC"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RootResponse(BaseModel):
    project: str = Field(..., example="ChronoLens")
    status: str = Field(..., example="running")
    version: str = Field(..., example="0.1")


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")


class UploadResponse(BaseModel):
    video_id: str = Field(..., description="Unique UUID generated for the uploaded video")
    filename: str = Field(..., description="Stored filename on the server filesystem")
    original_name: str = Field(..., description="Original filename uploaded by client")
    size: str = Field(..., description="Human readable file size")
    status: str = Field("uploaded", description="Status of the upload operation")
    message: str = Field("Video uploaded successfully. Processing started.")


class StatusResponse(BaseModel):
    videoId: str
    status: ProcessingStatusEnum
    currentStage: str
    message: str
    updatedAt: str
    error: Optional[str] = None


class VideoMetadata(BaseModel):
    videoId: str
    filename: str
    duration: float
    fps: float
    resolution: str
    codec: str
    size: str
    uploadedAt: Optional[str] = ""
    status: ProcessingStatusEnum = ProcessingStatusEnum.UPLOADED



class FrameMetadata(BaseModel):
    frameNumber: int
    timestamp: float
    imagePath: str
    videoId: str


class DetectionItem(BaseModel):
    trackId: Optional[int] = None
    videoId: str
    frameNumber: int
    timestamp: float
    boundingBox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    objectClass: str


class TrackItem(BaseModel):
    trackId: int
    videoId: str
    objectClass: str
    confidence: float
    startTime: float
    endTime: float
    frames: List[int]
    trajectory: List[Dict[str, Any]] = []


class WordTimestampItem(BaseModel):
    word: str
    startTime: float
    endTime: float


class TranscriptItem(BaseModel):
    videoId: str
    startTime: float
    endTime: float
    text: str
    normalizedText: Optional[str] = None
    language: str = "en"
    segmentId: Optional[str] = None
    confidence: Optional[float] = 1.0
    words: Optional[List[WordTimestampItem]] = None
    whisperModel: Optional[str] = None
    runtime: Optional[str] = None
    computeType: Optional[str] = None
    vadEnabled: Optional[bool] = None
    wordTimestampsEnabled: Optional[bool] = None


class SummaryResponse(BaseModel):
    videoId: str
    videoMetadata: Optional[VideoMetadata] = None
    frameCount: int = 0
    objectsDetected: int = 0
    trackCount: int = 0
    transcriptLength: int = 0
    processingTime: str = "0.00s"
    transcript: List[TranscriptItem] = []
    status: ProcessingStatusEnum = ProcessingStatusEnum.COMPLETED
    error: Optional[str] = None


# --- Debug Dashboard Models ---

class VideoInfoDebug(BaseModel):
    videoId: str
    filename: str
    duration: float
    fps: float
    resolution: str
    fileSize: str
    codec: str
    currentProcessingStatus: str


class FrameExtractionDebug(BaseModel):
    totalFramesExtracted: int
    extractionFps: float = 1.0
    frames: List[FrameMetadata] = []


class YoloDetectionFrameGroup(BaseModel):
    frameNumber: int
    timestamp: float
    detections: List[Dict[str, Any]] = []


class YoloDetectionDebug(BaseModel):
    totalDetections: int
    framesWithDetections: List[YoloDetectionFrameGroup] = []


class ByteTrackItemDebug(BaseModel):
    trackId: int
    objectClass: str
    startTime: float
    endTime: float
    totalFramesTracked: int
    firstFrame: int
    lastFrame: int
    frames: List[int] = []
    trackDurationSec: float


class WhisperTranscriptDebug(BaseModel):
    language: str = "en"
    segments: List[TranscriptItem] = []


class PerformanceTimingsDebug(BaseModel):
    metadataExtractionSec: float = 0.0
    frameExtractionSec: float = 0.0
    yoloDetectionSec: float = 0.0
    byteTrackSec: float = 0.0
    whisperSec: float = 0.0
    mongoDbSec: float = 0.0
    totalProcessingTimeSec: float = 0.0


class StorageSummaryDebug(BaseModel):
    videosCollectionCount: int = 0
    framesCollectionCount: int = 0
    detectionsCollectionCount: int = 0
    tracksCollectionCount: int = 0
    transcriptsCollectionCount: int = 0


class AnnotatedAssetsDebug(BaseModel):
    annotatedVideoUrl: str
    annotatedFramesDirUrl: str


class InferenceConfigurationDebug(BaseModel):
    yoloModel: str = "yolo26m.pt"
    imgsz: int = 1280
    confidence: float = 0.25
    iou: float = 0.45
    device: str = "CUDA"
    byteTrackEnabled: bool = True
    whisperModel: str = "base"
    frameExtractionFps: float = 1.0



class DebugResponse(BaseModel):
    videoInformation: VideoInfoDebug
    frameExtraction: FrameExtractionDebug
    yoloDetection: YoloDetectionDebug
    byteTrackSummary: List[ByteTrackItemDebug] = []
    whisperTranscript: WhisperTranscriptDebug
    processingPerformance: PerformanceTimingsDebug
    storageSummary: StorageSummaryDebug
    annotatedAssets: AnnotatedAssetsDebug
    inferenceConfiguration: InferenceConfigurationDebug = InferenceConfigurationDebug()


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message description")


# --- Track Timeline Inspector Models ---

class TrackDetectionItem(BaseModel):
    frameNumber: int
    timestamp: float
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    frameImage: str
    annotatedFrame: str
    croppedObject: str


class TrackTrajectoryStatistics(BaseModel):
    trackLifetimeSec: float
    averageConfidence: float
    minimumConfidence: float
    maximumConfidence: float
    confidenceVariance: float
    largestBoundingBox: List[float]
    smallestBoundingBox: List[float]
    averageBoundingBoxArea: float
    objectMovementDistance: float
    framesMissing: int
    detectionSuccessRate: float


class TrackDetailsResponse(BaseModel):
    videoId: str
    trackId: int
    objectClass: str
    averageConfidence: float
    minimumConfidence: float
    maximumConfidence: float
    totalFramesTracked: int
    trackDuration: float
    startTime: float
    endTime: float
    detections: List[TrackDetectionItem] = []
    statistics: TrackTrajectoryStatistics


# --- Phase 2.0 Semantic Embedding Engine Schemas ---

class FrameEmbeddingItem(BaseModel):
    videoId: str
    frameNumber: int
    timestamp: float
    faissId: int
    embeddingDimension: int
    embeddingModel: str
    vectorNorm: float
    generationTimeSec: float
    frameImage: str


class ObjectEmbeddingItem(BaseModel):
    videoId: str
    trackId: int
    objectClass: str
    frameNumber: int
    timestamp: float
    faissId: int
    embeddingDimension: int
    embeddingModel: str
    vectorNorm: float
    cropImage: str


class EmbeddingStatistics(BaseModel):
    totalFrameEmbeddings: int
    totalObjectEmbeddings: int
    frameFaissIndexSize: int
    objectFaissIndexSize: int
    embeddingModel: str
    embeddingDimension: int
    averageGenerationTimeSec: float
    totalSemanticProcessingTimeSec: float
    averageVectorNorm: float
    fastestFrameSec: float
    slowestFrameSec: float


class EmbeddingsResponse(BaseModel):
    videoId: str
    embeddingModel: str
    embeddingDimension: int
    totalFrameEmbeddings: int
    totalObjectEmbeddings: int
    frameFaissSize: int
    objectFaissSize: int
    semanticProcessingTimeSec: float
    statistics: EmbeddingStatistics
    frameEmbeddings: List[FrameEmbeddingItem] = []
    objectEmbeddings: List[ObjectEmbeddingItem] = []


class OcrDetectionItem(BaseModel):
    text: str
    normalizedText: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class OcrFrameResultItem(BaseModel):
    videoId: str
    frameNumber: int
    timestamp: float
    detections: List[OcrDetectionItem] = []




