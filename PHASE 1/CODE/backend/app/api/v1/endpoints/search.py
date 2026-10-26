import logging
from fastapi import APIRouter, HTTPException, status
from app.search.search_models import SearchQueryRequest, SearchResponse
from app.search.semantic_search_service import SemanticSearchService

logger = logging.getLogger("chronolens.api.v1.search")

router = APIRouter(tags=["Semantic Retrieval Engine"])


@router.post("/search", response_model=SearchResponse)
@router.post("/api/search", response_model=SearchResponse)
def semantic_search(request: SearchQueryRequest):
    """
    Phase 2.2 Intelligent Semantic Retrieval Endpoint:
    Encodes English text query into OpenCLIP text embedding vector,
    searches dual FAISS indices, applies similarity threshold filtering,
    consolidates duplicate track trajectories, and returns detailed search analytics.
    """
    try:
        logger.info(f"[SearchAPI] Received search request: query='{request.query}', threshold={request.similarityThreshold}")
        return SemanticSearchService.search(request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"[SearchAPI] Search execution error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic retrieval failed: {str(e)}"
        )
