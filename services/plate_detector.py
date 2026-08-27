"""
Optional custom license-plate detector using a YOLO (ultralytics) model.

This stage is OFF by default (see backend/config.USE_YOLO_PLATE_DETECTOR).
By default the pipeline relies on PaddleOCR's own text detector to find
the plate directly (see services/plate_ocr.py), which needs no extra
weight file. Enable this only if you have sourced/trained a license-plate
YOLO model and placed it at backend/config.YOLO_PLATE_MODEL_PATH.
"""
import logging
from pathlib import Path

logger = logging.getLogger("plate_detector")

_model = None
_model_load_attempted = False


def _load_model():
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True

    from backend.config import YOLO_PLATE_MODEL_PATH
    if not Path(YOLO_PLATE_MODEL_PATH).exists():
        logger.warning(
            "YOLO plate model not found at %s. Falling back to PaddleOCR full-frame "
            "detection. Set USE_YOLO_PLATE_DETECTOR=false to silence this warning.",
            YOLO_PLATE_MODEL_PATH,
        )
        return None

    from ultralytics import YOLO
    _model = YOLO(YOLO_PLATE_MODEL_PATH)
    logger.info("Loaded YOLO plate detector from %s", YOLO_PLATE_MODEL_PATH)
    return _model


def detect_plate_boxes(frame, conf_threshold: float = 0.4):
    """
    Returns a list of [x1, y1, x2, y2, confidence] boxes for detected plates.
    Returns an empty list if the model isn't available (caller should then
    fall back to PaddleOCR full-frame detection).
    """
    model = _load_model()
    if model is None:
        return []

    results = model.predict(frame, conf=conf_threshold, verbose=False)
    boxes = []
    for r in results:
        for b in r.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            conf = float(b.conf[0])
            boxes.append([x1, y1, x2, y2, conf])
    return boxes
