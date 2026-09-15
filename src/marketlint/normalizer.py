from __future__ import annotations

import re

from marketlint.models import Market, NormalizedRules

TIMEZONE = re.compile(r"\b(UTC|GMT|ET|EST|EDT|CT|CST|CDT|PT|PST|PDT)\b", re.I)
BOUNDARY = re.compile(r"\b(before|after|by|until|above|below|exceed|at least|at most|more than|less than)\b", re.I)
EXACT = re.compile(r"\b(exactly|equal(?:s)?|equal to)\b", re.I)
FALLBACK = re.compile(r"\b(if unavailable|fallback|otherwise|in the event|if no|if .* unavailable)\b", re.I)


def normalize_rules(market: Market) -> NormalizedRules:
    text = "\n".join(filter(None, [market.question, market.resolution_rules, market.description]))
    timezone_match = TIMEZONE.search(text)
    return NormalizedRules(
        text=text,
        timezone=timezone_match.group(1).upper() if timezone_match else None,
        has_boundary_language=bool(BOUNDARY.search(text)),
        has_exact_boundary_language=bool(EXACT.search(text)),
        has_fallback_language=bool(FALLBACK.search(text)),
        source=market.resolution_source,
        deadline=market.end_time,
    )
