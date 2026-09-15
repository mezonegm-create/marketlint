from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TestStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class RelationKind(StrEnum):
    DUPLICATE = "duplicate"
    IMPLIES = "implies"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"


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


class NormalizedRules(BaseModel):
    text: str
    timezone: str | None = None
    has_boundary_language: bool = False
    has_exact_boundary_language: bool = False
    has_fallback_language: bool = False
    source: str | None = None
    deadline: datetime | None = None


class MarketTest(BaseModel):
    code: str
    name: str
    status: TestStatus
    detail: str


class Counterexample(BaseModel):
    code: str
    title: str
    scenario: str
    question: str


class MarketRelation(BaseModel):
    kind: RelationKind
    severity: Severity
    left_market_id: str | None = None
    right_market_id: str | None = None
    title: str
    detail: str


class LintReport(BaseModel):
    market: Market
    findings: list[Finding] = Field(default_factory=list)
    normalized_rules: NormalizedRules | None = None
    tests: list[MarketTest] = Field(default_factory=list)
    counterexamples: list[Counterexample] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(item.severity == Severity.ERROR for item in self.findings) or any(
            item.status == TestStatus.FAIL for item in self.tests
        )


class EventReport(BaseModel):
    platform: str = "polymarket"
    url: HttpUrl
    slug: str
    markets: list[LintReport] = Field(default_factory=list)
    relations: list[MarketRelation] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(report.has_errors for report in self.markets)
