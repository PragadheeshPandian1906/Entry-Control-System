"""
Data-access layer. Routes call these functions instead of touching the
ORM/session directly, keeping backend/routes.py thin.
"""
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import User, EntryLog
from services.plate_validator import (
    normalize_plate,
    generate_ocr_correction_variants,
    best_fuzzy_match,
)


def create_user(db: Session, name: str, vehicle_type: str, plate_number: str,
                 embedding, face_image_path: str) -> User:
    user = User(
        name=name,
        vehicle_type=vehicle_type,
        plate_number=normalize_plate(plate_number),
        face_image_path=face_image_path,
    )
    user.set_embedding(embedding)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_plate_numbers(db: Session) -> list[str]:
    return [row[0] for row in db.query(User.plate_number).all()]


def find_user_by_plate(db: Session, detected_plate: str) -> Optional[User]:
    """
    Exact match first. If that fails, try common OCR-confusion character
    swaps, then fall back to edit-distance fuzzy matching so a slightly
    misread plate (tilt, glare, partial occlusion) can still be resolved.
    """
    if not detected_plate:
        return None

    # 1. Exact match
    user = db.query(User).filter(User.plate_number == detected_plate).first()
    if user:
        return user

    # 2. OCR-confusion character-swap variants (O<->0, I<->1, ...)
    for variant in generate_ocr_correction_variants(detected_plate):
        user = db.query(User).filter(User.plate_number == variant).first()
        if user:
            return user

    # 3. Fuzzy (edit-distance) match against all known plates
    known_plates = get_all_plate_numbers(db)
    best_plate, _dist = best_fuzzy_match(detected_plate, known_plates)
    if best_plate:
        return db.query(User).filter(User.plate_number == best_plate).first()

    return None


def log_entry_attempt(db: Session, *, detected_plate, ocr_confidence,
                       matched_user, face_similarity, plate_matched,
                       face_matched, decision, reason, snapshot_path) -> EntryLog:
    entry = EntryLog(
        detected_plate=detected_plate,
        ocr_confidence=ocr_confidence,
        matched_user_name=matched_user.name if matched_user else None,
        face_similarity=face_similarity,
        plate_matched=plate_matched,
        face_matched=face_matched,
        decision=decision,
        reason=reason,
        snapshot_path=snapshot_path,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_recent_logs(db: Session, limit: int = 50) -> list[EntryLog]:
    return (
        db.query(EntryLog)
        .order_by(EntryLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def plate_exists(db: Session, plate_number: str) -> bool:
    return db.query(User).filter(User.plate_number == normalize_plate(plate_number)).first() is not None
