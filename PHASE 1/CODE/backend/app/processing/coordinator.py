import time
import logging
from pathlib import Path
from typing import Dict, Any, List

from app.core.config import settings
from app.models.schemas import ProcessingStatusEnum, FrameMetadata, DetectionItem, TrackItem
from app.database.mongo import mongo_db, MongoDBConnectionError
from app.processing.metadata import MetadataExtractor
from app.processing.video.frame_extractor import FrameExtractor
from app.processing.detection.object_detector import object_detector
from app.processing.tracking.tracker import tracker
from app.processing.audio.audio_transcriber import transcriber
from app.processing.embedding_generator import SemanticEmbeddingProcessor
from app.processing.debug.annotator import AnnotatedVideoGenerator
from app.processing.attributes.attribute_extractor import AttributeExtractor
from app.processing.attributes.scene_analyzer import SceneAnalyzer
from app.processing.text.ocr_extractor import OCRExtractor
from app.processing.ocr.paddle_ocr_service import paddle_ocr_service
import cv2



logger = logging.getLogger("chronolens.processing.coordinator")


class PipelineCoordinator:
    """
    Pipeline Coordinator: Orchestrates the sequential video processing workflow,
    manages state transitions, tracks stage timing performance, runs automatic pipeline validation,
    and centrally writes structured data into MongoDB.
    """
    @staticmethod
    def _validate_pipeline_results(
        video_id: str,
        frames_list: List[FrameMetadata],
        detections_list: List[DetectionItem],
        tracks_list: List[TrackItem],
        annotated_video_path: Path
    ):
        """
        Runs strict automatic validation checks before marking a video COMPLETED.
        Raises RuntimeError with explicit diagnostic error if validation fails.
        """
        logger.info(f"[PipelineCoordinator] Running automatic pipeline validation for video_id={video_id}...")

        # 1. Extracted frames > 0
        if not frames_list or len(frames_list) == 0:
            raise RuntimeError("Validation Failure: Frame extraction produced 0 frames.")

        # 2. Detections count >= 0
        if detections_list is None:
            raise RuntimeError("Validation Failure: Detections list is None.")

        # 3. Track IDs reference valid detections
        valid_detection_tracks = {d.trackId for d in detections_list if d.trackId is not None}
        for track in tracks_list:
            if track.trackId not in valid_detection_tracks and len(track.frames) > 0:
                raise RuntimeError(f"Validation Failure: Track #{track.trackId} does not reference valid detection entries.")

            # 4. Track duration correct (endTime >= startTime)
            if track.endTime < track.startTime:
                raise RuntimeError(f"Validation Failure: Track #{track.trackId} has invalid duration (endTime {track.endTime} < startTime {track.startTime}).")

        # 5. Annotated video exists
        if not annotated_video_path.exists() or annotated_video_path.stat().st_size == 0:
            raise RuntimeError(f"Validation Failure: Annotated video file does not exist at {annotated_video_path}.")

        # 6. MongoDB write succeeded
        summary = mongo_db.get_summary(video_id)
        if not summary or summary.get("frameCount", 0) == 0:
            raise RuntimeError("Validation Failure: MongoDB database document verification failed.")

        logger.info(f"[PipelineCoordinator] Pipeline validation PASSED for video_id={video_id}.")

    @staticmethod
    def process_video(video_id: str, video_path: Path, original_filename: str):
        existing_doc = mongo_db.get_video(video_id)
        if existing_doc and existing_doc.get("status") == ProcessingStatusEnum.COMPLETED.value:
            logger.info(f"[PipelineCoordinator] Video {video_id} is already indexed and COMPLETED. Skipping duplicate processing.")
            return

        start_total = time.time()
        stage_timings: Dict[str, float] = {}
        logger.info(f"========== [PipelineCoordinator] STARTING PROCESSING FOR {video_id} ==========")


        try:
            # 1. State: UPLOADED -> METADATA_EXTRACTION
            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.METADATA_EXTRACTION,
                current_stage="Extracting Video Metadata",
                message="Extracting duration, resolution, codec, and frame rate..."
            )

            metadata = MetadataExtractor.extract_metadata(
                video_path=video_path,
                video_id=video_id,
                original_filename=original_filename
            )
            t_mongo_0 = time.time()
            mongo_db.upsert_video(metadata.dict())
            stage_timings["mongoDbSec"] = round(stage_timings.get("mongoDbSec", 0.0) + (time.time() - t_mongo_0), 2)
            stage_timings["metadataExtractionSec"] = round(time.time() - t0, 2)
            logger.info(f"Video Uploaded & Metadata Extracted for {video_id} ({stage_timings['metadataExtractionSec']}s)")

            # 2. State: FRAME_EXTRACTION
            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.FRAME_EXTRACTION,
                current_stage="Extracting Frames (1 FPS)",
                message="Extracting frames at 1 FPS using FFmpeg..."
            )
            logger.info(f"Frame Extraction Started for {video_id}")

            frames_list = FrameExtractor.extract_frames_1fps(video_path=video_path, video_id=video_id)
            frames_dicts = [f.dict() for f in frames_list]
            
            t_mongo_0 = time.time()
            mongo_db.insert_frames(frames_dicts, video_id=video_id)
            stage_timings["mongoDbSec"] = round(stage_timings.get("mongoDbSec", 0.0) + (time.time() - t_mongo_0), 2)
            stage_timings["frameExtractionSec"] = round(time.time() - t0, 2)
            logger.info(f"Frame Extraction Completed for {video_id}. Total frames: {len(frames_list)} ({stage_timings['frameExtractionSec']}s)")

            # 3. State: OBJECT_DETECTION
            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.OBJECT_DETECTION,
                current_stage="Object Detection (YOLO26m)",
                message="Detecting objects across extracted frames using YOLO26m..."

            )
            logger.info(f"YOLO Started for {video_id}")

            detections_list = object_detector.detect_objects(frames=frames_list, video_id=video_id)
            stage_timings["yoloDetectionSec"] = round(time.time() - t0, 2)
            logger.info(f"YOLO Completed for {video_id}. Total detections: {len(detections_list)} ({stage_timings['yoloDetectionSec']}s)")

            # 4. State: OBJECT_TRACKING
            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.OBJECT_TRACKING,
                current_stage="Object Tracking (ByteTrack)",
                message="Assigning consistent Track IDs using ByteTrack..."
            )
            logger.info(f"ByteTrack Started for {video_id}")

            updated_detections, tracks_list = tracker.track_objects(detections=detections_list, video_id=video_id)
            stage_timings["byteTrackSec"] = round(time.time() - t0, 2)

            # Save detections & tracks to MongoDB
            t_mongo_0 = time.time()
            detections_dicts = [d.dict() for d in updated_detections]
            tracks_dicts = [t.dict() for t in tracks_list]
            mongo_db.insert_detections(detections_dicts, video_id=video_id)
            mongo_db.insert_tracks(tracks_dicts, video_id=video_id)
            # Generate BOLD annotated frames and Web H.264 video on disk for Debug Dashboard & Search
            try:
                AnnotatedVideoGenerator.generate_annotated_video(
                    video_id=video_id,
                    frames=frames_dicts,
                    detections=detections_dicts,
                    fps=settings.FRAME_EXTRACTION_FPS,
                    force_regenerate=True
                )
                logger.info(f"[PipelineCoordinator] Annotated frames and video successfully generated for {video_id}")
            except Exception as ann_err:
                logger.warning(f"[PipelineCoordinator] Annotated frames generation notice for {video_id}: {str(ann_err)}")

            # 5. State: AUDIO_TRANSCRIPTION

            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.AUDIO_TRANSCRIPTION,
                current_stage="Audio Transcription (Whisper)",
                message="Extracting audio track and running OpenAI Whisper transcription..."
            )
            logger.info(f"Whisper Started for {video_id}")

            transcripts_list = transcriber.transcribe_video_audio(video_path=video_path, video_id=video_id)
            transcripts_dicts = [tr.dict() for tr in transcripts_list]
            
            t_mongo_0 = time.time()
            mongo_db.insert_transcripts(transcripts_dicts, video_id=video_id)
            stage_timings["mongoDbSec"] = round(stage_timings.get("mongoDbSec", 0.0) + (time.time() - t_mongo_0), 2)
            stage_timings["whisperSec"] = round(time.time() - t0, 2)

            # Persist transcripts to local metadata JSON for file-based search fallback
            try:
                meta_dir = settings.BASE_DIR / "storage" / "metadata"
                meta_dir.mkdir(parents=True, exist_ok=True)
                t_file = meta_dir / "transcripts.json"
                existing_segs = []
                if t_file.exists():
                    try:
                        with open(t_file, "r", encoding="utf-8") as _tf:
                            existing_segs = json.load(_tf)
                    except Exception:
                        existing_segs = []
                existing_segs = [s for s in existing_segs if s.get("videoId") != video_id]
                existing_segs.extend(transcripts_dicts)
                with open(t_file, "w", encoding="utf-8") as _tf:
                    json.dump(existing_segs, _tf, indent=2)
            except Exception as _fe:
                logger.warning(f"Failed to persist transcripts to metadata JSON: {_fe}")

            logger.info(f"Whisper Completed for {video_id}. Total segments: {len(transcripts_list)} ({stage_timings['whisperSec']}s)")


            # 6. State: SEMANTIC_EMBEDDING (OpenCLIP & FAISS)
            t0 = time.time()
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.SEMANTIC_EMBEDDING,
                current_stage="Semantic Embedding Engine (OpenCLIP ViT-L/14 & FAISS)",
                message="Generating OpenCLIP normalized 768d vectors and indexing in FAISS..."
            )
            logger.info(f"Semantic Embedding Engine Started for {video_id}")

            embedding_metrics = SemanticEmbeddingProcessor.process_video_embeddings(
                video_id=video_id,
                frames=frames_dicts,
                detections=detections_dicts
            )
            stage_timings["semanticEmbeddingSec"] = round(time.time() - t0, 2)
            logger.info(f"Semantic Embedding Engine Completed for {video_id} ({stage_timings['semanticEmbeddingSec']}s)")

            # 7. State: VISUAL_ATTRIBUTES & SCENE_ANALYSIS
            t0 = time.time()
            try:
                # Scene Analysis on sampled frames (1 frame every 3 seconds)
                step_sample = max(1, int(settings.FRAME_EXTRACTION_FPS * 3))
                sampled_frames = frames_dicts[::step_sample]
                scenes_data = []
                for sf in sampled_frames:
                    fn = sf.get("frameNumber", 1)
                    frame_path = settings.FRAMES_DIR / video_id / f"frame_{fn:04d}.jpg"
                    if frame_path.exists():
                        frame_dets = [d for d in detections_dicts if d.get("frameNumber") == fn]
                        scene_info = SceneAnalyzer.analyze_frame_scene(
                            frame_img=str(frame_path),
                            frame_number=fn,
                            detections_in_frame=frame_dets
                        )
                        scene_info["videoId"] = video_id
                        scenes_data.append(scene_info)

                if scenes_data:
                    mongo_db.insert_scenes(scenes_data, video_id=video_id)

                # Optical Character Recognition (OCR) on sampled frames using PaddleOCRService
                logger.info(f"[PipelineCoordinator] Running PaddleOCR indexing for video_id={video_id}...")
                ocr_records = paddle_ocr_service.reindex_video_ocr(video_id=video_id)
                logger.info(f"[PipelineCoordinator] Saved {len(ocr_records)} PaddleOCR records for video_id={video_id}")


                # Attribute Extraction on Track Representative Crops (GPU Batched Acceleration)
                PipelineCoordinator._update_status(
                    video_id=video_id,
                    status=ProcessingStatusEnum.OBJECT_TRACKING,
                    currentStage="Extracting Visual Attributes",
                    message=f"Extracting clothing colors and visual accessories across {len(tracks_dicts)} tracks..."
                )

                attributes_data = []
                track_crop_items = []

                for trk in tracks_dicts:
                    tid = trk.get("trackId")
                    cls_name = trk.get("objectClass", "object")
                    trk_frames = trk.get("frames", [])

                    sup_fn = trk_frames[0] if trk_frames else 1
                    crop_file = None
                    existing_crop_url = None

                    if trk_frames:
                        for fn in trk_frames:
                            test_file = settings.DEBUG_DIR / video_id / "tracks" / str(tid) / f"frame_{fn:04d}.jpg"
                            if test_file.exists():
                                sup_fn = fn
                                crop_file = test_file
                                existing_crop_url = f"/static/storage/debug/{video_id}/tracks/{tid}/frame_{fn:04d}.jpg"
                                break

                    if crop_file is None:
                        crop_file = settings.DEBUG_DIR / video_id / "tracks" / str(tid) / f"frame_{sup_fn:04d}.jpg"
                        existing_crop_url = f"/static/storage/debug/{video_id}/tracks/{tid}/frame_{sup_fn:04d}.jpg"

                    if crop_file.exists():
                        crop_bgr = cv2.imread(str(crop_file))
                        if crop_bgr is not None:
                            track_crop_items.append({
                                "tid": tid,
                                "cls_name": cls_name,
                                "sup_fn": sup_fn,
                                "existing_crop_url": existing_crop_url,
                                "crop_bgr": crop_bgr
                            })

                if track_crop_items:
                    # Batch generate image embeddings on GPU in 1 pass
                    bgr_list = [item["crop_bgr"] for item in track_crop_items]
                    crop_embs = openclip_engine.generate_image_embeddings_batch(bgr_list, batch_size=32)

                    for item, c_emb in zip(track_crop_items, crop_embs):
                        tid = item["tid"]
                        cls_name = item["cls_name"]
                        sup_fn = item["sup_fn"]
                        existing_crop_url = item["existing_crop_url"]
                        crop_bgr = item["crop_bgr"]

                        if cls_name == "person":
                            attr_doc = AttributeExtractor.extract_person_attributes(
                                crop_bgr=crop_bgr,
                                track_id=tid,
                                supporting_frame=sup_fn,
                                existing_crop_url=existing_crop_url,
                                crop_emb=c_emb
                            )
                        elif cls_name in {"car", "truck", "bus", "motorcycle", "bicycle"}:
                            attr_doc = AttributeExtractor.extract_vehicle_attributes(
                                crop_bgr=crop_bgr,
                                object_class=cls_name,
                                track_id=tid,
                                supporting_frame=sup_fn,
                                existing_crop_url=existing_crop_url,
                                crop_emb=c_emb
                            )
                        else:
                            attr_doc = {
                                "trackId": tid,
                                "objectClass": cls_name,
                                "supportingFrame": sup_fn,
                                "cropUrl": existing_crop_url
                            }

                        attr_doc["videoId"] = video_id
                        attributes_data.append(attr_doc)

                if attributes_data:
                    mongo_db.insert_attributes(attributes_data, video_id=video_id)

            except Exception as attr_err:
                logger.warning(f"[PipelineCoordinator] Attribute extraction notice for {video_id}: {str(attr_err)}")

            stage_timings["visualAttributesSec"] = round(time.time() - t0, 2)

            # 8. Generate Annotated Video Debug Assets
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.OBJECT_TRACKING,
                currentStage="Compiling Debug Annotated Video",
                message="Rendering high-visibility bounding box overlay and Web H.264 stream..."
            )

            annotated_video_path, _ = AnnotatedVideoGenerator.generate_annotated_video(
                video_id=video_id,
                frames=frames_dicts,
                detections=detections_dicts,
                fps=settings.FRAME_EXTRACTION_FPS
            )

            # 9. Run Automatic Pipeline Validation

            PipelineCoordinator._validate_pipeline_results(
                video_id=video_id,
                frames_list=frames_list,
                detections_list=updated_detections,
                tracks_list=tracks_list,
                annotated_video_path=annotated_video_path
            )

            # 8. State: DATABASE_SYNC & COMPLETED
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.DATABASE_SYNC,
                current_stage="Finalizing Database Sync",
                message="Synchronizing all metadata and indexes in MongoDB..."
            )

            total_elapsed = round(time.time() - start_total, 2)
            stage_timings["totalProcessingTimeSec"] = total_elapsed
            processing_time_str = f"{total_elapsed:.2f} seconds"

            t_mongo_0 = time.time()
            mongo_db.upsert_video({
                "videoId": video_id,
                "status": ProcessingStatusEnum.COMPLETED.value,
                "currentStage": "Processing Completed Successfully",
                "message": f"Processing finished in {processing_time_str}.",
                "processingTime": processing_time_str,
                "stageTimings": stage_timings,
                "inferenceConfiguration": {
                    "yoloModel": settings.YOLO_MODEL,
                    "imgsz": settings.YOLO_IMGSZ,
                    "confidence": settings.YOLO_CONFIDENCE,
                    "iou": settings.YOLO_IOU,
                    "device": settings.INFERENCE_DEVICE,
                    "byteTrackEnabled": settings.BYTETRACK_ENABLED,
                    "whisperModel": settings.WHISPER_MODEL,
                    "frameExtractionFps": settings.FRAME_EXTRACTION_FPS
                }
            })
            yolo_time = stage_timings.get("yoloDetectionSec", 0.0)
            openclip_time = stage_timings.get("semanticEmbeddingSec", 0.0)

            print("\n========================================", flush=True)
            print("ChronoLens AI Performance Benchmarks", flush=True)
            print(f"Video ID               : {video_id}", flush=True)
            print(f"YOLO Detection Time    : {yolo_time:.2f}s", flush=True)
            print(f"OpenCLIP Embedding Time: {openclip_time:.2f}s", flush=True)
            print(f"Total AI Processing Time: {total_elapsed:.2f}s", flush=True)
            print("========================================\n", flush=True)


            logger.info(f"========== [PipelineCoordinator] PROCESSING COMPLETED FOR {video_id} in {processing_time_str} ==========")


        except MongoDBConnectionError as e:
            error_msg = f"MongoDB Failure: {str(e)}"
            logger.error(f"[PipelineCoordinator] {error_msg}")
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.FAILED,
                current_stage="Processing Failed",
                message="Pipeline failed due to database connectivity issue.",
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Pipeline Processing Failure: {str(e)}"
            logger.error(f"[PipelineCoordinator] {error_msg}", exc_info=True)
            PipelineCoordinator._update_status(
                video_id=video_id,
                status=ProcessingStatusEnum.FAILED,
                current_stage="Processing Failed",
                message="Video processing encountered an error during pipeline execution.",
                error=error_msg
            )

    @staticmethod
    def _update_status(
        video_id: str,
        status: ProcessingStatusEnum,
        current_stage: str,
        message: str,
        error: str = None
    ):
        """Helper to log and update state machine status in database."""
        logger.info(f"[State Machine] Video {video_id} -> {status.value}: {current_stage}")
        try:
            mongo_db.update_video_status(
                video_id=video_id,
                status=status.value,
                current_stage=current_stage,
                message=message,
                error=error
            )
        except Exception as err:
            logger.error(f"Failed to update video status in MongoDB for {video_id}: {str(err)}")


pipeline_coordinator = PipelineCoordinator()
