from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional
from app.services.universe_service import UniverseService

router = APIRouter(prefix="/api/universes", tags=["Stock Universes"])

@router.get("")
def list_universes():
    return UniverseService.list_universes()

@router.get("/{universe_id}")
def get_universe_members(
    universe_id: str,
    limit: int = Query(100, ge=10, le=500),
    offset: int = Query(0, ge=0)
):
    res = UniverseService.get_universe_members(universe_id, limit, offset)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/watchlist/add")
def add_to_watchlist(payload: dict = Body(...)):
    token = payload.get("instrument_token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing instrument_token")
    ok = UniverseService.add_to_watchlist(token)
    return {"success": ok, "instrument_token": token}

@router.post("/watchlist/remove")
def remove_from_watchlist(payload: dict = Body(...)):
    token = payload.get("instrument_token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing instrument_token")
    ok = UniverseService.remove_from_watchlist(token)
    return {"success": ok, "instrument_token": token}
