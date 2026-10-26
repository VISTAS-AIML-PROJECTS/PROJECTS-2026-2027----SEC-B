import logging
from pathlib import Path
from typing import List
import cv2
import numpy as np
from app.core.config import settings, get_runtime_device
from app.models.schemas import FrameMetadata, DetectionItem

logger = logging.getLogger("chronolens.processing.object_detector")

# Indoor office categories whitelist (excludes non-indoor categories like car, airplane, boat)
NON_INDOOR_CLASSES = {"car", "truck", "airplane", "bus", "train", "boat"}

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]


class ObjectDetector:
    """
    Deterministic YOLO26m Object Detector for ChronoLens Pipeline.
    Reads centralized locked settings (YOLO26m, imgsz=1280, conf=0.25, iou=0.45).
    Binds automatically to CUDA GPU acceleration when available, else CPU.
    Strict Policy: Fallback heuristics are permanently disabled.
    """
    def __init__(self):
        self.model_name = settings.YOLO_MODEL
        self.min_confidence = settings.YOLO_CONFIDENCE
        self.imgsz = settings.YOLO_IMGSZ
        self.iou_thresh = settings.YOLO_IOU
        self.device = get_runtime_device()
        self.model = None
        self.ort_session = None

    def _log_active_config(self, video_id: str):
        """Prints active deterministic inference configuration for every processed video."""
        logger.info(f"[ObjectDetector] Active Inference Configuration for video_id={video_id}:")
        print("\n========================================")
        print("ChronoLens Object Detector Configuration")
        print(f"Video ID: {video_id}")
        print(f"Model: {self.model_name}")
        print(f"Image Size: {self.imgsz}")
        print(f"Confidence: {self.min_confidence}")
        print(f"IoU: {self.iou_thresh}")
        print(f"Runtime Device: {self.device.upper()}")
        print("========================================\n")


    def _load_model(self):
        if self.model is not None or self.ort_session is not None:
            return

        # Attempt 1: PyTorch Ultralytics
        try:
            from ultralytics import YOLO
            logger.info(f"[ObjectDetector] Loading PyTorch YOLO model '{self.model_name}'...")
            self.model = YOLO(self.model_name)
            return
        except Exception as e:
            logger.warning(f"[ObjectDetector] PyTorch load notice: {str(e)}.")

        # Attempt 2: ONNX Runtime native execution
        try:
            import onnxruntime as ort
            onnx_path = Path("storage/models") / f"{Path(self.model_name).stem}.onnx"
            if onnx_path.exists():
                logger.info(f"[ObjectDetector] Loading ONNX Runtime session from {onnx_path}...")
                self.ort_session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
                return
        except Exception as e:
            logger.warning(f"[ObjectDetector] ONNX Runtime session notice: {str(e)}.")

    def detect_objects(self, frames: List[FrameMetadata], video_id: str) -> List[DetectionItem]:
        """
        Runs object detection across extracted video frames using locked YOLO settings.
        Strict Policy: If YOLO model fails or produces zero detections, zero detections are returned.
        No contour/heuristic fallback algorithms are executed.
        """
        self._log_active_config(video_id)

        try:
            self._load_model()
        except Exception as e:
            logger.error(f"[ObjectDetector] Model loading error: {str(e)}. Returning ZERO detections per strict policy.")
            return []

        logger.info(f"[ObjectDetector] Running YOLO inference on {len(frames)} frames for video_id={video_id}")

        detections: List[DetectionItem] = []

        for frame in frames:
            img_path = Path(frame.imagePath)
            if not img_path.exists():
                continue

            try:
                # 1. PyTorch YOLO Inference
                if self.model is not None:
                    results = self.model(
                        str(img_path),
                        imgsz=self.imgsz,
                        conf=self.min_confidence,
                        iou=self.iou_thresh,
                        device=self.device,
                        verbose=False
                    )

                    for res in results:
                        boxes = res.boxes
                        if boxes is None:
                            continue
                        
                        for box in boxes:
                            xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                            conf = float(box.conf[0].item())
                            cls_id = int(box.cls[0].item())
                            class_name = self.model.names.get(cls_id, f"class_{cls_id}").lower()

                            if class_name in NON_INDOOR_CLASSES:
                                continue

                            detections.append(
                                DetectionItem(
                                    trackId=None,
                                    videoId=video_id,
                                    frameNumber=frame.frameNumber,
                                    timestamp=frame.timestamp,
                                    boundingBox=[round(val, 2) for val in xyxy],
                                    confidence=round(conf, 4),
                                    objectClass=class_name
                                )
                            )
                
                # 2. ONNX Runtime Engine Inference
                elif self.ort_session is not None:
                    img = cv2.imread(str(img_path))
                    if img is None:
                        continue
                    
                    h, w = img.shape[:2]
                    # Preprocess image to imgsz
                    resized = cv2.resize(img, (self.imgsz, self.imgsz))
                    input_blob = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).transpose(2, 0, 1).astype(np.float32) / 255.0
                    input_blob = np.expand_dims(input_blob, axis=0)

                    input_name = self.ort_session.get_inputs()[0].name
                    outputs = self.ort_session.run(None, {input_name: input_blob})[0]
                    # Postprocess YOLOv8 ONNX output shape [1, 84, N]
                    predictions = np.squeeze(outputs).T
                    
                    boxes, confidences, class_ids = [], [], []
                    x_factor = w / float(self.imgsz)
                    y_factor = h / float(self.imgsz)

                    for pred in predictions:
                        scores = pred[4:]
                        cls_id = np.argmax(scores)
                        max_score = float(scores[cls_id])

                        if max_score >= self.min_confidence:
                            xc, yc, bw, bh = pred[0], pred[1], pred[2], pred[3]
                            x1 = (xc - bw / 2.0) * x_factor
                            y1 = (yc - bh / 2.0) * y_factor
                            x2 = (xc + bw / 2.0) * x_factor
                            y2 = (yc + bh / 2.0) * y_factor

                            cls_name = COCO_CLASSES[cls_id] if cls_id < len(COCO_CLASSES) else f"class_{cls_id}"
                            if cls_name.lower() in NON_INDOOR_CLASSES:
                                continue

                            boxes.append([x1, y1, x2 - x1, y2 - y1])
                            confidences.append(max_score)
                            class_ids.append(cls_id)

                    indices = cv2.dnn.NMSBoxes(boxes, confidences, self.min_confidence, self.iou_thresh)
                    for i in indices:
                        idx = i[0] if isinstance(i, (list, tuple, np.ndarray)) else i
                        box = boxes[idx]
                        x1, y1, bw, bh = box
                        cls_id = class_ids[idx]
                        cls_name = COCO_CLASSES[cls_id] if cls_id < len(COCO_CLASSES) else f"class_{cls_id}"

                        detections.append(
                            DetectionItem(
                                trackId=None,
                                videoId=video_id,
                                frameNumber=frame.frameNumber,
                                timestamp=frame.timestamp,
                                boundingBox=[round(x1, 2), round(y1, 2), round(x1 + bw, 2), round(y1 + bh, 2)],
                                confidence=round(confidences[idx], 4),
                                objectClass=cls_name.lower()
                            )
                        )

            except Exception as e:
                logger.error(f"[ObjectDetector] Detection error on frame {frame.frameNumber}: {str(e)}")

        logger.info(f"[ObjectDetector] Generated {len(detections)} object detections across {len(frames)} frames.")
        return detections


object_detector = ObjectDetector()
