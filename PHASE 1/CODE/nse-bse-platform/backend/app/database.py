import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
-- Core Instruments Table for NSE & BSE Cash and Derivatives
CREATE TABLE IF NOT EXISTS instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_token TEXT UNIQUE NOT NULL,      -- e.g. NSE:738561, BSE:500325, NFO:45612
    exchange_token TEXT NOT NULL,              -- Provider internal/exchange token
    trading_symbol TEXT NOT NULL,              -- e.g. RELIANCE, NIFTY24OCTFUT, NIFTY24OCT25000CE
    name TEXT,                                 -- RELIANCE INDUSTRIES LTD
    exchange TEXT NOT NULL,                    -- NSE, BSE, NFO, BFO, CDS
    segment TEXT NOT NULL,                     -- NSE-EQ, BSE-EQ, NFO-FUT, NFO-OPT, BFO-FUT, BFO-OPT, INDICES
    instrument_type TEXT NOT NULL,             -- EQ, FUTSTK, OPTSTK, FUTIDX, OPTIDX, INDEX
    isin TEXT,                                 -- INE002A01018
    series TEXT,                               -- EQ, BE, A, B, etc.
    tick_size REAL DEFAULT 0.05,
    lot_size INTEGER DEFAULT 1,
    strike REAL DEFAULT 0.0,
    option_type TEXT,                          -- CE, PE, NULL
    expiry TEXT,                               -- YYYY-MM-DD
    underlying_symbol TEXT,                    -- RELIANCE, NIFTY, SENSEX
    has_derivatives INTEGER DEFAULT 0,         -- 1 = has active F&O contracts, 0 = no
    is_active INTEGER DEFAULT 1,               -- 1 = active, 0 = inactive
    listing_status TEXT DEFAULT 'ACTIVE',      -- ACTIVE, SUSPENDED, DELISTED, EXPIRED
    trading_status TEXT DEFAULT 'TRADING',     -- TRADING, HALTED, CLOSED
    provider TEXT NOT NULL,                    -- kite, upstox, nse_bse
    metadata_json TEXT,                        -- JSON for extra provider properties
    last_sync_at TEXT NOT NULL
);

-- Indexes for lightning fast queries across 100k+ instruments
CREATE INDEX IF NOT EXISTS idx_inst_exchange ON instruments(exchange);
CREATE INDEX IF NOT EXISTS idx_inst_segment ON instruments(segment);
CREATE INDEX IF NOT EXISTS idx_inst_symbol ON instruments(trading_symbol);
CREATE INDEX IF NOT EXISTS idx_inst_underlying ON instruments(underlying_symbol);
CREATE INDEX IF NOT EXISTS idx_inst_type ON instruments(instrument_type);
CREATE INDEX IF NOT EXISTS idx_inst_expiry ON instruments(expiry);
CREATE INDEX IF NOT EXISTS idx_inst_active ON instruments(is_active);
CREATE INDEX IF NOT EXISTS idx_inst_isin ON instruments(isin);
CREATE INDEX IF NOT EXISTS idx_inst_fno ON instruments(has_derivatives);
CREATE INDEX IF NOT EXISTS idx_inst_exch_sym ON instruments(exchange, trading_symbol);

-- FTS5 Full-Text Search Virtual Table for fast search
CREATE VIRTUAL TABLE IF NOT EXISTS instruments_fts USING fts5(
    trading_symbol,
    name,
    isin,
    exchange,
    segment,
    instrument_type,
    underlying_symbol,
    content='instruments',
    content_rowid='id'
);

-- Triggers to keep FTS5 synchronized with instruments table
CREATE TRIGGER IF NOT EXISTS inst_ai AFTER INSERT ON instruments BEGIN
  INSERT INTO instruments_fts(rowid, trading_symbol, name, isin, exchange, segment, instrument_type, underlying_symbol)
  VALUES (new.id, new.trading_symbol, new.name, new.isin, new.exchange, new.segment, new.instrument_type, new.underlying_symbol);
END;

CREATE TRIGGER IF NOT EXISTS inst_ad AFTER DELETE ON instruments BEGIN
  INSERT INTO instruments_fts(instruments_fts, rowid, trading_symbol, name, isin, exchange, segment, instrument_type, underlying_symbol)
  VALUES('delete', old.id, old.trading_symbol, old.name, old.isin, old.exchange, old.segment, old.instrument_type, old.underlying_symbol);
END;

CREATE TRIGGER IF NOT EXISTS inst_au AFTER UPDATE ON instruments BEGIN
  INSERT INTO instruments_fts(instruments_fts, rowid, trading_symbol, name, isin, exchange, segment, instrument_type, underlying_symbol)
  VALUES('delete', old.id, old.trading_symbol, old.name, old.isin, old.exchange, old.segment, old.instrument_type, old.underlying_symbol);
  INSERT INTO instruments_fts(rowid, trading_symbol, name, isin, exchange, segment, instrument_type, underlying_symbol)
  VALUES (new.id, new.trading_symbol, new.name, new.isin, new.exchange, new.segment, new.instrument_type, new.underlying_symbol);
END;

-- Sync History Table
CREATE TABLE IF NOT EXISTS sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,                      -- RUNNING, COMPLETED, FAILED
    total_downloaded INTEGER DEFAULT 0,
    total_inserted INTEGER DEFAULT 0,
    total_updated INTEGER DEFAULT 0,
    newly_listed_count INTEGER DEFAULT 0,
    delisted_count INTEGER DEFAULT 0,
    expired_count INTEGER DEFAULT 0,
    lot_size_changed_count INTEGER DEFAULT 0,
    error_message TEXT,
    details_json TEXT
);

-- Sync Changes Log Table
CREATE TABLE IF NOT EXISTS sync_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_id INTEGER,
    change_type TEXT NOT NULL,                 -- NEW_LISTING, DELISTED, EXPIRED, LOT_SIZE_CHANGE, SYMBOL_CHANGE
    instrument_token TEXT NOT NULL,
    trading_symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TEXT NOT NULL,
    FOREIGN KEY(sync_id) REFERENCES sync_history(id)
);

-- Universes
CREATE TABLE IF NOT EXISTS universes (
    id TEXT PRIMARY KEY,                       -- ALL_NSE, ALL_BSE, NIFTY_50, FNO_STOCKS, etc.
    name TEXT NOT NULL,
    description TEXT,
    is_system INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Universe Members
CREATE TABLE IF NOT EXISTS universe_members (
    universe_id TEXT NOT NULL,
    instrument_token TEXT NOT NULL,
    PRIMARY KEY(universe_id, instrument_token),
    FOREIGN KEY(universe_id) REFERENCES universes(id)
);

-- Live Quotes & Market Snapshot Cache
CREATE TABLE IF NOT EXISTS live_quotes (
    instrument_token TEXT PRIMARY KEY,
    last_price REAL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    change REAL,
    change_percent REAL,
    volume INTEGER,
    oi INTEGER,
    oi_change INTEGER,
    iv REAL,
    bid REAL,
    ask REAL,
    provider_timestamp TEXT,
    status TEXT DEFAULT 'OK',                  -- OK, UNAVAILABLE, STALE
    updated_at TEXT NOT NULL
);
"""

@contextmanager
def get_db():
    conn = sqlite3.connect(
        settings.database_path,
        timeout=30.0,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes tables, indexes, triggers and default universes."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        
        # Populate Default Universes if not exist
        default_universes = [
            ("ALL_NSE", "All NSE Equities", "Complete universe of active NSE cash equities", 1),
            ("ALL_BSE", "All BSE Equities", "Complete universe of active BSE cash equities", 1),
            ("NSE_AND_BSE", "NSE & BSE Combined", "All listed equities across both NSE and BSE", 1),
            ("NIFTY_50", "NIFTY 50", "50 largest Indian blue-chip companies listed on NSE", 1),
            ("NIFTY_100", "NIFTY 100", "Top 100 companies by market cap on NSE", 1),
            ("NIFTY_200", "NIFTY 200", "Top 200 companies on NSE", 1),
            ("FNO_STOCKS", "F&O Eligible Equities", "All equity underlyings eligible for trading in F&O contracts", 1),
            ("CUSTOM_WATCHLIST", "My Watchlist", "User curated custom watchlist", 0),
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO universes (id, name, description, is_system, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            default_universes
        )
        conn.commit()
    logger.info("Database initialized successfully at %s", settings.database_path)
