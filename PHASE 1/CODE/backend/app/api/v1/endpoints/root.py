from fastapi import APIRouter
from app.models.schemas import RootResponse
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=RootResponse)
async def get_root() -> RootResponse:
    """
    Returns project metadata.
    """
    return RootResponse(
        project=settings.PROJECT_NAME,
        status=settings.STATUS,
        version=settings.VERSION,
    )
