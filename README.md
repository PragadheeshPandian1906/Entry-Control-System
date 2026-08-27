# AI Smart Entry Control System — Setup Guide

A working prototype vehicle-entry system: it reads a license plate from a
camera frame, recognizes the driver's face, and grants/denies entry based
on whether *both* match a registered user.

> See **TESTING.md** for the demo scenarios and what inputs to try.

---

## 1. Requirements

- Python **3.11+**
- A webcam (built-in laptop cam is fine)
- ~2–3 GB free disk space (for OCR + face-recognition model downloads)
- Internet connection for the **first run only** (PaddleOCR and
  InsightFace auto-download their model weights the first time each is used)

---

## 2. Install

```bash
# From the project root
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> **Windows note:** if `paddlepaddle` fails to install, grab the CPU wheel
> directly from https://www.paddlepaddle.org.cn/en/install/quick and follow
> their pip command for your Python version, then re-run
> `pip install -r requirements.txt`.

> **Apple Silicon (M1/M2/M3) note:** `onnxruntime` and `paddlepaddle` both
> ship arm64 wheels on PyPI, so a plain `pip install -r requirements.txt`
> should work. If you hit build errors, install `onnxruntime-silicon`
> instead of `onnxruntime`.

---

## 3. Run it

```bash
python run.py
```

You should see log lines ending with something like:

```
INFO | app | Database initialized. Server starting up.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open **http://localhost:8000** in your browser. Allow camera access when prompted.

The first time you hit **Register** or **Capture & Check Entry**, PaddleOCR
and InsightFace will download their model files (a few hundred MB total) —
this only happens once and is cached locally after that.

---

## 4. Using the dashboard

### Register a user (do this first)
1. Go to the **Register User** tab.
2. Allow camera access, frame your face clearly, click **Capture Face**.
3. Fill in **Name**, **Vehicle Type**, and **Plate Number** (e.g. `TN09AB1234`
   — spacing/case doesn't matter, it gets normalized automatically).
4. Click **Register User**.

### Check an entry
1. Go to the **Live Entry Check** tab.
2. Hold up your phone showing a picture of the registered plate, with your
   face also visible in the same webcam frame (see TESTING.md for exact
   framing tips).
3. Click **Capture & Check Entry**. The dashboard shows:
   - Detected plate + OCR confidence
   - Whether the plate matched a registered user
   - Face similarity score + whether it matched
   - Final decision: 🟢 **ACCESS GRANTED** or 🔴 **SECURITY VERIFICATION REQUIRED**

### View logs
The **Entry Logs** tab lists every attempt (plate, OCR confidence, matched
driver, face similarity, decision) — this is your EntryLogs audit trail.

---

## 5. Project structure

```
AI-Entry-System/
  backend/
    app.py            FastAPI app, startup, dashboard route
    config.py          All thresholds & paths in one place
    database.py        SQLAlchemy engine/session
    models.py           User, EntryLog ORM models
    routes.py          /api/register, /api/recognize, /api/logs, /api/users
  services/
    plate_ocr.py        PaddleOCR full-frame plate reading (default path)
    plate_detector.py   Optional YOLO plate detector (off by default)
    plate_validator.py  Plate normalization + OCR-error-tolerant fuzzy matching
    face_engine.py      InsightFace detection + embedding + cosine similarity
    decision_engine.py  Pure ACCESS_GRANTED / SECURITY_VERIFICATION logic
    database_service.py CRUD + plate lookup (exact -> OCR-correction -> fuzzy)
    logger_service.py   Logging setup (writes to logs/app.log)
  utils/
    image_utils.py      bytes/base64 <-> OpenCV frame conversions, snapshot saving
    drawing.py           Bounding-box + decision-banner overlays for saved snapshots
  templates/index.html  Dashboard UI (3 tabs: Entry Check / Register / Logs)
  static/                CSS + vanilla JS (webcam capture, fetch calls)
  database/entry.db     SQLite DB (auto-created on first run)
  uploads/               Saved annotated entry-attempt snapshots
  registered_faces/      Saved registration face images
  logs/app.log           Application log file
  run.py                 Launcher (python run.py)
```

---

## 6. How the plate detection works (important design note)

Rather than requiring you to source or train a custom YOLO license-plate
model (which most student setups don't have on hand), this prototype's
**default mode** runs PaddleOCR's own text detector across the *whole*
frame, then keeps whichever detected text box is shaped like a plate
(`services/plate_ocr.py` + `services/plate_validator.py`). This means the
system is fully functional right after `pip install`, with zero extra
weight files to hunt down.

If you *do* have a trained YOLO plate-detector `.pt` file, drop it at
`models/plate_detector.pt` and set the environment variable
`USE_YOLO_PLATE_DETECTOR=true` before running — the pipeline will crop to
that box first and OCR only the crop (faster, more precise).

---

## 7. Configuration

All tunables live in `backend/config.py` (or override via environment
variables of the same name where noted):

| Setting | Default | Meaning |
|---|---|---|
| `FACE_SIMILARITY_THRESHOLD` | 0.45 | Minimum cosine similarity to count as a face match |
| `OCR_MIN_CONFIDENCE` | 0.35 | Minimum PaddleOCR confidence to trust a text box |
| `PLATE_FUZZY_MAX_EDITS` | 2 | Allowed character edit-distance for OCR-error-tolerant plate lookup |
| `USE_YOLO_PLATE_DETECTOR` | false | Enable the optional YOLO crop-first stage |
| `HOST` / `PORT` | 0.0.0.0 / 8000 | Server bind address |

---

## 8. Troubleshooting

- **"Could not access webcam"** — check browser camera permissions; on
  some systems Chrome requires `localhost` (not `127.0.0.1`) for camera
  access, which is what this app already uses.
- **No face detected on registration** — make sure your face is
  well-lit, centered, and not too small in frame; try moving closer.
- **PaddleOCR/InsightFace download stalls** — they pull model weights
  from their respective CDNs on first use; if you're behind a restrictive
  network, run once on an unrestricted connection first, or manually
  pre-download per each library's docs.
- **`no such table` SQLite errors** — delete `database/entry.db` and
  restart; it's recreated automatically on startup.
