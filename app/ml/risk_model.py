from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Expected anomaly proportions for transaction-like and market feature distributions.
TRANSACTION_CONTAMINATION = 0.08
MARKET_CONTAMINATION = 0.10
CONFIDENCE_SCALE = 2.0


class TransactionRiskModel:
    feature_names = [
        "amount",
        "balance",
        "transaction_count_24h",
        "avg_amount_30d",
        "chargeback_count_90d",
        "device_change_count_30d",
        "geo_distance_km",
        "hour_of_day",
    ]

    def __init__(self) -> None:
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            contamination=TRANSACTION_CONTAMINATION, random_state=42
        )
        self._is_fitted = False

    def _generate_baseline(self, n: int = 1200) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        return pd.DataFrame(
            {
                "amount": np.clip(rng.gamma(shape=2.2, scale=120.0, size=n), 1, None),
                "balance": np.clip(rng.normal(12000, 5000, size=n), 100, None),
                "transaction_count_24h": rng.integers(1, 18, size=n),
                "avg_amount_30d": np.clip(rng.gamma(shape=2.0, scale=100.0, size=n), 1, None),
                "chargeback_count_90d": rng.integers(0, 3, size=n),
                "device_change_count_30d": rng.integers(0, 3, size=n),
                "geo_distance_km": np.abs(rng.normal(12, 18, size=n)),
                "hour_of_day": rng.integers(6, 23, size=n),
            }
        )

    def ensure_fitted(self) -> None:
        if self._is_fitted:
            return
        baseline = self._generate_baseline()
        scaled = self.scaler.fit_transform(baseline[self.feature_names])
        self.model.fit(scaled)
        self._is_fitted = True

    def _to_frame(self, observation: dict) -> pd.DataFrame:
        default = {
            "amount": 100.0,
            "balance": 5000.0,
            "transaction_count_24h": 3.0,
            "avg_amount_30d": 120.0,
            "chargeback_count_90d": 0.0,
            "device_change_count_30d": 0.0,
            "geo_distance_km": 8.0,
            "hour_of_day": 13.0,
        }
        default.update(observation)

        frame = pd.DataFrame([{k: float(default[k]) for k in self.feature_names}])
        frame["hour_of_day"] = frame["hour_of_day"].clip(0, 23)
        return frame

    def predict(self, observation: dict) -> dict:
        self.ensure_fitted()
        frame = self._to_frame(observation)
        scaled = self.scaler.transform(frame[self.feature_names])

        raw_score = float(self.model.decision_function(scaled)[0])
        anomaly_score = float(-raw_score)

        risk_score = float(1.0 / (1.0 + np.exp(4.0 * raw_score)))
        if risk_score >= 0.75:
            label = "high_risk"
        elif risk_score >= 0.45:
            label = "moderate_risk"
        else:
            label = "low_risk"

        confidence = min(1.0, abs(anomaly_score) * CONFIDENCE_SCALE)

        return {
            "features_used": frame.iloc[0].to_dict(),
            "anomaly_score": round(anomaly_score, 6),
            "risk_score": round(risk_score, 6),
            "label": label,
            "confidence": round(confidence, 6),
            "model": "IsolationForest",
        }


def detect_market_anomaly(feature_frame: pd.DataFrame) -> dict:
    feature_cols = [
        "return_1d",
        "rolling_volatility_20d",
        "rsi_14",
        "momentum_10d",
        "drawdown",
    ]
    if feature_frame.empty or len(feature_frame) < 30:
        return {
            "anomaly_score": 0.0,
            "label": "insufficient_data",
            "confidence": 0.0,
            "model": "IsolationForest",
        }

    frame = feature_frame[feature_cols].dropna().copy()
    scaler = StandardScaler()
    scaled = scaler.fit_transform(frame)

    model = IsolationForest(contamination=MARKET_CONTAMINATION, random_state=42)
    model.fit(scaled)

    latest_scaled = scaled[-1].reshape(1, -1)
    raw_score = float(model.decision_function(latest_scaled)[0])
    anomaly_score = float(-raw_score)
    risk_score = float(1.0 / (1.0 + np.exp(4.0 * raw_score)))

    if risk_score >= 0.75:
        label = "high_risk"
    elif risk_score >= 0.45:
        label = "moderate_risk"
    else:
        label = "low_risk"

    confidence = min(1.0, abs(anomaly_score) * CONFIDENCE_SCALE)

    return {
        "anomaly_score": round(anomaly_score, 6),
        "risk_score": round(risk_score, 6),
        "label": label,
        "confidence": round(confidence, 6),
        "model": "IsolationForest",
    }


_transaction_risk_model = TransactionRiskModel()


def get_transaction_risk_model() -> TransactionRiskModel:
    return _transaction_risk_model
