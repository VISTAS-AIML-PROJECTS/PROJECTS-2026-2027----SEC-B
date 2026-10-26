import logging
from fastapi import APIRouter, HTTPException, status
from app.services.reset_service import DevelopmentResetService

logger = logging.getLogger("chronolens.api.v1.developer")

router = APIRouter(tags=["Developer Utilities"])


@router.post("/reset")
@router.post("/developer/reset")
@router.post("/api/developer/reset")
def reset_developer_data():

    """
    Developer-Only Endpoint: Resets development data.
    Purges uploads, frames, audio, debug assets, FAISS indices, and MongoDB collections.
    Restores clean empty state for benchmarking.
    """
    logger.info("[DeveloperAPI] Received POST reset request")
    result = DevelopmentResetService.reset_all_development_data()
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )
    return result
