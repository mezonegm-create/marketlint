from __future__ import annotations

import re

from marketlint.counterexamples import generate_counterexamples
from marketlint.market_tests import build_market_tests
from marketlint.models import Finding, LintReport, Market, RiskSummary, Severity
from marketlint.normalizer import normalize_rules

SOURCE_WORDS = re.compile(
    r"\b(source|according to|reported by|published by|resolution source)\b",
    re.IGNORECASE,
)
SUBJECTIVE_TERMS = re.compile(
    r"\b("
    r"major|significant|substantial|meaningful|notable|material|"
    r"widely recognized|generally considered|credible|prominent"
    r")\b",
    re.IGNORECASE,
)
DEFINITION_LANGUAGE = re.compile(
    r"\b("
    r"defined as|for (?:the )?purposes? of this market|means|specifically|"
    r"at least|at most|more than|less than|greater than|fewer than|"
    r"equal to|equals|exceed(?:s|ed|ing)?|above|below|under|over"
    r")\b",
    re.IGNORECASE,
)
REVISION_SENSITIVE = re.compile(
    r"\b(preliminary|initial|advance estimate|provisional|subject to revision|revised)\b",
    re.IGNORECASE,
)
REVISION_POLICY = re.compile(
    r"\b(first release|initial release|first published|final release|final value|"
    r"latest revision|revisions? (?:will|do) not count|ignore revisions?|"
    r"as (?:first|initially) published)\b",
    re.IGNORECASE,
)


def _undefined_subjective_terms(text: str) -> list[str]:
    matches = list(SUBJECTIVE_TERMS.finditer(text))
    if not matches or DEFINITION_LANGUAGE.search(text):
        return []
    return list(dict.fromkeys(match.group(0).lower() for match in matches))


def _risk_summary(findings: list[Finding]) -> RiskSummary:
    errors = sum(item.severity == Severity.ERROR for item in findings)
    warnings = sum(item.severity == Severity.WARNING for item in findings)
    info = sum(item.severity == Severity.INFO for item in findings)
    if errors:
        level = "high"
    elif warnings >= 2:
        level = "elevated"
    elif warnings == 1:
        level = "review"
    else:
        level = "low"
    return RiskSummary(level=level, errors=errors, warnings=warnings, info=info)


def lint_market(market: Market) -> LintReport:
    rules = normalize_rules(market)
    text = rules.text
    findings: list[Finding] = []

    if not market.resolution_rules and not market.description:
        findings.append(Finding(code="ML001", severity=Severity.ERROR, title="Missing resolution rules", detail="No resolution text was available to inspect."))

    if rules.has_boundary_language and not rules.timezone and market.end_time:
        findings.append(Finding(code="ML002", severity=Severity.WARNING, title="Time boundary without explicit timezone", detail="The market uses boundary language and has an end time, but the inspected rules do not explicitly name a timezone."))

    if not market.resolution_source and not SOURCE_WORDS.search(text):
        findings.append(Finding(code="ML003", severity=Severity.WARNING, title="Resolution source not explicit", detail="MarketLint could not identify an explicit resolution source in normalized market data or rule text."))

    if not market.outcomes:
        findings.append(Finding(code="ML004", severity=Severity.WARNING, title="Outcomes unavailable", detail="No outcomes were available in normalized market data."))

    if market.prices and market.outcomes and len(market.prices) != len(market.outcomes):
        findings.append(Finding(code="ML005", severity=Severity.ERROR, title="Outcome/price shape mismatch", detail="The number of prices does not match the number of outcomes."))

    if market.resolution_source and not rules.has_fallback_language:
        findings.append(Finding(code="ML006", severity=Severity.INFO, title="No explicit source fallback detected", detail="A resolution source is named, but MarketLint did not detect a fallback procedure if it becomes unavailable."))

    subjective_terms = _undefined_subjective_terms(text)
    if subjective_terms:
        findings.append(
            Finding(
                code="ML007",
                severity=Severity.WARNING,
                title="Potentially subjective resolution language",
                detail="The rules use judgment-dependent language without a detected objective definition or measurable threshold.",
                evidence=[f"subjective term: {term}" for term in subjective_terms],
            )
        )

    revision_terms = list(REVISION_SENSITIVE.finditer(text))
    if revision_terms and not REVISION_POLICY.search(text):
        terms = list(dict.fromkeys(match.group(0).lower() for match in revision_terms))
        findings.append(
            Finding(
                code="ML008",
                severity=Severity.WARNING,
                title="Revision-sensitive data without a clear revision policy",
                detail=(
                    "The rules reference data that may be preliminary or revised, but MarketLint "
                    "did not detect which publication or revision controls resolution."
                ),
                evidence=[f"revision-sensitive term: {term}" for term in terms],
            )
        )

    return LintReport(
        market=market,
        findings=findings,
        normalized_rules=rules,
        tests=build_market_tests(market, rules),
        counterexamples=generate_counterexamples(market, rules),
        risk_summary=_risk_summary(findings),
    )
