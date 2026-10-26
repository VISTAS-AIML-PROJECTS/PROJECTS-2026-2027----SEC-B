from fastapi import APIRouter
from app.api.v1.endpoints import root, health, upload, status, summary, debug, embeddings, developer, search

api_router = APIRouter()

api_router.include_router(root.router, tags=["Root"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(status.router, tags=["Status"])
api_router.include_router(summary.router, tags=["Summary"])
api_router.include_router(debug.router, tags=["Debug"])
api_router.include_router(embeddings.router, tags=["Semantic Embeddings"])
api_router.include_router(developer.router, tags=["Developer Utilities"])
api_router.include_router(search.router, tags=["Semantic Retrieval"])
