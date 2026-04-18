from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    url: str
    secret: str


class FinanceAnalyzeRequest(BaseModel):
    ticker: str = Field(default="AAPL")
    period: str = Field(default="6mo")
    analysis_type: Optional[str] = Field(default="standard")
    secret: str


class RiskDetectRequest(BaseModel):
    observation: dict[str, Any]
    secret: str


class AgentRunRequest(BaseModel):
    prompt: str
    secret: str
