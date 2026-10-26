import io
import gzip
import csv
import logging
import httpx
from typing import List, Dict, Any
from app.sync.provider_base import InstrumentProvider
from app.config import settings

logger = logging.getLogger(__name__)

class UpstoxInstrumentProvider(InstrumentProvider):
    @property
    def name(self) -> str:
        return "upstox"

    async def fetch_instruments(self) -> List[Dict[str, Any]]:
        """
        Fetches instrument master from Upstox.
        """
        url = settings.upstox_instruments_url
        logger.info("Downloading Upstox instrument master from %s...", url)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                content = response.content
                # Decompress gzip
                with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                    csv_text = gz.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(csv_text))
                rows = list(reader)
                logger.info("Parsed %d raw instruments from Upstox master", len(rows))
                return rows
        except Exception as e:
            logger.error("Error fetching Upstox master: %s", str(e))
            raise e
