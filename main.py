from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent, TOOLS
from dotenv import load_dotenv
import uvicorn, os, time
from shared_store import url_time, BASE64_STORE, run_counter

load_dotenv()

SECRET = os.getenv("SECRET")

app = FastAPI(
    title="Autonomous Multi-Tool LLM Agent",
    description="A production-grade autonomous AI agent powered by Gemini 2.5 Flash and LangGraph.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()


# ── HEALTH CHECK ──────────────────────────────────────────────────────
@app.get("/healthz", tags=["Monitoring"])
def healthz():
    """Liveness probe for deployment health checks."""
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME)
    }


# ── LIVE STATUS ───────────────────────────────────────────────────────
@app.get("/status", tags=["Monitoring"])
def status():
    """Live agent telemetry — model, tools, run count, uptime."""
    return {
        "status": "running",
        "model": "gemini-2.5-flash",
        "tools_available": len(TOOLS),
        "tools": [t.name for t in TOOLS],
        "total_runs": run_counter["total"],
        "uptime_seconds": int(time.time() - START_TIME)
    }


# ── SOLVE ENDPOINT ────────────────────────────────────────────────────
@app.post("/solve", tags=["Agent"])
async def solve(request: Request, background_tasks: BackgroundTasks):
    """
    Trigger the autonomous agent on a task URL.
    Returns immediately with 200 OK; agent runs in background.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    url = data.get("url")
    secret = data.get("secret")

    if not url or not secret:
        raise HTTPException(status_code=400, detail="Both 'url' and 'secret' are required.")
    if secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    url_time.clear()
    BASE64_STORE.clear()
    run_counter["total"] += 1

    os.environ["url"] = url
    os.environ["offset"] = "0"
    url_time[url] = time.time()

    background_tasks.add_task(run_agent, url)

    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "Agent started.", "run_id": run_counter["total"]}
    )


# ── STOCK ANALYSIS ENDPOINT ───────────────────────────────────────────
@app.post("/analyze/stock", tags=["Finance"])
async def analyze_stock(request: Request):
    """
    Direct financial analysis — no task URL needed.
    Returns OHLCV summary, return %, volatility, RSI, and trend signal.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    secret = data.get("secret")
    if secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    ticker = data.get("ticker", "AAPL").upper()
    period = data.get("period", "3mo")

    try:
        from tools.stock_data import _analyze_stock_internal
        result = _analyze_stock_internal(ticker, period)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
