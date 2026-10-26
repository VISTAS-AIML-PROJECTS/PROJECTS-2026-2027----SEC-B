import logging
from typing import Dict, Any

logger = logging.getLogger("chronolens.search.analytics")


class SearchAnalyticsBuilder:
    """
    Phase 2.2 Search Analytics Builder.
    Compiles detailed metrics tracking candidates retrieved, threshold rejections,
    accepted items, consolidated tracks, final returned results, and execution latency.
    """

    @staticmethod
    def build_analytics(
        candidates_retrieved: int,
        results_rejected_by_threshold: int,
        accepted_results: int,
        grouped_tracks: int,
        final_returned_results: int,
        similarity_threshold: float,
        filtering_time_ms: float,
        grouping_time_ms: float,
        ranking_time_ms: float,
        weight_semantic: float,
        weight_yolo: float,
        weight_persistence: float,
        total_retrieval_time_ms: float,
        route: str = "GENERIC",
        speech_mode: str = None,
        target_phrase: str = None,
        matching_method: str = None,
        query_parsing_time_ms: float = 0.0,
        model_initialization_time_ms: float = 0.0,
        tokenizer_time_ms: float = 0.0,
        query_embedding_time_ms: float = 0.0,
        gpu_synchronization_time_ms: float = 0.0,
        frame_search_time_ms: float = 0.0,
        object_search_time_ms: float = 0.0,
        threshold_filtering_time_ms: float = 0.0,
        metadata_lookup_time_ms: float = 0.0,
        track_grouping_time_ms: float = 0.0,
        attribute_verification_time_ms: float = 0.0,
        relational_verification_time_ms: float = 0.0,
        result_enrichment_time_ms: float = 0.0,
        serialization_time_ms: float = 0.0,
        other_unaccounted_time_ms: float = 0.0
    ) -> Dict[str, Any]:
        """
        Builds dictionary of search analytics metrics.
        """
        analytics = {
            "candidatesRetrieved": candidates_retrieved,
            "resultsRejectedByThreshold": results_rejected_by_threshold,
            "acceptedResults": accepted_results,
            "groupedTracks": grouped_tracks,
            "finalReturnedResults": final_returned_results,
            "similarityThreshold": round(float(similarity_threshold), 4),
            "filteringTimeMs": round(float(filtering_time_ms), 3),
            "groupingTimeMs": round(float(grouping_time_ms), 3),
            "rankingTimeMs": round(float(ranking_time_ms), 3),
            "weightSemantic": round(float(weight_semantic), 2),
            "weightYOLO": round(float(weight_yolo), 2),
            "weightPersistence": round(float(weight_persistence), 2),
            "totalRetrievalTimeMs": round(float(total_retrieval_time_ms), 3),

            # Phase 1 High-Resolution Stage Breakdown
            "queryParsingTimeMs": round(float(query_parsing_time_ms), 3),
            "modelInitializationTimeMs": round(float(model_initialization_time_ms), 3),
            "tokenizerTimeMs": round(float(tokenizer_time_ms), 3),
            "queryEmbeddingTimeMs": round(float(query_embedding_time_ms), 3),
            "gpuSynchronizationTimeMs": round(float(gpu_synchronization_time_ms), 3),
            "frameSearchTimeMs": round(float(frame_search_time_ms), 3),
            "objectSearchTimeMs": round(float(object_search_time_ms), 3),
            "thresholdFilteringTimeMs": round(float(threshold_filtering_time_ms), 3),
            "metadataLookupTimeMs": round(float(metadata_lookup_time_ms), 3),
            "trackGroupingTimeMs": round(float(track_grouping_time_ms), 3),
            "attributeVerificationTimeMs": round(float(attribute_verification_time_ms), 3),
            "relationalVerificationTimeMs": round(float(relational_verification_time_ms), 3),
            "resultEnrichmentTimeMs": round(float(result_enrichment_time_ms), 3),
            "serializationTimeMs": round(float(serialization_time_ms), 3),
            "otherUnaccountedTimeMs": round(float(other_unaccounted_time_ms), 3),

            "route": route,
            "speechMode": speech_mode,
            "targetPhrase": target_phrase,
            "matchingMethod": matching_method
        }

        logger.info(f"[SearchAnalytics] {analytics}")
        return analytics

