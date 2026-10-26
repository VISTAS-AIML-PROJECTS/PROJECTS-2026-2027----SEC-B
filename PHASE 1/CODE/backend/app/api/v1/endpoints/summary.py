import asyncio
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import SummaryResponse, ErrorResponse
from app.database.mongo import mongo_db, MongoDBConnectionError

router = APIRouter()


@router.get(
    "/video/{videoId}/summary",
    response_model=SummaryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video ID not found"},
        500: {"model": ErrorResponse, "description": "Database query error"}
    }
)
async def get_video_summary(videoId: str) -> SummaryResponse:
    """
    Returns aggregated metadata, frame count, detected objects, track count,
    and transcript details for a processed video.
    """
    try:
        summary_data = await asyncio.to_thread(mongo_db.get_summary, videoId)
        if not summary_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video summary for '{videoId}' not found."
            )

        return SummaryResponse(**summary_data)
    except MongoDBConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Failure: {str(err)}"
        )
