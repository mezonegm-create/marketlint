from __future__ import annotations

import re

from marketlint.counterexamples import generate_counterexamples
from marketlint.market_tests import build_market_tests
from marketlint.models import Finding, LintReport, Market, Severity
from marketlint.normalizer import normalize_rules

SOURCE_WORDS = re.compile(r"\b(source|according to|reported by|published by|resolution source)\b", re.I)


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

    return LintReport(
        market=market,
        findings=findings,
        normalized_rules=rules,
        tests=build_market_tests(market, rules),
        counterexamples=generate_counterexamples(market, rules),
    )
