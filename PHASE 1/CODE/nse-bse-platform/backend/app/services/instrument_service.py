import logging
import sqlite3
from typing import List, Dict, Any, Optional
from app.database import get_db

logger = logging.getLogger(__name__)

class InstrumentService:
    @staticmethod
    def search_instruments(
        query: str = "",
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
        instrument_type: Optional[str] = None,
        universe_id: Optional[str] = None,
        has_fno: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "trading_symbol",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Sub-millisecond full-text search and filtering across the entire NSE & BSE universe.
        """
        page = max(1, page)
        page_size = min(max(10, page_size), 200)
        offset = (page - 1) * page_size
        direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        # Default ordering: prioritize liquid F&O stocks, NSE over BSE, and real tickers over numeric bonds
        if not query and sort_by == "trading_symbol":
            order_sql = f"i.has_derivatives DESC, (CASE WHEN i.trading_symbol GLOB '[0-9]*' THEN 1 ELSE 0 END) ASC, (CASE WHEN i.exchange = 'NSE' THEN 0 ELSE 1 END) ASC, i.trading_symbol {direction}"
        elif query and sort_by == "trading_symbol":
            clean_q = query.strip().upper()
            order_sql = f"(CASE WHEN UPPER(i.trading_symbol) = '{clean_q}' THEN 0 WHEN UPPER(i.trading_symbol) LIKE '{clean_q}%' THEN 1 ELSE 2 END) ASC, i.has_derivatives DESC, (CASE WHEN i.exchange = 'NSE' THEN 0 ELSE 1 END) ASC, i.trading_symbol ASC"
        else:
            allowed_sort = {
                "trading_symbol": "i.trading_symbol",
                "name": "i.name",
                "exchange": "i.exchange",
                "segment": "i.segment",
                "instrument_type": "i.instrument_type",
                "strike": "i.strike",
                "expiry": "i.expiry"
            }
            order_col = allowed_sort.get(sort_by, "i.trading_symbol")
            order_sql = f"{order_col} {direction}"

        where_clauses = ["i.is_active = 1"]
        params: List[Any] = []

        # Full-Text Search and flexible substring match
        if query and query.strip():
            clean_q = query.strip().replace('"', '""').replace("'", "''")
            fts_query = f'"{clean_q}"*'
            where_clauses.append("""
                (i.id IN (SELECT rowid FROM instruments_fts WHERE instruments_fts MATCH ?)
                 OR UPPER(i.trading_symbol) LIKE ?
                 OR UPPER(i.name) LIKE ?
                 OR REPLACE(UPPER(i.name), ' ', '') LIKE ?
                 OR UPPER(i.underlying_symbol) LIKE ?)
            """)
            q_pattern = f"%{clean_q.upper()}%"
            q_nospaces = f"%{clean_q.upper().replace(' ', '')}%"
            params.extend([fts_query, q_pattern, q_pattern, q_nospaces, q_pattern])
        elif instrument_type == "EQ":
            # For general equity browsing without search query, exclude numeric bond/debt tickers and dash series
            where_clauses.append("i.trading_symbol NOT GLOB '[0-9]*' AND i.trading_symbol NOT LIKE '%-%'")

        # Universe join/filter
        join_clause = ""
        if universe_id:
            join_clause = "INNER JOIN universe_members um ON i.instrument_token = um.instrument_token AND um.universe_id = ?"
            params.append(universe_id)

        # Filters
        if exchange:
            where_clauses.append("i.exchange = ?")
            params.append(exchange.upper())

        if segment:
            where_clauses.append("i.segment = ?")
            params.append(segment.upper())

        if instrument_type:
            where_clauses.append("i.instrument_type = ?")
            params.append(instrument_type.upper())

        if has_fno is True:
            where_clauses.append("i.has_derivatives = 1")
        elif has_fno is False:
            where_clauses.append("i.has_derivatives = 0")

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        count_sql = f"""
            SELECT COUNT(*) as total
            FROM instruments i
            {join_clause}
            {where_sql}
        """

        data_sql = f"""
            SELECT 
                i.id, i.instrument_token, i.exchange_token, i.trading_symbol,
                i.name, i.exchange, i.segment, i.instrument_type, i.isin,
                i.series, i.tick_size, i.lot_size, i.strike, i.option_type,
                i.expiry, i.underlying_symbol, i.is_active, i.listing_status,
                i.trading_status, i.provider, i.metadata_json, i.last_sync_at,
                i.has_derivatives,
                lq.last_price, lq.change_percent, lq.volume
            FROM instruments i
            {join_clause}
            LEFT JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?
        """

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()["total"]

            data_params = params + [page_size, offset]
            cursor.execute(data_sql, data_params)
            rows = [dict(r) for r in cursor.fetchall()]

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
            "instruments": rows
        }

    @staticmethod
    def get_instrument_by_token(token: str) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT 
                i.*,
                lq.last_price, lq.open, lq.high, lq.low, lq.close,
                lq.change, lq.change_percent, lq.volume, lq.oi, lq.oi_change,
                lq.iv, lq.bid, lq.ask, lq.status as quote_status,
                EXISTS (
                    SELECT 1 FROM instruments d 
                    WHERE d.underlying_symbol = i.trading_symbol 
                      AND d.exchange IN ('NFO', 'BFO') 
                      AND d.is_active = 1
                ) as has_derivatives
            FROM instruments i
            LEFT JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
            WHERE i.instrument_token = ?
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (token,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def check_derivatives_availability(symbol: str) -> Dict[str, Any]:
        """
        Checks if derivatives (Futures/Options) exist for an underlying symbol.
        """
        clean_sym = symbol.strip().upper()
        sql = """
            SELECT exchange, instrument_type, COUNT(*) as cnt
            FROM instruments
            WHERE underlying_symbol = ? AND exchange IN ('NFO', 'BFO') AND is_active = 1
            GROUP BY exchange, instrument_type
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (clean_sym,))
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    "symbol": clean_sym,
                    "has_derivatives": False,
                    "message": "Futures/Options are not available for this instrument.",
                    "contracts_count": 0,
                    "breakdown": {}
                }
            
            breakdown = {r["instrument_type"]: r["cnt"] for r in rows}
            total_contracts = sum(breakdown.values())
            return {
                "symbol": clean_sym,
                "has_derivatives": True,
                "message": f"Active derivatives available ({total_contracts} contracts).",
                "contracts_count": total_contracts,
                "breakdown": breakdown
            }
