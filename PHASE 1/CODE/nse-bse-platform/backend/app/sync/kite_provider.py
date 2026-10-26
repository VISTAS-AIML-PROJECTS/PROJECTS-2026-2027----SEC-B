import io
import csv
import logging
import httpx
from typing import List, Dict, Any
from app.sync.provider_base import InstrumentProvider
from app.config import settings

logger = logging.getLogger(__name__)

class KiteInstrumentProvider(InstrumentProvider):
    @property
    def name(self) -> str:
        return "kite"

    async def fetch_instruments(self) -> List[Dict[str, Any]]:
        """
        Fetches the complete official Kite instrument master CSV.
        This provides ~100,000+ legitimate real-world instruments across:
        - NSE Cash Equities
        - BSE Cash Equities
        - NFO Futures & Options (Index & Stock derivatives)
        - BFO Futures & Options
        - Indices (NIFTY, BANKNIFTY, SENSEX, etc.)
        """
        url = settings.kite_instruments_url
        logger.info("Downloading official instrument master from %s...", url)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                csv_text = response.text
                logger.info("Successfully downloaded %d bytes of instrument master CSV", len(csv_text))
                
                reader = csv.DictReader(io.StringIO(csv_text))
                rows = list(reader)
                logger.info("Parsed %d raw instruments from Kite master", len(rows))
                return rows
        except Exception as e:
            logger.error("Error fetching live Kite master CSV: %s", str(e))
            raise e
