import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import api_router
from app.services.queue_service import queue_service
from app.database.mongo import mongo_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chronolens.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ChronoLens - AI Powered Video Intelligence Framework (Developer Debug Dashboard)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for storage (frames & debug annotated videos)
app.mount("/static/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include API endpoints
app.include_router(api_router)


from app.services.semantic.openclip_engine import openclip_engine
from app.services.semantic.faiss_manager import faiss_manager

@app.on_event("startup")
async def startup_event():
    """Ensure storage directories exist, initialize semantic engines, and start background queue worker."""
    import torch
    from app.core.config import get_runtime_device
    dev = get_runtime_device().upper()

    print("\n========================================", flush=True)
    print("ChronoLens Runtime Audit", flush=True)
    print(f"PyTorch Version : {torch.__version__}", flush=True)
    print(f"CUDA Build      : {torch.version.cuda}", flush=True)
    print(f"CUDA Available  : {torch.cuda.is_available()}", flush=True)
    print(f"Runtime Device  : {dev}", flush=True)
    if not torch.cuda.is_available():
        print(f"Reason          : CUDA-enabled PyTorch not detected ({torch.__version__})", flush=True)
    print("", flush=True)
    print(f"YOLO Model: YOLO26m", flush=True)
    print(f"YOLO Device: {dev}", flush=True)
    print(f"YOLO Image Size: {settings.YOLO_IMGSZ}", flush=True)
    print(f"YOLO Confidence: {settings.YOLO_CONFIDENCE}", flush=True)
    print(f"YOLO IoU: {settings.YOLO_IOU}", flush=True)
    print("Tracker: ByteTrack", flush=True)
    print(f"OpenCLIP Device : {dev}", flush=True)
    print("FAISS Device    : CPU (Host Memory)", flush=True)
    print("========================================\n", flush=True)



    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    settings.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    settings.DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)


    # Initialize MongoDB connection
    try:
        mongo_db.connect()
    except Exception as e:
        logger.warning(f"MongoDB startup warning: {str(e)}")

    # Initialize Phase 2.0 OpenCLIP ViT-L/14 Engine, Dual FAISS Manager & AttributeReranker
    try:
        openclip_engine.initialize()
        openclip_engine.prewarm()
        faiss_manager.initialize(dimension=openclip_engine.embedding_dim)
        from app.search.attribute_reranker import attribute_reranker
        attribute_reranker._initialize_model()
    except Exception as e:
        logger.error(f"Semantic Engine initialization error: {str(e)}")

    # Audit & Log Startup Data Restoration Status
    try:
        frame_vecs, object_vecs = faiss_manager.get_counts()
        all_vids = mongo_db.get_all_videos()
        completed_vids = [v for v in all_vids if v.get("status") == "COMPLETED"]
        print("\n========================================", flush=True)
        print("ChronoLens Data Restoration Audit", flush=True)
        print(f"MongoDB Status       : CONNECTED ({len(all_vids)} total videos, {len(completed_vids)} completed)", flush=True)
        print(f"FAISS Frame Vectors  : {frame_vecs} (persisted)", flush=True)
        print(f"FAISS Object Vectors : {object_vecs} (persisted)", flush=True)
        print(f"Application State    : READY", flush=True)
        print("========================================\n", flush=True)
    except Exception as audit_err:
        logger.warning(f"Data restoration audit notice: {str(audit_err)}")

    # Start background processing queue worker
    await queue_service.start_worker()



@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully stop background queue worker."""
    logger.info("Shutting down ChronoLens Phase 1 Backend Service...")
    await queue_service.stop_worker()
