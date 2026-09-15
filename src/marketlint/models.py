from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Finding(BaseModel):
    code: str
    severity: Severity
    title: str
    detail: str
    evidence: list[str] = Field(default_factory=list)


class Market(BaseModel):
    platform: str
    url: HttpUrl
    market_id: str | None = None
    question: str
    description: str | None = None
    resolution_rules: str | None = None
    resolution_source: str | None = None
    end_time: datetime | None = None
    outcomes: list[str] = Field(default_factory=list)
    prices: list[float] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict, exclude=True)


class LintReport(BaseModel):
    market: Market
    findings: list[Finding] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity == Severity.ERROR for item in self.findings)
