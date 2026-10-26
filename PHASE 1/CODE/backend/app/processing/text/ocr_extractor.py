import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger("chronolens.processing.ocr")

_easyocr_reader = None
_easyocr_attempted = False

def get_easyocr_reader():
    global _easyocr_reader, _easyocr_attempted
    if not _easyocr_attempted:
        _easyocr_attempted = True
        try:
            import easyocr
            import torch
            use_gpu = torch.cuda.is_available()
            _easyocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
            logger.info(f"[OCRExtractor] Initialized EasyOCR (GPU={use_gpu}).")
        except Exception as e:
            logger.info(f"[OCRExtractor] EasyOCR load notice (falling back to PyTesseract/OpenCV): {e}")
    return _easyocr_reader

try:
    import pytesseract
except Exception:
    pytesseract = None


class OCRExtractor:
    """
    Phase 2.6 Optical Character Recognition (OCR) Engine.
    Extracts visible text phrases from video frames to enable exact and partial text search
    (e.g., "Student service", "CHICANO", room numbers, building signs).
    """

    @classmethod
    def extract_frame_text(cls, frame_bgr: np.ndarray) -> List[str]:
        """
        Extracts clean text strings found in a frame.
        Includes contrast enhancement (CLAHE) and resolution upscaling for low-res CCTV frames.
        Returns a list of unique lower-case text tokens and full phrases.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        extracted_words: List[str] = []
        reader = get_easyocr_reader()

        # Image Preprocessing for low-res or low-contrast text (e.g., CCTV walls)
        h, w = frame_bgr.shape[:2]
        # Scale up slightly if resolution is small
        if w < 1920:
            scale = 1.5
            proc_img = cv2.resize(frame_bgr, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        else:
            proc_img = frame_bgr.copy()

        # Apply CLAHE to enhance text contrast on walls/signs
        lab = cv2.cvtColor(proc_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_bgr = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)

        # 1. EasyOCR Primary Extraction
        if reader is not None:
            try:
                rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
                results = reader.readtext(rgb, detail=0)
                for res in results:
                    cleaned = str(res).strip().lower()
                    # Filter out tiny single noise characters unless digit
                    if len(cleaned) >= 2 or cleaned.isdigit():
                        extracted_words.append(cleaned)
            except Exception as ex:
                logger.warning(f"[OCRExtractor] EasyOCR extraction warning: {ex}")

        # 2. PyTesseract Fallback
        if not extracted_words and pytesseract is not None:
            try:
                gray = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray)
                for line in text.splitlines():
                    cleaned = line.strip().lower()
                    if len(cleaned) >= 2 or cleaned.isdigit():
                        extracted_words.append(cleaned)
            except Exception:
                pass

        # Deduplicate while preserving order
        seen = set()
        unique_text = []
        for w in extracted_words:
            if w not in seen:
                seen.add(w)
                unique_text.append(w)

        return unique_text

