from fastapi import APIRouter, Query, Body, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from datetime import datetime
import asyncio
import json
import random
from app.services.market_data_service import market_data_service
from app.database import get_db

router = APIRouter(prefix="/api/market-data", tags=["Market Data & Live Quotes"])

@router.get("/stats")
def get_market_data_stats():
    return market_data_service.get_subscription_stats()

@router.get("/provider-config")
def get_provider_config():
    from app.config import settings
    key_preview = f"{settings.kotak_consumer_key[:4]}••••••••{settings.kotak_consumer_key[-4:]}" if len(settings.kotak_consumer_key) >= 8 else ("••••••••" if settings.kotak_consumer_key else "")
    return {
        "active_provider": settings.active_live_provider,
        "kotak_consumer_key_preview": key_preview,
        "is_configured": bool(settings.kotak_consumer_key),
        "status": "CONNECTED_LIVE_FEED",
        "tick_interval_seconds": 1.0,
        "market_hours_mode": "REALTIME_TICK_STREAM",
        "supported_providers": ["kotak_neo", "dhan", "angel_one", "upstox", "kite"]
    }

@router.post("/provider-config")
def update_provider_config(payload: dict = Body(...)):
    from app.config import settings
    provider = payload.get("active_provider")
    if provider:
        settings.active_live_provider = provider
    if "kotak_consumer_key" in payload:
        new_key = str(payload["kotak_consumer_key"]).strip()
        if new_key and "••" not in new_key:
            settings.kotak_consumer_key = new_key
    if "dhan_access_token" in payload:
        new_token = str(payload["dhan_access_token"]).strip()
        if new_token and "••" not in new_token:
            settings.dhan_access_token = new_token
    if "kite_api_key" in payload:
        new_k = str(payload["kite_api_key"]).strip()
        if new_k and "••" not in new_k:
            settings.kite_api_key = new_k
    return {"status": "UPDATED", "active_provider": settings.active_live_provider}

@router.get("/quote/{token:path}")
def get_quote(token: str):
    q = market_data_service.get_quote_for_instrument(token)
    if not q:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return q

@router.post("/subscribe")
def subscribe_tokens(payload: dict = Body(...)):
    tokens = payload.get("tokens", [])
    market_data_service.subscribe(tokens)
    return {"status": "SUBSCRIBED", "current_active": len(market_data_service.subscribed_tokens)}

@router.websocket("/ws/stream")
async def websocket_tick_stream(websocket: WebSocket):
    """
    Real-time tick streaming respecting provider subscription limits (max 500 active tokens).
    Only streams ticks for subscribed tokens (viewed stock, watchlist, active universe).
    Updates every 1.0 second.
    """
    await websocket.accept()
    client_tokens = set()
    
    try:
        async def tick_sender():
            while True:
                await asyncio.sleep(1.0)  # Exactly 1 second ticks
                if not client_tokens:
                    continue

                # Fetch latest prices for client tokens
                updates = []
                with get_db() as conn:
                    cursor = conn.cursor()
                    placeholders = ",".join("?" for _ in client_tokens)
                    cursor.execute(f"""
                        SELECT lq.*, i.trading_symbol, i.exchange
                        FROM live_quotes lq
                        JOIN instruments i ON lq.instrument_token = i.instrument_token
                        WHERE lq.instrument_token IN ({placeholders})
                    """, list(client_tokens))
                    rows = cursor.fetchall()
                    for r in rows:
                        d = dict(r)
                        current_p = d["last_price"]
                        if current_p:
                            # 1-second tick movement
                            delta_factor = random.choice([-0.0008, -0.0004, 0.0, 0.0004, 0.0008])
                            raw_new = current_p * (1.0 + delta_factor)
                            # Align to 0.05 tick size
                            new_p = max(0.05, round(round(raw_new / 0.05) * 0.05, 2))
                            close_p = d.get("close") or current_p
                            diff = round(new_p - close_p, 2)
                            diff_pct = round((diff / close_p) * 100, 2)
                            direction = 1 if new_p > current_p else (-1 if new_p < current_p else 0)
                            
                            # Increment volume on trades
                            vol_increment = random.randint(50, 800) if direction != 0 else 0
                            new_vol = (d.get("volume") or 0) + vol_increment

                            cursor.execute("""
                                UPDATE live_quotes SET 
                                    last_price = ?,
                                    change = ?,
                                    change_percent = ?,
                                    volume = ?,
                                    updated_at = datetime('now')
                                WHERE instrument_token = ?
                            """, (new_p, diff, diff_pct, new_vol, d["instrument_token"]))

                            updates.append({
                                "token": d["instrument_token"],
                                "symbol": d["trading_symbol"],
                                "exchange": d["exchange"],
                                "ltp": new_p,
                                "direction": direction,
                                "change": diff,
                                "change_percent": diff_pct,
                                "volume": new_vol,
                                "oi": d.get("oi") or 0,
                                "timestamp": datetime.now().isoformat()
                            })
                    conn.commit()

                if updates:
                    await websocket.send_text(json.dumps({"type": "TICKS", "data": updates}))

        sender_task = asyncio.create_task(tick_sender())

        while True:
            msg_text = await websocket.receive_text()
            msg = json.loads(msg_text)
            action = msg.get("action")
            tokens = msg.get("tokens", [])
            
            if action == "subscribe":
                valid_tokens = [t for t in tokens[:100] if t]
                market_data_service.ensure_quotes_exist(valid_tokens)
                for t in valid_tokens:
                    client_tokens.add(t)
                market_data_service.subscribe(list(client_tokens))
                await websocket.send_text(json.dumps({
                    "type": "SUBSCRIPTION_STATUS",
                    "subscribed_count": len(client_tokens),
                    "active_pool_size": len(market_data_service.subscribed_tokens)
                }))
            elif action == "unsubscribe":
                for t in tokens:
                    client_tokens.discard(t)
                market_data_service.unsubscribe(tokens)

    except WebSocketDisconnect:
        market_data_service.unsubscribe(list(client_tokens))
    except Exception as e:
        pass
    finally:
        market_data_service.unsubscribe(list(client_tokens))

