from __future__ import annotations

import re

from marketlint.models import Counterexample, Market, NormalizedRules

STRICT = re.compile(r"\b(above|below|exceed|more than|less than|before|after)\b", re.I)
INCLUSIVE = re.compile(r"\b(at least|at most|by|until)\b", re.I)


def generate_counterexamples(market: Market, rules: NormalizedRules) -> list[Counterexample]:
    cases: list[Counterexample] = []
    text = rules.text

    if STRICT.search(text):
        cases.append(Counterexample(
            code="CE001",
            title="Exact-boundary case",
            scenario="The observed value or event occurs exactly at the stated threshold or deadline.",
            question="Do the rules clearly say whether equality counts?",
        ))
    elif INCLUSIVE.search(text):
        cases.append(Counterexample(
            code="CE001",
            title="Exact-boundary case",
            scenario="The observed value or event occurs exactly at the stated threshold or deadline.",
            question="Is the inclusive boundary interpretation explicit and consistent?",
        ))

    if market.end_time and not rules.timezone and rules.has_boundary_language:
        cases.append(Counterexample(
            code="CE002",
            title="Timezone-edge case",
            scenario="The event occurs near the deadline and falls on different calendar dates in different timezones.",
            question="Which timezone controls resolution?",
        ))

    if not market.resolution_source:
        cases.append(Counterexample(
            code="CE003",
            title="Conflicting-source case",
            scenario="Two credible data sources report different outcomes for the same event.",
            question="Which source has authority to resolve the market?",
        ))

    if market.resolution_source and not rules.has_fallback_language:
        cases.append(Counterexample(
            code="CE004",
            title="Source-unavailable case",
            scenario="The named resolution source is unavailable, delayed, corrected, or stops publishing.",
            question="Do the rules define a fallback source or procedure?",
        ))

    return cases
