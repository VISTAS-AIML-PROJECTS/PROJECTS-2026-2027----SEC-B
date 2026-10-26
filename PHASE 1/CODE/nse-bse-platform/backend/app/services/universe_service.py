import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_db

logger = logging.getLogger(__name__)

class UniverseService:
    @staticmethod
    def list_universes() -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                u.id, u.name, u.description, u.is_system, u.created_at,
                COUNT(um.instrument_token) as member_count
            FROM universes u
            LEFT JOIN universe_members um ON u.id = um.universe_id
            GROUP BY u.id
            ORDER BY u.is_system DESC, u.name ASC
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def get_universe_members(universe_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM universes WHERE id = ?", (universe_id,))
            u = cursor.fetchone()
            if not u:
                return {"error": "Universe not found"}

            cursor.execute("SELECT COUNT(*) as total FROM universe_members WHERE universe_id = ?", (universe_id,))
            total = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT 
                    i.instrument_token, i.trading_symbol, i.name, i.exchange,
                    i.segment, i.instrument_type, i.series, i.lot_size,
                    lq.last_price, lq.change_percent, lq.volume
                FROM universe_members um
                JOIN instruments i ON um.instrument_token = i.instrument_token
                LEFT JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
                WHERE um.universe_id = ?
                ORDER BY i.trading_symbol ASC
                LIMIT ? OFFSET ?
            """, (universe_id, limit, offset))
            rows = [dict(r) for r in cursor.fetchall()]

            return {
                "universe": dict(u),
                "total": total,
                "limit": limit,
                "offset": offset,
                "members": rows
            }

    @staticmethod
    def add_to_watchlist(instrument_token: str) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                VALUES ('CUSTOM_WATCHLIST', ?)
            """, (instrument_token,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def remove_from_watchlist(instrument_token: str) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM universe_members 
                WHERE universe_id = 'CUSTOM_WATCHLIST' AND instrument_token = ?
            """, (instrument_token,))
            conn.commit()
            return cursor.rowcount > 0
