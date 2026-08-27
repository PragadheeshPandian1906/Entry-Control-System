# Testing Guide — Demo Scenarios & Test Cases

This system was built around the exact demo you described: your **laptop
webcam** captures both **your face** and **a phone screen showing a vehicle
image with a visible plate**, in a single frame. Frame both in view of the
webcam before clicking "Capture & Check Entry".

## Framing tips
- Hold the phone at chest height, screen facing the webcam, plate text
  large and in focus (fill at least ~150px width in a 720p frame).
- Keep your face in the same shot, reasonably lit, looking toward the camera.
- Avoid glare on the phone screen — tilt slightly if you see a reflection.

---

## Setup before testing

1. Run the app (`python run.py`), open http://localhost:8000
2. Go to **Register User** tab, capture your face, and register:
   - Name: `Pragadheesh`
   - Vehicle Type: `Car`
   - Plate Number: `TN09AB1234`

---

## Scenario 1 — Registered User (expect ACCESS GRANTED)

**Input:** Display `TN09AB1234` on your phone (a plain text/image of a
Toyota with that plate works well) and stand in frame as `Pragadheesh`.

**Expected output:**
```
✓ Plate Detected: TN09AB1234
✓ Face Recognized
✓ Database Match
🟢 ACCESS GRANTED
```

**What to check:** `plate_matched: true`, `face_matched: true`,
`matched_user_name: "Pragadheesh"`.

---

## Scenario 2 — Unknown Vehicle (expect SECURITY VERIFICATION REQUIRED)

**Input:** Display a plate that was never registered, e.g. `TN11XY9999`,
with anyone's face in frame.

**Expected output:**
```
Plate Found: TN11XY9999
Database: Not Found
🔴 SECURITY VERIFICATION REQUIRED
```

**What to check:** `plate_matched: false`, `reason: "Plate not found in
database — unknown vehicle."`

---

## Scenario 3 — Plate Belongs to Someone Else (expect SECURITY VERIFICATION REQUIRED)

**Input:** Display the registered plate `TN09AB1234`, but have a
**different person** (or yourself wearing a mask/sunglasses that
significantly changes your face) stand in frame instead of the registered
owner.

**Expected output:**
```
Plate Match ✓
Face Match ✗
Possible Unauthorized Driver
🔴 SECURITY VERIFICATION REQUIRED
```

**What to check:** `plate_matched: true`, `face_matched: false`,
`face_similarity` noticeably below `0.45`.

---

## Scenario 4 — OCR Error Handling (expect ACCESS GRANTED via fuzzy match)

**Input:** Display the plate slightly tilted, partially covered by a
finger, or with screen glare so PaddleOCR misreads 1–2 characters (e.g.
reads `TN09AB12I4` instead of `TN09AB1234`), with the registered face in frame.

**Expected behavior:** The system tries the raw OCR text, then common
OCR-confusion swaps (`O↔0`, `I↔1`, `S↔5`, etc. — see
`backend/config.OCR_CHAR_CORRECTIONS`), then an edit-distance fuzzy match
(up to 2 characters off) against all registered plates
(`services/plate_validator.best_fuzzy_match`). If it recovers the correct
plate, the flow continues to face matching as normal.

**What to check:** Even with a slightly garbled `raw_ocr_text`, the
returned `detected_plate` should resolve to `TN09AB1234` and
`matched_user_name` should be populated, so long as the misread is within
2 character edits.

> If the OCR error is too severe (more than 2 characters off, or the text
> region isn't detected at all), the system correctly falls through to
> Scenario 2's "unknown vehicle" behavior — this is expected, not a bug.

---

## Checking the audit trail

After running through the scenarios, open the **Entry Logs** tab (or
`GET /api/logs`) — every attempt should be listed with its timestamp,
detected plate, OCR confidence, matched driver, face similarity, and
final decision.

## API reference for manual/automated testing

```
POST /api/register
  form-data: name, plate_number, vehicle_type, face_image (file)

POST /api/recognize
  form-data: frame_image (file)
  -> { detected_plate, raw_ocr_text, ocr_confidence, plate_matched,
       matched_user_name, face_detected, face_similarity, face_matched,
       decision, reason, snapshot_path }

GET /api/logs?limit=50
GET /api/users
GET /health
```

You can exercise `/api/recognize` directly with curl for quick checks:
```bash
curl -X POST http://localhost:8000/api/recognize \
  -F "frame_image=@/path/to/test_frame.jpg"
```
