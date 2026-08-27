"""
REST API routes.

  POST /api/register    - register a new user (name, plate, vehicle type, face image)
  POST /api/recognize    - run the full entry-check pipeline on one frame
  GET  /api/logs         - recent entry attempts
  GET  /api/users        - registered users (for the admin/debug view)
"""
import logging

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.config import UPLOADS_DIR, REGISTERED_FACES_DIR
from backend.database import get_db
from services import database_service, plate_ocr, face_engine, decision_engine
from utils.image_utils import bytes_to_bgr, save_snapshot
from utils.drawing import draw_box, draw_decision_banner, GREEN, RED

logger = logging.getLogger("routes")
router = APIRouter(prefix="/api")


@router.post("/register")
async def register_user(
    name: str = Form(...),
    plate_number: str = Form(...),
    vehicle_type: str = Form("Car"),
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if database_service.plate_exists(db, plate_number):
        raise HTTPException(status_code=409, detail=f"Plate '{plate_number}' is already registered.")

    image_bytes = await face_image.read()
    frame = bytes_to_bgr(image_bytes)

    face = face_engine.get_largest_face(frame)
    if face is None:
        raise HTTPException(status_code=422, detail="No face detected in the provided image. Try again with better lighting/framing.")

    saved_path = save_snapshot(frame, REGISTERED_FACES_DIR, prefix="face")

    user = database_service.create_user(
        db,
        name=name,
        vehicle_type=vehicle_type,
        plate_number=plate_number,
        embedding=face.embedding,
        face_image_path=saved_path,
    )

    logger.info("Registered user id=%s name=%s plate=%s", user.id, user.name, user.plate_number)
    return {
        "id": user.id,
        "name": user.name,
        "plate_number": user.plate_number,
        "vehicle_type": user.vehicle_type,
        "det_score": float(face.det_score),
    }


@router.post("/recognize")
async def recognize_entry(
    frame_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image_bytes = await frame_image.read()
    frame = bytes_to_bgr(image_bytes)
    annotated = frame.copy()

    # --- Step 1: plate detection + OCR ---
    plate_result = plate_ocr.read_plate(frame)
    detected_plate = plate_result["plate_number"]
    ocr_confidence = plate_result["confidence"]

    matched_user = database_service.find_user_by_plate(db, detected_plate) if detected_plate else None

    if plate_result["box"]:
        label = f"Plate: {plate_result['raw_text']} ({ocr_confidence:.2f})"
        draw_box(annotated, plate_result["box"], label, color=GREEN if matched_user else RED)

    # --- Step 2: face detection + similarity ---
    face_similarity = None
    detected_face = face_engine.get_largest_face(frame)

    if detected_face is not None and matched_user is not None:
        face_similarity = face_engine.cosine_similarity(
            detected_face.embedding, matched_user.get_embedding()
        )

    if detected_face is not None:
        label = f"Face sim: {face_similarity:.2f}" if face_similarity is not None else "Face detected"
        draw_box(annotated, detected_face.bbox, label,
                 color=GREEN if (face_similarity or 0) >= 0.45 else RED)

    # --- Step 3: decision ---
    result = decision_engine.decide(matched_user, face_similarity)
    draw_decision_banner(annotated, result.decision)
    snapshot_path = save_snapshot(annotated, UPLOADS_DIR, prefix="entry")

    database_service.log_entry_attempt(
        db,
        detected_plate=detected_plate,
        ocr_confidence=ocr_confidence,
        matched_user=matched_user,
        face_similarity=face_similarity,
        plate_matched=result.plate_matched,
        face_matched=result.face_matched,
        decision=result.decision,
        reason=result.reason,
        snapshot_path=snapshot_path,
    )

    return {
        "detected_plate": detected_plate,
        "raw_ocr_text": plate_result["raw_text"],
        "ocr_confidence": ocr_confidence,
        "plate_matched": result.plate_matched,
        "matched_user_name": matched_user.name if matched_user else None,
        "face_detected": detected_face is not None,
        "face_similarity": face_similarity,
        "face_matched": result.face_matched,
        "decision": result.decision,
        "reason": result.reason,
        "snapshot_path": snapshot_path,
    }


@router.get("/logs")
def list_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = database_service.get_recent_logs(db, limit=limit)
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "detected_plate": log.detected_plate,
            "ocr_confidence": log.ocr_confidence,
            "matched_user_name": log.matched_user_name,
            "face_similarity": log.face_similarity,
            "plate_matched": log.plate_matched,
            "face_matched": log.face_matched,
            "decision": log.decision,
            "reason": log.reason,
        }
        for log in logs
    ]


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = database_service.get_all_users(db)
    return [
        {
            "id": u.id,
            "name": u.name,
            "vehicle_type": u.vehicle_type,
            "plate_number": u.plate_number,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]
