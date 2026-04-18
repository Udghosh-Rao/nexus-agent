from typing import Optional

from langchain_core.tools import tool

from app.tools.finance import analyze_finance_internal


def _analyze_stock_internal(ticker: str, period: str = "6mo") -> dict:
    result = analyze_finance_internal(ticker=ticker, period=period, with_explanation=False)
    if "error" in result:
        return result

    indicators = result.get("indicators", {})
    price_summary = result.get("price_summary", {})

    return {
        "ticker": result.get("ticker"),
        "period": result.get("period"),
        "current_price": price_summary.get("current_price"),
        "return_pct": round(float(price_summary.get("period_return", 0)) * 100, 4),
        "volatility_pct": round(float(indicators.get("rolling_volatility_20d", 0)) * 100, 4),
        "rsi": indicators.get("rsi_14"),
        "momentum": indicators.get("momentum_10d"),
        "drawdown": indicators.get("drawdown"),
        "trend": result.get("trend_summary"),
        "signal": result.get("signal"),
        "support": indicators.get("support_20d"),
        "resistance": indicators.get("resistance_20d"),
        "ml_prediction": result.get("ml_prediction"),
        "data_points": price_summary.get("data_points"),
        "recent_ohlcv": result.get("recent_ohlcv", []),
    }


@tool
def get_stock_data(ticker: str, period: Optional[str] = "6mo") -> dict:
    """Backward-compatible stock analysis tool built on the upgraded finance pipeline."""
    return _analyze_stock_internal(ticker=ticker, period=period or "6mo")
