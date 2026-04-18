import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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


app.include_router(agent_router)
app.include_router(finance_router)
app.include_router(monitoring_router)
