from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from app.ml.finance_features import summarize_finance_features
from app.ml.risk_model import detect_market_anomaly, get_transaction_risk_model
from app.services.groq_client import explain_metrics
from app.services.metrics import metrics_store


def analyze_finance_internal(ticker: str, period: str = "6mo", with_explanation: bool = True) -> dict:
    metrics_store.inc("finance_analyses_completed")
    summary = summarize_finance_features(ticker=ticker, period=period)
    if "error" in summary:
        return summary

    market_ml = detect_market_anomaly(summary["feature_frame"])
    summary.pop("feature_frame", None)

    result = {
        **summary,
        "ml_prediction": market_ml,
    }

    if with_explanation:
        explanation = explain_metrics(
            "finance_analysis",
            {
                "ticker": result["ticker"],
                "period": result["period"],
                "price_summary": result["price_summary"],
                "indicators": result["indicators"],
                "trend_summary": result["trend_summary"],
                "signal": result["signal"],
                "ml_prediction": result["ml_prediction"],
            },
        )
        result["explanation"] = explanation

    return result


def detect_risk_internal(observation: dict, with_explanation: bool = True) -> dict:
    metrics_store.inc("ml_inference_count")
    model = get_transaction_risk_model()
    result = model.predict(observation)

    if with_explanation:
        explanation = explain_metrics(
            "transaction_risk_detection",
            {
                "features_used": result["features_used"],
                "anomaly_score": result["anomaly_score"],
                "risk_score": result["risk_score"],
                "label": result["label"],
                "confidence": result["confidence"],
            },
        )
        result["explanation"] = explanation

    return result


@tool
def analyze_finance(ticker: str, period: Optional[str] = "6mo") -> dict:
    """Analyze financial market data and compute indicators + ML anomaly/risk outputs."""
    metrics_store.inc("tool_calls.analyze_finance")
    return analyze_finance_internal(ticker=ticker, period=period or "6mo", with_explanation=True)


@tool
def detect_risk(observation: dict) -> dict:
    """Detect anomaly/risk on transaction-like structured financial observations."""
    metrics_store.inc("tool_calls.detect_risk")
    return detect_risk_internal(observation=observation, with_explanation=True)
