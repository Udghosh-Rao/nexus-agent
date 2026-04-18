import time

from fastapi import APIRouter

from app.config import settings
from app.services.metrics import metrics_store
from app.tools import ALL_PRIMARY_TOOLS

router = APIRouter(tags=["Monitoring"])
START_TIME = time.time()


@router.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_seconds": int(time.time() - START_TIME)}


@router.get("/status")
def status():
    snapshot = metrics_store.snapshot()
    return {
        "status": "running",
        "model": settings.groq_model,
        "tools_available": len(ALL_PRIMARY_TOOLS),
        "tools": [t.name for t in ALL_PRIMARY_TOOLS],
        "uptime_seconds": int(time.time() - START_TIME),
        "counters": snapshot["counters"],
    }


@router.get("/metrics")
def metrics():
    return metrics_store.snapshot()
