from fastapi import APIRouter, Query
from app.services.ml_model_service import MLModelService

router = APIRouter(prefix="/api/models", tags=["Model Lab & Benchmarking"])

@router.get("/benchmarks")
def get_benchmarks():
    return MLModelService.get_benchmarks()

@router.get("/inference")
def run_model_inference(
    symbol: str = Query(..., description="Stock or index symbol"),
    strategy: str = Query("global", description="global, sector, or per_stock")
):
    return MLModelService.evaluate_inference(symbol=symbol, strategy=strategy)
