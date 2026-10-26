from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/api/prediction", tags=["AI Market Future Prediction Engine"])

@router.get("/forecast")
def get_forecast(
    symbol: str = Query(..., description="Stock or index trading symbol, e.g. RELIANCE, NIFTY, TCS")
):
    """
    Computes real-time multi-horizon future prediction, ATR price targets,
    confluence indicators, and guardrail validation.
    """
    result = prediction_service.get_forecast_for_symbol(symbol)
    if not result.get("can_predict") and result.get("status") == "DATA_UNAVAILABLE":
        raise HTTPException(status_code=404, detail=result.get("message", "Instrument not found"))
    return result

@router.get("/opportunities")
def get_top_market_opportunities():
    """
    Scans active benchmark and F&O instruments and identifies high-probability
    long and short trading setups based on multi-indicator confluence.
    """
    return prediction_service.get_market_opportunities()
