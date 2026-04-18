from __future__ import annotations

import os
import time
from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import HumanMessage, trim_messages
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.config import settings
from app.services.groq_client import get_groq_llm
from app.services.metrics import metrics_store
from app.tools import FINANCE_TOOLS
from app.tools.general import GENERAL_TOOLS
from app.utils.logging import get_logger
from shared_store import url_time

logger = get_logger(__name__)


class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    task_type: Literal["finance", "general", "unsupported"]


def _build_tool_llm(tools):
    llm = get_groq_llm(temperature=0)
    if llm is None:
        return None
    return llm.bind_tools(tools)


finance_llm = _build_tool_llm(FINANCE_TOOLS)
general_llm = _build_tool_llm(GENERAL_TOOLS)


def _classify_task(text: str) -> Literal["finance", "general", "unsupported"]:
    t = (text or "").lower()
    finance_keywords = [
        "ticker",
        "stock",
        "finance",
        "returns",
        "volatility",
        "rsi",
        "drawdown",
        "risk",
        "anomaly",
        "market",
        "portfolio",
        "ohlcv",
    ]
    general_keywords = [
        "http",
        "url",
        "web",
        "scrape",
        "code",
        "python",
        "ocr",
        "audio",
        "transcribe",
        "file",
        "download",
    ]

    if any(k in t for k in finance_keywords):
        return "finance"
    if any(k in t for k in general_keywords):
        return "general"
    return "unsupported"


def classify_node(state: AgentState):
    last = state["messages"][-1]
    content = getattr(last, "content", "")
    if isinstance(content, list):
        content = " ".join(str(x) for x in content)

    task_type = _classify_task(str(content))
    return {"task_type": task_type}


def _invoke_llm(state: AgentState, llm, fallback_message: str):
    if llm is None:
        return {
            "messages": [
                HumanMessage(
                    content=fallback_message,
                )
            ]
        }

    trimmed = trim_messages(
        messages=state["messages"],
        max_tokens=settings.max_tokens,
        strategy="last",
        include_system=True,
        start_on="human",
        token_counter=llm,
    )
    result = llm.invoke(trimmed)
    return {"messages": [result]}


def finance_agent_node(state: AgentState):
    metrics_store.inc("agent.finance_routed")
    return _invoke_llm(
        state,
        finance_llm,
        "Finance tools unavailable because GROQ_API_KEY is missing. Use /analyze/finance or set GROQ_API_KEY.",
    )


def general_agent_node(state: AgentState):
    metrics_store.inc("agent.general_routed")
    return _invoke_llm(
        state,
        general_llm,
        "General tool orchestration unavailable because GROQ_API_KEY is missing.",
    )


def unsupported_node(state: AgentState):
    metrics_store.inc("agent.unsupported_routed")
    return {
        "messages": [
            HumanMessage(
                content=(
                    "Unsupported task type. Provide a finance/risk request or a concrete web/code task."
                )
            )
        ]
    }


def _route_by_task_type(state: AgentState):
    return state.get("task_type", "unsupported")


def _route_after_llm(state: AgentState):
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def _tool_error_handler(exc: Exception) -> dict:
    metrics_store.inc("failed_runs")
    metrics_store.inc("tool_execution_failures")
    logger.warning("tool_execution_failed reason=%s", exc)
    return {"error": f"Tool execution failed: {exc}"}


graph = StateGraph(AgentState)
graph.add_node("classify", classify_node)
graph.add_node("finance_agent", finance_agent_node)
graph.add_node("general_agent", general_agent_node)
graph.add_node("finance_tools", ToolNode(FINANCE_TOOLS, handle_tool_errors=_tool_error_handler))
graph.add_node("general_tools", ToolNode(GENERAL_TOOLS, handle_tool_errors=_tool_error_handler))
graph.add_node("unsupported", unsupported_node)

graph.add_edge(START, "classify")
graph.add_conditional_edges(
    "classify",
    _route_by_task_type,
    {
        "finance": "finance_agent",
        "general": "general_agent",
        "unsupported": "unsupported",
    },
)

graph.add_conditional_edges(
    "finance_agent",
    _route_after_llm,
    {"tools": "finance_tools", END: END},
)
graph.add_conditional_edges(
    "general_agent",
    _route_after_llm,
    {"tools": "general_tools", END: END},
)
graph.add_edge("finance_tools", "finance_agent")
graph.add_edge("general_tools", "general_agent")
graph.add_edge("unsupported", END)

agent_app = graph.compile()


# System constraint for grounded tool-first behavior in autonomous runs.
SYSTEM_PROMPT = (
    "You are an autonomous AI quant research assistant. Prefer computed outputs from tools and avoid "
    "hallucinated metrics. Use finance tools for market/risk tasks; use general tools only when needed."
)


def run_agent(task_input: str):
    metrics_store.inc("total_runs")
    start = time.perf_counter()

    cur_url = os.getenv("url")
    if cur_url:
        url_time[cur_url] = time.time()

    try:
        initial_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_input},
        ]
        result = agent_app.invoke(
            {"messages": initial_messages, "task_type": "general"},
            config={"recursion_limit": settings.recursion_limit},
        )
        return result
    except Exception as exc:
        metrics_store.inc("failed_runs")
        logger.error("agent_run_failed reason=%s", exc)
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics_store.observe_latency("agent.run", elapsed_ms)
