import asyncio
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import StatusResponse, ProcessingStatusEnum, ErrorResponse
from app.database.mongo import mongo_db, MongoDBConnectionError

router = APIRouter()


@router.get(
    "/video/{videoId}/status",
    response_model=StatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video ID not found"},
        500: {"model": ErrorResponse, "description": "Database connection error"}
    }
)
async def get_video_status(videoId: str) -> StatusResponse:
    """
    Returns the current granular processing status and active stage of a video.
    """
    try:
        video_doc = await asyncio.to_thread(mongo_db.get_video, videoId)
        if not video_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video ID '{videoId}' not found."
            )

        raw_status = str(video_doc.get("status", ProcessingStatusEnum.UPLOADED.value)).upper()
        try:
            enum_status = ProcessingStatusEnum(raw_status)
        except ValueError:
            enum_status = ProcessingStatusEnum.COMPLETED if raw_status == "COMPLETED" else ProcessingStatusEnum.UPLOADED

        current_stage = video_doc.get("currentStage", "Processing")
        message = video_doc.get("message", "Processing in progress...")
        updated_at = video_doc.get("updatedAt", "")
        err_msg = video_doc.get("error")

        return StatusResponse(
            videoId=videoId,
            status=enum_status,
            currentStage=current_stage,
            message=message,
            updatedAt=str(updated_at),
            error=err_msg
        )

    except MongoDBConnectionError as err:
        return StatusResponse(
            videoId=videoId,
            status=ProcessingStatusEnum.FAILED,
            currentStage="MongoDB Connection Failed",
            message="MongoDB service is not running locally on port 27017.",
            updatedAt="Now",
            error=f"MongoDB Failure: {str(err)}"
        )
