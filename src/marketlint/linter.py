from __future__ import annotations

import re

from marketlint.models import Finding, LintReport, Market, Severity

BOUNDARY_WORDS = re.compile(r"\b(before|after|by|until|between|above|below|exceed|at least|more than|less than)\b", re.I)
SOURCE_WORDS = re.compile(r"\b(source|according to|reported by|published by|resolution source)\b", re.I)
TIMEZONE_WORDS = re.compile(r"\b(UTC|GMT|ET|EST|EDT|CT|CST|CDT|PT|PST|PDT)\b", re.I)


def lint_market(market: Market) -> LintReport:
    text = "\n".join(filter(None, [market.question, market.description, market.resolution_rules]))
    findings: list[Finding] = []

    if not market.resolution_rules and not market.description:
        findings.append(Finding(code="ML001", severity=Severity.ERROR, title="Missing resolution rules", detail="No resolution text was available to inspect."))

    if BOUNDARY_WORDS.search(text) and not TIMEZONE_WORDS.search(text) and market.end_time:
        findings.append(Finding(code="ML002", severity=Severity.WARNING, title="Time boundary without explicit timezone", detail="The market uses boundary language and has an end time, but the inspected rules do not explicitly name a timezone."))

    if not market.resolution_source and not SOURCE_WORDS.search(text):
        findings.append(Finding(code="ML003", severity=Severity.WARNING, title="Resolution source not explicit", detail="MarketLint could not identify an explicit resolution source in the normalized market data or rule text."))

    if not market.outcomes:
        findings.append(Finding(code="ML004", severity=Severity.WARNING, title="Outcomes unavailable", detail="No outcomes were available in normalized market data."))

    if market.prices and market.outcomes and len(market.prices) != len(market.outcomes):
        findings.append(Finding(code="ML005", severity=Severity.ERROR, title="Outcome/price shape mismatch", detail="The number of prices does not match the number of outcomes."))

    return LintReport(market=market, findings=findings)
