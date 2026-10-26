from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.instrument_service import InstrumentService

router = APIRouter(prefix="/api/instruments", tags=["Instruments"])

@router.get("/search")
def search_instruments(
    q: str = Query("", description="Search by symbol, company name, ISIN, etc."),
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE, BSE, NFO, BFO)"),
    segment: Optional[str] = Query(None, description="Filter by segment (NSE-EQ, BSE-EQ, NFO-FUT, NFO-OPT, etc.)"),
    instrument_type: Optional[str] = Query(None, description="EQ, FUTSTK, OPTSTK, FUTIDX, OPTIDX, INDEX"),
    universe_id: Optional[str] = Query(None, description="Filter by universe e.g. NIFTY_50, FNO_STOCKS"),
    has_fno: Optional[bool] = Query(None, description="Filter stocks having F&O contracts"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    sort_by: str = Query("trading_symbol"),
    sort_order: str = Query("asc")
):
    return InstrumentService.search_instruments(
        query=q,
        exchange=exchange,
        segment=segment,
        instrument_type=instrument_type,
        universe_id=universe_id,
        has_fno=has_fno,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/check-fno/{symbol}")
def check_derivatives_availability(symbol: str):
    return InstrumentService.check_derivatives_availability(symbol)

@router.get("/detail/{token:path}")
def get_instrument_detail(token: str):
    inst = InstrumentService.get_instrument_by_token(token)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found in database")
    return inst
