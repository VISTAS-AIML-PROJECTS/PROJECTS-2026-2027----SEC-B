import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np
from PIL import Image

from app.core.config import settings
from app.models.schemas import OcrDetectionItem, OcrFrameResultItem

logger = logging.getLogger("chronolens.processing.ocr")


def normalize_ocr_text(text: str) -> str:
    """Normalizes recognized OCR text for clean text search."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


class PaddleOCRService:
    """
    Isolated PaddleOCR service for visual text detection & recognition in video frames.
    Loads once, fails gracefully without breaking system startup or indexing.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PaddleOCRService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, lang: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True
        self.lang = lang or getattr(settings, "OCR_LANG", "en")
        self.min_confidence = float(getattr(settings, "OCR_MIN_CONFIDENCE", 0.50))
        self.ocr_engine = None
        self.is_available = False
        self.execution_device = "disabled"

    def initialize(self) -> bool:
        """Loads PaddleOCR singleton model safely with CPU/GPU fallback."""
        if self.ocr_engine is not None:
            return self.is_available

        if not getattr(settings, "ENABLE_OCR", True):
            logger.info("[PaddleOCR] ENABLE_OCR=false — PaddleOCR service disabled via config.")
            self.is_available = False
            return False

        try:
            os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
            os.environ["FLAGS_use_mkldnn"] = "0"

            try:
                import paddle.inference
                paddle.inference.Config.enable_mkldnn = lambda self: self.disable_mkldnn()
            except Exception:
                pass

            from paddleocr import PaddleOCR

            logger.info(f"[PaddleOCR] Initializing PaddleOCR model (lang='{self.lang}')...")
            try:
                self.ocr_engine = PaddleOCR(
                    use_textline_orientation=True,
                    lang=self.lang,
                )
                self.execution_device = "CPU/GPU (PaddleX Auto)"
            except Exception as gpu_err:
                logger.warning(f"[PaddleOCR] Primary init notice ({gpu_err}). Falling back to standard PaddleOCR...")
                self.ocr_engine = PaddleOCR(lang=self.lang)
                self.execution_device = "CPU/GPU (PaddleX Auto)"

            self.is_available = True
            logger.info(f"[PaddleOCR] PaddleOCR initialized successfully on device='{self.execution_device}'.")
            return True

        except Exception as err:
            logger.warning(f"[PaddleOCR] Initialization failed ({err}). ChronoLens will continue operating without OCR.")
            self.ocr_engine = None
            self.is_available = False
            self.execution_device = "unavailable"
            return False

    def process_frame(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image],
        video_id: str,
        frame_number: int,
        timestamp: float
    ) -> List[OcrDetectionItem]:
        """
        Runs PaddleOCR on a single frame image and returns filtered OCR detection items.
        """
        if not self.initialize() or self.ocr_engine is None:
            return []

        detections: List[OcrDetectionItem] = []

        try:
            # Prepare image input
            if isinstance(image_input, (str, Path)):
                img_path = str(image_input)
                if not os.path.exists(img_path):
                    logger.warning(f"[PaddleOCR] Frame file not found: {img_path}")
                    return []
                img_data = img_path
            elif isinstance(image_input, Image.Image):
                img_data = np.array(image_input.convert("RGB"))
            elif isinstance(image_input, np.ndarray):
                img_data = image_input
            else:
                return []

            if hasattr(self.ocr_engine, "predict"):
                raw_res = list(self.ocr_engine.predict(img_data))
            else:
                raw_res = self.ocr_engine.ocr(img_data)

            if not raw_res:
                return []

            res_item = raw_res[0]

            # 1. Check PaddleX 3.7 dict output format
            if isinstance(res_item, dict):
                rec_texts = res_item.get("rec_texts", [])
                rec_scores = res_item.get("rec_scores", [])
                rec_boxes = res_item.get("rec_boxes", [])

                for i, text_raw in enumerate(rec_texts):
                    txt = str(text_raw).strip()
                    conf = float(rec_scores[i]) if i < len(rec_scores) else 0.50
                    if not txt or conf < self.min_confidence:
                        continue

                    bbox = [0.0, 0.0, 100.0, 100.0]
                    if i < len(rec_boxes):
                        b = rec_boxes[i]
                        if isinstance(b, (list, tuple, np.ndarray)):
                            if len(b) == 4:
                                bbox = [round(float(b[0]), 2), round(float(b[1]), 2), round(float(b[2]), 2), round(float(b[3]), 2)]
                            elif len(b) == 8 or (isinstance(b[0], (list, tuple, np.ndarray)) and len(b) >= 4):
                                pts = b.tolist() if hasattr(b, "tolist") else b
                                xs = [float(p[0]) for p in pts]
                                ys = [float(p[1]) for p in pts]
                                bbox = [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]

                    norm_t = normalize_ocr_text(txt)
                    detections.append(
                        OcrDetectionItem(
                            text=txt,
                            normalizedText=norm_t,
                            confidence=round(conf, 4),
                            bbox=bbox
                        )
                    )

            # 2. Legacy list output format
            elif isinstance(res_item, list):
                for line in res_item:
                    if not line or len(line) < 2:
                        continue

                    poly_coords = line[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    text_info = line[1]    # (text_string, confidence_score)

                    if not text_info or len(text_info) < 2:
                        continue

                    raw_text = str(text_info[0]).strip()
                    confidence = float(text_info[1])

                    if not raw_text or confidence < self.min_confidence:
                        continue

                    xs = [float(pt[0]) for pt in poly_coords]
                    ys = [float(pt[1]) for pt in poly_coords]
                    bbox = [round(min(xs), 2), round(min(ys), 2), round(max(xs), 2), round(max(ys), 2)]

                    norm_text = normalize_ocr_text(raw_text)

                    detections.append(
                        OcrDetectionItem(
                            text=raw_text,
                            normalizedText=norm_text,
                            confidence=round(confidence, 4),
                            bbox=bbox
                        )
                    )

        except Exception as frame_err:
            logger.warning(f"[PaddleOCR] Error processing frame {frame_number} for video {video_id}: {frame_err}")

        return detections

    def reindex_video_ocr(self, video_id: str, batch_size: int = 25, max_frames: int = 0) -> List[Dict[str, Any]]:
        """
        Independent OCR re-indexing operation for an existing video.
        Scans frames, delegates to isolated GPU worker if available, with batch persistence & resume support.
        """
        import json
        import subprocess
        from app.database.mongo import mongo_db

        logger.info(f"[PaddleOCR] Starting OCR re-indexing for video_id={video_id}...")

        # Search for frame directory
        search_dirs = [
            settings.STORAGE_DIR / "debug" / video_id / "frames",
            settings.FRAMES_DIR / video_id,
            settings.STORAGE_DIR / "frames" / video_id,
            settings.BASE_DIR / "storage" / "frames" / video_id
        ]

        frames_dir = None
        for sd in search_dirs:
            if sd.exists():
                frames_dir = sd
                break

        if frames_dir is None or not frames_dir.exists():
            logger.warning(f"[PaddleOCR] Frame directory not found for video_id={video_id}")
            return []

        frame_files = sorted(list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.png")))
        if not frame_files:
            logger.warning(f"[PaddleOCR] No frame images found in {frames_dir}")
            return []

        # 1. Delegate to Isolated GPU Worker if present
        gpu_python = settings.BASE_DIR / "scratch" / "gpu_ocr_venv" / "Scripts" / "python.exe"
        gpu_worker_script = settings.BASE_DIR / "scratch" / "gpu_ocr_worker.py"

        if gpu_python.exists() and gpu_worker_script.exists():
            logger.info(f"[PaddleOCR] Launching isolated GPU OCR worker for video_id={video_id}...")
            cmd = [
                str(gpu_python),
                str(gpu_worker_script),
                "--video_id", video_id,
                "--frames_dir", str(frames_dir),
                "--batch_size", str(batch_size)
            ]
            if max_frames > 0:
                cmd.extend(["--max_frames", str(max_frames)])

            try:
                proc_res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"[PaddleOCR] GPU worker executed cleanly: {proc_res.stdout.strip()[-200:]}")
                mongo_db.connect()
                return mongo_db.get_ocr_texts(video_id)
            except Exception as gpu_exec_err:
                logger.warning(f"[PaddleOCR] GPU worker execution notice ({gpu_exec_err}). Falling back to CPU batch processing...")

        # 2. CPU Batch Fallback with Incremental Persistence & Resume Support
        mongo_db.connect()
        persisted_docs = mongo_db.get_ocr_texts(video_id)
        persisted_frames = set(int(d["frameNumber"]) for d in persisted_docs if d.get("frameNumber") is not None)

        ocr_sample_fps = float(getattr(settings, "OCR_SAMPLE_INTERVAL", 1.0))
        unprocessed_files = []
        for f_path in frame_files:
            f_num_match = re.search(r"(\d+)", f_path.stem)
            f_num = int(f_num_match.group(1)) if f_num_match else 1
            if f_num not in persisted_frames:
                unprocessed_files.append((f_num, f_path))

        if max_frames > 0:
            unprocessed_files = unprocessed_files[:max_frames]

        logger.info(f"[PaddleOCR] Processing {len(unprocessed_files)} remaining frames on CPU in batches of {batch_size}...")

        for i in range(0, len(unprocessed_files), batch_size):
            batch_tuples = unprocessed_files[i : i + batch_size]
            batch_docs = []

            for frame_num, f_path in batch_tuples:
                timestamp = round(float(frame_num - 1) / max(1.0, ocr_sample_fps), 2)
                try:
                    dets = self.process_frame(
                        image_input=f_path,
                        video_id=video_id,
                        frame_number=frame_num,
                        timestamp=timestamp
                    )
                    if dets:
                        batch_docs.append({
                            "videoId": video_id,
                            "frameNumber": frame_num,
                            "timestamp": timestamp,
                            "detections": [d.dict() for d in dets]
                        })
                except Exception as fe:
                    logger.warning(f"[PaddleOCR] CPU frame processing error for {f_path.name}: {fe}")

            if batch_docs:
                mongo_db.upsert_ocr_batch(batch_docs, video_id=video_id)

        return mongo_db.get_ocr_texts(video_id)


paddle_ocr_service = PaddleOCRService()
