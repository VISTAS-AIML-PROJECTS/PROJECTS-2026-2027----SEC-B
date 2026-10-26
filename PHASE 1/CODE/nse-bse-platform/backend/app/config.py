import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Load .env file securely from backend directory
load_dotenv(BASE_DIR / "backend" / ".env")
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "market_master.db"

class Settings(BaseModel):
    app_name: str = "NSE & BSE Full Market Coverage Terminal"
    app_version: str = "1.0.0"
    debug: bool = True
    database_path: str = str(DATABASE_PATH)
    
    # Provider endpoints (Public genuine dumps)
    kite_instruments_url: str = "https://api.kite.trade/instruments"
    upstox_instruments_url: str = "https://assets.upstox.com/market-quote/instruments/exchange/complete.csv.gz"
    
    # Sync Configuration
    auto_sync_on_startup: bool = True
    sync_schedule_cron: str = "0 8 * * 1-5"  # 8:00 AM Mon-Fri before market open
    
    # Active Provider ("kite", "upstox", "hybrid")
    active_provider: str = "kite"
    
    # Live Market Data Provider Configuration (loaded securely from .env)
    active_live_provider: str = os.getenv("ACTIVE_LIVE_PROVIDER", "kotak_neo")
    kotak_consumer_key: str = os.getenv("KOTAK_CONSUMER_KEY", "")
    kotak_consumer_secret: str = os.getenv("KOTAK_CONSUMER_SECRET", "")
    kotak_client_code: str = os.getenv("KOTAK_CLIENT_CODE", "")
    kotak_mobile: str = os.getenv("KOTAK_MOBILE", "")
    kotak_mpin: str = os.getenv("KOTAK_MPIN", "")
    
    # Optional other provider keys
    dhan_client_id: str = os.getenv("DHAN_CLIENT_ID", "")
    dhan_access_token: str = os.getenv("DHAN_ACCESS_TOKEN", "")
    kite_api_key: str = os.getenv("KITE_API_KEY", "")
    kite_access_token: str = os.getenv("KITE_ACCESS_TOKEN", "")
    upstox_api_key: str = os.getenv("UPSTOX_API_KEY", "")
    upstox_access_token: str = os.getenv("UPSTOX_ACCESS_TOKEN", "")

    # Pre-configured universes
    default_universes: list = [
        "ALL_NSE",
        "ALL_BSE",
        "NSE_AND_BSE",
        "NIFTY_50",
        "NIFTY_100",
        "NIFTY_200",
        "FNO_STOCKS",
        "CUSTOM_WATCHLIST"
    ]

settings = Settings()
