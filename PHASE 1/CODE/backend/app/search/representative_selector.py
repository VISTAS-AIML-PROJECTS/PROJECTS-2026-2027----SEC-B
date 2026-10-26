import logging
from typing import List, Dict, Any

logger = logging.getLogger("chronolens.search.representative")


class RepresentativeSelector:
    """
    Phase 2.2 Representative Result Selector.
    Selects a single representative thumbnail frame/crop for each grouped track trajectory.
    Priority: Highest OpenCLIP cosine similarity.
    """

    @staticmethod
    def select_representative(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Picks the record with the maximum similarityScore.
        """
        if not records:
            raise ValueError("Cannot select representative from empty record list.")

        # Sort by similarityScore descending
        sorted_records = sorted(records, key=lambda r: float(r.get("similarityScore", 0.0)), reverse=True)
        representative = sorted_records[0]

        logger.debug(
            f"[RepresentativeSelector] Selected representative frame #{representative.get('frameNumber')} "
            f"with sim={representative.get('similarityScore')} for Track #{representative.get('trackId')}"
        )
        return representative
