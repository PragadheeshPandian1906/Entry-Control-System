"""
Central logging configuration. Writes to logs/app.log and stdout.
"""
import logging
import sys

from backend.config import LOGS_DIR

_configured = False


def setup_logging():
    global _configured
    if _configured:
        return
    _configured = True

    log_file = LOGS_DIR / "app.log"
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Quiet down noisy third-party libraries
    for noisy in ("ppocr", "paddleocr", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
