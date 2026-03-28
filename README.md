<div align="center">

# 🤖 Autonomous Multi-Tool LLM Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-FF6B35?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**A production-grade autonomous AI agent that perceives, reasons, and acts across web, code, media, and financial data — deployed as a REST API.**

[Features](#-features) • [Architecture](#-architecture) • [Tools](#-tools) • [Quick Start](#-quick-start) • [API Docs](#-api-reference)

</div>

---

## 🎯 What This Does

This agent accepts a URL or natural language task, autonomously breaks it into sub-tasks, selects the right tools, executes them in sequence, handles failures gracefully, and returns structured results — all without human intervention.

**Real-world capabilities:**
- 🌐 Render and parse any JavaScript-heavy webpage
- 💻 Write, execute, and self-correct Python code on the fly
- 📊 Fetch live stock/financial data and run analysis
- 🖼️ Extract text from images using OCR
- 🎙️ Transcribe audio files to text
- 📁 Download, process, and analyze files from any URL
- 🔁 Auto-recover from LLM errors without crashing

---

## ✨ Features

| Feature | Description |
|---|---|
| **LangGraph State Machine** | Cyclic agent graph with conditional routing, tool execution, and error recovery nodes |
| **9 Specialized Tools** | Web scraping, code execution, OCR, audio transcription, stock data, file handling |
| **Malformed JSON Recovery** | Detects and auto-corrects invalid LLM tool calls without crashing |
| **Token Context Management** | Dynamically trims message history to stay within 60K token limits |
| **Rate Limiting** | InMemoryRateLimiter with configurable requests/sec to avoid API quota exhaustion |
| **Timeout Handling** | 180s per-task watchdog with graceful degradation (submits fallback instead of hanging) |
| **Base64 Memory Store** | Encodes images to Base64 without polluting LLM context window |
| **REST API** | FastAPI with background tasks, health check, live status, and CORS support |
| **Finance Tool** | Live OHLCV stock data, returns, volatility, and RSI via yfinance |

---

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Server │
│ POST /solve │ GET /healthz │ GET /status │
└────────────────────────┬────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ LangGraph Agent Graph │
│ │
│ ┌─────────┐ tool_calls? ┌──────────────┐ │
│ │ START │ ───────────────► │ ToolNode │ │
│ └────┬────┘ │ (8 tools) │ │
│ │ └──────┬───────┘ │
│ ▼ │ │
│ ┌──────────┐ malformed? ┌────────▼──────────┐ │
│ │ Agent │ ◄──────────── │ handle_malformed │ │
│ │ Node │ └───────────────────┘ │
│ └────┬─────┘ │
│ │ END? │
│ ▼ │
│ [END] │
└─────────────────────────────────────────────────────────────┘
│
┌──────────────┼──────────────┐
▼ ▼ ▼
[Web Scraper] [Code Runner] [Stock Data]
[OCR / Audio] [File / HTTP] [Base64 Enc]

text

---

## 🛠️ Tools

| Tool | Description |
|---|---|
| `get_rendered_html` | Full JS-rendered page scraping via Playwright |
| `run_code` | Sandboxed Python execution with stdout/stderr capture |
| `post_request` | HTTP POST with Base64 placeholder resolution and retry logic |
| `download_file` | Stream-download any file from URL to local storage |
| `add_dependencies` | Runtime pip install via `uv add` |
| `ocr_image_tool` | Tesseract OCR on images (bytes / path / base64) |
| `transcribe_audio` | MP3/WAV → text via Google Speech Recognition |
| `encode_image_to_base64` | Safe Base64 encoding without LLM context overflow |
| `get_stock_data` ⭐ | Live OHLCV, returns, volatility, RSI for any ticker |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Udghosh-Rao/autonomous-llm-agent.git
cd autonomous-llm-agent
pip install uv
uv sync
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your keys
```

### 3. Run the Server
```bash
uvicorn main:app --reload --port 7860
```

### 4. Send a Task
```bash
curl -X POST http://localhost:7860/solve \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-task-url.com", "secret": "your-secret"}'
```

---

## 📡 API Reference

### `POST /solve`
Trigger the agent on a task URL.

**Request Body:**
```json
{
  "url": "https://task-endpoint.example.com",
  "secret": "your-secret-key"
}
```

**Response:**
```json
{ "status": "ok" }
```

---

### `GET /healthz`
Liveness probe for deployment health checks.

**Response:**
```json
{ "status": "ok", "uptime_seconds": 3600 }
```

---

### `GET /status`
Live agent telemetry — tools loaded, model info, run count.

**Response:**
```json
{
  "status": "running",
  "model": "gemini-2.5-flash",
  "tools_available": 9,
  "tools": ["run_code", "get_rendered_html", "..."],
  "total_runs": 42,
  "uptime_seconds": 7200
}
```

---

### `POST /analyze/stock` ⭐
Direct financial analysis endpoint — no task URL needed.

**Request Body:**
```json
{
  "ticker": "AAPL",
  "period": "3mo",
  "secret": "your-secret-key"
}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "period": "3mo",
  "current_price": 213.49,
  "return_pct": 8.34,
  "volatility_pct": 1.82,
  "rsi": 58.3,
  "trend": "Bullish",
  "data_points": 63
}
```

---

## 🧠 Design Decisions

**Why LangGraph over vanilla LangChain?**
LangGraph provides a stateful, cyclic graph — essential for agents that need to loop (retry, recover, re-plan). Linear chains break on errors.

**Why Base64 key store?**
Passing raw Base64 strings through LLM context causes token overflow, routing failures, and malformed JSON. A UUID key placeholder keeps context clean.

**Why background tasks in FastAPI?**
Agent runs can take 2–10 minutes. Blocking the HTTP thread would cause client timeouts. Background tasks return `200 OK` immediately and run the agent asynchronously.

---

## 📦 Tech Stack

- **LLM:** Google Gemini 2.5 Flash
- **Agent Framework:** LangGraph + LangChain
- **API:** FastAPI + Uvicorn
- **Web Scraping:** Playwright + BeautifulSoup4
- **Finance Data:** yfinance
- **OCR:** Pytesseract + Pillow
- **Audio:** SpeechRecognition + pydub
- **Package Manager:** uv

---

## 👤 Author

**Udghosh Rao** — IIT Madras BS Data Science
[LinkedIn](https://linkedin.com/in/udghosh-rao) • [GitHub](https://github.com/Udghosh-Rao)

---

<div align="center">⭐ Star this repo if you found it useful!</div>
