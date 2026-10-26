from abc import ABC, abstractmethod
from typing import List, Dict, Any

class InstrumentProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider, e.g. 'kite', 'upstox'"""
        pass

    @abstractmethod
    async def fetch_instruments(self) -> List[Dict[str, Any]]:
        """Download and return raw instrument rows as dictionaries."""
        pass
