import time
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes_agent import router as agent_router
from app.api.routes_finance import router as finance_router
from app.api.routes_monitoring import router as monitoring_router
from app.config import settings
from app.services.metrics import metrics_store

app = FastAPI(
    title=settings.app_name,
    description=(
        "Autonomous AI Quant Research & Risk Analysis Agent with LangGraph orchestration, "
        "financial indicators, ML anomaly detection, and Groq-based explanation."
    ),
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    route = request.url.path
    start = time.perf_counter()
    metrics_store.inc("api_total_runs")
    
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            metrics_store.inc("api_failed_runs")
        return response
    except Exception:
        metrics_store.inc("api_failed_runs")
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics_store.observe_latency(route, elapsed_ms)

# API Routers
app.include_router(agent_router)
app.include_router(finance_router)
app.include_router(monitoring_router)

# UI Routes
static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    # Fallback to relative path if cwd is not root
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Nexus Agent API is running. UI index.html not found.",
        "debug": {
            "static_dir": static_dir,
            "exists": os.path.exists(static_dir),
            "cwd": os.getcwd(),
            "file": __file__
        }
    }
