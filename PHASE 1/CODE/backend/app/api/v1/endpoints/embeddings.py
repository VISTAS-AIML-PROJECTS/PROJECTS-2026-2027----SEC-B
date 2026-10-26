import asyncio
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import EmbeddingsResponse, ErrorResponse
from app.services.debug_service import debug_service

logger = logging.getLogger("chronolens.api.v1.endpoints.embeddings")

router = APIRouter()


@router.get(
    "/video/{videoId}/embeddings",
    response_model=EmbeddingsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video or embeddings not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Phase 2.0 Semantic Embeddings Diagnostics & FAISS Index Metadata"
)
@router.get("/api/video/{videoId}/embeddings", include_in_schema=False)
async def get_video_embeddings(videoId: str):
    """
    Developer-Only Debug Endpoint for Phase 2.0 Semantic Embedding Engine.
    Returns OpenCLIP ViT-L/14 embedding metadata, dual FAISS index sizes, frame explorer list,
    and object crop embedding list.
    """
    try:
        diagnostics = await asyncio.to_thread(debug_service.get_video_embeddings_diagnostics, videoId)
        return diagnostics
    except Exception as e:
        logger.error(f"[EmbeddingsAPI] Exception for videoId={videoId}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching embedding diagnostics: {str(e)}"
        )
