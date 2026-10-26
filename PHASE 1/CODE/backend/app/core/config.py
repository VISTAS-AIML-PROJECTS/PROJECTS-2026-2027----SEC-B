import os
from pathlib import Path
from typing import Set, List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Absolute path to backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DEFAULT_DIR = BACKEND_DIR / "app" / "uploads"
STORAGE_DEFAULT_DIR = BACKEND_DIR / "storage"


class Settings(BaseSettings):
    PROJECT_NAME: str = "ChronoLens"
    VERSION: str = "0.1"
    STATUS: str = "running"
    
    # Storage & Upload limits
    BASE_DIR: Path = BACKEND_DIR
    MAX_UPLOAD_SIZE_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    ALLOWED_EXTENSIONS: Set[str] = {"mp4", "avi", "mov", "mkv"}
    UPLOADS_DIR: Path = UPLOADS_DEFAULT_DIR
    STORAGE_DIR: Path = STORAGE_DEFAULT_DIR
    FRAMES_DIR: Path = STORAGE_DEFAULT_DIR / "frames"
    VIDEOS_DIR: Path = STORAGE_DEFAULT_DIR / "videos"
    DEBUG_DIR: Path = STORAGE_DEFAULT_DIR / "debug"
    CLIPS_DIR: Path = STORAGE_DEFAULT_DIR / "clips"
    FAISS_DIR: Path = STORAGE_DEFAULT_DIR / "faiss"
    FRAME_FAISS_PATH: Path = STORAGE_DEFAULT_DIR / "faiss" / "frame.index"
    OBJECT_FAISS_PATH: Path = STORAGE_DEFAULT_DIR / "faiss" / "object.index"

    # MongoDB Database Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "chronolens"

    # Locked Phase 1 Deterministic Inference Pipeline Settings
    YOLO_MODEL: str = "yolo26m.pt"
    YOLO_IMGSZ: int = 1280
    YOLO_CONFIDENCE: float = 0.25
    YOLO_IOU: float = 0.45
    FRAME_EXTRACTION_FPS: float = 1.0
    BYTETRACK_ENABLED: bool = True
    WHISPER_MODEL: str = "large-v3-turbo"
    WHISPER_COMPUTE_TYPE: str = "float16"
    WHISPER_VAD_FILTER: bool = True
    WHISPER_LANGUAGE: Optional[str] = "en"
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_TEMPERATURE: float = 0.0
    WHISPER_CONDITION_ON_PREVIOUS_TEXT: bool = True
    WHISPER_NO_SPEECH_THRESHOLD: float = 0.60
    WHISPER_COMPRESSION_RATIO_THRESHOLD: float = 2.4
    WHISPER_LOG_PROB_THRESHOLD: float = -1.0
    INFERENCE_DEVICE: str = "CUDA"


    # Phase 2.0 OpenCLIP & FAISS Settings
    OPENCLIP_MODEL: str = "ViT-L-14"
    OPENCLIP_PRETRAINED: str = "laion2b_s32b_b82k"

    # Phase 2.2 Retrieval & Refinement Settings
    SIMILARITY_THRESHOLD: float = 0.20

    # Phase 2.3 Hybrid Ranking Settings
    RANKING_WEIGHT_SEMANTIC: float = 0.75
    RANKING_WEIGHT_YOLO: float = 0.15
    RANKING_WEIGHT_PERSISTENCE: float = 0.10

    # Phase 3.19 Feature Flags for Dedicated Attribute Routing & PP-Human PAR
    ENABLE_ATTRIBUTE_V2: bool = True
    ENABLE_CLOTHING_COLOR_V2: bool = True
    ENABLE_GLASSES_PAR: bool = False
    ENABLE_HAT_PAR: bool = False
    ENABLE_BAG_PAR: bool = False


    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ]

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return {ext.strip().lstrip(".").lower() for ext in v.split(",") if ext.strip()}
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def get_runtime_device() -> str:
    """Returns 'cuda' if PyTorch CUDA acceleration is available, else 'cpu'."""
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


# Ensure required storage directories exist
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
settings.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
settings.DEBUG_DIR.mkdir(parents=True, exist_ok=True)
settings.CLIPS_DIR.mkdir(parents=True, exist_ok=True)
settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)
