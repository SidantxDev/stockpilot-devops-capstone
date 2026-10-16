"""FastAPI entrypoint: health/readiness probes, metrics and the inventory API."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.config import settings
from app.database import get_db
from app.routes import products

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Inventory management API for the StockPilot DevSecOps capstone.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exposes http_requests_total, http_request_duration_seconds, etc. on /metrics.
Instrumentator(
    excluded_handlers=["/metrics", "/health", "/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(products.router)


@app.get("/", tags=["meta"])
def root():
    return {"service": settings.app_name, "version": __version__, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    """Liveness: the process is up. Deliberately does not touch the database."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only report READY when the database answers."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any DB failure means "not ready"
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "error": str(exc)[:200]})
    return {"status": "READY"}
