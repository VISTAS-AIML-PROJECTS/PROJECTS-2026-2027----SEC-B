from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.derivatives_service import DerivativesService

router = APIRouter(prefix="/api/derivatives", tags=["Derivatives"])

@router.get("/option-chain")
def get_option_chain(
    symbol: str = Query(..., description="Underlying symbol, e.g. NIFTY, RELIANCE, TCS"),
    expiry: Optional[str] = Query(None, description="Contract expiry date YYYY-MM-DD")
):
    return DerivativesService.get_option_chain(symbol=symbol, expiry=expiry)

@router.get("/futures")
def get_futures_dashboard(
    symbol: str = Query(..., description="Underlying symbol, e.g. NIFTY, RELIANCE, TCS")
):
    return DerivativesService.get_futures_dashboard(symbol=symbol)

@router.get("/expiries")
def get_expiries(
    symbol: str = Query(..., description="Underlying symbol")
):
    expiries = DerivativesService.get_available_expiries(symbol)
    return {
        "symbol": symbol.strip().upper(),
        "expiries": expiries,
        "has_derivatives": len(expiries) > 0
    }
