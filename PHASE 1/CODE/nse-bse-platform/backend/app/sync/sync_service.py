import logging
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.config import settings
from app.sync.kite_provider import KiteInstrumentProvider
from app.sync.upstox_provider import UpstoxInstrumentProvider
from app.sync.change_detector import ChangeDetector

logger = logging.getLogger(__name__)

INDEX_NAMES = {
    "NIFTY", "NIFTY 50", "BANKNIFTY", "NIFTY BANK", "FINNIFTY", "NIFTY FIN SERVICE",
    "MIDCPNIFTY", "NIFTY MID SELECT", "NIFTYNEXT50", "NIFTY IT", "SENSEX", "BANKEX",
    "BSE SENSEX", "BSE BANKEX", "NIFTY AUTO", "NIFTY PHARMA", "NIFTY FMCG"
}

NIFTY_50_SYMBOLS = {
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN",
    "LICI", "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI",
    "SUNPHARMA", "ADANIENT", "KOTAKBANK", "TITAN", "ONGC", "TATAMOTORS",
    "NTPC", "AXISBANK", "POWERGRID", "ADANIPORTS", "ULTRACEMCO", "WIPRO",
    "COALINDIA", "BAJAJFINSV", "TATASTEEL", "M&M", "JSWSTEEL", "ASIANPAINT",
    "SIEMENS", "GRASIM", "SBILIFE", "TECHM", "NESTLEIND", "HINDALCO",
    "BRITANNIA", "BAJAJ-AUTO", "CIPLA", "APOLLOHOSP", "DRREDDY", "DIVISLAB",
    "BPCL", "HEROMOTOCO", "EICHERMOT", "INDUSINDBK", "BEL", "TRENT"
}

class SyncService:
    def __init__(self):
        self.providers = {
            "kite": KiteInstrumentProvider(),
            "upstox": UpstoxInstrumentProvider()
        }
        self.is_syncing = False
        self.last_sync_status = "IDLE"

    def normalize_row(self, row: Dict[str, Any], provider_name: str, today_str: str) -> Optional[Dict[str, Any]]:
        exchange = (row.get("exchange") or "").strip().upper()
        if exchange not in ("NSE", "BSE", "NFO", "BFO"):
            return None  # We only target NSE, BSE and their derivatives
            
        raw_token = str(row.get("instrument_token") or "").strip()
        exchange_token = str(row.get("exchange_token") or raw_token).strip()
        trading_symbol = (row.get("tradingsymbol") or row.get("trading_symbol") or "").strip()
        name = (row.get("name") or "").strip()
        segment = (row.get("segment") or "").strip().upper()
        raw_type = (row.get("instrument_type") or "").strip().upper()
        expiry = (row.get("expiry") or "").strip()
        strike_str = str(row.get("strike") or "0").strip()
        lot_size_str = str(row.get("lot_size") or "1").strip()
        tick_size_str = str(row.get("tick_size") or "0.05").strip()

        if not raw_token or not trading_symbol:
            return None

        # Stable unique instrument ID preventing any cross-exchange collision
        instrument_token = f"{exchange}:{raw_token}"

        try:
            strike = float(strike_str)
        except ValueError:
            strike = 0.0

        try:
            lot_size = int(float(lot_size_str))
        except ValueError:
            lot_size = 1

        try:
            tick_size = float(tick_size_str)
        except ValueError:
            tick_size = 0.05

        # Classify Instrument Type and Underlying
        option_type = None
        if raw_type in ("CE", "PE"):
            option_type = raw_type

        is_index = name.upper() in INDEX_NAMES or trading_symbol.upper() in INDEX_NAMES or segment == "INDICES"
        
        if exchange in ("NFO", "BFO"):
            if raw_type == "FUT":
                instrument_type = "FUTIDX" if is_index else "FUTSTK"
            elif raw_type in ("CE", "PE"):
                instrument_type = "OPTIDX" if is_index else "OPTSTK"
            else:
                instrument_type = raw_type or "DERIVATIVE"
            underlying_symbol = name if name else trading_symbol
        elif segment == "INDICES":
            instrument_type = "INDEX"
            underlying_symbol = trading_symbol
        else:
            instrument_type = "EQ"
            underlying_symbol = trading_symbol

        # Normalize segment tag
        if exchange == "NSE":
            normalized_segment = "INDICES" if is_index else "NSE-EQ"
        elif exchange == "BSE":
            normalized_segment = "INDICES" if is_index else "BSE-EQ"
        elif exchange == "NFO":
            normalized_segment = "NFO-OPT" if raw_type in ("CE", "PE") else "NFO-FUT"
        elif exchange == "BFO":
            normalized_segment = "BFO-OPT" if raw_type in ("CE", "PE") else "BFO-FUT"
        else:
            normalized_segment = segment

        # Check Active / Expired status
        is_active = 1
        listing_status = "ACTIVE"
        if expiry and expiry < today_str:
            is_active = 0
            listing_status = "EXPIRED"

        metadata = {
            "raw_segment": segment,
            "raw_instrument_type": raw_type,
            "source_provider": provider_name
        }

        return {
            "instrument_token": instrument_token,
            "exchange_token": exchange_token,
            "trading_symbol": trading_symbol,
            "name": name if name else trading_symbol,
            "exchange": exchange,
            "segment": normalized_segment,
            "instrument_type": instrument_type,
            "isin": None,  # Will be populated or enriched where available
            "series": "EQ" if instrument_type == "EQ" else None,
            "tick_size": tick_size,
            "lot_size": lot_size,
            "strike": strike,
            "option_type": option_type,
            "expiry": expiry if expiry else None,
            "underlying_symbol": underlying_symbol,
            "is_active": is_active,
            "listing_status": listing_status,
            "trading_status": "TRADING",
            "provider": provider_name,
            "metadata_json": json.dumps(metadata),
            "last_sync_at": datetime.now().isoformat()
        }

    async def run_sync(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full sync pipeline:
        Download -> Validate -> Normalize -> Detect Changes -> Database Upsert -> Update Universes
        """
        if self.is_syncing:
            return {"status": "ALREADY_RUNNING", "message": "A synchronization is currently in progress."}

        self.is_syncing = True
        self.last_sync_status = "RUNNING"
        provider_name = provider_name or settings.active_provider
        provider = self.providers.get(provider_name, self.providers["kite"])
        
        started_at = datetime.now().isoformat()
        sync_id = None
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO sync_history (started_at, provider, status)
                       VALUES (?, ?, ?)""",
                    (started_at, provider.name, "RUNNING")
                )
                sync_id = cursor.lastrowid
                conn.commit()

            # 1. Download
            logger.info("Starting instrument sync from provider: %s", provider.name)
            raw_rows = await provider.fetch_instruments()
            total_downloaded = len(raw_rows)

            # 2. Normalize and Validate
            today_str = date.today().isoformat()
            normalized_list: List[Dict[str, Any]] = []
            for r in raw_rows:
                norm = self.normalize_row(r, provider.name, today_str)
                if norm:
                    normalized_list.append(norm)

            logger.info("Normalized %d instruments (NSE/BSE/NFO/BFO)", len(normalized_list))

            # 3. Fetch existing snapshot for change detection
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT instrument_token, trading_symbol, exchange, lot_size, is_active, expiry, instrument_type FROM instruments")
                existing_records = {row["instrument_token"]: dict(row) for row in cursor.fetchall()}

            # 4. Detect Changes
            changes, change_stats = ChangeDetector.detect_changes(existing_records, normalized_list)

            # 5. Bulk Upsert into Database
            logger.info("Upserting %d instruments into database...", len(normalized_list))
            upsert_sql = """
            INSERT INTO instruments (
                instrument_token, exchange_token, trading_symbol, name, exchange,
                segment, instrument_type, isin, series, tick_size, lot_size,
                strike, option_type, expiry, underlying_symbol, is_active,
                listing_status, trading_status, provider, metadata_json, last_sync_at
            ) VALUES (
                :instrument_token, :exchange_token, :trading_symbol, :name, :exchange,
                :segment, :instrument_type, :isin, :series, :tick_size, :lot_size,
                :strike, :option_type, :expiry, :underlying_symbol, :is_active,
                :listing_status, :trading_status, :provider, :metadata_json, :last_sync_at
            )
            ON CONFLICT(instrument_token) DO UPDATE SET
                trading_symbol = excluded.trading_symbol,
                name = excluded.name,
                segment = excluded.segment,
                instrument_type = excluded.instrument_type,
                tick_size = excluded.tick_size,
                lot_size = excluded.lot_size,
                strike = excluded.strike,
                option_type = excluded.option_type,
                expiry = excluded.expiry,
                underlying_symbol = excluded.underlying_symbol,
                is_active = excluded.is_active,
                listing_status = excluded.listing_status,
                trading_status = excluded.trading_status,
                metadata_json = excluded.metadata_json,
                last_sync_at = excluded.last_sync_at;
            """

            with get_db() as conn:
                cursor = conn.cursor()
                # Batch upsert in chunks of 2000
                chunk_size = 2000
                for i in range(0, len(normalized_list), chunk_size):
                    chunk = normalized_list[i:i + chunk_size]
                    cursor.executemany(upsert_sql, chunk)

                # Record changes in sync_changes table
                if changes:
                    change_rows = [
                        (sync_id, c["change_type"], c["instrument_token"], c["trading_symbol"],
                         c["exchange"], c["old_value"], c["new_value"], c["detected_at"])
                        for c in changes[:2000] # save top changes
                    ]
                    cursor.executemany(
                        """INSERT INTO sync_changes (sync_id, change_type, instrument_token, trading_symbol,
                                                    exchange, old_value, new_value, detected_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        change_rows
                    )

                # 6. Update Universes
                # ALL_NSE
                cursor.execute("""
                    INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                    SELECT 'ALL_NSE', instrument_token FROM instruments
                    WHERE exchange = 'NSE' AND instrument_type = 'EQ' AND is_active = 1
                """)
                # ALL_BSE
                cursor.execute("""
                    INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                    SELECT 'ALL_BSE', instrument_token FROM instruments
                    WHERE exchange = 'BSE' AND instrument_type = 'EQ' AND is_active = 1
                """)
                # NSE_AND_BSE
                cursor.execute("""
                    INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                    SELECT 'NSE_AND_BSE', instrument_token FROM instruments
                    WHERE exchange IN ('NSE', 'BSE') AND instrument_type = 'EQ' AND is_active = 1
                """)
                # FNO_STOCKS: Equities whose symbol matches an active derivative underlying
                cursor.execute("""
                    INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                    SELECT DISTINCT 'FNO_STOCKS', eq.instrument_token
                    FROM instruments eq
                    INNER JOIN instruments deriv ON eq.trading_symbol = deriv.underlying_symbol
                    WHERE eq.instrument_type = 'EQ' AND eq.exchange = 'NSE' AND eq.is_active = 1
                      AND deriv.exchange IN ('NFO', 'BFO') AND deriv.is_active = 1
                """)
                # NIFTY_50
                for sym in NIFTY_50_SYMBOLS:
                    cursor.execute("""
                        INSERT OR IGNORE INTO universe_members (universe_id, instrument_token)
                        SELECT 'NIFTY_50', instrument_token FROM instruments
                        WHERE exchange = 'NSE' AND trading_symbol = ? AND instrument_type = 'EQ'
                        LIMIT 1
                    """, (sym,))

                completed_at = datetime.now().isoformat()
                cursor.execute(
                    """UPDATE sync_history SET
                       completed_at = ?,
                       status = 'COMPLETED',
                       total_downloaded = ?,
                       total_inserted = ?,
                       total_updated = ?,
                       newly_listed_count = ?,
                       delisted_count = ?,
                       expired_count = ?,
                       lot_size_changed_count = ?,
                       details_json = ?
                       WHERE id = ?""",
                    (completed_at, total_downloaded, len(normalized_list), len(existing_records),
                     change_stats["newly_listed"], change_stats["delisted"],
                     change_stats["expired"], change_stats["lot_size_changes"],
                     json.dumps(change_stats), sync_id)
                )
                conn.commit()

            self.last_sync_status = "COMPLETED"
            self.is_syncing = False
            logger.info("Sync finished successfully. Total instruments: %d", len(normalized_list))

            return {
                "sync_id": sync_id,
                "status": "COMPLETED",
                "provider": provider.name,
                "total_downloaded": total_downloaded,
                "total_instruments": len(normalized_list),
                "change_stats": change_stats,
                "completed_at": completed_at
            }

        except Exception as e:
            logger.exception("Error during synchronization: %s", str(e))
            self.last_sync_status = "FAILED"
            self.is_syncing = False
            if sync_id:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """UPDATE sync_history SET
                           status = 'FAILED',
                           error_message = ?,
                           completed_at = ?
                           WHERE id = ?""",
                        (str(e), datetime.now().isoformat(), sync_id)
                    )
                    conn.commit()
            return {"status": "FAILED", "error": str(e)}

sync_service = SyncService()
