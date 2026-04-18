from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None


def get_groq_llm(temperature: float = 0):
    if not settings.groq_api_key or ChatGroq is None:
        return None
    return ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature,
    )


def explain_metrics(kind: str, computed_payload: dict[str, Any]) -> dict[str, Any]:
    llm = get_groq_llm(temperature=0)
    if llm is None:
        return {
            "summary": "Groq explanation unavailable; computed metrics are returned directly.",
            "rationale": "Set GROQ_API_KEY to enable model-grounded narrative explanations.",
            "source": "fallback",
        }

    prompt = (
        "You are a financial/quant AI assistant. Use only the provided computed metrics. "
        "Do not invent values. Return strict JSON with keys: summary, rationale. "
        f"Analysis kind: {kind}. Metrics: {json.dumps(computed_payload, default=str)}"
    )

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = " ".join(str(part) for part in content)

        cleaned = content.strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]

        parsed = json.loads(cleaned)
        return {
            "summary": str(parsed.get("summary", "")).strip(),
            "rationale": str(parsed.get("rationale", "")).strip(),
            "source": "groq",
        }
    except Exception as exc:
        logger.warning("groq_explanation_failed reason=%s", exc)
        return {
            "summary": "Computed risk/indicator outputs suggest caution; explanation fallback used.",
            "rationale": "LLM parsing failed, so this is a deterministic fallback based on computed outputs.",
            "source": "fallback",
        }
