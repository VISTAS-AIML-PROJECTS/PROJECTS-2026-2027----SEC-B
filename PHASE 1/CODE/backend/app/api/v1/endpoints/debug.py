import os
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from app.core.config import settings
from app.models.schemas import DebugResponse, ErrorResponse, TrackDetailsResponse
from app.services.debug_service import debug_service
from app.database.mongo import MongoDBConnectionError

router = APIRouter()


@router.get(
    "/video/{videoId}/debug",
    response_model=DebugResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video ID not found"},
        500: {"model": ErrorResponse, "description": "Database query or debug generation error"}
    }
)
async def get_video_debug(videoId: str) -> DebugResponse:
    """
    Returns complete development debug diagnostics, stage execution timings,
    YOLO detection breakdown, ByteTrack summaries, storage counts, and annotated video URLs.
    """
    try:
        debug_payload = await asyncio.to_thread(debug_service.get_debug_diagnostics, videoId)
        if not debug_payload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Debug diagnostics for '{videoId}' not found."
            )
        return debug_payload
    except MongoDBConnectionError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB Failure: {str(err)}"
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug generation failed: {str(err)}"
        )


@router.get(
    "/video/{videoId}/track/{trackId}",
    response_model=TrackDetailsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Track ID or Video ID not found"},
        500: {"model": ErrorResponse, "description": "Trajectory query error"}
    }
)
@router.get("/api/video/{videoId}/track/{trackId}", response_model=TrackDetailsResponse)
async def get_track_details(videoId: str, trackId: int) -> TrackDetailsResponse:
    """
    Returns single ByteTrack trajectory details across video frames.
    Computes spatial-temporal trajectory statistics and lazily generates cropped object thumbnails.
    """
    try:
        track_payload = await asyncio.to_thread(debug_service.get_track_timeline_diagnostics, videoId, trackId)
        if not track_payload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track ID '{trackId}' for video '{videoId}' not found."
            )
        return track_payload
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Track trajectory retrieval failed: {str(err)}"
        )


@router.get("/video/{videoId}/stream")
@router.get("/api/video/{videoId}/stream")
async def stream_annotated_video(videoId: str, request: Request):
    """
    HTTP Range-capable streaming endpoint (206 Partial Content).
    Enables native HTML5 video playback and duration parsing across all browsers.
    Supports both /video/... and /api/video/... routes.
    """
    video_path = settings.DEBUG_DIR / videoId / "annotated_video.mp4"
    if not video_path.exists():
        try:
            await asyncio.to_thread(debug_service.get_debug_diagnostics, videoId)
        except Exception:
            pass

    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotated video for '{videoId}' not found."
        )

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        try:
            bytes_type, byte_range = range_header.split("=")
            start_str, end_str = byte_range.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            chunk_size = (end - start) + 1

            with open(video_path, "rb") as video_file:
                video_file.seek(start)
                data = video_file.read(chunk_size)

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
            }
            return Response(content=data, status_code=206, headers=headers)
        except Exception:
            pass

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )

