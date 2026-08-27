"""
Central configuration for the AI Smart Entry Control System prototype.
All tunable thresholds and paths live here so the rest of the codebase
never hardcodes magic numbers.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Directories ---
DATABASE_DIR = BASE_DIR / "database"
UPLOADS_DIR = BASE_DIR / "uploads"
LOGS_DIR = BASE_DIR / "logs"
REGISTERED_FACES_DIR = BASE_DIR / "registered_faces"
MODELS_DIR = BASE_DIR / "models"

for d in (DATABASE_DIR, UPLOADS_DIR, LOGS_DIR, REGISTERED_FACES_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Database ---
DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'entry.db'}"

# --- Plate detection strategy ---
# Default (False): use PaddleOCR's built-in text detector on the full frame,
#   then filter detected text boxes for plate-shaped strings. Works out of
#   the box with just `pip install`, no extra weight files to source.
# True: use a custom YOLO license-plate detector (ultralytics). Requires you
#   to supply a trained .pt weight file at YOLO_PLATE_MODEL_PATH.
USE_YOLO_PLATE_DETECTOR = os.getenv("USE_YOLO_PLATE_DETECTOR", "false").lower() == "true"
YOLO_PLATE_MODEL_PATH = str(MODELS_DIR / "plate_detector.pt")

# --- Thresholds ---
OCR_MIN_CONFIDENCE = 0.35          # minimum PaddleOCR confidence to trust a text box
FACE_SIMILARITY_THRESHOLD = 0.45   # cosine similarity threshold for InsightFace buffalo_l embeddings
PLATE_FUZZY_MAX_EDITS = 2          # allowed character edit-distance for OCR-error tolerant plate matching

# --- Indian plate normalization ---
# Common OCR confusions to try when an exact/fuzzy DB match fails.
OCR_CHAR_CORRECTIONS = {
    "O": "0", "Q": "0", "D": "0",
    "I": "1", "L": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
    "G": "6",
}

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
