import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, get_db
from app.services.market_data_service import market_data_service
from app.sync.sync_service import sync_service

# Routers
from app.routers import instruments, derivatives, sync, universes, models_lab, market_data, prediction, ai_copilot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NSE & BSE Full Market Coverage Database...")
    init_db()
    
    # Check if database has instruments, if empty run initial sync automatically
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM instruments")
        count = cursor.fetchone()["cnt"]

    if count == 0 and settings.auto_sync_on_startup:
        logger.info("No instruments found in database. Starting initial synchronization in background...")
        asyncio.create_task(sync_service.run_sync())
    else:
        logger.info("Database contains %d instruments. Seeding baseline quotes in background...", count)
        asyncio.get_event_loop().run_in_executor(None, market_data_service.seed_initial_quotes_for_active_instruments)

    yield
    logger.info("Shutting down NSE & BSE Platform...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Terminal and analytics platform covering the complete NSE & BSE equity and derivative universe.",
    lifespan=lifespan
)

# Enable CORS for local frontend dev server & web sockets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(instruments.router)
app.include_router(derivatives.router)
app.include_router(sync.router)
app.include_router(universes.router)
app.include_router(models_lab.router)
app.include_router(market_data.router)
app.include_router(prediction.router)
app.include_router(ai_copilot.router)

@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "OPERATIONAL",
        "docs_url": "/docs"
    }

@app.get("/health")
def health():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM instruments WHERE is_active = 1")
        active_count = cursor.fetchone()["count"]

    return {
        "status": "HEALTHY",
        "active_instruments": active_count,
        "sync_status": sync_service.last_sync_status,
        "is_syncing": sync_service.is_syncing
    }
