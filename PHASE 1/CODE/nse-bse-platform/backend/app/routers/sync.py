import asyncio
from fastapi import APIRouter, BackgroundTasks, Query
from typing import Optional
from app.sync.sync_service import sync_service
from app.database import get_db

router = APIRouter(prefix="/api/sync", tags=["Instrument Master Sync"])

@router.post("/trigger")
async def trigger_sync(background_tasks: BackgroundTasks, provider: Optional[str] = None):
    """
    Triggers the Instrument Master Synchronization Service.
    Downloads, validates, normalizes, detects changes and updates database.
    """
    if sync_service.is_syncing:
        return {"status": "ALREADY_RUNNING", "message": "Synchronization is already underway."}

    # Run in background task so API responds immediately
    background_tasks.add_task(sync_service.run_sync, provider)
    return {
        "status": "STARTED",
        "message": f"Instrument Master synchronization started with provider '{provider or 'kite'}'.",
        "timestamp": asyncio.get_event_loop().time()
    }

@router.get("/status")
def get_sync_status():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_history ORDER BY id DESC LIMIT 1")
        last_sync = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_active FROM instruments WHERE is_active = 1")
        total_active = cursor.fetchone()["total_active"]
        
        cursor.execute("SELECT exchange, COUNT(*) as cnt FROM instruments WHERE is_active = 1 GROUP BY exchange")
        exchange_counts = {r["exchange"]: r["cnt"] for r in cursor.fetchall()}

    return {
        "is_syncing": sync_service.is_syncing,
        "current_status": sync_service.last_sync_status,
        "last_sync": dict(last_sync) if last_sync else None,
        "total_active_instruments": total_active,
        "exchange_breakdown": exchange_counts
    }

@router.get("/history")
def get_sync_history(limit: int = 20):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_history ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

@router.get("/changes")
def get_sync_changes(
    sync_id: Optional[int] = None,
    change_type: Optional[str] = None,
    limit: int = 100
):
    sql = "SELECT * FROM sync_changes WHERE 1=1"
    params = []
    if sync_id:
        sql += " AND sync_id = ?"
        params.append(sync_id)
    if change_type:
        sql += " AND change_type = ?"
        params.append(change_type)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
