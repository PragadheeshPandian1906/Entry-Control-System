"""
Face detection + embedding using InsightFace's FaceAnalysis pipeline
('buffalo_l' pack — detection + 512-d ArcFace recognition in one model
bundle, auto-downloaded on first use).
"""
import logging

import numpy as np

logger = logging.getLogger("face_engine")

_app = None


def _get_app():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace FaceAnalysis ('buffalo_l') initialized.")
    return _app


def detect_faces(frame):
    """Returns a list of insightface Face objects (has .bbox, .embedding, .det_score)."""
    app = _get_app()
    return app.get(frame)


def get_largest_face(frame):
    """Convenience: returns the single largest detected face, or None."""
    faces = detect_faces(frame)
    if not faces:
        return None

    def area(f):
        x1, y1, x2, y2 = f.bbox
        return (x2 - x1) * (y2 - y1)

    return max(faces, key=area)


def cosine_similarity(vec_a, vec_b) -> float:
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
