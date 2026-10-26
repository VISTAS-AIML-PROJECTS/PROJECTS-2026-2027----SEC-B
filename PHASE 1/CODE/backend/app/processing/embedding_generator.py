import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from app.core.config import settings
from app.database.mongo import mongo_db
from app.services.semantic.openclip_engine import openclip_engine
from app.services.semantic.faiss_manager import faiss_manager
from app.processing.debug.crop_generator import ObjectCropGenerator

logger = logging.getLogger("chronolens.processing.embedding_generator")


class SemanticEmbeddingProcessor:
    """
    Phase 2.0 Semantic Embedding Processor.
    Generates normalized OpenCLIP ViT-L/14 image embeddings for every extracted video frame
    and every tracked object crop. Stores vector indices inside FAISS and metadata inside MongoDB.
    """

    @staticmethod
    def process_video_embeddings(
        video_id: str,
        frames: List[Dict[str, Any]],
        detections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes frame and object crop semantic embedding generation.
        Returns detailed performance metrics and count statistics.
        """
        logger.info(f"[SemanticProcessor] Starting OpenCLIP embedding generation for video_id={video_id} across {len(frames)} frames & {len(detections)} object detections")

        start_total = time.time()
        frame_embeddings_meta = []
        object_embeddings_meta = []
        gen_times = []

        db = mongo_db.db

        # ---------------------------------------------------------------------
        # 1. Generate Frame Level Embeddings (Batched GPU Inferences & FAISS Writes)
        # ---------------------------------------------------------------------
        sorted_frames = sorted(frames, key=lambda f: f.get("frameNumber", 0))
        valid_frames = []
        valid_img_paths = []

        for frame in sorted_frames:
            img_path = Path(frame.get("imagePath", ""))
            if not img_path.exists():
                alt_path = settings.BASE_DIR / img_path
                if alt_path.exists():
                    img_path = alt_path
                else:
                    logger.warning(f"[SemanticProcessor] Frame image missing at {img_path}. Skipping.")
                    continue
            valid_frames.append(frame)
            valid_img_paths.append(img_path)

        total_valid_frames = len(valid_frames)
        batch_size = 32

        for i in range(0, total_valid_frames, batch_size):
            chunk_frames = valid_frames[i:i + batch_size]
            chunk_paths = valid_img_paths[i:i + batch_size]

            t0 = time.time()
            vecs = openclip_engine.generate_image_embeddings_batch(chunk_paths, batch_size=batch_size)
            faiss_ids = faiss_manager.add_frame_vectors_batch(vecs)
            chunk_elapsed = round(time.time() - t0, 4)
            avg_per_item = chunk_elapsed / max(1, len(chunk_frames))

            for frame, faiss_id in zip(chunk_frames, faiss_ids):
                frame_num = frame.get("frameNumber")
                ts = frame.get("timestamp", 0.0)
                gen_times.append(avg_per_item)

                meta = {
                    "videoId": video_id,
                    "frameNumber": frame_num,
                    "timestamp": ts,
                    "faissId": faiss_id,
                    "embeddingDimension": openclip_engine.embedding_dim,
                    "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
                    "vectorNorm": 1.0,
                    "generationTimeSec": round(avg_per_item, 4),
                    "type": "frame"
                }
                frame_embeddings_meta.append(meta)

                if db is not None:
                    db.frames.update_one(
                        {"videoId": video_id, "frameNumber": frame_num},
                        {"$set": {
                            "faissId": faiss_id,
                            "embeddingDimension": openclip_engine.embedding_dim,
                            "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
                            "embeddingNorm": 1.0,
                            "embeddingGenerationTimeSec": round(avg_per_item, 4)
                        }}
                    )

            processed_count = min(i + batch_size, total_valid_frames)
            mongo_db.update_video_status(
                video_id,
                "PROCESSING",
                "EMBEDDING_GENERATION",
                f"Generating OpenCLIP Frame Embeddings ({processed_count}/{total_valid_frames})..."
            )

        # ---------------------------------------------------------------------
        # 2. Generate Tracked Object Crop Embeddings (Keyframe Selection & GPU Batched)
        # ---------------------------------------------------------------------
        track_groups: Dict[Any, List[Dict[str, Any]]] = {}
        untracked_dets: List[Dict[str, Any]] = []

        for det in detections:
            tid = det.get("trackId")
            if tid is not None:
                if tid not in track_groups:
                    track_groups[tid] = []
                track_groups[tid].append(det)
            else:
                untracked_dets.append(det)

        # Select representative keyframe detections (top 2 per track ID)
        selected_dets_map: Dict[Any, List[Dict[str, Any]]] = {}
        all_selected_dets: List[Dict[str, Any]] = []

        for tid, det_list in track_groups.items():
            sorted_dets = sorted(det_list, key=lambda d: d.get("confidence", 0.0), reverse=True)
            k_dets = [sorted_dets[0]]
            if len(sorted_dets) > 1:
                mid_idx = len(sorted_dets) // 2
                if sorted_dets[mid_idx] != sorted_dets[0]:
                    k_dets.append(sorted_dets[mid_idx])
            selected_dets_map[tid] = k_dets
            all_selected_dets.extend(k_dets)

        # Include max 1 untracked detection per frame
        untracked_by_frame = {}
        for det in untracked_dets:
            fn = det.get("frameNumber")
            if fn not in untracked_by_frame:
                untracked_by_frame[fn] = det
                all_selected_dets.append(det)

        valid_dets = []
        valid_crop_imgs = []
        valid_crop_urls = []

        for det in all_selected_dets:
            track_id = det.get("trackId")
            frame_num = det.get("frameNumber", 0)
            box = det.get("boundingBox", [0, 0, 0, 0])

            crop_url, crop_img = ObjectCropGenerator.get_or_create_crop(
                video_id=video_id,
                track_id=track_id or 0,
                frame_number=frame_num,
                bbox=box
            )

            if crop_img is not None:
                valid_dets.append(det)
                valid_crop_imgs.append(crop_img)
                valid_crop_urls.append(crop_url)

        total_valid_dets = len(valid_dets)

        for i in range(0, total_valid_dets, batch_size):
            chunk_dets = valid_dets[i:i + batch_size]
            chunk_imgs = valid_crop_imgs[i:i + batch_size]
            chunk_urls = valid_crop_urls[i:i + batch_size]

            t0 = time.time()
            vecs = openclip_engine.generate_image_embeddings_batch(chunk_imgs, batch_size=batch_size)
            faiss_ids = faiss_manager.add_object_vectors_batch(vecs)
            chunk_elapsed = round(time.time() - t0, 4)
            avg_per_item = chunk_elapsed / max(1, len(chunk_dets))

            for det, faiss_id, crop_url in zip(chunk_dets, faiss_ids, chunk_urls):
                track_id = det.get("trackId")
                frame_num = det.get("frameNumber", 0)
                ts = det.get("timestamp", 0.0)
                obj_cls = det.get("objectClass", "object")
                gen_times.append(avg_per_item)

                meta = {
                    "videoId": video_id,
                    "trackId": track_id,
                    "objectClass": obj_cls,
                    "frameNumber": frame_num,
                    "timestamp": ts,
                    "faissId": faiss_id,
                    "embeddingDimension": openclip_engine.embedding_dim,
                    "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
                    "vectorNorm": 1.0,
                    "generationTimeSec": round(avg_per_item, 4),
                    "cropUrl": crop_url,
                    "type": "object"
                }
                object_embeddings_meta.append(meta)

                # Link faissId across all frame detections belonging to this trackId in MongoDB
                if db is not None:
                    if track_id is not None:
                        db.detections.update_many(
                            {"videoId": video_id, "trackId": track_id},
                            {"$set": {
                                "faissId": faiss_id,
                                "embeddingDimension": openclip_engine.embedding_dim,
                                "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
                                "embeddingNorm": 1.0,
                                "embeddingGenerationTimeSec": round(avg_per_item, 4)
                            }}
                        )
                    else:
                        db.detections.update_one(
                            {"videoId": video_id, "frameNumber": frame_num},
                            {"$set": {
                                "faissId": faiss_id,
                                "embeddingDimension": openclip_engine.embedding_dim,
                                "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
                                "embeddingNorm": 1.0,
                                "embeddingGenerationTimeSec": round(avg_per_item, 4)
                            }}
                        )

            processed_count = min(i + batch_size, total_valid_dets)
            mongo_db.update_video_status(
                video_id,
                "PROCESSING",
                "EMBEDDING_GENERATION",
                f"Generating OpenCLIP Track Crop Embeddings ({processed_count}/{total_valid_dets})..."
            )

        # Save metadata records to db.embeddings collection for Developer Inspector UI
        if db is not None and (frame_embeddings_meta or object_embeddings_meta):
            db.embeddings.delete_many({"videoId": video_id})
            all_meta = frame_embeddings_meta + object_embeddings_meta
            db.embeddings.insert_many(all_meta)

        total_elapsed = round(time.time() - start_total, 4)
        avg_gen_time = round(float(sum(gen_times) / max(1, len(gen_times))), 4)
        min_gen_time = round(float(min(gen_times) if gen_times else 0.0), 4)
        max_gen_time = round(float(max(gen_times) if gen_times else 0.0), 4)

        frame_faiss_size, object_faiss_size = faiss_manager.get_counts()

        metrics = {
            "videoId": video_id,
            "totalFrameEmbeddings": len(frame_embeddings_meta),
            "totalObjectEmbeddings": len(object_embeddings_meta),
            "frameFaissIndexSize": frame_faiss_size,
            "objectFaissIndexSize": object_faiss_size,
            "embeddingModel": f"OpenCLIP-{openclip_engine.model_name}",
            "embeddingDimension": openclip_engine.embedding_dim,
            "averageGenerationTimeSec": avg_gen_time,
            "fastestFrameSec": min_gen_time,
            "slowestFrameSec": max_gen_time,
            "totalSemanticProcessingTimeSec": total_elapsed,
            "averageVectorNorm": 1.0
        }

        logger.info(f"[SemanticProcessor] Completed embedding generation for video_id={video_id} in {total_elapsed}s. Frames: {len(frame_embeddings_meta)}, Objects: {len(object_embeddings_meta)}")

        return metrics
