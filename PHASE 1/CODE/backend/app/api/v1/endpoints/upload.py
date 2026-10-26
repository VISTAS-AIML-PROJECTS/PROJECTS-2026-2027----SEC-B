import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, status, HTTPException
from app.models.schemas import UploadResponse, ErrorResponse, ProcessingStatusEnum
from app.services.upload_service import UploadService
from app.services.queue_service import queue_service
from app.core.config import settings
from app.database.mongo import mongo_db

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Unsupported file type or invalid input"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum size limit (2GB)"},
        500: {"model": ErrorResponse, "description": "Server processing error"},
    },
)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    """
    Accepts video uploads (.mp4, .avi, .mov, .mkv) up to 2GB.
    Saves file locally, initializes video status in MongoDB, and enqueues job into processing queue.
    Returns immediately with HTTP 201 Created.
    """
    # 1. Process upload & save locally
    res: UploadResponse = await UploadService.process_video_upload(file)

    saved_file_path = settings.UPLOADS_DIR / res.filename

    # 2. Register initial UPLOADED status in MongoDB
    try:
        mongo_db.upsert_video({
            "videoId": res.video_id,
            "filename": res.original_name,
            "storedFilename": res.filename,
            "size": res.size,
            "status": ProcessingStatusEnum.UPLOADED.value,
            "currentStage": "Uploaded Successfully",
            "message": "Video uploaded successfully. Processing started.",
            "uploadedAt": settings.PROJECT_NAME
        })
    except Exception as e:
        # Log MongoDB failure but keep stored file
        print(f"Warning: Initial MongoDB video registration failed: {str(e)}")

    # 3. Enqueue job into Processing Queue
    await queue_service.enqueue_video(
        video_id=res.video_id,
        video_path=saved_file_path,
        original_filename=res.original_name
    )

    res.message = "Video uploaded successfully. Processing started."
    return res
