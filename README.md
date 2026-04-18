# Autonomous AI Quant Research & Risk Analysis Agent

A production-oriented LangGraph + FastAPI system for **financial analytics**, **ML-based anomaly/risk detection**, and **Groq-grounded explanation**.

## Positioning

This project is designed to signal:
- **AI Engineering:** autonomous tool orchestration with LangGraph
- **Data Science / ML:** feature engineering + Isolation Forest inference
- **LLM Systems:** Groq-powered interpretation constrained by computed outputs
- **Finance / Quant:** technical indicators, trend analysis, drawdown, support/resistance approximations
- **Backend Engineering:** structured APIs, monitoring endpoints, and deployment-ready configuration

## Problem It Solves

Many LLM demos generate ungrounded financial commentary. This repository uses a safer pattern:

1. Compute market and risk signals from real data/features
2. Run ML/statistical analysis first
3. Use Groq to explain **computed outputs**, not fabricate them

## Core Capabilities

- LangGraph autonomous agent with task routing (`finance`, `general`, `unsupported`)
- Finance analytics pipeline:
  - returns
  - rolling volatility
  - moving averages (20/50)
  - RSI(14)
  - momentum
  - drawdown
  - support/resistance approximation
  - trend + signal classification (`bullish`/`bearish`/`neutral`)
- ML layer:
  - Isolation Forest for market anomaly/risk scoring
  - Isolation Forest for transaction-like risk detection
  - outputs: anomaly score, risk score, label, confidence
- Groq explanation layer grounded in computed metrics
- FastAPI domain endpoints (`/analyze/finance`, `/detect/risk`, `/metrics`)
- Legacy multi-tool support retained for web/code/ocr/audio/file workflows

## Architecture Overview

```text
FastAPI
 ├─ /analyze/finance ──> feature engineering ──> ML scoring ──> Groq explanation
 ├─ /detect/risk    ──> structured features  ──> ML scoring ──> Groq explanation
 ├─ /agent/run      ──> LangGraph classify ──> finance/general tool routing
 └─ /metrics,/status,/healthz

LangGraph
 START -> classify -> (finance_agent | general_agent | unsupported)
 finance_agent <-> finance_tools
 general_agent <-> general_tools
```

## Example Use Cases

### 1) Quant-style market analysis
Input ticker + period and get:
- indicator snapshot
- trend/signal summary
- ML risk/anomaly estimate
- concise narrative explanation

### 2) Transaction-like risk detection
Input structured observation and get:
- anomaly score
- risk score
- risk label + confidence
- grounded explanation

## API Reference

### `POST /analyze/finance`
Request:
```json
{
  "ticker": "AAPL",
  "period": "6mo",
  "analysis_type": "standard",
  "secret": "your-secret"
}
```

Response includes:
- `price_summary`
- `indicators`
- `trend_summary`
- `signal`
- `ml_prediction`
- `explanation`

### `POST /detect/risk`
Request:
```json
{
  "observation": {
    "amount": 3200,
    "balance": 7000,
    "transaction_count_24h": 14,
    "avg_amount_30d": 220,
    "chargeback_count_90d": 2,
    "device_change_count_30d": 1,
    "geo_distance_km": 950,
    "hour_of_day": 2
  },
  "secret": "your-secret"
}
```

Response includes:
- `anomaly_score`
- `risk_score`
- `label`
- `confidence`
- `explanation`

### `POST /agent/run`
Runs LangGraph task routing on prompt-style input.

### `POST /solve`
Retained for URL/task-runner style autonomous workflows.

### `GET /healthz`
Service liveness.

### `GET /status`
Runtime status, configured model, tool inventory, counters.

### `GET /metrics`
Lightweight observability snapshot (counters + latency summaries).

## Metrics & Observability

Tracked metrics include:
- API total/failed runs
- total agent runs
- finance analyses completed
- ML inference count
- tool invocation counters
- route-level latency summaries (avg/p95)

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Set required variables in `.env`:
- `GROQ_API_KEY`
- `SECRET`
- optional `GROQ_MODEL`, `RECURSION_LIMIT`, `MAX_TOKENS`

Run server:
```bash
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

## Deployment Notes (including Hugging Face Spaces)

- Fully environment-variable driven config
- Works as a standard ASGI app (`main:app`)
- For Hugging Face Spaces (Docker/Gradio-less backend style), expose port `7860` and set env vars in Space secrets
- Optional: add a thin Gradio UI later; backend APIs are already deployment-ready

## Limitations

- Market anomaly model is unsupervised and should not be treated as investment advice
- Transaction-risk baseline uses synthetic normal profile initialization unless replaced with domain data
- LLM explanations depend on `GROQ_API_KEY`; fallback explanation is deterministic when key is absent

## Future Work

- Train risk models on domain datasets and persist calibrated artifacts
- Add backtesting/evaluation pipeline for finance signals
- Add authentication/authorization beyond shared secret
- Add OpenTelemetry/Prometheus exporters for production monitoring
