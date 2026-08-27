"""
Reads the license plate text out of a frame using EasyOCR.

Default strategy: run EasyOCR's text detector+recognizer across the
whole frame, then keep the highest-confidence text box that *looks like*
a plate (see plate_validator.looks_like_plate).

If backend.config.USE_YOLO_PLATE_DETECTOR is True and a weight file is
present, that YOLO box is used to crop the plate region first, and OCR
is then run only on that crop (faster, more precise).
"""
import logging
from backend.config import USE_YOLO_PLATE_DETECTOR, OCR_MIN_CONFIDENCE
from services import plate_detector
from services.plate_validator import normalize_plate, looks_like_plate
from utils.image_utils import crop_box

logger = logging.getLogger("plate_ocr")

_reader = None


def _get_reader():
    """
    Lazy initializer for EasyOCR Reader.
    Loads models into memory only once when called.
    """
    global _reader
    if _reader is None:
        import easyocr
        # gpu=True will automatically fallback to CPU if CUDA is not available
        _reader = easyocr.Reader(['en'], gpu=False)
        logger.info("EasyOCR Reader initialized successfully.")
    return _reader


def read_plate(frame):
    """
    Reads license plate text from a given image frame.

    Returns:
        dict: {
            "raw_text": str | None,
            "plate_number": str | None,   # normalized
            "confidence": float,
            "box": [x1, y1, x2, y2] | None,
        }
    """
    default_response = {
        "raw_text": None,
        "plate_number": None,
        "confidence": 0.0,
        "box": None,
    }

    # Guard check: Ensure valid input frame
    if frame is None or frame.size == 0:
        logger.warning("Received an empty or invalid frame.")
        return default_response

    search_frame = frame
    offset = (0, 0)

    # Step 1: Optional YOLO Plate Cropping
    if USE_YOLO_PLATE_DETECTOR:
        try:
            yolo_boxes = plate_detector.detect_plate_boxes(frame)
            if yolo_boxes:
                # Select the box with highest detection confidence
                best = max(yolo_boxes, key=lambda b: b[4])
                x1, y1, x2, y2 = map(int, best[:4])

                # Verify box dimensions
                if x2 > x1 and y2 > y1:
                    cropped = crop_box(frame, [x1, y1, x2, y2])
                    if cropped is not None and cropped.size > 0:
                        search_frame = cropped
                        offset = (x1, y1)
        except Exception as err:
            logger.error(f"YOLO detection failed: {err}. Falling back to full frame.")

    # Step 2: Run EasyOCR
    reader = _get_reader()
    try:
        # detail=1 returns output formatted as: [ (bbox, text, prob), ... ]
        results = reader.readtext(search_frame, detail=1)
    except Exception as err:
        logger.error(f"EasyOCR execution failed: {err}")
        return default_response

    if not results:
        return default_response

    candidates = []

    # Step 3: Process Detected Bounding Boxes & Text
    for bbox, text, conf in results:
        # Filter low-confidence detections
        if conf < OCR_MIN_CONFIDENCE:
            continue

        normalized = normalize_plate(text)
        
        # Check against license plate rules
        if looks_like_plate(normalized):
            # bbox layout: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]

            # Convert crop-relative box back to original frame absolute coordinates
            abs_box = [
                int(min(xs)) + offset[0],
                int(min(ys)) + offset[1],
                int(max(xs)) + offset[0],
                int(max(ys)) + offset[1],
            ]
            candidates.append((normalized, text, float(conf), abs_box))

    if not candidates:
        return default_response

    # Step 4: Return candidate with highest confidence score
    normalized, raw_text, conf, box = max(candidates, key=lambda c: c[2])
    return {
        "raw_text": raw_text,
        "plate_number": normalized,
        "confidence": conf,
        "box": box,
    }