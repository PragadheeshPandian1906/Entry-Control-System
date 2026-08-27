"""
Pure decision logic — no I/O, easy to unit test.

Given the plate lookup result and the face similarity score, decides
ACCESS_GRANTED vs SECURITY_VERIFICATION_REQUIRED, with a human-readable reason.
"""
from dataclasses import dataclass
from typing import Optional

from backend.config import FACE_SIMILARITY_THRESHOLD

ACCESS_GRANTED = "ACCESS_GRANTED"
SECURITY_VERIFICATION_REQUIRED = "SECURITY_VERIFICATION_REQUIRED"


@dataclass
class DecisionResult:
    decision: str
    reason: str
    plate_matched: bool
    face_matched: bool


def decide(
    plate_found_user: Optional[object],  # a User ORM instance, or None
    face_similarity: Optional[float],
) -> DecisionResult:
    if plate_found_user is None:
        return DecisionResult(
            decision=SECURITY_VERIFICATION_REQUIRED,
            reason="Plate not found in database — unknown vehicle.",
            plate_matched=False,
            face_matched=False,
        )

    face_matched = bool(face_similarity is not None and face_similarity >= FACE_SIMILARITY_THRESHOLD)

    if face_matched:
        return DecisionResult(
            decision=ACCESS_GRANTED,
            reason="Plate and registered face both matched.",
            plate_matched=True,
            face_matched=True,
        )

    if face_similarity is None:
        reason = "Plate matched, but no face was detected in the frame."
    else:
        reason = "Plate matched, but the face does not match the registered owner (possible unauthorized driver)."

    return DecisionResult(
        decision=SECURITY_VERIFICATION_REQUIRED,
        reason=reason,
        plate_matched=True,
        face_matched=False,
    )
