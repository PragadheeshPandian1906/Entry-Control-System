"""
FastAPI application entrypoint for the AI Smart Entry Control System.

Run with:  python run.py
(or)       uvicorn backend.app:app --host 0.0.0.0 --port 8000
"""
import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from backend.config import BASE_DIR
from backend.database import init_db
from backend.routes import router as api_router
from services.logger_service import setup_logging

setup_logging()
logger = logging.getLogger("app")

app = FastAPI(title="AI Smart Entry Control System", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized. Server starting up.")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
def health():
    return {"status": "ok"}
