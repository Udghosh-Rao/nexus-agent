from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def load_ohlcv(ticker: str, period: str = "6mo") -> pd.DataFrame:
    df = yf.download(ticker, period=period, progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    if df.empty:
        return df

    required = ["Open", "High", "Low", "Close", "Volume"]
    available = [c for c in required if c in df.columns]
    return df[available].dropna()


def build_finance_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    frame = df.copy()
    frame["return_1d"] = close.pct_change()
    frame["rolling_volatility_20d"] = frame["return_1d"].rolling(20).std() * np.sqrt(252)
    frame["ma_20"] = close.rolling(20).mean()
    frame["ma_50"] = close.rolling(50).mean()
    frame["rsi_14"] = _rsi(close)
    frame["momentum_10d"] = close / close.shift(10) - 1
    frame["drawdown"] = close / close.cummax() - 1
    frame["support_20d"] = low.rolling(20).min()
    frame["resistance_20d"] = high.rolling(20).max()

    return frame.dropna().copy()


def classify_signal(ma_20: float, ma_50: float, rsi_14: float, momentum_10d: float) -> str:
    if ma_20 > ma_50 and rsi_14 >= 55 and momentum_10d > 0:
        return "bullish"
    if ma_20 < ma_50 and rsi_14 <= 45 and momentum_10d < 0:
        return "bearish"
    return "neutral"


def summarize_finance_features(ticker: str, period: str = "6mo") -> dict:
    df = load_ohlcv(ticker=ticker, period=period)
    if df.empty:
        return {"error": f"No data found for ticker '{ticker}'."}

    features = build_finance_feature_frame(df)
    if features.empty:
        return {"error": "Not enough data points to compute rolling indicators."}

    last = features.iloc[-1]
    close = df["Close"].astype(float)

    period_return = (float(close.iloc[-1]) / float(close.iloc[0])) - 1
    trend_summary = "uptrend" if last["ma_20"] > last["ma_50"] else "downtrend"
    signal = classify_signal(
        ma_20=float(last["ma_20"]),
        ma_50=float(last["ma_50"]),
        rsi_14=float(last["rsi_14"]),
        momentum_10d=float(last["momentum_10d"]),
    )

    return {
        "ticker": ticker.upper(),
        "period": period,
        "price_summary": {
            "current_price": round(float(close.iloc[-1]), 4),
            "period_return": round(float(period_return), 6),
            "data_points": int(len(df)),
        },
        "indicators": {
            "return_1d": round(float(last["return_1d"]), 6),
            "rolling_volatility_20d": round(float(last["rolling_volatility_20d"]), 6),
            "ma_20": round(float(last["ma_20"]), 4),
            "ma_50": round(float(last["ma_50"]), 4),
            "rsi_14": round(float(last["rsi_14"]), 4),
            "momentum_10d": round(float(last["momentum_10d"]), 6),
            "drawdown": round(float(last["drawdown"]), 6),
            "support_20d": round(float(last["support_20d"]), 4),
            "resistance_20d": round(float(last["resistance_20d"]), 4),
        },
        "trend_summary": trend_summary,
        "signal": signal,
        "feature_frame": features,
        "recent_ohlcv": df.tail(5).round(4).to_dict(orient="records"),
    }
