from fastapi import APIRouter, HTTPException

from app.api.schemas import FinanceAnalyzeRequest, RiskDetectRequest
from app.config import settings
from app.services.metrics import metrics_store
from app.tools.finance import analyze_finance_internal, detect_risk_internal

router = APIRouter(tags=["Finance"])


@router.post("/analyze/finance")
def analyze_finance(payload: FinanceAnalyzeRequest):
    if payload.secret != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    result = analyze_finance_internal(ticker=payload.ticker, period=payload.period, with_explanation=True)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    result["analysis_type"] = payload.analysis_type or "standard"
    return result


@router.post("/analyze/stock")
def analyze_stock_compat(payload: FinanceAnalyzeRequest):
    """Backward-compatible alias for /analyze/finance."""
    return analyze_finance(payload)


@router.post("/detect/risk")
def detect_risk(payload: RiskDetectRequest):
    if payload.secret != settings.secret:
        raise HTTPException(status_code=403, detail="Invalid secret.")

    metrics_store.inc("risk_analyses_completed")
    return detect_risk_internal(observation=payload.observation, with_explanation=True)
