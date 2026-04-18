import os
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agent.graph import run_agent
from app.api.schemas import AgentRunRequest, SolveRequest
from app.config import settings
from shared_store import BASE64_STORE, run_counter, url_time

router = APIRouter(tags=["Agent"])


@router.post("/solve")
def solve(payload: SolveRequest, background_tasks: BackgroundTasks):
    if payload.secret != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    url_time.clear()
    BASE64_STORE.clear()
    run_counter["total"] += 1

    os.environ["url"] = payload.url
    os.environ["offset"] = "0"
    url_time[payload.url] = time.time()

    background_tasks.add_task(run_agent, payload.url)
    return {"status": "ok", "message": "Agent started.", "run_id": run_counter["total"]}


@router.post("/agent/run")
def run_agent_endpoint(payload: AgentRunRequest):
    if payload.secret != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    try:
        result = run_agent(payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    messages = result.get("messages", []) if isinstance(result, dict) else []
    if not messages:
        return {"status": "ok", "result": "No output"}

    last = messages[-1]
    content = getattr(last, "content", str(last))
    return {"status": "ok", "result": content}
