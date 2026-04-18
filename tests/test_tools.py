from app.ml.finance_features import classify_signal
from app.ml.risk_model import get_transaction_risk_model


def test_signal_classification_bullish():
    signal = classify_signal(ma_20=120, ma_50=100, rsi_14=62, momentum_10d=0.05)
    assert signal == "bullish"


def test_signal_classification_bearish():
    signal = classify_signal(ma_20=90, ma_50=110, rsi_14=35, momentum_10d=-0.08)
    assert signal == "bearish"


def test_signal_classification_boundaries_default_to_neutral():
    signal = classify_signal(ma_20=100, ma_50=100, rsi_14=55, momentum_10d=0)
    assert signal == "neutral"


def test_transaction_risk_model_outputs_expected_keys():
    model = get_transaction_risk_model()
    result = model.predict(
        {
            "amount": 1200,
            "balance": 4000,
            "transaction_count_24h": 8,
            "avg_amount_30d": 150,
            "chargeback_count_90d": 1,
            "device_change_count_30d": 1,
            "geo_distance_km": 220,
            "hour_of_day": 1,
        }
    )

    assert "anomaly_score" in result
    assert "risk_score" in result
    assert "label" in result
    assert "confidence" in result
