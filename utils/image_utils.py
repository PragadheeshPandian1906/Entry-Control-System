"""
Image conversion and persistence helpers shared across services.
"""
import base64
import time
from pathlib import Path

import cv2
import numpy as np


def bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes (from an uploaded file) into an OpenCV BGR array."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image bytes — unsupported or corrupt image data.")
    return frame


def base64_to_bgr(b64_string: str) -> np.ndarray:
    """Decode a base64 (optionally data-URL prefixed) string into a BGR array."""
    if "," in b64_string and b64_string.strip().startswith("data:"):
        b64_string = b64_string.split(",", 1)[1]
    image_bytes = base64.b64decode(b64_string)
    return bytes_to_bgr(image_bytes)


def save_snapshot(frame: np.ndarray, directory: Path, prefix: str = "snapshot") -> str:
    """Save a frame to disk with a timestamped filename. Returns the file path as a string."""
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{int(time.time() * 1000)}.jpg"
    path = directory / filename
    cv2.imwrite(str(path), frame)
    return str(path)


def crop_box(frame: np.ndarray, box) -> np.ndarray:
    """Crop a region from a frame given box=[x1, y1, x2, y2] (ints), clamped to bounds."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in box]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return frame.copy()
    return frame[y1:y2, x1:x2].copy()
