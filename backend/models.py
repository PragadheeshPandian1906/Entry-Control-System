"""
ORM models: Users and EntryLogs.
Face embeddings are stored as JSON-encoded float lists (SQLite has no
native vector/array column, and this keeps the prototype dependency-light).
"""
import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    vehicle_type = Column(String(60), nullable=False, default="Car")
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    face_embedding = Column(Text, nullable=False)  # JSON list[float]
    face_image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def set_embedding(self, vector):
        self.face_embedding = json.dumps(list(map(float, vector)))

    def get_embedding(self):
        return json.loads(self.face_embedding)


class EntryLog(Base):
    __tablename__ = "entry_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    detected_plate = Column(String(20), nullable=True)
    ocr_confidence = Column(Float, nullable=True)

    matched_user_name = Column(String(120), nullable=True)
    face_similarity = Column(Float, nullable=True)

    plate_matched = Column(Boolean, default=False)
    face_matched = Column(Boolean, default=False)

    decision = Column(String(40), nullable=False)  # ACCESS_GRANTED | SECURITY_VERIFICATION_REQUIRED
    reason = Column(String(120), nullable=True)

    snapshot_path = Column(String(255), nullable=True)
