# Nexus Agent

> **Autonomous AI Quant Research & Risk Analysis Agent**  
> LangGraph-orchestrated autonomous agent with financial analytics, ML-based anomaly detection, and Groq-grounded explanations.

---

## Overview

Nexus Agent is a production-oriented system that combines **LangGraph** for autonomous task routing, **FastAPI** for structured REST endpoints, **Isolation Forest** ML models for anomaly and risk scoring, and **Groq (LLaMA 3.3-70B)** for grounded, hallucination-resistant narrative explanations.

The core design philosophy: _compute first, explain second_. Rather than letting an LLM fabricate financial commentary, all indicators and risk scores are computed deterministically from real data before being passed to the model for interpretation.

---

## Architecture

```
FastAPI
 ├─ /analyze/finance ──▶ feature engineering ──▶ ML scoring ──▶ Groq explanation
 ├─ /detect/risk     ──▶ structured features  ──▶ ML scoring ──▶ Groq explanation
 ├─ /agent/run       ──▶ LangGraph classify   ──▶ finance / general tool routing
 └─ /metrics, /status, /healthz

LangGraph Graph
 START ──▶ classify ──▶ finance_agent ◀──▶ finance_tools
                   └──▶ general_agent ◀──▶ general_tools
                   └──▶ unsupported   ──▶ END
```

### Key Components

| Layer | Technology | Role |
|---|---|---|
| Agent Orchestration | LangGraph + LangChain | Task classification and tool routing |
| LLM Backend | Groq (`llama-3.3-70b-versatile`) | Explanation of computed outputs |
| Finance Features | yfinance + pandas/numpy | OHLCV ingestion & indicator engineering |
| ML Risk Models | scikit-learn `IsolationForest` | Anomaly and risk scoring |
| API | FastAPI + uvicorn | REST endpoints and observability |
| UI | Static HTML | Frontend served at `/` |

---

## Features

### Finance Analytics Pipeline
- Daily returns, rolling 20-day annualised volatility
- Moving averages: MA-20 and MA-50
- RSI(14) via exponential weighted smoothing
- 10-day momentum, maximum drawdown
- 20-day support & resistance approximation
- Signal classification: `bullish` / `bearish` / `neutral`

### ML Risk Detection
- **Market anomaly model** — Isolation Forest on `return_1d`, `rolling_volatility_20d`, `rsi_14`, `momentum_10d`, `drawdown`
- **Transaction risk model** — Isolation Forest on 8 structured features (amount, balance, geo distance, etc.)
- Outputs: anomaly score, risk score (sigmoid-calibrated), label (`low_risk` / `moderate_risk` / `high_risk`), confidence

### LangGraph Agent Tools

**Finance tools** — triggered by keywords like `stock`, `ticker`, `rsi`, `volatility`, `risk`, `portfolio`:
- `get_stock_data` — full indicator snapshot via the finance pipeline

**General tools** — triggered by keywords like `http`, `web`, `scrape`, `code`, `ocr`, `audio`:
- `get_rendered_html` — Playwright-based JS-rendered page scraper
- `run_code` — sandboxed Python code execution
- `post_request` — outbound HTTP POST
- `download_file` — file download utility
- `add_dependencies` — runtime pip install
- `ocr_image_tool` — Tesseract OCR on images
- `transcribe_audio` — SpeechRecognition audio transcription
- `encode_image_to_base64` — image encoding helper

---

## API Reference

### `POST /analyze/finance`
Run the full quant analytics pipeline on a ticker.

```json
// Request
{
  "ticker": "AAPL",
  "period": "6mo",
  "analysis_type": "standard",
  "secret": "your-secret"
}

// Response fields
{
  "ticker", "period",
  "price_summary": { "current_price", "period_return", "data_points" },
  "indicators": { "return_1d", "rolling_volatility_20d", "ma_20", "ma_50",
                  "rsi_14", "momentum_10d", "drawdown", "support_20d", "resistance_20d" },
  "trend_summary",  // "uptrend" | "downtrend"
  "signal",         // "bullish" | "bearish" | "neutral"
  "ml_prediction":  { "anomaly_score", "risk_score", "label", "confidence" },
  "explanation":    { "summary", "rationale", "source" }
}
```

### `POST /detect/risk`
Score a transaction-like observation against the risk model.

```json
// Request
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

// Response fields
{ "anomaly_score", "risk_score", "label", "confidence", "explanation" }
```

### `POST /agent/run`
Send a free-form prompt to the LangGraph agent for autonomous tool routing.

```json
{ "prompt": "Analyze TSLA stock for the last 3 months", "secret": "your-secret" }
```

### `POST /solve`
Legacy URL-based autonomous task trigger (background execution).

### `GET /healthz`
Service liveness check.

### `GET /status`
Runtime status: model name, tool inventory, request counters.

### `GET /metrics`
Lightweight observability: per-route latency (avg/p95), counters for API runs, agent runs, ML inferences, and tool invocations.

---

## Setup

### Prerequisites
- Python 3.11+
- A [Groq API key](https://console.groq.com)

### Installation

```bash
git clone <repo-url>
cd nexus-agent-main

pip install -r requirements.txt
playwright install chromium

cp .env.example .env
# Edit .env and fill in your values
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes | — | Groq API key for LLM calls |
| `SECRET` | Yes | — | Shared secret for endpoint auth |
| `EMAIL` | No | — | Optional agent identity |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `RECURSION_LIMIT` | No | `300` | LangGraph recursion cap |
| `MAX_TOKENS` | No | `24000` | Token budget for message trimming |

### Running Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

The API and UI will be available at `http://localhost:7860`.

---

## Docker

```bash
# Build
docker build -t nexus-agent .

# Run
docker run -p 7860:7860 \
  -e GROQ_API_KEY=your_key \
  -e SECRET=your_secret \
  nexus-agent
```

The Dockerfile installs Tesseract OCR, ffmpeg, and Playwright Chromium automatically.

---

## Deployment on Hugging Face Spaces

1. Push the repo to a HF Space configured as **Docker** SDK.
2. Set `GROQ_API_KEY` and `SECRET` as Space secrets.
3. The app binds to port `7860` by default — no additional configuration needed.

---

## Project Structure

```
nexus-agent-main/
├── main.py                        # ASGI entry point
├── requirements.txt
├── Dockerfile
├── shared_store.py                # Global shared state (url_time, BASE64_STORE)
├── .env.example
│
├── app/
│   ├── agent/
│   │   └── graph.py               # LangGraph state graph & run_agent()
│   ├── api/
│   │   ├── app.py                 # FastAPI app, middleware, router registration
│   │   ├── routes_agent.py        # /solve and /agent/run endpoints
│   │   ├── routes_finance.py      # /analyze/finance and /detect/risk endpoints
│   │   ├── routes_monitoring.py   # /healthz, /status, /metrics endpoints
│   │   └── schemas.py             # Pydantic request/response models
│   ├── config.py                  # Settings loaded from environment
│   ├── ml/
│   │   ├── finance_features.py    # OHLCV loading, indicator engineering, signal classification
│   │   └── risk_model.py          # TransactionRiskModel + detect_market_anomaly()
│   ├── services/
│   │   ├── groq_client.py         # ChatGroq initialisation + explain_metrics()
│   │   └── metrics.py             # In-memory metrics store
│   ├── tools/
│   │   ├── finance.py             # Finance tool wrappers (LangChain @tool)
│   │   └── general.py             # General tool list
│   └── utils/
│       └── logging.py             # Logger factory
│
├── tools/                         # Standalone general-purpose tools
│   ├── web_scraper.py             # Playwright-based HTML scraper
│   ├── run_code.py                # Sandboxed code execution
│   ├── send_request.py            # HTTP POST helper
│   ├── download_file.py           # File downloader
│   ├── add_dependencies.py        # Runtime pip install
│   ├── image_content_extracter.py # OCR via Tesseract
│   ├── audio_transcribing.py      # Audio transcription
│   ├── encode_image_to_base64.py  # Image encoder
│   └── stock_data.py              # get_stock_data @tool (LangChain-compatible)
│
├── static/
│   └── index.html                 # Frontend UI
│
└── tests/
    ├── conftest.py
    └── test_tools.py
```

---

## Observability

Nexus Agent ships with a lightweight in-process metrics layer:

- `api_total_runs` / `api_failed_runs` — HTTP middleware counters
- `total_runs` / `failed_runs` — agent-level counters
- `agent.finance_routed` / `agent.general_routed` / `agent.unsupported_routed`
- `ml_inference_count`
- Per-route latency histograms (avg + p95) via `metrics_store.observe_latency()`

Access at `GET /metrics`.

---

## Limitations

- Market anomaly model is **unsupervised** — do not treat outputs as investment advice.
- Transaction risk model is initialized with a synthetic baseline; replace with domain data for production use.
- LLM explanations require a valid `GROQ_API_KEY`; a deterministic fallback is returned when the key is absent or the call fails.
- Auth is based on a single shared secret — add proper auth for multi-user deployments.

---

## Future Work

- [ ] Train and persist calibrated risk models on domain datasets
- [ ] Backtesting and evaluation pipeline for finance signals
- [ ] OpenTelemetry / Prometheus exporters for production monitoring
- [ ] OAuth2 or API-key-per-user authentication
- [ ] Optional Gradio/Streamlit UI layer on top of existing REST backend

---

## License

This project is for research and portfolio demonstration purposes.  
Not financial advice. Use at your own risk.
