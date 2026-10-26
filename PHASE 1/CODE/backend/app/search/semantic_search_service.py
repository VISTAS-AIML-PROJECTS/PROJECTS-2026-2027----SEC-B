import re
import time
import math
import logging
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.database.mongo import mongo_db
from app.services.semantic.faiss_manager import faiss_manager
from app.search.query_embedder import QueryEmbedder
from app.search.result_filter import ResultFilter
from app.search.track_grouping import TrackGrouper
from app.search.search_analytics import SearchAnalyticsBuilder
from app.search.search_models import (
    SearchQueryRequest,
    SearchResponse,
    FrameSearchResult,
    ObjectSearchResult,
    SearchStatistics,
    SearchAnalytics
)
from app.search.ranking_engine import hybrid_ranking_engine
from app.search.attribute_filter import AttributeFilter
from app.search.query_router import QueryRouter
from app.search.attribute_retrieval_engine import attribute_retrieval_engine
from app.processing.ocr.ocr_annotator import OcrAnnotator
from app.processing.ocr.paddle_ocr_service import normalize_ocr_text

logger = logging.getLogger("chronolens.search.service")



class SemanticSearchService:
    """
    Phase 2.3 Intelligent Semantic Retrieval & Hybrid Ranking Engine.
    Executes text query embedding, dual FAISS search, similarity threshold filtering,
    duplicate track trajectory consolidation, representative thumbnail selection,
    deterministic hybrid ranking calculation, and search analytics compilation.
    """

    @staticmethod
    def _get_default_existing_video_id() -> str:
        if settings.UPLOADS_DIR.exists():
            for p in settings.UPLOADS_DIR.iterdir():
                if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
                    return p.stem
        if settings.DEBUG_DIR.exists():
            for p in settings.DEBUG_DIR.iterdir():
                if p.is_dir():
                    return p.name
        return "video_001"

    @classmethod
    def _get_metadata_matched_tracks(cls, query_attrs: Dict[str, Any], db: Any) -> List[Dict[str, Any]]:
        """
        Queries metadata store (MongoDB or storage/metadata/attributes.json)
        for tracks satisfying explicit query attributes.
        Returns list of matching attribute records.
        """
        req_upper_color = query_attrs.get("upperClothingColor")
        req_lower_color = query_attrs.get("lowerClothingColor")
        req_vehicle_color = query_attrs.get("vehicleColor")
        req_hat = query_attrs.get("hasHat")
        req_backpack = query_attrs.get("hasBackpack")
        req_helmet = query_attrs.get("hasHelmet")
        req_glasses = query_attrs.get("hasGlasses")
        req_obj_class = query_attrs.get("requiredObjectClass")

        matched = []

        if db is not None:
            try:
                mongo_query = {}
                if req_obj_class:
                    req_cls_norm = str(req_obj_class).lower()
                    if req_cls_norm == "person":
                        mongo_query["objectClass"] = "person"
                    elif req_cls_norm in {"car", "vehicle"}:
                        mongo_query["objectClass"] = {"$in": ["car", "bus", "truck", "motorcycle", "vehicle"]}

                if req_upper_color:
                    mongo_query["upperClothingColor"] = {"$regex": f"^{req_upper_color}$", "$options": "i"}
                if req_lower_color:
                    mongo_query["lowerClothingColor"] = {"$regex": f"^{req_lower_color}$", "$options": "i"}
                if req_vehicle_color:
                    mongo_query["vehicleColor"] = {"$regex": f"^{req_vehicle_color}$", "$options": "i"}
                if req_hat is True:
                    mongo_query["hasHat"] = True
                if req_backpack is True:
                    mongo_query["hasBackpack"] = True
                if req_helmet is True:
                    mongo_query["hasHelmet"] = True
                if req_glasses is True:
                    mongo_query["hasGlasses"] = True

                matched = list(db.attributes.find(mongo_query, {"_id": 0}))
            except Exception as e:
                logger.warning(f"[SemanticSearch] MongoDB attribute query failed: {e}")
                matched = []

        if not matched:
            attr_file = settings.BASE_DIR / "storage" / "metadata" / "attributes.json"
            if not attr_file.exists():
                attr_file = settings.BASE_DIR / "backend" / "storage" / "metadata" / "attributes.json"

            if attr_file.exists():
                try:
                    import json
                    with open(attr_file, "r", encoding="utf-8") as f:
                        all_attrs = json.load(f)

                    for item in all_attrs:
                        cand_cls = str(item.get("objectClass", "")).lower()
                        match = True

                        if req_obj_class:
                            req_cls_norm = str(req_obj_class).lower()
                            if req_cls_norm == "person" and cand_cls != "person":
                                match = False
                            elif req_cls_norm in {"car", "vehicle"} and cand_cls not in {"car", "bus", "truck", "motorcycle", "vehicle"}:
                                match = False

                        if req_upper_color and match:
                            act_u = str(item.get("upperClothingColor", "")).lower()
                            if act_u != str(req_upper_color).lower():
                                match = False

                        if req_lower_color and match:
                            act_l = str(item.get("lowerClothingColor", "")).lower()
                            if act_l != str(req_lower_color).lower():
                                match = False

                        if req_vehicle_color and match:
                            act_v = str(item.get("vehicleColor", "")).lower()
                            if act_v != str(req_vehicle_color).lower():
                                match = False

                        if req_hat is True and match:
                            if item.get("hasHat") is not True:
                                match = False

                        if req_backpack is True and match:
                            if item.get("hasBackpack") is not True:
                                match = False

                        if req_helmet is True and match:
                            if item.get("hasHelmet") is not True:
                                match = False

                        if req_glasses is True and match:
                            if item.get("hasGlasses") is not True:
                                match = False

                        if match:
                            matched.append(item)
                except Exception as e:
                    logger.warning(f"[SemanticSearch] File attribute fallback failed: {e}")

        return matched

    _file_metadata_cache = None

    @classmethod
    def _lookup_object_class(cls, faiss_id: Any, db: Any) -> str:
        if db is not None:
            try:
                meta = db.embeddings.find_one({"faissId": faiss_id, "type": "object"}, {"_id": 0, "objectClass": 1})
                if not meta:
                    meta = db.detections.find_one({"faissId": faiss_id}, {"_id": 0, "objectClass": 1})
                if not meta:
                    meta = db.tracks.find_one({"trackId": faiss_id}, {"_id": 0, "objectClass": 1})
                if not meta:
                    meta = db.attributes.find_one({"trackId": faiss_id}, {"_id": 0, "objectClass": 1})
                if meta and meta.get("objectClass"):
                    return str(meta["objectClass"]).lower()
            except Exception:
                pass

        if cls._file_metadata_cache is None:
            cls._file_metadata_cache = {}
            emb_file = settings.BASE_DIR / "storage" / "metadata" / "embeddings.json"
            if not emb_file.exists():
                emb_file = settings.BASE_DIR / "backend" / "storage" / "metadata" / "embeddings.json"
            if emb_file.exists():
                try:
                    import json
                    with open(emb_file, "r", encoding="utf-8") as f:
                        emb_list = json.load(f)
                        for e in emb_list:
                            if e.get("type") == "object" and "faissId" in e and "objectClass" in e:
                                cls._file_metadata_cache[e["faissId"]] = str(e["objectClass"]).lower()
                                cls._file_metadata_cache[str(e["faissId"])] = str(e["objectClass"]).lower()
                                if "trackId" in e:
                                    cls._file_metadata_cache[e["trackId"]] = str(e["objectClass"]).lower()
                                    cls._file_metadata_cache[str(e["trackId"])] = str(e["objectClass"]).lower()
                except Exception:
                    pass

        if cls._file_metadata_cache and (faiss_id in cls._file_metadata_cache or str(faiss_id) in cls._file_metadata_cache):
            return cls._file_metadata_cache.get(faiss_id) or cls._file_metadata_cache.get(str(faiss_id))

        return ""

    @classmethod
    def _search_speech(
        cls,
        query_text: str,
        top_k: int,
        db: Any
    ) -> List[Dict[str, Any]]:
        """
        Phase 3.19 Speech/Whisper Production Search Route.
        
        Supports word-level timestamp search, contiguous word sequence exact matching,
        cross-segment sliding windows (1..3 segments), high-confidence approximate fallback,
        and strict legacy transcript backward compatibility.
        """
        import json as _json
        import re as _re
        from difflib import SequenceMatcher

        # Helper 1: Clean and normalize individual word token
        def _clean_word(w: str) -> str:
            if not w:
                return ""
            w_clean = str(w).lower().replace("’", "'").replace("‘", "'").replace("`", "'")
            # Strip surrounding non-alphanumeric except apostrophe
            w_strip = _re.sub(r"^[^\w']+|[^\w']+$", "", w_clean)
            return w_strip

        # Common phonetic/transcription variant map
        TRANSCRIPTION_VARIANTS = {
            "somethin": "something",
            "goin": "going",
            "wanna": "want to",
            "didja": "did you",
            "gonna": "going to",
            "gotta": "got to",
            "kinda": "kind of",
            "sorta": "sort of",
            "ya": "you",
            "y'all": "you all",
        }

        def _words_match_equal(w1: str, w2: str) -> bool:
            c1 = _clean_word(w1)
            c2 = _clean_word(w2)
            if not c1 or not c2:
                return False
            if c1 == c2:
                return True
            if TRANSCRIPTION_VARIANTS.get(c1) == c2 or TRANSCRIPTION_VARIANTS.get(c2) == c1:
                return True
            return False

        def _tokenize_text(t: str) -> List[str]:
            if not t:
                return []
            t_clean = str(t).lower().replace("’", "'").replace("‘", "'").replace("`", "'")
            raw_tokens = _re.findall(r"\b[\w']+\b", t_clean)
            res = []
            for tok in raw_tokens:
                c = _clean_word(tok)
                if c:
                    res.append(c)
            return res

        raw_q = query_text.strip()

        # 1. Detect explicit quoted phrase for MODE A
        quoted_match = _re.search(r'"([^"]+)"|\'([^\']+)\'', raw_q)
        extracted_phrase = (quoted_match.group(1) or quoted_match.group(2) or "").strip() if quoted_match else ""
        if extracted_phrase:
            target_phrase = extracted_phrase
            is_exact_mode = True
        else:
            meta_phrases = [
                r"^what\s+(did|was|were|has|have|is|are)\s+(he|she|they|the\s+person|someone|anyone)?\s*(say|said|saying|speaking|talk|talked|talking|speak|spoken|mention|mentioned|about)?\s*",
                r"^who\s+(said|spoke|talked|mentioned)\s*",
                r"^someone\s+(said|saying|spoke|speaking)\s*",
                r"^find\s+the\s+person\s+(saying|speaking|talking)\s*",
                r"^find\s+someone\s+(saying|speaking|talking)\s*",
                r"^did\s+anyone\s+(mention|say|speak|talk)\s+about\s*",
            ]
            target_phrase = raw_q.lower()
            for mp in meta_phrases:
                target_phrase = _re.sub(mp, "", target_phrase).strip()
            is_exact_mode = False

        target_words = _tokenize_text(target_phrase)
        if not target_words:
            target_words = _tokenize_text(raw_q)

        logger.info(f"[SpeechSearch] Mode={'EXACT_PHRASE' if is_exact_mode else 'NATURAL'}, target_phrase='{target_phrase}', target_words={target_words}")

        # 2. Retrieve all transcript segments from MongoDB or metadata fallback
        all_segments = []
        if db is not None:
            try:
                res = db.transcripts.find({}, {"_id": 0})
                docs = []
                if hasattr(res, "limit"):
                    try:
                        docs = list(res.limit(500))
                    except Exception:
                        docs = list(res)
                else:
                    docs = list(res)
                
                if not docs and hasattr(res, "return_value"):
                    try:
                        docs = list(res.return_value)
                    except Exception:
                        pass

                if docs:
                    all_segments.extend(docs)
            except Exception as _me:
                logger.warning(f"[SpeechSearch] Mongo transcript retrieval exception: {_me}")

        if not all_segments:
            transcript_dir = settings.BASE_DIR / "storage" / "metadata"
            if not transcript_dir.exists():
                transcript_dir = settings.BASE_DIR / "backend" / "storage" / "metadata"
            possible_files = list(transcript_dir.glob("*transcripts*.json")) if transcript_dir.exists() else []
            for tf in possible_files:
                try:
                    with open(tf, "r", encoding="utf-8") as _f:
                        all_segments.extend(_json.load(_f))
                except Exception as _fe:
                    logger.warning(f"[SpeechSearch] Transcript file read error: {_fe}")

        if not all_segments:
            logger.info("[SpeechSearch] Zero total transcript segments found.")
            return []

        # Group segments by videoId and sort chronologically by startTime
        video_groups = {}
        for seg in all_segments:
            vid = seg.get("videoId", "")
            if vid not in video_groups:
                video_groups[vid] = []
            video_groups[vid].append(seg)

        for vid in video_groups:
            video_groups[vid].sort(key=lambda s: float(s.get("startTime", s.get("start", 0.0))))

        # 3. Construct 1-segment, 2-segment, and 3-segment sliding windows
        candidate_windows = []

        for vid, segs in video_groups.items():
            n = len(segs)
            for i in range(n):
                # Window size 1
                candidate_windows.append({
                    "videoId": vid,
                    "segments": [segs[i]],
                    "startTime": float(segs[i].get("startTime", segs[i].get("start", 0.0))),
                    "endTime": float(segs[i].get("endTime", segs[i].get("end", 0.0))),
                })

                # Window size 2
                if i + 1 < n:
                    gap = float(segs[i+1].get("startTime", segs[i+1].get("start", 0.0))) - float(segs[i].get("endTime", segs[i].get("end", 0.0)))
                    if gap <= 4.0:
                        candidate_windows.append({
                            "videoId": vid,
                            "segments": [segs[i], segs[i+1]],
                            "startTime": float(segs[i].get("startTime", segs[i].get("start", 0.0))),
                            "endTime": float(segs[i+1].get("endTime", segs[i+1].get("end", 0.0))),
                        })

                # Window size 3
                if i + 2 < n:
                    gap1 = float(segs[i+1].get("startTime", segs[i+1].get("start", 0.0))) - float(segs[i].get("endTime", segs[i].get("end", 0.0)))
                    gap2 = float(segs[i+2].get("startTime", segs[i+2].get("start", 0.0))) - float(segs[i+1].get("endTime", segs[i+1].get("end", 0.0)))
                    if gap1 <= 4.0 and gap2 <= 4.0:
                        candidate_windows.append({
                            "videoId": vid,
                            "segments": [segs[i], segs[i+1], segs[i+2]],
                            "startTime": float(segs[i].get("startTime", segs[i].get("start", 0.0))),
                            "endTime": float(segs[i+2].get("endTime", segs[i+2].get("end", 0.0))),
                        })

        # 4. Evaluate Exact Matches vs High-Confidence Approximate Matches
        exact_matches = []
        approx_matches = []
        n_target = len(target_words)

        for win in candidate_windows:
            vid = win["videoId"]
            win_words = []
            full_window_text_parts = []

            for seg in win["segments"]:
                seg_text = str(seg.get("text", "")).strip()
                if seg_text:
                    full_window_text_parts.append(seg_text)
                seg_st = float(seg.get("startTime", seg.get("start", 0.0)))
                seg_et = float(seg.get("endTime", seg.get("end", 0.0)))

                seg_word_items = seg.get("words")
                if seg_word_items and isinstance(seg_word_items, list):
                    for w_dict in seg_word_items:
                        if isinstance(w_dict, dict):
                            raw_w = str(w_dict.get("word", "")).strip()
                            w_st = float(w_dict.get("startTime", w_dict.get("start", seg_st)))
                            w_et = float(w_dict.get("endTime", w_dict.get("end", seg_et)))
                        else:
                            raw_w = str(getattr(w_dict, "word", "")).strip()
                            w_st = float(getattr(w_dict, "startTime", seg_st))
                            w_et = float(getattr(w_dict, "endTime", seg_et))
                        clean_w = _clean_word(raw_w)
                        if clean_w:
                            win_words.append({
                                "word": raw_w,
                                "norm": clean_w,
                                "startTime": w_st,
                                "endTime": w_et,
                                "has_word_ts": True,
                                "seg_text": seg_text,
                                "seg_st": seg_st,
                                "seg_et": seg_et
                            })
                else:
                    # Legacy transcript fallback: tokenize text manually
                    tokens = _tokenize_text(seg_text)
                    for tok in tokens:
                        win_words.append({
                            "word": tok,
                            "norm": tok,
                            "startTime": seg_st,
                            "endTime": seg_et,
                            "has_word_ts": False,
                            "seg_text": seg_text,
                            "seg_st": seg_st,
                            "seg_et": seg_et
                        })

            if not win_words or n_target == 0:
                continue

            full_window_text = " ".join(full_window_text_parts)
            n_win = len(win_words)

            # Check contiguous exact sequence match
            found_exact_idx = -1
            for k in range(0, n_win - n_target + 1):
                match_all = True
                for j in range(n_target):
                    if not _words_match_equal(target_words[j], win_words[k + j]["norm"]):
                        match_all = False
                        break
                if match_all:
                    found_exact_idx = k
                    break

            if found_exact_idx >= 0:
                w_start_item = win_words[found_exact_idx]
                w_end_item = win_words[found_exact_idx + n_target - 1]

                if w_start_item["has_word_ts"]:
                    matched_start = round(w_start_item["startTime"], 2)
                    matched_end = round(w_end_item["endTime"], 2)
                else:
                    # Legacy fallback
                    matched_start = round(w_start_item["seg_st"], 2)
                    matched_end = round(w_end_item["seg_et"], 2)

                matched_end = max(matched_end, round(matched_start + 0.5, 2))
                frame_num = max(1, int(matched_start))

                score = 1.00 if n_win == n_target else 0.98
                badge = "Exact Phrase Match" if is_exact_mode else "Phrase Match"
                method = "Exact Phrase Match" if is_exact_mode else "Phrase Match"

                exact_matches.append({
                    "videoId": vid,
                    "frameNumber": frame_num,
                    "timestamp": matched_start,
                    "endTime": matched_end,
                    "text": full_window_text,
                    "matchedPhrase": target_phrase,
                    "confidenceBadge": badge,
                    "matchingMethod": method,
                    "score": score,
                    "windowSize": len(win["segments"])
                })

        # 5. If ZERO exact matches exist, evaluate High-Confidence Approximate Matches
        if not exact_matches:
            for win in candidate_windows:
                vid = win["videoId"]
                win_words = []
                full_window_text_parts = []

                for seg in win["segments"]:
                    seg_text = str(seg.get("text", "")).strip()
                    if seg_text:
                        full_window_text_parts.append(seg_text)
                    seg_st = float(seg.get("startTime", seg.get("start", 0.0)))
                    seg_et = float(seg.get("endTime", seg.get("end", 0.0)))

                    seg_word_items = seg.get("words")
                    if seg_word_items and isinstance(seg_word_items, list):
                        for w_dict in seg_word_items:
                            if isinstance(w_dict, dict):
                                raw_w = str(w_dict.get("word", "")).strip()
                                w_st = float(w_dict.get("startTime", w_dict.get("start", seg_st)))
                                w_et = float(w_dict.get("endTime", w_dict.get("end", seg_et)))
                            else:
                                raw_w = str(getattr(w_dict, "word", "")).strip()
                                w_st = float(getattr(w_dict, "startTime", seg_st))
                                w_et = float(getattr(w_dict, "endTime", seg_et))
                            clean_w = _clean_word(raw_w)
                            if clean_w:
                                win_words.append({
                                    "word": raw_w,
                                    "norm": clean_w,
                                    "startTime": w_st,
                                    "endTime": w_et,
                                    "has_word_ts": True,
                                    "seg_st": seg_st,
                                    "seg_et": seg_et
                                })
                    else:
                        tokens = _tokenize_text(seg_text)
                        for tok in tokens:
                            win_words.append({
                                "word": tok,
                                "norm": tok,
                                "startTime": seg_st,
                                "endTime": seg_et,
                                "has_word_ts": False,
                                "seg_st": seg_st,
                                "seg_et": seg_et
                            })

                if not win_words or n_target == 0:
                    continue

                full_window_text = " ".join(full_window_text_parts)
                n_win = len(win_words)

                # Slide over windows of length ~ n_target
                best_approx_score = 0.0
                best_match_range = (0, min(n_win - 1, n_target - 1))

                for k in range(0, max(1, n_win - n_target + 1)):
                    window_slice = win_words[k : k + n_target]
                    if not window_slice:
                        continue

                    matched_w_count = 0.0
                    for j in range(min(n_target, len(window_slice))):
                        t_word = target_words[j]
                        w_word = window_slice[j]["norm"]
                        if _words_match_equal(t_word, w_word):
                            matched_w_count += 1.0
                        else:
                            sim = SequenceMatcher(None, t_word, w_word).ratio()
                            if sim >= 0.70:
                                matched_w_count += sim

                    seq_score = matched_w_count / float(n_target)
                    if seq_score > best_approx_score:
                        best_approx_score = seq_score
                        best_match_range = (k, k + len(window_slice) - 1)

                # Require high confidence threshold >= 0.80 for word sequence matching
                if is_exact_mode and best_approx_score >= 0.80:
                    start_w = win_words[best_match_range[0]]
                    end_w = win_words[best_match_range[1]]

                    if start_w["has_word_ts"]:
                        matched_start = round(start_w["startTime"], 2)
                        matched_end = round(end_w["endTime"], 2)
                    else:
                        matched_start = round(start_w["seg_st"], 2)
                        matched_end = round(end_w["seg_et"], 2)

                    matched_end = max(matched_end, round(matched_start + 0.5, 2))
                    score = round(0.75 + best_approx_score * 0.15, 4)
                    badge = "Approximate Phrase Match"
                    method = "Approximate Phrase Match"

                    approx_matches.append({
                        "videoId": vid,
                        "frameNumber": max(1, int(matched_start)),
                        "timestamp": matched_start,
                        "endTime": matched_end,
                        "text": full_window_text,
                        "matchedPhrase": target_phrase,
                        "confidenceBadge": badge,
                        "matchingMethod": method,
                        "score": score,
                        "windowSize": len(win["segments"])
                    })
                elif not is_exact_mode and best_approx_score >= 0.50:
                    start_w = win_words[best_match_range[0]]
                    end_w = win_words[best_match_range[1]]
                    matched_start = round(start_w["seg_st"], 2)
                    matched_end = round(end_w["seg_et"], 2)
                    score = round(min(0.88, max(0.50, best_approx_score)), 4)
                    badge = "Speech Match"
                    method = "Natural Speech Match"

                    approx_matches.append({
                        "videoId": vid,
                        "frameNumber": max(1, int(matched_start)),
                        "timestamp": matched_start,
                        "endTime": matched_end,
                        "text": full_window_text,
                        "matchedPhrase": target_phrase,
                        "confidenceBadge": badge,
                        "matchingMethod": method,
                        "score": score,
                        "windowSize": len(win["segments"])
                    })

        # 6. Exact matches MUST ALWAYS outrank approximate matches
        if exact_matches:
            exact_matches.sort(key=lambda x: (x["score"], -x["windowSize"]), reverse=True)
            dedup_exact = []
            seen_ts = set()
            for em in exact_matches:
                k = (em["videoId"], round(em["timestamp"], 1))
                if k not in seen_ts:
                    seen_ts.add(k)
                    dedup_exact.append(em)
            return dedup_exact[:top_k]

        elif approx_matches:
            approx_matches.sort(key=lambda x: x["score"], reverse=True)
            dedup_approx = []
            seen_ts = set()
            for am in approx_matches:
                k = (am["videoId"], round(am["timestamp"], 1))
                if k not in seen_ts:
                    seen_ts.add(k)
                    dedup_approx.append(am)
            return dedup_approx[:top_k]

        return []



    _resolve_crop_cache: Dict[Tuple[str, int, Optional[int]], Tuple[str, str, int, float, List[float]]] = {}

    @classmethod
    def _resolve_track_crop_and_frame(
        cls,
        vid: str,
        tid: int,
        track_doc: Dict[str, Any],
        best_frame_num: Optional[int] = None,
        db: Any = None
    ) -> Tuple[str, str, int, float, List[float]]:
        """
        Resolves representative frame, timestamp, bbox, cropThumbnail URL, and annotatedFrame URL
        for a specific Track ID (SOURCE OF TRUTH).
        Ensures exact track bbox crop exists (generating dynamically if needed) and returns valid static URLs.
        """
        cache_key = (vid, int(tid), best_frame_num)
        if cache_key in cls._resolve_crop_cache:
            return cls._resolve_crop_cache[cache_key]
        from app.processing.debug.crop_generator import ObjectCropGenerator
        debug_dir = settings.DEBUG_DIR
        crop_dir = debug_dir / vid / "tracks" / str(tid)
        crop_dir.mkdir(parents=True, exist_ok=True)

        trajectory = track_doc.get("trajectory", [])
        frames = track_doc.get("frames", [])

        # Build map of trajectory points for THIS exact trackId: frameNumber -> point dict
        traj_by_frame = {}
        for pt in trajectory:
            fn = int(pt.get("frameNumber", -1))
            if fn > 0:
                traj_by_frame[fn] = pt

        selected_frame = None
        selected_ts = float(track_doc.get("startTime", 0.0))
        selected_bbox = None

        # 1. If best_frame_num provided, use it
        if best_frame_num is not None:
            selected_frame = best_frame_num

        # 2. Pick frame with highest detection confidence in THIS track's trajectory
        if selected_frame is None and trajectory:
            sorted_traj = sorted(trajectory, key=lambda d: float(d.get("confidence", 0.0)), reverse=True)
            non_intro = [pt for pt in sorted_traj if int(pt.get("frameNumber", 1)) > 1]
            best_pt = non_intro[0] if non_intro else sorted_traj[0]
            selected_frame = int(best_pt.get("frameNumber", 1))
            selected_ts = float(best_pt.get("timestamp", selected_frame / 25.0))
            selected_bbox = best_pt.get("boundingBox")

        # 3. Pick middle frame from existing crops on disk for THIS track
        if selected_frame is None:
            existing_crops = sorted(crop_dir.glob("*.jpg"))
            if existing_crops:
                mid_crop = existing_crops[len(existing_crops) // 2]
                try:
                    selected_frame = int(mid_crop.stem.replace("frame_", ""))
                    selected_ts = selected_frame / 25.0
                except Exception:
                    pass

        # 4. Fallback to middle frame in track frames list
        if selected_frame is None and frames:
            mid_f = frames[len(frames) // 2]
            selected_frame = int(mid_f)
            selected_ts = selected_frame / 25.0

        if selected_frame is None:
            selected_frame = 1
            selected_ts = 1.0

        # Look up exact bbox and timestamp for THIS trackId on selected_frame
        if selected_frame in traj_by_frame:
            pt = traj_by_frame[selected_frame]
            selected_ts = float(pt.get("timestamp", selected_ts if selected_ts > 0 else selected_frame / 25.0))
            selected_bbox = pt.get("boundingBox")

        if selected_ts <= 0.0 and selected_frame > 0:
            selected_ts = round(selected_frame / 25.0, 2)

        # Fallback lookup in MongoDB detections for THIS exact (videoId, trackId, frameNumber)
        if selected_bbox is None and db is not None:
            try:
                d_doc = db.detections.find_one(
                    {"videoId": vid, "trackId": tid, "frameNumber": selected_frame},
                    {"_id": 0, "boundingBox": 1, "timestamp": 1}
                )
                if not d_doc:
                    d_doc = db.detections.find_one(
                        {"videoId": vid, "trackId": str(tid), "frameNumber": selected_frame},
                        {"_id": 0, "boundingBox": 1, "timestamp": 1}
                    )
                if d_doc:
                    selected_bbox = d_doc.get("boundingBox")
                    if d_doc.get("timestamp"):
                        selected_ts = float(d_doc["timestamp"])
            except Exception:
                pass

        crop_file = crop_dir / f"frame_{selected_frame:04d}.jpg"
        crop_url = f"/static/storage/debug/{vid}/tracks/{tid}/frame_{selected_frame:04d}.jpg"
        annotated_url = f"/static/storage/debug/{vid}/frames/frame_{selected_frame:04d}.jpg"

        # Dynamically generate crop from EXACT track bbox if crop file missing or invalid
        if not crop_file.exists() or crop_file.stat().st_size < 100:
            if selected_bbox:
                try:
                    c_url, _ = ObjectCropGenerator.get_or_create_crop(
                        video_id=vid,
                        track_id=int(tid),
                        frame_number=selected_frame,
                        bbox=selected_bbox,
                        padding_pct=0.10
                    )
                    if c_url:
                        crop_url = c_url
                except Exception as _ce:
                    logger.warning(f"[EvidenceResolver] Crop generation error for track {tid} frame {selected_frame}: {_ce}")

        # FALLBACK RULE: If exact track crop missing, fallback to annotated frame of THIS track, NEVER another track!
        res = (crop_url, annotated_url, selected_frame, selected_ts, (selected_bbox or []))
        cls._resolve_crop_cache[cache_key] = res
        return res

    @classmethod
    def _run_attribute_v2_search(
        cls,
        query_text: str,
        route_info: Dict[str, Any],
        video_id_filter: Any,
        top_k: int,
        db: Any,
        raw_object_hits: Optional[List[Tuple[int, float]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 3.19 Dedicated Attribute V2 Search.
        Pre-filters candidates, evaluates PAR/attribute engine, sorts by final_track_score,
        and returns enriched result dicts with exact Track ID evidence consistency.
        """
        import json as _json
        import numpy as _np
        from pathlib import Path as _Path

        tracks_meta_path = settings.BASE_DIR / "storage" / "metadata" / "tracks.json"
        debug_dir = settings.DEBUG_DIR

        if not tracks_meta_path.exists():
            logger.warning("[AttributeV2] tracks.json not found — falling back to empty result.")
            return []

        try:
            with open(tracks_meta_path, "r", encoding="utf-8") as _f:
                all_tracks = _json.load(_f)
        except Exception as _e:
            logger.warning(f"[AttributeV2] Failed to read tracks.json: {_e}")
            return []

        # Filter to person tracks, optionally by video_id
        person_tracks = [
            t for t in all_tracks
            if str(t.get("objectClass", "")).lower() == "person"
            and (video_id_filter is None or t.get("videoId") == video_id_filter)
        ]

        if not person_tracks:
            logger.warning("[AttributeV2] No person tracks found in tracks.json.")
            return []

        # Collect candidate track IDs from raw_object_hits if provided
        candidate_tids = set()
        if raw_object_hits:
            emb_file = settings.BASE_DIR / "storage" / "metadata" / "embeddings.json"
            if emb_file.exists():
                try:
                    with open(emb_file, "r", encoding="utf-8") as f:
                        emb_list = _json.load(f)
                        faiss_map = {e["faissId"]: int(e["trackId"]) for e in emb_list if e.get("type") == "object" and "faissId" in e and "trackId" in e}
                        for fid, sim in raw_object_hits:
                            if fid in faiss_map:
                                candidate_tids.add(faiss_map[fid])
                except Exception:
                    pass

        if candidate_tids:
            prioritized_tracks = [t for t in person_tracks if int(t.get("trackId", -1)) in candidate_tids]
            other_tracks = [t for t in person_tracks if int(t.get("trackId", -1)) not in candidate_tids]
            other_tracks.sort(key=lambda t: float(t.get("durationSec", len(t.get("frames", [])))), reverse=True)
            eval_tracks = (prioritized_tracks + other_tracks)[:60]
        else:
            sorted_tracks = sorted(person_tracks, key=lambda t: float(t.get("durationSec", len(t.get("frames", [])))), reverse=True)
            eval_tracks = sorted_tracks[:60]

        logger.info(f"[AttributeV2] Evaluating {len(eval_tracks)} candidate person tracks for route={route_info.get('route')}")

        batch_items = []
        track_map = {}

        for track in eval_tracks:
            tid = track.get("trackId")
            vid = track.get("videoId", "")
            if tid is None:
                continue

            crop_dir = debug_dir / vid / "tracks" / str(tid)
            crop_paths = sorted(crop_dir.glob("*.jpg")) if crop_dir.exists() else []

            # If no crops exist yet, try generating keyframe crop for evaluation
            if not crop_paths and track.get("trajectory"):
                first_t = track["trajectory"][0]
                fn = int(first_t.get("frameNumber", 1))
                box = first_t.get("boundingBox")
                if box:
                    from app.processing.debug.crop_generator import ObjectCropGenerator
                    try:
                        ObjectCropGenerator.get_or_create_crop(vid, int(tid), fn, box)
                        crop_paths = sorted(crop_dir.glob("*.jpg")) if crop_dir.exists() else []
                    except Exception:
                        pass

            if not crop_paths:
                continue

            int_tid = int(tid)
            batch_items.append({"track_id": int_tid, "crop_paths": crop_paths})
            track_map[int_tid] = (track, crop_paths)

        if not batch_items:
            return []

        try:
            eval_results = attribute_retrieval_engine.evaluate_person_tracks_batch(
                track_items=batch_items,
                route_info=route_info
            )
        except Exception as _eval_err:
            logger.warning(f"[AttributeV2] evaluate_person_tracks_batch error: {_eval_err}")
            eval_results = []

        scored_results = []
        for result in eval_results:
            tid = result.get("track_id")
            if tid not in track_map:
                continue

            track, crop_paths = track_map[tid]
            vid = track.get("videoId", "")
            final_score = result.get("final_track_score", 0.0)

            # Pick best frame directly from crop_paths evaluated in evaluate_person_tracks_batch
            best_frame_num = None
            if result.get("frame_scores") and crop_paths:
                f_scores = result.get("frame_scores", [])
                sampled_crops = crop_paths[:5]
                if f_scores and len(f_scores) == len(sampled_crops):
                    best_idx = int(_np.argmax(f_scores))
                    try:
                        best_frame_num = int(sampled_crops[best_idx].stem.replace("frame_", ""))
                    except Exception:
                        best_frame_num = None

            # Resolve representative frame, timestamp, bbox, and crop URLs ensuring exact Track ID evidence
            crop_url, annotated_url, frame_num, ts, bbox = cls._resolve_track_crop_and_frame(
                vid=vid,
                tid=int(tid),
                track_doc=track,
                best_frame_num=best_frame_num,
                db=db
            )

            scored_results.append({
                "_v2_faiss_sentinel": 0,
                "videoId": vid,
                "trackId": int(tid),
                "objectClass": str(track.get("objectClass", "person")),
                "frameNumber": frame_num,
                "timestamp": ts,
                "bbox": bbox,
                "cropThumbnail": crop_url,
                "annotatedFrame": annotated_url,
                "evidenceType": "track_crop",
                "similarityScore": round(final_score, 4),
                "appearanceCount": len(track.get("frames", [frame_num])),
                "firstSeen": float(track.get("startTime", ts)),
                "lastSeen": float(track.get("endTime", ts)),
                "trackDurationSec": float(track.get("durationSec", 0.0)),
                "averageYOLOConfidence": float(track.get("confidence", 0.85)),
                "trackPersistence": float(track.get("persistence", 0.50)),
            })

        scored_results.sort(key=lambda x: x["similarityScore"], reverse=True)
        return scored_results[:top_k]

    @classmethod
    def search(cls, request: SearchQueryRequest) -> SearchResponse:

        total_start = time.time()
        t_perf_start = time.perf_counter()

        query_parsing_ms = 0.0
        model_init_ms = 0.0
        tokenizer_ms = 0.0
        query_embed_ms = 0.0
        gpu_sync_ms = 0.0
        frame_search_ms = 0.0
        object_search_ms = 0.0
        total_filter_ms = 0.0
        metadata_lookup_ms = 0.0
        grouping_time_ms = 0.0
        attribute_verification_ms = 0.0
        relational_verification_ms = 0.0
        result_enrichment_ms = 0.0
        ranking_time_ms = 0.0
        serialization_time_ms = 0.0

        t0_parse = time.perf_counter()
        query_text = request.query.strip()
        top_k = request.topK

        # Use request similarityThreshold override if provided, else use settings
        threshold = (
            request.similarityThreshold
            if request.similarityThreshold is not None
            else getattr(settings, "SIMILARITY_THRESHOLD", 0.20)
        )

        logger.info(f"[SemanticSearch] Executing Phase 2.3 Search: '{query_text}' (topK={top_k}, threshold={threshold})")

        # 0. Route Classification (Bypass visual embedding & FAISS when route is SPEECH)
        route_info = QueryRouter.classify(query_text)
        route_name = route_info.get("route", "GENERIC_SEMANTIC")
        query_parsing_ms = round((time.perf_counter() - t0_parse) * 1000.0, 3)

        try:
            db = mongo_db.db
        except Exception as err:
            logger.warning(f"[SemanticSearch] MongoDB not available ({str(err)}). Using fallback in-memory FAISS defaults.")
            db = None

        if route_name == "SPEECH":
            speech_mode = route_info.get("speechMode", "NATURAL")
            target_phrase = route_info.get("targetPhrase", "")
            logger.info(f"[SemanticSearch] Immediate SPEECH Route for '{query_text}': speech_mode={speech_mode}, target_phrase='{target_phrase}'")
            t_speech_start = time.time()
            speech_frames = cls._search_speech(query_text=query_text, top_k=top_k, db=db)
            speech_search_ms = round((time.time() - t_speech_start) * 1000.0, 2)
            total_search_ms = round((time.time() - total_start) * 1000.0, 2)

            from app.services.clip_generator import ClipGeneratorService
            speech_frame_results: List[FrameSearchResult] = []
            for rank_pos, sf in enumerate(speech_frames[:top_k], start=1):
                v_id = sf.get("videoId", "")
                ts = float(sf.get("timestamp", 0.0))
                end_ts = float(sf.get("endTime", ts + 1.0))
                fn = int(sf.get("frameNumber", int(ts)))
                
                clip_start = max(0.0, ts - 1.5)
                clip_end = end_ts + 1.5
                
                c_url, c_start, c_end, c_dur = ClipGeneratorService.generate_result_clip(
                    video_id=v_id,
                    match_timestamp=ts,
                    identifier_tag=f"speech{fn}",
                    start_override=clip_start,
                    end_override=clip_end,
                    precise_mode=True
                )

                ann_url = f"/static/storage/debug/{v_id}/frames/frame_{fn:04d}.jpg"
                sc = float(sf.get("score", 0.92))
                badge = sf.get("confidenceBadge", "Exact Phrase Match")
                method = sf.get("matchingMethod", "Exact Phrase Match")
                try:
                    speech_frame_results.append(FrameSearchResult(
                        videoId=v_id,
                        frameNumber=fn,
                        timestamp=ts,
                        thumbnail=ann_url,
                        annotatedFrame=ann_url,
                        faissId=0,
                        similarityScore=sc,
                        similarityPercentage=f"{round(sc * 100.0, 2)}%",
                        indexOrigin="SpeechTranscript/Whisper",
                        finalScore=sc,
                        finalScorePercentage=f"{round(sc * 100.0, 2)}%",
                        rankingPosition=rank_pos,
                        confidenceBadge=badge,
                        explanation=f"Whisper transcript {method.lower()}: \"{sf.get('text', '')}\" [{ts:.1f}s–{end_ts:.1f}s]",

                        averageYOLOConfidence=0.0,
                        trackPersistence=0.0,
                        videoClipUrl=c_url,
                        clipStartTime=c_start,
                        clipEndTime=c_end,
                        clipDuration=c_dur,
                        evidenceType="speech_transcript",
                    ))
                except Exception as sp_err:
                    logger.warning(f"[SemanticSearch] Speech result build error: {sp_err}")

            matching_method = speech_frames[0].get("matchingMethod") if speech_frames else ("Exact Phrase Match" if speech_mode == "EXACT_PHRASE" else "Natural Speech Match")

            stats_sp = SearchStatistics(
                queryEmbeddingTimeMs=0.0,
                frameSearchTimeMs=speech_search_ms,
                objectSearchTimeMs=0.0,
                totalSearchTimeMs=total_search_ms
            )
            analytics_dict_sp = SearchAnalyticsBuilder.build_analytics(
                candidates_retrieved=len(speech_frames),
                results_rejected_by_threshold=0,
                accepted_results=len(speech_frame_results),
                grouped_tracks=0,
                final_returned_results=len(speech_frame_results),
                similarity_threshold=threshold,
                filtering_time_ms=0.0,
                grouping_time_ms=0.0,
                ranking_time_ms=0.0,
                weight_semantic=1.0,
                weight_yolo=0.0,
                weight_persistence=0.0,
                total_retrieval_time_ms=total_search_ms,
                route="SPEECH",
                speech_mode=speech_mode,
                target_phrase=target_phrase,
                matching_method=matching_method
            )
            logger.info(
                f"[SemanticSearch] SPEECH route complete. Query='{query_text}', "
                f"Method={matching_method}, Results={len(speech_frame_results)}, Latency={total_search_ms}ms"
            )
            return SearchResponse(
                query=query_text,
                topK=top_k,
                similarityThreshold=threshold,
                frameResults=speech_frame_results,
                objectResults=[],
                statistics=stats_sp,
                analytics=SearchAnalytics(**analytics_dict_sp),
                route="SPEECH",
                speechMode=speech_mode,
                targetPhrase=target_phrase,
                matchingMethod=matching_method
            )

        if route_name == "OCR":
            target_phrase = route_info.get("targetPhrase") or route_info.get("ocrTextQuery", "")
            if not target_phrase:
                parsed_attrs = AttributeFilter.parse_query(query_text)
                target_phrase = parsed_attrs.get("ocrTextQuery", "")

            q_raw = target_phrase.strip()
            q_norm = normalize_ocr_text(q_raw)
            q_tokens = [t for t in q_norm.split() if t]
            q_compact = re.sub(r"\s+", "", q_norm)

            logger.info(f"[SemanticSearch] Immediate OCR Route for '{query_text}': target_phrase='{q_raw}', norm='{q_norm}'")
            t_ocr_start = time.time()
            ocr_frame_results: List[FrameSearchResult] = []
            ocr_candidates_retrieved = 0

            def _get_ocr_annotated_url(vid: str, fn: int, rec_data: dict, t_text: str = None, t_box: list = None) -> str:
                src_frame = settings.STORAGE_DIR / "debug" / vid / "frames" / f"frame_{fn:04d}.jpg"
                if not src_frame.exists():
                    src_frame = settings.FRAMES_DIR / vid / f"frame_{fn:04d}.jpg"
                
                dets = rec_data.get("detections", [])
                if src_frame.exists() and dets:
                    url = OcrAnnotator.annotate_frame(
                        image_input=src_frame,
                        video_id=vid,
                        frame_number=fn,
                        detections=dets,
                        target_text=t_text,
                        target_bbox=t_box
                    )
                    if url:
                        return url
                return f"/static/storage/debug/{vid}/ocr/ocr_frame_{fn:04d}.jpg"

            # Helper for Fix 3: Space-insensitive representation
            def _compact_norm(text: str) -> str:
                if not text:
                    return ""
                n = normalize_ocr_text(text)
                return re.sub(r"\s+", "", n)

            # Helper for Fix 4: Conservative OCR typo tolerance rule
            def _check_conservative_typo_match(t1: str, t2: str) -> bool:
                from difflib import SequenceMatcher
                n1 = normalize_ocr_text(t1).strip()
                n2 = normalize_ocr_text(t2).strip()
                if len(n1) < 5 or len(n2) < 5:
                    return False
                if n1[:3] != n2[:3] and not n1.endswith(n2) and not n2.endswith(n1):
                    return False
                ratio = SequenceMatcher(None, n1, n2).ratio()
                return ratio >= 0.82

            if q_norm and db is not None:
                # FIX 1 — MULTI-TOKEN CANDIDATE GENERATION
                escaped_q = re.escape(q_norm)
                escaped_compact = re.escape(q_compact)
                or_clauses = [
                    {"extractedText": {"$regex": escaped_q, "$options": "i"}},
                    {"tokens": {"$regex": escaped_q, "$options": "i"}},
                    {"detections.text": {"$regex": escaped_q, "$options": "i"}},
                    {"detections.normalizedText": {"$regex": escaped_q, "$options": "i"}},
                    {"detections.text": {"$regex": escaped_compact, "$options": "i"}},
                    {"detections.normalizedText": {"$regex": escaped_compact, "$options": "i"}}
                ]

                # Include constituent tokens in MongoDB candidate retrieval
                for tok in q_tokens:
                    if len(tok) >= 2:
                        tok_esc = re.escape(tok)
                        or_clauses.extend([
                            {"extractedText": {"$regex": tok_esc, "$options": "i"}},
                            {"tokens": {"$regex": tok_esc, "$options": "i"}},
                            {"detections.text": {"$regex": tok_esc, "$options": "i"}},
                            {"detections.normalizedText": {"$regex": tok_esc, "$options": "i"}}
                        ])
                        # If token length >= 5, check prefix regex for typo tolerance candidates
                        if len(tok) >= 5:
                            prefix_esc = re.escape(tok[:4])
                            or_clauses.extend([
                                {"detections.text": {"$regex": prefix_esc, "$options": "i"}},
                                {"detections.normalizedText": {"$regex": prefix_esc, "$options": "i"}}
                            ])

                ocr_records = list(db.ocr.find({"$or": or_clauses}, {"_id": 0}))

                if ocr_records:
                    ocr_candidates_retrieved = len(ocr_records)
                    frame_candidates = []

                    for rec in ocr_records:
                        vid = rec.get("videoId", "")
                        fn = int(rec.get("frameNumber", 0))
                        ts = float(rec.get("timestamp", fn))
                        dets = rec.get("detections", [])
                        if not dets:
                            continue

                        # FIX 2 — VERTICAL + MULTI-LINE PHRASE RECONSTRUCTION
                        # Sort detections top-to-bottom, left-to-right (reading order)
                        sorted_dets = sorted(
                            dets,
                            key=lambda d: (d.get("bbox", [0, 0, 0, 0])[1], d.get("bbox", [0, 0, 0, 0])[0])
                        )

                        # Cluster detections into horizontal text lines
                        lines = []
                        for d in sorted_dets:
                            b = d.get("bbox", [0, 0, 0, 0])
                            if len(b) < 4:
                                continue
                            h_box = max(1.0, b[3] - b[1])
                            cy_box = (b[1] + b[3]) / 2.0

                            placed = False
                            for line in lines:
                                line_h = min(item.get("bbox", [0, 0, 0, 0])[3] - item.get("bbox", [0, 0, 0, 0])[1] for item in line)
                                line_cy = sum((item.get("bbox", [0, 0, 0, 0])[1] + item.get("bbox", [0, 0, 0, 0])[3]) / 2.0 for item in line) / len(line)
                                if abs(cy_box - line_cy) <= 0.5 * max(1.0, line_h):
                                    line.append(d)
                                    placed = True
                                    break
                            if not placed:
                                lines.append([d])

                        reconstructed_phrases = []

                        # A. Horizontal line phrases
                        for line in lines:
                            line_sorted = sorted(line, key=lambda d: d.get("bbox", [0, 0, 0, 0])[0])
                            txt_combined = " ".join(d.get("text", "").strip() for d in line_sorted)
                            norm_combined = normalize_ocr_text(txt_combined)
                            boxes = [d.get("bbox", [0, 0, 0, 0]) for d in line_sorted if len(d.get("bbox", [])) == 4]
                            if boxes:
                                fused_box = [
                                    min(b[0] for b in boxes),
                                    min(b[1] for b in boxes),
                                    max(b[2] for b in boxes),
                                    max(b[3] for b in boxes)
                                ]
                                avg_conf = sum(float(d.get("confidence", 0.9)) for d in line_sorted) / len(line_sorted)
                                reconstructed_phrases.append({
                                    "text": txt_combined,
                                    "normalizedText": norm_combined,
                                    "confidence": avg_conf,
                                    "bbox": fused_box,
                                    "is_reconstructed": True,
                                    "component_dets": line_sorted
                                })

                        # B. Vertical / multi-line stack phrases (Fix 2)
                        if len(lines) >= 2:
                            for idx_a in range(len(lines)):
                                for idx_b in range(idx_a + 1, min(len(lines), idx_a + 3)):
                                    line_a = lines[idx_a]
                                    line_b = lines[idx_b]
                                    
                                    # Bounds of line_a and line_b
                                    box_a = [
                                        min(d["bbox"][0] for d in line_a),
                                        min(d["bbox"][1] for d in line_a),
                                        max(d["bbox"][2] for d in line_a),
                                        max(d["bbox"][3] for d in line_a)
                                    ]
                                    box_b = [
                                        min(d["bbox"][0] for d in line_b),
                                        min(d["bbox"][1] for d in line_b),
                                        max(d["bbox"][2] for d in line_b),
                                        max(d["bbox"][3] for d in line_b)
                                    ]

                                    h_a = max(1.0, box_a[3] - box_a[1])
                                    h_b = max(1.0, box_b[3] - box_b[1])
                                    w_a = max(1.0, box_a[2] - box_a[0])
                                    w_b = max(1.0, box_b[2] - box_b[0])

                                    cx_a = (box_a[0] + box_a[2]) / 2.0
                                    cx_b = (box_b[0] + box_b[2]) / 2.0

                                    vertical_gap = box_b[1] - box_a[3]
                                    horizontal_align = abs(cx_a - cx_b) <= 1.2 * max(w_a, w_b)

                                    if vertical_gap >= -0.3 * h_a and vertical_gap <= 2.0 * max(h_a, h_b) and horizontal_align:
                                        stacked_dets = sorted(line_a, key=lambda d: d["bbox"][0]) + sorted(line_b, key=lambda d: d["bbox"][0])
                                        txt_stack = " ".join(d.get("text", "").strip() for d in stacked_dets)
                                        norm_stack = normalize_ocr_text(txt_stack)
                                        fused_box_stack = [
                                            min(d["bbox"][0] for d in stacked_dets),
                                            min(d["bbox"][1] for d in stacked_dets),
                                            max(d["bbox"][2] for d in stacked_dets),
                                            max(d["bbox"][3] for d in stacked_dets)
                                        ]
                                        avg_conf_stack = sum(float(d.get("confidence", 0.9)) for d in stacked_dets) / len(stacked_dets)
                                        reconstructed_phrases.append({
                                            "text": txt_stack,
                                            "normalizedText": norm_stack,
                                            "confidence": avg_conf_stack,
                                            "bbox": fused_box_stack,
                                            "is_reconstructed": True,
                                            "component_dets": stacked_dets
                                        })

                        # ── EVALUATE 8 MATCH TIERS (Fix 5 & Fix 6) ──
                        best_tier = 9
                        best_tier_name = "None"
                        best_quality = 0.0
                        best_det = None
                        best_box = None

                        # Check reconstructed phrases first for Tier 3
                        for r_phrase in reconstructed_phrases:
                            r_norm = r_phrase["normalizedText"]
                            r_compact = _compact_norm(r_phrase["text"])

                            # Tier 3: Reconstructed Frame Phrase (Exact or conservative typo)
                            if len(q_tokens) > 1:
                                is_reconstructed_match = False
                                if r_norm == q_norm or r_compact == q_compact:
                                    is_reconstructed_match = True
                                else:
                                    # Check component token alignment for typo-tolerant reconstructed phrase
                                    r_tokens = [t for t in r_norm.split() if t]
                                    n_q = len(q_tokens)
                                    if len(r_tokens) >= n_q:
                                        for i in range(len(r_tokens) - n_q + 1):
                                            slice_toks = r_tokens[i : i + n_q]
                                            match_slice = True
                                            for qt, st in zip(q_tokens, slice_toks):
                                                if qt != st and not _check_conservative_typo_match(qt, st):
                                                    match_slice = False
                                                    break
                                            if match_slice:
                                                is_reconstructed_match = True
                                                break

                                if is_reconstructed_match and 3 < best_tier:
                                    best_tier = 3
                                    best_tier_name = "Tier 3: Reconstructed Phrase"
                                    best_quality = 0.88
                                    best_det = r_phrase
                                    best_box = r_phrase["bbox"]

                        # Check individual detections for Tiers 1, 2, 4, 5, 6, 7, 8
                        for d in dets:
                            d_text_raw = str(d.get("text", "")).strip()
                            d_norm = d.get("normalizedText") or normalize_ocr_text(d_text_raw)
                            d_compact = _compact_norm(d_text_raw)
                            d_conf = float(d.get("confidence", 0.85))
                            d_box = d.get("bbox", [0, 0, 100, 100])
                            d_tokens = [t for t in d_norm.split() if t]

                            # Tier 1: Exact Standalone Detection (FIX 5: Requires raw string equality)
                            if d_text_raw == q_raw and len(q_tokens) == 1 and len(d_tokens) == 1:
                                if 1 < best_tier:
                                    best_tier = 1
                                    best_tier_name = "Tier 1: Exact Standalone"
                                    best_quality = 1.00
                                    best_det = d
                                    best_box = d_box

                            # Tier 2: Exact Phrase Match
                            elif (d_text_raw == q_raw or d_norm == q_norm) and len(q_tokens) > 1:
                                if 2 < best_tier:
                                    best_tier = 2
                                    best_tier_name = "Tier 2: Exact Phrase"
                                    best_quality = 0.95
                                    best_det = d
                                    best_box = d_box

                            # Tier 4: Exact Token Inside Multi-Word Detection (\b word boundary)
                            elif len(q_tokens) == 1 and (re.search(r'\b' + re.escape(q_norm) + r'\b', d_norm) or re.search(r'\b' + re.escape(q_raw.lower()) + r'\b', d_text_raw.lower())):
                                if 4 < best_tier:
                                    best_tier = 4
                                    best_tier_name = "Tier 4: Exact Token"
                                    best_quality = 0.80
                                    best_det = d
                                    best_box = d_box

                            # Tier 5: Normalized Match
                            elif d_norm == q_norm or (len(q_tokens) == 1 and q_norm in d_tokens):
                                if 5 < best_tier:
                                    best_tier = 5
                                    best_tier_name = "Tier 5: Normalized Match"
                                    best_quality = 0.72
                                    best_det = d
                                    best_box = d_box

                            # Tier 6: Space-Insensitive Match (FIX 3)
                            elif q_compact == d_compact or (len(q_compact) >= 4 and q_compact in d_compact):
                                if 6 < best_tier:
                                    best_tier = 6
                                    best_tier_name = "Tier 6: Space-Insensitive Match"
                                    best_quality = 0.68
                                    best_det = d
                                    best_box = d_box

                            # Tier 7: Conservative OCR Typo-Tolerant Match (FIX 4)
                            elif len(q_tokens) == 1 and any(_check_conservative_typo_match(q_norm, dt) for dt in d_tokens):
                                if 7 < best_tier:
                                    best_tier = 7
                                    best_tier_name = "Tier 7: Conservative Typo Match"
                                    best_quality = 0.60
                                    best_det = d
                                    best_box = d_box

                            # Tier 8: Sub-word Substring Fallback
                            elif q_norm in d_text_raw.lower() or q_norm in d_norm:
                                if 8 < best_tier:
                                    best_tier = 8
                                    best_tier_name = "Tier 8: Substring Fallback"
                                    best_quality = 0.50
                                    best_det = d
                                    best_box = d_box

                        if best_det is not None and best_tier <= 8:
                            conf_val = float(best_det.get("confidence", 0.85))
                            box_w = max(1.0, best_box[2] - best_box[0]) if len(best_box) == 4 else 10.0
                            box_h = max(1.0, best_box[3] - best_box[1]) if len(best_box) == 4 else 10.0
                            vis_signal = min(1.0, (box_w * box_h / (1920.0 * 1080.0)) * 10.0)
                            
                            # FIX 7 — RANKING FORMULA (Unchanged)
                            final_score = round(0.60 * best_quality + 0.35 * conf_val + 0.05 * vis_signal, 4)

                            frame_candidates.append({
                                "videoId": vid,
                                "frameNumber": fn,
                                "timestamp": ts,
                                "matchedText": best_det.get("text", q_raw),
                                "matchedNorm": q_norm,
                                "matchTier": best_tier,
                                "matchTierName": best_tier_name,
                                "matchQuality": best_quality,
                                "confidence": conf_val,
                                "bbox": best_box,
                                "score": final_score,
                                "rec_data": rec
                            })

                    # 3. Strict Temporal Grouping & Gapped Persistent Text Handling
                    # Group consecutive frames requiring: same matchedNorm, gap <= 3s, spatial continuity
                    frame_candidates.sort(key=lambda c: (c["videoId"], c["frameNumber"]))
                    
                    occurrences = []
                    curr_group = []

                    def _boxes_overlap(b1, b2):
                        if not b1 or not b2 or len(b1) < 4 or len(b2) < 4:
                            return True
                        # Centroid distance check
                        c1_x, c1_y = (b1[0] + b1[2]) / 2.0, (b1[1] + b1[3]) / 2.0
                        c2_x, c2_y = (b2[0] + b2[2]) / 2.0, (b2[1] + b2[3]) / 2.0
                        dist = ((c1_x - c2_x)**2 + (c1_y - c2_y)**2)**0.5
                        return dist <= 150.0

                    for cand in frame_candidates:
                        if not curr_group:
                            curr_group.append(cand)
                        else:
                            prev = curr_group[-1]
                            same_vid = (cand["videoId"] == prev["videoId"])
                            time_gap = cand["timestamp"] - prev["timestamp"]
                            spatial_cont = _boxes_overlap(cand["bbox"], prev["bbox"])

                            if same_vid and time_gap <= 3.0 and spatial_cont:
                                curr_group.append(cand)
                            else:
                                occurrences.append(curr_group)
                                curr_group = [cand]

                    if curr_group:
                        occurrences.append(curr_group)

                    # 4. Select Peak Keyframe per Occurrence & Package Result Cards
                    occurrence_results = []
                    for occ in occurrences:
                        peak_cand = max(occ, key=lambda c: c["score"])
                        start_ts = min(c["timestamp"] for c in occ)
                        end_ts = max(c["timestamp"] for c in occ)
                        total_frames = len(occ)

                        peak_cand["occurrenceStart"] = start_ts
                        peak_cand["occurrenceEnd"] = end_ts
                        peak_cand["occurrenceFrames"] = total_frames
                        occurrence_results.append(peak_cand)

                    # Rank occurrences primarily by peak score (descending), then start time (ascending)
                    occurrence_results.sort(key=lambda c: (-c["score"], c["occurrenceStart"]))

                    from app.services.clip_generator import ClipGeneratorService

                    for rank_pos, cand in enumerate(occurrence_results[:top_k], start=1):
                        vid = cand["videoId"]
                        fn = cand["frameNumber"]
                        ts = cand["timestamp"]
                        sc = cand["score"]
                        rec_data = cand["rec_data"]
                        tier_name = cand["matchTierName"]
                        ocr_txt = cand["matchedText"]
                        start_ts = cand["occurrenceStart"]
                        end_ts = cand["occurrenceEnd"]

                        ann_url = _get_ocr_annotated_url(vid, fn, rec_data, t_text=q_raw, t_box=cand["bbox"])

                        clip_start = max(0.0, ts - 1.5)
                        clip_end = ts + 1.5
                        c_url, c_start, c_end, c_dur = ClipGeneratorService.generate_result_clip(
                            video_id=vid,
                            match_timestamp=ts,
                            identifier_tag=f"ocr{fn}",
                            start_override=clip_start,
                            end_override=clip_end,
                            precise_mode=True
                        )

                        occ_str = f"Occurrence Range: {start_ts:.1f}s → {end_ts:.1f}s ({cand['occurrenceFrames']} frames)" if end_ts > start_ts else f"Occurrence Frame: #{fn} ({ts:.1f}s)"

                        try:
                            ocr_frame_results.append(FrameSearchResult(
                                videoId=vid,
                                frameNumber=fn,
                                timestamp=ts,
                                thumbnail=ann_url,
                                annotatedFrame=ann_url,
                                faissId=0,
                                similarityScore=sc,
                                similarityPercentage=f"{round(sc * 100.0, 2)}%",
                                indexOrigin="PaddleOCR/MongoDB",
                                finalScore=sc,
                                finalScorePercentage=f"{round(sc * 100.0, 2)}%",
                                rankingPosition=rank_pos,
                                confidenceBadge=tier_name,
                                explanation=f"PaddleOCR [{tier_name}] matched \"{ocr_txt}\" at frame {fn} (Conf: {round(cand['confidence']*100, 1)}%, Score: {sc}). {occ_str}",
                                averageYOLOConfidence=0.0,
                                trackPersistence=0.0,
                                videoClipUrl=c_url,
                                clipStartTime=c_start,
                                clipEndTime=c_end,
                                clipDuration=c_dur,
                                evidenceType="ocr_detection"
                            ))
                        except Exception as ocr_err:
                            logger.warning(f"[SemanticSearch] OCR result build error: {ocr_err}")

            ocr_search_ms = round((time.time() - t_ocr_start) * 1000.0, 2)
            total_search_ms = round((time.time() - total_start) * 1000.0, 2)

            stats_ocr = SearchStatistics(
                queryEmbeddingTimeMs=0.0,
                frameSearchTimeMs=ocr_search_ms,
                objectSearchTimeMs=0.0,
                totalSearchTimeMs=total_search_ms
            )
            analytics_dict_ocr = SearchAnalyticsBuilder.build_analytics(
                candidates_retrieved=ocr_candidates_retrieved,
                results_rejected_by_threshold=0,
                accepted_results=len(ocr_frame_results),
                grouped_tracks=0,
                final_returned_results=len(ocr_frame_results),
                similarity_threshold=threshold,
                filtering_time_ms=0.0,
                grouping_time_ms=0.0,
                ranking_time_ms=0.0,
                weight_semantic=1.0,
                weight_yolo=0.0,
                weight_persistence=0.0,
                total_retrieval_time_ms=total_search_ms,
                route="OCR",
                target_phrase=target_phrase
            )
            logger.info(
                f"[SemanticSearch] OCR route complete. Query='{query_text}', "
                f"Target='{target_phrase}', Results={len(ocr_frame_results)}, Latency={total_search_ms}ms"
            )
            return SearchResponse(
                query=query_text,
                topK=top_k,
                similarityThreshold=threshold,
                frameResults=ocr_frame_results,
                objectResults=[],
                statistics=stats_ocr,
                analytics=SearchAnalytics(**analytics_dict_ocr),
                route="OCR",
                targetPhrase=target_phrase
            )

        # 1. Text Embedding Generation for visual/semantic routes
        query_vec, query_embed_ms = QueryEmbedder.embed_query(query_text)

        # 1.5 Parse Query Attributes Upfront to Determine Search Strategy
        parsed_query_attrs = AttributeFilter.parse_query(query_text)
        is_explicit_native_object = parsed_query_attrs.get("explicitNativeObjectQuery", False)
        target_native_class = parsed_query_attrs.get("requiredObjectClass")

        req_upper_color = parsed_query_attrs.get("upperClothingColor")
        req_lower_color = parsed_query_attrs.get("lowerClothingColor")
        req_vehicle_color = parsed_query_attrs.get("vehicleColor")
        req_hat = parsed_query_attrs.get("hasHat")
        req_backpack = parsed_query_attrs.get("hasBackpack")
        req_helmet = parsed_query_attrs.get("hasHelmet")
        req_glasses = parsed_query_attrs.get("hasGlasses")
        req_obj_class = parsed_query_attrs.get("requiredObjectClass")

        has_attr_filter = any(v is not None for v in [
            req_upper_color, req_lower_color, req_vehicle_color,
            req_hat, req_backpack, req_helmet, req_glasses, req_obj_class
        ])

        total_obj_vectors = getattr(faiss_manager.object_index, "ntotal", 0) if hasattr(faiss_manager, "object_index") and faiss_manager.object_index else 0

        v2_route_info = QueryRouter.classify(query_text) if getattr(settings, "ENABLE_ATTRIBUTE_V2", False) else {}
        v2_route = v2_route_info.get("route", "GENERIC_SEMANTIC")

        # === PHASE 3.19 DEDICATED ATTRIBUTE V2 ROUTING (Feature-Flagged) ===
        if getattr(settings, "ENABLE_ATTRIBUTE_V2", False) and v2_route in ("CLOTHING_COLOR", "HUMAN_ATTRIBUTE", "BAG_RELATION"):
            logger.info(f"[SemanticSearch] ATTRIBUTE_V2 Route active for '{query_text}': route={v2_route}")

            # PART 2 FIX: FAISS Object Search timer measures ONLY actual FAISS search operation
            t_faiss_start = time.time()
            raw_object_hits = faiss_manager.search_object_index(query_vec, top_k=min(100, max(top_k * 5, total_obj_vectors))) if total_obj_vectors > 0 else []
            object_search_ms = round((time.time() - t_faiss_start) * 1000.0, 2)
            frame_search_ms = 0.0

            t_v2_start = time.time()
            v2_object_dicts = cls._run_attribute_v2_search(
                query_text=query_text,
                route_info=v2_route_info,
                video_id_filter=None,
                top_k=top_k,
                db=db,
                raw_object_hits=raw_object_hits
            )
            attr_eval_ms = round((time.time() - t_v2_start) * 1000.0, 2)
            raw_frame_hits = []
            accepted_frame_hits = []
            frame_rejected = 0
            f_filter_ms = 0.0
            accepted_object_hits = [(item["_v2_faiss_sentinel"], item["similarityScore"]) for item in v2_object_dicts]
            object_rejected = 0
            o_filter_ms = attr_eval_ms
            candidates_retrieved = len(v2_object_dicts)
            results_rejected = 0

            # Build clip URLs and return early as a SearchResponse
            from app.services.clip_generator import ClipGeneratorService
            total_search_ms = round((time.time() - total_start) * 1000.0, 2)

            object_results_v2: List[ObjectSearchResult] = []
            for rank_pos, item in enumerate(v2_object_dicts[:top_k], start=1):
                v_id = item.get("videoId", "")
                t_id = item.get("trackId", 0)
                ts = float(item.get("timestamp", 0.0))
                c_url, c_start, c_end, c_dur = ClipGeneratorService.generate_result_clip(
                    video_id=v_id, match_timestamp=ts, identifier_tag=f"v2track{t_id}"
                )
                sc = item.get("similarityScore", 0.0)
                try:
                    object_results_v2.append(ObjectSearchResult(
                        videoId=v_id,
                        trackId=int(t_id),
                        objectClass="person",
                        frameNumber=int(item.get("frameNumber", 1)),
                        timestamp=ts,
                        cropThumbnail=item.get("cropThumbnail", ""),
                        annotatedFrame=item.get("annotatedFrame", ""),
                        faissId=0,
                        similarityScore=sc,
                        similarityPercentage=f"{round(sc * 100.0, 2)}%",
                        appearanceCount=int(item.get("appearanceCount", 1)),
                        firstSeen=float(item.get("firstSeen", ts)),
                        lastSeen=float(item.get("lastSeen", ts)),
                        trackDurationSec=float(item.get("trackDurationSec", 0.0)),
                        indexOrigin=f"AttributeV2/{v2_route}",
                        finalScore=sc,
                        finalScorePercentage=f"{round(sc * 100.0, 2)}%",
                        rankingPosition=rank_pos,
                        confidenceBadge="Strong Match" if sc >= 0.70 else "Good Match" if sc >= 0.50 else "Possible Match",
                        explanation=f"Phase 3.19 Dedicated Attribute Engine: {v2_route} route (score={sc:.4f})",
                        averageYOLOConfidence=float(item.get("averageYOLOConfidence", 0.85)),
                        trackPersistence=float(item.get("trackPersistence", 0.50)),
                        bestSimilarityScore=sc,
                        bestSimilarityPercentage=f"{round(sc * 100.0, 2)}%",
                        videoClipUrl=c_url,
                        clipStartTime=c_start,
                        clipEndTime=c_end,
                        clipDuration=c_dur,
                    ))
                except Exception as v2_item_err:
                    logger.warning(f"[SemanticSearch] ATTRIBUTE_V2 result build error for track {t_id}: {v2_item_err}")

            stats_v2 = SearchStatistics(
                queryEmbeddingTimeMs=query_embed_ms,
                frameSearchTimeMs=0.0,
                objectSearchTimeMs=object_search_ms,
                totalSearchTimeMs=total_search_ms
            )
            analytics_dict_v2 = SearchAnalyticsBuilder.build_analytics(
                candidates_retrieved=candidates_retrieved,
                results_rejected_by_threshold=0,
                accepted_results=len(object_results_v2),
                grouped_tracks=0,
                final_returned_results=len(object_results_v2),
                similarity_threshold=threshold,
                filtering_time_ms=0.0,
                grouping_time_ms=0.0,
                ranking_time_ms=0.0,
                weight_semantic=1.0,
                weight_yolo=0.0,
                weight_persistence=0.0,
                total_retrieval_time_ms=total_search_ms
            )
            logger.info(
                f"[SemanticSearch] ATTRIBUTE_V2 complete. Query='{query_text}', "
                f"route={v2_route}, results={len(object_results_v2)}, total_ms={total_search_ms}"
            )
            return SearchResponse(
                query=query_text,
                topK=top_k,
                similarityThreshold=threshold,
                frameResults=[],
                objectResults=object_results_v2,
                matchingMethod=f"Attribute Engine V2 ({v2_route})",
                statistics=stats_v2,
                analytics=SearchAnalytics(**analytics_dict_v2),
                route=v2_route
            )

        # === STRICT NATIVE OBJECT ROUTING ===
        elif is_explicit_native_object and target_native_class:
            logger.info(f"[SemanticSearch] Strict Native Object Route for '{query_text}': Target Class '{target_native_class}'")
            t_obj_start = time.time()
            obj_candidate_k = min(150, max(top_k * 5, total_obj_vectors)) if total_obj_vectors > 0 else top_k
            raw_object_hits = faiss_manager.search_object_index(query_vec, top_k=obj_candidate_k)
            object_search_ms = round((time.time() - t_obj_start) * 1000.0, 2)
            frame_search_ms = 0.0
            raw_frame_hits = []

            accepted_frame_hits = []
            frame_rejected = 0
            f_filter_ms = 0.0

            gated_object_hits = []
            for fid, sim in raw_object_hits:
                cand_cls = cls._lookup_object_class(fid, db)
                if cand_cls == target_native_class:
                    gated_object_hits.append((fid, sim))

            accepted_object_hits = gated_object_hits
            object_rejected = len(raw_object_hits) - len(accepted_object_hits)
            o_filter_ms = 0.0

            candidates_retrieved = len(raw_object_hits)
            results_rejected = object_rejected

        else:
            # Standard Dual FAISS Search for context, scene, attribute, or relational queries
            obj_candidate_k = min(150, max(top_k, total_obj_vectors)) if (has_attr_filter and total_obj_vectors > 0) else top_k

            t_frame_start = time.time()
            raw_frame_hits = faiss_manager.search_frame_index(query_vec, top_k=top_k)
            frame_search_ms = round((time.time() - t_frame_start) * 1000.0, 2)

            t_obj_start = time.time()
            raw_object_hits = faiss_manager.search_object_index(query_vec, top_k=obj_candidate_k)
            object_search_ms = round((time.time() - t_obj_start) * 1000.0, 2)

            candidates_retrieved = len(raw_frame_hits) + len(raw_object_hits)

            accepted_frame_hits, frame_rejected, f_filter_ms = ResultFilter.filter_by_threshold(raw_frame_hits, threshold)

            if not has_attr_filter:
                accepted_object_hits, object_rejected, o_filter_ms = ResultFilter.filter_by_threshold(raw_object_hits, threshold)
            else:
                t0_attr_aug = time.time()
                accepted_object_hits = list(raw_object_hits)

                matched_metadata = cls._get_metadata_matched_tracks(parsed_query_attrs, db)

                existing_track_ids = set()
                for fid, sim in raw_object_hits:
                    try:
                        existing_track_ids.add(int(fid))
                        existing_track_ids.add(str(fid))
                    except Exception:
                        existing_track_ids.add(str(fid))

                for m_item in matched_metadata:
                    tid = m_item.get("trackId")
                    if tid is not None:
                        already_exists = (tid in existing_track_ids) or (str(tid) in existing_track_ids)
                        try:
                            if int(tid) in existing_track_ids:
                                already_exists = True
                        except Exception:
                            pass

                        if not already_exists:
                            raw_sim = 0.18
                            int_tid = None
                            try:
                                int_tid = int(tid)
                            except Exception:
                                pass

                            if hasattr(faiss_manager.object_index, "reconstruct") and int_tid is not None and int_tid < total_obj_vectors:
                                try:
                                    vec = faiss_manager.object_index.reconstruct(int_tid)
                                    raw_sim = float(np.dot(query_vec, vec))
                                except Exception:
                                    pass

                            accepted_object_hits.append((str(tid), round(raw_sim, 4)))
                            existing_track_ids.add(tid)
                            existing_track_ids.add(str(tid))
                            if int_tid is not None:
                                existing_track_ids.add(int_tid)

                object_rejected = max(0, len(raw_object_hits) - len(accepted_object_hits))
                o_filter_ms = round((time.time() - t0_attr_aug) * 1000.0, 2)

            results_rejected = frame_rejected + object_rejected
        accepted_results = len(accepted_frame_hits) + len(accepted_object_hits)
        total_filter_ms = round(f_filter_ms + o_filter_ms, 3)

        # 4. Enrich Accepted Frame Hits with Metadata & Signal Extraction
        frame_raw_dicts: List[Dict[str, Any]] = []
        if accepted_frame_hits:
            default_vid = cls._get_default_existing_video_id()

            for faiss_id, sim in accepted_frame_hits:
                meta = None
                if db is not None:
                    try:
                        meta = db.embeddings.find_one({"faissId": faiss_id, "type": "frame"}, {"_id": 0})
                        if not meta:
                            meta = db.frames.find_one({"faissId": faiss_id}, {"_id": 0})
                    except Exception:
                        pass

                video_id = meta.get("videoId") if meta else default_vid
                frame_num = int(meta.get("frameNumber", int(faiss_id) + 1)) if meta else int(faiss_id) + 1
                ts = float(meta.get("timestamp", float(frame_num))) if meta else float(frame_num)

                annotated_url = f"/static/storage/debug/{video_id}/frames/frame_{frame_num:04d}.jpg"
                raw_frame_url = f"/static/storage/frames/{video_id}/frame_{frame_num:04d}.jpg"

                # Use annotated frame if file exists on disk, else fallback to raw frame
                annotated_file = settings.DEBUG_DIR / video_id / "frames" / f"frame_{frame_num:04d}.jpg"
                thumb_url = annotated_url if annotated_file.exists() else raw_frame_url

                sim_score = round(float(sim), 4)
                sim_pct = f"{round(float(sim) * 100.0, 2)}%"

                # Extract YOLO confidence signal for frame
                yolo_conf = 0.0
                scene_doc = None
                if db is not None:
                    try:
                        frame_dets = list(db.detections.find({"videoId": video_id, "frameNumber": frame_num}, {"_id": 0}))
                        yolo_conf = (
                            round(max([float(d.get("confidence", 0.0)) for d in frame_dets]), 4)
                            if frame_dets else 0.0
                        )
                        scene_doc = db.scenes.find_one({"videoId": video_id, "frameNumber": frame_num}, {"_id": 0})
                    except Exception:
                        pass

                frame_raw_dicts.append({
                    "videoId": video_id,
                    "frameNumber": frame_num,
                    "timestamp": ts,
                    "thumbnail": thumb_url,
                    "annotatedFrame": annotated_url,
                    "faissId": faiss_id,
                    "similarityScore": sim_score,
                    "similarityPercentage": sim_pct,
                    "averageYOLOConfidence": yolo_conf,
                    "trackPersistence": 0.50,  # neutral frame persistence baseline
                    "indexOrigin": "Frame FAISS Index",
                    "sceneContext": scene_doc
                })

        # 4.5. Enforce Scene Context Filtering on Frame Results if query explicitly contains scene criteria
        parsed_query_attrs = AttributeFilter.parse_query(query_text)
        req_env = parsed_query_attrs.get("environment")
        req_loc = parsed_query_attrs.get("locationType")

        scene_rejected_count = 0
        if (req_env or req_loc) and frame_raw_dicts:
            filtered_frames = []
            for f_item in frame_raw_dicts:
                scene_ctx = f_item.get("sceneContext") or {}
                actual_env = scene_ctx.get("environment")
                actual_loc = scene_ctx.get("locationType")

                match = True
                if req_env and actual_env and str(actual_env).lower() != str(req_env).lower():
                    match = False
                if req_loc and actual_loc and str(actual_loc).lower() != str(req_loc).lower():
                    match = False

                if match:
                    filtered_frames.append(f_item)
                else:
                    scene_rejected_count += 1

        results_rejected = results_rejected + scene_rejected_count

        # 4.5.5. Enforce OCR Text Match Filtering if query contains text search intent (e.g. "Student service", "CHICANO")
        ocr_query = parsed_query_attrs.get("ocrTextQuery")
        if ocr_query and db is not None:
            q_lower = ocr_query.lower().strip()
            # Search OCR records collection in MongoDB
            ocr_records = list(db.ocr.find({
                "$or": [
                    {"extractedText": {"$regex": q_lower, "$options": "i"}},
                    {"tokens": {"$elemMatch": {"$regex": q_lower, "$options": "i"}}}
                ]
            }, {"_id": 0}))

            if ocr_records:
                ocr_frame_map = {}
                for rec in ocr_records:
                    vid = rec.get("videoId")
                    fn = rec.get("frameNumber")
                    ocr_txt = rec.get("extractedText", "")
                    ocr_frame_map[(vid, fn)] = (ocr_txt, rec)

                def _get_ocr_annotated_url(vid: str, fn: int, rec_data: dict) -> str:
                    ocr_dir = settings.STORAGE_DIR / "debug" / vid / "ocr"
                    ocr_file = ocr_dir / f"ocr_frame_{fn:04d}.jpg"
                    if ocr_file.exists():
                        return f"/static/storage/debug/{vid}/ocr/ocr_frame_{fn:04d}.jpg"
                    
                    # Generate lazily using OcrAnnotator if source frame exists
                    src_frame = settings.STORAGE_DIR / "debug" / vid / "frames" / f"frame_{fn:04d}.jpg"
                    if not src_frame.exists():
                        src_frame = settings.FRAMES_DIR / vid / f"frame_{fn:04d}.jpg"
                    
                    dets = rec_data.get("detections", [])
                    if src_frame.exists() and dets:
                        url = OcrAnnotator.annotate_frame(
                            image_input=src_frame,
                            video_id=vid,
                            frame_number=fn,
                            detections=dets
                        )
                        if url:
                            return url
                    return f"/static/storage/debug/{vid}/ocr/ocr_frame_{fn:04d}.jpg"

                filtered_ocr_frames = []
                existing_keys = set()

                if frame_raw_dicts:
                    for f_item in frame_raw_dicts:
                        key = (f_item.get("videoId"), f_item.get("frameNumber"))
                        if key in ocr_frame_map:
                            ocr_txt, rec_data = ocr_frame_map[key]
                            f_item["similarityScore"] = max(f_item.get("similarityScore", 0.0), 0.95)
                            f_item["similarityPercentage"] = f"{round(f_item['similarityScore'] * 100.0, 2)}%"
                            f_item["ocrMatchText"] = ocr_txt
                            f_item["annotatedFrame"] = _get_ocr_annotated_url(key[0], key[1], rec_data)
                            filtered_ocr_frames.append(f_item)
                            existing_keys.add(key)

                # Pull matching OCR frames directly if top-k vector search missed them
                for (vid, fn), (ocr_txt, rec_data) in ocr_frame_map.items():
                    if (vid, fn) not in existing_keys:
                        f_doc = db.frames.find_one({"videoId": vid, "frameNumber": fn}, {"_id": 0})
                        if f_doc:
                            ts = f_doc.get("timestamp", 0.0)
                            ann_url = _get_ocr_annotated_url(vid, fn, rec_data)
                            filtered_ocr_frames.append({
                                "videoId": vid,
                                "frameNumber": fn,
                                "timestamp": ts,
                                "annotatedFrame": ann_url,
                                "similarityScore": 0.92,
                                "similarityPercentage": "92.0%",
                                "ocrMatchText": ocr_txt,
                                "indexOrigin": "OCR Text Match"
                            })

                if filtered_ocr_frames:
                    frame_raw_dicts = filtered_ocr_frames
                    logger.info(f"[SemanticSearch] OCR Text Search for '{ocr_query}': Matched {len(frame_raw_dicts)} frames.")




        # 4.6. Enforce Frame-Level Relational Filtering if query contains relational intent
        rel_info = parsed_query_attrs.get("relationInfo")
        rel_rejected_count = 0

        if rel_info and db is not None and frame_raw_dicts:
            p_obj = str(rel_info.get("primaryObject", "")).lower()
            rel = str(rel_info.get("relation", "")).lower()
            s_obj = str(rel_info.get("secondaryObject", "")).lower()

            rel_before = len(frame_raw_dicts)
            filtered_rel_frames = []

            for f_item in frame_raw_dicts:
                vid = f_item.get("videoId")
                fn = f_item.get("frameNumber")

                frame_dets = list(db.detections.find({"videoId": vid, "frameNumber": fn}, {"_id": 0}))
                p_dets = [d for d in frame_dets if str(d.get("objectClass", "")).lower() == p_obj]
                s_dets = [d for d in frame_dets if str(d.get("objectClass", "")).lower() == s_obj]

                match = False
                if p_dets and s_dets:
                    if rel == "with" or rel == "before" or rel == "after":
                        match = True
                    elif rel == "near" or rel == "riding":
                        min_dist_norm = 999.0
                        has_overlap = False

                        for pd in p_dets:
                            p_box = pd.get("boundingBox", [0, 0, 0, 0])
                            p_cx = (p_box[0] + p_box[2]) / 2.0
                            p_cy = (p_box[1] + p_box[3]) / 2.0

                            for sd in s_dets:
                                s_box = sd.get("boundingBox", [0, 0, 0, 0])
                                s_cx = (s_box[0] + s_box[2]) / 2.0
                                s_cy = (s_box[1] + s_box[3]) / 2.0

                                # Check bounding box overlap
                                ix1 = max(p_box[0], s_box[0])
                                iy1 = max(p_box[1], s_box[1])
                                ix2 = min(p_box[2], s_box[2])
                                iy2 = min(p_box[3], s_box[3])
                                if ix2 > ix1 and iy2 > iy1:
                                    has_overlap = True

                                # Distance calculation
                                is_norm = max(p_box[2], s_box[2]) <= 1.5
                                if is_norm:
                                    diag = math.sqrt(2.0)
                                else:
                                    w_max = max(p_box[2], s_box[2], 1920)
                                    h_max = max(p_box[3], s_box[3], 1080)
                                    diag = math.sqrt(w_max**2 + h_max**2)

                                dist = math.sqrt((p_cx - s_cx)**2 + (p_cy - s_cy)**2)
                                norm_dist = dist / diag if diag > 0 else 0.0
                                if norm_dist < min_dist_norm:
                                    min_dist_norm = norm_dist

                        if rel == "near":
                            if min_dist_norm <= 0.25:
                                match = True
                        elif rel == "riding":
                            if has_overlap or min_dist_norm <= 0.30:
                                match = True

                if match:
                    filtered_rel_frames.append(f_item)
                else:
                    rel_rejected_count += 1

            frame_raw_dicts = filtered_rel_frames
            rel_kept = len(frame_raw_dicts)
            results_rejected = results_rejected + rel_rejected_count

            logger.info(
                f"[SemanticSearch] Relational frame filter for '{query_text}': "
                f"Relation='{rel}' ({p_obj} -> {s_obj}), Before={rel_before}, Kept={rel_kept}, Rejected={rel_rejected_count}"
            )

        # 5. Enrich Accepted Object Hits with Metadata & Signal Extraction
        raw_object_records: List[Dict[str, Any]] = []
        if accepted_object_hits:
            default_vid = cls._get_default_existing_video_id()

            for faiss_id, sim in accepted_object_hits:
                meta = None
                if db is not None:
                    try:
                        meta = db.embeddings.find_one({"faissId": faiss_id, "type": "object"}, {"_id": 0})
                        if not meta:
                            meta = db.detections.find_one({"faissId": faiss_id}, {"_id": 0})
                    except Exception:
                        pass

                video_id = meta.get("videoId") if meta else default_vid
                track_id = None
                a_doc = None
                fa_doc = None

                if meta and meta.get("trackId") is not None:
                    try:
                        track_id = int(meta.get("trackId"))
                    except Exception:
                        track_id = meta.get("trackId")

                if track_id is None:
                    try:
                        possible_tid = int(faiss_id)
                        if db is not None:
                            a_doc = db.attributes.find_one({"trackId": possible_tid}, {"_id": 0})
                            if not a_doc:
                                a_doc = db.attributes.find_one({"trackId": str(possible_tid)}, {"_id": 0})
                            if a_doc:
                                track_id = possible_tid
                                if a_doc.get("videoId"):
                                    video_id = a_doc.get("videoId")
                        if track_id is None and (possible_tid in file_attr_map or str(possible_tid) in file_attr_map):
                            track_id = possible_tid
                            fa_doc = file_attr_map.get(possible_tid) or file_attr_map.get(str(possible_tid))
                            if fa_doc and fa_doc.get("videoId"):
                                video_id = fa_doc.get("videoId")
                    except Exception:
                        pass

                if track_id is None:
                    try:
                        track_id = int(faiss_id)
                    except Exception:
                        track_id = 1

                ts_val = None
                if meta:
                    obj_cls = str(meta.get("objectClass", "person"))
                    frame_num = int(meta.get("frameNumber", 1))
                    ts_val = meta.get("timestamp")
                    crop_url = meta.get("cropUrl") or f"/static/storage/debug/{video_id}/tracks/{track_id}/frame_{frame_num:04d}.jpg"
                elif a_doc or fa_doc:
                    attr_info = a_doc or fa_doc
                    obj_cls = str(attr_info.get("objectClass", "person"))
                    frame_num = int(attr_info.get("supportingFrame", 1))
                    ts_val = attr_info.get("timestamp")
                    crop_url = attr_info.get("cropUrl") or f"/static/storage/debug/{video_id}/tracks/{track_id}/frame_{frame_num:04d}.jpg"
                else:
                    obj_cls = "person"
                    try:
                        frame_num = int(faiss_id) + 1
                    except Exception:
                        frame_num = 1
                    ts_val = None
                    crop_url = f"/static/storage/debug/{video_id}/tracks/{track_id}/frame_{frame_num:04d}.jpg"

                if ts_val is not None:
                    ts = float(ts_val)
                elif db is not None:
                    f_doc = None
                    try:
                        f_doc = db.frames.find_one({"videoId": video_id, "frameNumber": frame_num}, {"_id": 0, "timestamp": 1})
                    except Exception:
                        pass
                    ts = float(f_doc.get("timestamp")) if (f_doc and f_doc.get("timestamp") is not None) else float(frame_num)
                else:
                    ts = float(frame_num)

                annotated_url = f"/static/storage/debug/{video_id}/frames/frame_{frame_num:04d}.jpg"
                sim_score = round(float(sim), 4)
                sim_pct = f"{round(float(sim) * 100.0, 2)}%"

                raw_object_records.append({
                    "videoId": video_id,
                    "trackId": track_id,
                    "objectClass": obj_cls,
                    "frameNumber": frame_num,
                    "timestamp": ts,
                    "cropThumbnail": crop_url,
                    "annotatedFrame": annotated_url,
                    "faissId": faiss_id,
                    "similarityScore": sim_score,
                    "similarityPercentage": sim_pct,
                    "indexOrigin": "Object FAISS Index"
                })

        # 6. Duplicate Track Grouping & Representative Thumbnail Selection
        consolidated_track_dicts, grouped_track_count, grouping_time_ms = TrackGrouper.group_object_results(raw_object_records)

        # 7. Extract Signals for Object Trajectories (Average YOLO Conf, Persistence & Visual Attributes)
        attr_file = settings.BASE_DIR / "storage" / "metadata" / "attributes.json"
        if not attr_file.exists():
            attr_file = settings.BASE_DIR / "backend" / "storage" / "metadata" / "attributes.json"

        file_attr_map = {}
        if attr_file.exists():
            try:
                import json
                with open(attr_file, "r", encoding="utf-8") as f:
                    file_attrs = json.load(f)
                    for item in file_attrs:
                        file_attr_map[item["trackId"]] = item
                        file_attr_map[str(item["trackId"])] = item
                        try:
                            file_attr_map[int(item["trackId"])] = item
                        except Exception:
                            pass
            except Exception:
                pass

        video_durations = {}
        for item in consolidated_track_dicts:
            vid = item.get("videoId")
            tid = item.get("trackId")
            dur = float(item.get("trackDurationSec", 0.0))

            avg_conf = 0.85
            persistence = 0.50
            attr_doc = None

            if db is not None:
                try:
                    if vid not in video_durations:
                        v_doc = db.videos.find_one({"videoId": vid}, {"_id": 0})
                        v_dur = float(v_doc.get("duration", 0.0)) if v_doc else 0.0
                        video_durations[vid] = v_dur

                    v_dur = video_durations.get(vid, 0.0)
                    persistence = round(min(1.0, max(0.0, dur / max(1.0, v_dur))), 4) if v_dur > 0 else 0.50

                    t_dets = list(db.detections.find({"videoId": vid, "trackId": tid}, {"_id": 0}))
                    if not t_dets:
                        t_dets = list(db.detections.find({"videoId": vid, "trackId": str(tid)}, {"_id": 0}))

                    confs = [float(d.get("confidence", 0.0)) for d in t_dets]
                    avg_conf = round(sum(confs) / len(confs), 4) if confs else 0.85

                    attr_doc = db.attributes.find_one({"videoId": vid, "trackId": tid}, {"_id": 0})
                    if not attr_doc:
                        try:
                            attr_doc = db.attributes.find_one({"videoId": vid, "trackId": int(tid)}, {"_id": 0})
                        except Exception:
                            pass
                except Exception:
                    pass

            if not attr_doc and tid in file_attr_map:
                attr_doc = file_attr_map[tid]

            item["averageYOLOConfidence"] = avg_conf
            item["trackPersistence"] = persistence
            item["visualAttributes"] = attr_doc
            if attr_doc and attr_doc.get("objectClass"):
                item["objectClass"] = attr_doc["objectClass"]

        # 7.5. Enforce Object Visual Attribute & Accessory Filtering
        req_upper_color = parsed_query_attrs.get("upperClothingColor")
        req_lower_color = parsed_query_attrs.get("lowerClothingColor")
        req_vehicle_color = parsed_query_attrs.get("vehicleColor")
        req_hat = parsed_query_attrs.get("hasHat")
        req_backpack = parsed_query_attrs.get("hasBackpack")
        req_helmet = parsed_query_attrs.get("hasHelmet")
        req_glasses = parsed_query_attrs.get("hasGlasses")
        req_obj_class = parsed_query_attrs.get("requiredObjectClass")

        has_attr_filter = any(v is not None for v in [
            req_upper_color, req_lower_color, req_vehicle_color,
            req_hat, req_backpack, req_helmet, req_glasses, req_obj_class
        ])

        if has_attr_filter and consolidated_track_dicts:
            candidates_before = len(consolidated_track_dicts)
            filtered_tracks = []
            for item in consolidated_track_dicts:
                v_attrs = item.get("visualAttributes") or {}
                cand_cls = str(item.get("objectClass", "")).lower()
                match = True

                # 1. Object Class Constraint Check
                if req_obj_class:
                    req_cls_norm = str(req_obj_class).lower()
                    if req_cls_norm == "person" and cand_cls != "person":
                        match = False
                    elif req_cls_norm in {"car", "vehicle"} and cand_cls not in {"car", "bus", "truck", "motorcycle", "vehicle"}:
                        match = False

                # 2. Lower Clothing Color Constraint Check
                if req_lower_color and match:
                    act_lower = v_attrs.get("lowerClothingColor")
                    if not act_lower or str(act_lower).lower() != str(req_lower_color).lower():
                        match = False

                # 3. Upper Clothing Color Constraint Check
                if req_upper_color and match:
                    act_upper = v_attrs.get("upperClothingColor")
                    if not act_upper or str(act_upper).lower() != str(req_upper_color).lower():
                        match = False

                # 4. Vehicle Color Constraint Check
                if req_vehicle_color and match:
                    act_v = v_attrs.get("vehicleColor")
                    if not act_v or str(act_v).lower() != str(req_vehicle_color).lower():
                        match = False

                # 5. Accessory Constraints Check
                if req_backpack is not None and match:
                    act_bp = v_attrs.get("hasBackpack")
                    if act_bp is False:
                        match = False

                if req_glasses is not None and match:
                    act_gl = v_attrs.get("hasGlasses")
                    if act_gl is False:
                        match = False

                if req_hat is not None and match:
                    act_ht = v_attrs.get("hasHat")
                    if act_ht is False:
                        match = False

                if req_helmet is not None and match:
                    act_hm = v_attrs.get("hasHelmet")
                    if act_hm is False:
                        match = False

                if match:
                    # Raw similarity score is PRESERVED UNCHANGED (no artificial boost)
                    filtered_tracks.append(item)

            candidates_kept = len(filtered_tracks)
            candidates_rejected = candidates_before - candidates_kept
            consolidated_track_dicts = filtered_tracks
            results_rejected = results_rejected + candidates_rejected

            logger.info(
                f"[SemanticSearch] Visual Attribute filter for '{query_text}': "
                f"Before={candidates_before}, Kept={candidates_kept}, Rejected={candidates_rejected}"
            )

        # 7.55. Phase 2.4 SigLIP2 Fine-Grained Candidate Evaluation (Stage A / Stage B Diagnostics)
        if has_attr_filter and consolidated_track_dicts:
            t0_attr_v = time.perf_counter()
            try:
                from app.search.attribute_reranker import attribute_reranker
                consolidated_track_dicts, siglip_metrics = attribute_reranker.rerank_attribute_candidates(
                    query_text,
                    consolidated_track_dicts
                )
            except Exception as siglip_err:
                logger.error(f"[SemanticSearch] SigLIP2 candidate evaluation error: {str(siglip_err)}", exc_info=True)
            attribute_verification_ms = round((time.perf_counter() - t0_attr_v) * 1000.0, 3)



        # 7.6. Enforce Relational Filtering for Object Results ("before", "after", "near", "riding", "with")
        if rel_info and db is not None and consolidated_track_dicts:
            rel = str(rel_info.get("relation", "")).lower()
            p_obj = str(rel_info.get("primaryObject", "")).lower()
            s_obj = str(rel_info.get("secondaryObject", "")).lower()

            if rel in {"before", "after"}:
                t_before = len(consolidated_track_dicts)
                filtered_temp_tracks = []

                for item in consolidated_track_dicts:
                    vid = item.get("videoId")
                    p_start = float(item.get("firstSeen", 0.0))

                    s_tracks = list(db.tracks.find({"videoId": vid, "objectClass": s_obj}, {"_id": 0}))
                    if not s_tracks:
                        s_tracks = [st for st in db.tracks.find({"videoId": vid}, {"_id": 0}) if str(st.get("objectClass", "")).lower() == s_obj]

                    match = False
                    if s_tracks:
                        s_start = min([float(st.get("startTime", 0.0)) for st in s_tracks])
                        if rel == "before" and p_start < s_start:
                            match = True
                        elif rel == "after" and p_start > s_start:
                            match = True

                    if match:
                        filtered_temp_tracks.append(item)

                t_kept = len(filtered_temp_tracks)
                t_rejected = t_before - t_kept
                consolidated_track_dicts = filtered_temp_tracks
                results_rejected = results_rejected + t_rejected

                logger.info(
                    f"[SemanticSearch] Temporal relational object filter for '{query_text}': "
                    f"Relation='{rel}' ({p_obj} -> {s_obj}), Before={t_before}, Kept={t_kept}, Rejected={t_rejected}"
                )
            elif rel in {"near", "riding", "with"}:
                t_before = len(consolidated_track_dicts)
                filtered_rel_tracks = []

                for item in consolidated_track_dicts:
                    vid = item.get("videoId")
                    tid = item.get("trackId")

                    # Get tracked frame numbers for this candidate track
                    cand_dets = list(db.detections.find({"videoId": vid, "trackId": tid}, {"_id": 0, "frameNumber": 1}))
                    if not cand_dets:
                        cand_dets = list(db.detections.find({"videoId": vid, "trackId": str(tid)}, {"_id": 0, "frameNumber": 1}))

                    cand_fns = sorted(list(set(d.get("frameNumber") for d in cand_dets if d.get("frameNumber") is not None)))
                    if not cand_fns and item.get("frameNumber") is not None:
                        cand_fns = [item.get("frameNumber")]

                    track_match = False
                    for fn in cand_fns:
                        frame_dets = list(db.detections.find({"videoId": vid, "frameNumber": fn}, {"_id": 0}))
                        p_dets = [d for d in frame_dets if str(d.get("objectClass", "")).lower() == p_obj]
                        s_dets = [d for d in frame_dets if str(d.get("objectClass", "")).lower() == s_obj]

                        if p_dets and s_dets:
                            if rel == "with":
                                track_match = True
                                break
                            elif rel in {"near", "riding"}:
                                min_dist_norm = 999.0
                                has_overlap = False

                                for pd in p_dets:
                                    p_box = pd.get("boundingBox", [0, 0, 0, 0])
                                    p_cx = (p_box[0] + p_box[2]) / 2.0
                                    p_cy = (p_box[1] + p_box[3]) / 2.0

                                    for sd in s_dets:
                                        s_box = sd.get("boundingBox", [0, 0, 0, 0])
                                        s_cx = (s_box[0] + s_box[2]) / 2.0
                                        s_cy = (s_box[1] + s_box[3]) / 2.0

                                        # Check bounding box overlap
                                        ix1 = max(p_box[0], s_box[0])
                                        iy1 = max(p_box[1], s_box[1])
                                        ix2 = min(p_box[2], s_box[2])
                                        iy2 = min(p_box[3], s_box[3])
                                        if ix2 > ix1 and iy2 > iy1:
                                            has_overlap = True

                                        # Distance calculation
                                        is_norm = max(p_box[2], s_box[2]) <= 1.5
                                        if is_norm:
                                            diag = math.sqrt(2.0)
                                        else:
                                            w_max = max(p_box[2], s_box[2], 1920)
                                            h_max = max(p_box[3], s_box[3], 1080)
                                            diag = math.sqrt(w_max**2 + h_max**2)

                                        dist = math.sqrt((p_cx - s_cx)**2 + (p_cy - s_cy)**2)
                                        norm_dist = dist / diag if diag > 0 else 0.0
                                        if norm_dist < min_dist_norm:
                                            min_dist_norm = norm_dist

                                if rel == "near" and min_dist_norm <= 0.25:
                                    track_match = True
                                    break
                                elif rel == "riding" and (has_overlap or min_dist_norm <= 0.30):
                                    track_match = True
                                    break

                    if track_match:
                        filtered_rel_tracks.append(item)

                t_kept = len(filtered_rel_tracks)
                t_rejected = t_before - t_kept
                consolidated_track_dicts = filtered_rel_tracks
                results_rejected = results_rejected + t_rejected

                logger.info(
                    f"[SemanticSearch] Spatial relational object filter for '{query_text}': "
                    f"Relation='{rel}' ({p_obj} -> {s_obj}), Before={t_before}, Kept={t_kept}, Rejected={t_rejected}"
                )

        # 8. Phase 2.3 Independent Hybrid Ranking Engine Execution


        ranked_frame_dicts, ranked_object_dicts, ranking_time_ms = hybrid_ranking_engine.rank(
            frame_raw_dicts,
            consolidated_track_dicts
        )

        # 8.5. Generate Video Clips for Top Ranked Search Results
        t0_enrich = time.perf_counter()
        from app.services.clip_generator import ClipGeneratorService

        for item in ranked_frame_dicts:
            v_id = item.get("videoId")
            ts = float(item.get("timestamp", 0.0))
            f_num = item.get("frameNumber", 0)
            c_url, c_start, c_end, c_dur = ClipGeneratorService.generate_result_clip(
                video_id=v_id,
                match_timestamp=ts,
                identifier_tag=f"f{f_num}"
            )
            item["videoClipUrl"] = c_url
            item["clipStartTime"] = c_start
            item["clipEndTime"] = c_end
            item["clipDuration"] = c_dur

        for item in ranked_object_dicts:
            v_id = item.get("videoId")
            t_id = item.get("trackId")

            rep_ts = item.get("timestamp")
            if rep_ts is not None and float(rep_ts) > 0.0:
                ts = float(rep_ts)
            else:
                f_num = item.get("frameNumber")
                lookup_ts = None
                if f_num is not None and db is not None:
                    try:
                        f_doc = db.frames.find_one({"videoId": v_id, "frameNumber": f_num}, {"_id": 0, "timestamp": 1})
                        if f_doc and f_doc.get("timestamp") is not None:
                            lookup_ts = float(f_doc["timestamp"])
                    except Exception:
                        pass
                if lookup_ts is not None and lookup_ts > 0.0:
                    ts = lookup_ts
                else:
                    ts = float(item.get("firstSeen", 0.0))

            item["timestamp"] = ts

            c_url, c_start, c_end, c_dur = ClipGeneratorService.generate_result_clip(
                video_id=v_id,
                match_timestamp=ts,
                identifier_tag=f"track{t_id}"
            )
            item["videoClipUrl"] = c_url
            item["clipStartTime"] = c_start
            item["clipEndTime"] = c_end
            item["clipDuration"] = c_dur
        result_enrichment_ms = round((time.perf_counter() - t0_enrich) * 1000.0, 3)

        t0_serial = time.perf_counter()
        frame_results: List[FrameSearchResult] = [
            FrameSearchResult(**item) for item in ranked_frame_dicts
        ]
        object_results: List[ObjectSearchResult] = [
            ObjectSearchResult(**item) for item in ranked_object_dicts
        ]
        serialization_time_ms = round((time.perf_counter() - t0_serial) * 1000.0, 3)

        final_returned_results = len(frame_results) + len(object_results)
        total_search_ms = round((time.time() - total_start) * 1000.0, 2)

        stage_sum = (
            query_parsing_ms + model_init_ms + tokenizer_ms + query_embed_ms +
            gpu_sync_ms + frame_search_ms + object_search_ms + total_filter_ms +
            metadata_lookup_ms + grouping_time_ms + attribute_verification_ms +
            relational_verification_ms + result_enrichment_ms + ranking_time_ms +
            serialization_time_ms
        )
        unaccounted_ms = max(0.0, round(total_search_ms - stage_sum, 3))

        # 9. Compile Search Statistics & Analytics
        stats = SearchStatistics(
            queryParsingTimeMs=round(query_parsing_ms, 3),
            modelInitializationTimeMs=round(model_init_ms, 3),
            tokenizerTimeMs=round(tokenizer_ms, 3),
            queryEmbeddingTimeMs=round(query_embed_ms, 3),
            gpuSynchronizationTimeMs=round(gpu_sync_ms, 3),
            frameSearchTimeMs=round(frame_search_ms, 3),
            objectSearchTimeMs=round(object_search_ms, 3),
            thresholdFilteringTimeMs=round(total_filter_ms, 3),
            metadataLookupTimeMs=round(metadata_lookup_ms, 3),
            trackGroupingTimeMs=round(grouping_time_ms, 3),
            attributeVerificationTimeMs=round(attribute_verification_ms, 3),
            relationalVerificationTimeMs=round(relational_verification_ms, 3),
            resultEnrichmentTimeMs=round(result_enrichment_ms, 3),
            serializationTimeMs=round(serialization_time_ms, 3),
            otherUnaccountedTimeMs=unaccounted_ms,
            totalSearchTimeMs=total_search_ms
        )

        analytics_dict = SearchAnalyticsBuilder.build_analytics(
            candidates_retrieved=candidates_retrieved,
            results_rejected_by_threshold=results_rejected,
            accepted_results=accepted_results,
            grouped_tracks=grouped_track_count,
            final_returned_results=final_returned_results,
            similarity_threshold=threshold,
            filtering_time_ms=total_filter_ms,
            grouping_time_ms=grouping_time_ms,
            ranking_time_ms=ranking_time_ms,
            weight_semantic=hybrid_ranking_engine.w_semantic,
            weight_yolo=hybrid_ranking_engine.w_yolo,
            weight_persistence=hybrid_ranking_engine.w_persistence,
            total_retrieval_time_ms=total_search_ms,
            query_parsing_time_ms=query_parsing_ms,
            model_initialization_time_ms=model_init_ms,
            tokenizer_time_ms=tokenizer_ms,
            query_embedding_time_ms=query_embed_ms,
            gpu_synchronization_time_ms=gpu_sync_ms,
            frame_search_time_ms=frame_search_ms,
            object_search_time_ms=object_search_ms,
            threshold_filtering_time_ms=total_filter_ms,
            metadata_lookup_time_ms=metadata_lookup_ms,
            track_grouping_time_ms=grouping_time_ms,
            attribute_verification_time_ms=attribute_verification_ms,
            relational_verification_time_ms=relational_verification_ms,
            result_enrichment_time_ms=result_enrichment_ms,
            serialization_time_ms=serialization_time_ms,
            other_unaccounted_time_ms=unaccounted_ms
        )

        analytics = SearchAnalytics(**analytics_dict)

        logger.info(
            f"[SemanticSearch] Phase 2.3 Hybrid Ranking Complete. "
            f"Query: '{query_text}', Returned: {final_returned_results} (Frames: {len(frame_results)}, Tracks: {len(object_results)}), "
            f"Ranking Time: {ranking_time_ms}ms, Total Latency: {total_search_ms}ms"
        )

        return SearchResponse(
            query=query_text,
            topK=top_k,
            similarityThreshold=threshold,
            frameResults=frame_results,
            objectResults=object_results,
            statistics=stats,
            analytics=analytics
        )
