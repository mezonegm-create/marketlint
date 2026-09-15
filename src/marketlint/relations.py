from __future__ import annotations

import re
from itertools import combinations

from marketlint.models import Market, MarketRelation, RelationKind, Severity

_NUMBER = re.compile(
    r"(?:\$|€|£)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|million|billion|k|m|b)?",
    re.IGNORECASE,
)
_ABOVE = re.compile(
    r"\b(above|over|more than|exceed(?:s|ed|ing)?|at least|greater than)\b",
    re.IGNORECASE,
)
_BELOW = re.compile(
    r"\b(below|under|less than|at most|fewer than|lower than)\b",
    re.IGNORECASE,
)


def _threshold(question: str) -> tuple[str, float] | None:
    number = _NUMBER.search(question)
    if not number:
        return None
    value = float(number.group(1))
    suffix = (number.group(2) or "").lower()
    if suffix in {"million", "m"}:
        value *= 1_000_000
    elif suffix in {"billion", "b"}:
        value *= 1_000_000_000
    elif suffix == "k":
        value *= 1_000
    if _ABOVE.search(question):
        return "above", value
    if _BELOW.search(question):
        return "below", value
    return None


def _topic(question: str) -> str:
    text = question.lower()
    text = _NUMBER.sub(" ", text)
    text = _ABOVE.sub(" ", text)
    text = _BELOW.sub(" ", text)
    text = re.sub(r"\b(will|be|by|before|after|on|in|at|the|a|an|is|does|do|of|to)\b", " ", text)
    return " ".join(re.findall(r"[a-z]{3,}", text))


def _similar_topic(left: Market, right: Market) -> bool:
    a = set(_topic(left.question).split())
    b = set(_topic(right.question).split())
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= 0.6


def _yes_price(market: Market) -> float | None:
    for index, outcome in enumerate(market.outcomes):
        if outcome.strip().lower() == "yes" and index < len(market.prices):
            return market.prices[index]
    return None


def _price_check(
    kind: RelationKind,
    left: Market,
    right: Market,
    lt: tuple[str, float],
    rt: tuple[str, float],
) -> tuple[bool | None, str | None]:
    lp = _yes_price(left)
    rp = _yes_price(right)
    if lp is None or rp is None:
        return None, None

    if kind == RelationKind.DUPLICATE:
        ok = abs(lp - rp) <= 0.02
        return ok, f"YES prices are {lp:.3f} and {rp:.3f}; duplicate markets differ by {abs(lp - rp):.3f}."

    if kind == RelationKind.MUTUALLY_EXCLUSIVE:
        total = lp + rp
        ok = total <= 1.02
        return ok, f"Mutually exclusive YES prices sum to {total:.3f}."

    ldir, lvalue = lt
    rdir, rvalue = rt
    left_is_tighter = lvalue > rvalue if ldir == "above" else lvalue < rvalue
    tighter_price, looser_price = (lp, rp) if left_is_tighter else (rp, lp)
    ok = tighter_price <= looser_price + 0.02
    return ok, f"Tighter-threshold YES price is {tighter_price:.3f}; looser-threshold YES price is {looser_price:.3f}."


def _relation(
    *,
    kind: RelationKind,
    left: Market,
    right: Market,
    lt: tuple[str, float],
    rt: tuple[str, float],
    severity: Severity,
    title: str,
    detail: str,
) -> MarketRelation:
    price_consistent, price_detail = _price_check(kind, left, right, lt, rt)
    if price_consistent is False:
        severity = Severity.WARNING
    return MarketRelation(
        kind=kind,
        severity=severity,
        left_market_id=left.market_id,
        right_market_id=right.market_id,
        title=title,
        detail=detail,
        price_consistent=price_consistent,
        price_detail=price_detail,
    )


def analyze_relations(markets: list[Market]) -> list[MarketRelation]:
    """Find deterministic logical relations and price tensions among siblings."""
    relations: list[MarketRelation] = []
    for left, right in combinations(markets, 2):
        if not _similar_topic(left, right):
            continue
        lt = _threshold(left.question)
        rt = _threshold(right.question)
        if not lt or not rt:
            continue
        ldir, lvalue = lt
        rdir, rvalue = rt
        if ldir == rdir and lvalue == rvalue:
            relations.append(_relation(
                kind=RelationKind.DUPLICATE,
                left=left,
                right=right,
                lt=lt,
                rt=rt,
                severity=Severity.WARNING,
                title="Potential duplicate threshold markets",
                detail="Sibling markets appear to ask the same directional threshold question.",
            ))
        elif ldir == "above" and rdir == "below" and lvalue >= rvalue:
            relations.append(_relation(
                kind=RelationKind.MUTUALLY_EXCLUSIVE,
                left=left,
                right=right,
                lt=lt,
                rt=rt,
                severity=Severity.INFO,
                title="Mutually exclusive threshold pair",
                detail=f"Both YES outcomes cannot hold if the value must be above {lvalue:g} and below {rvalue:g}.",
            ))
        elif ldir == "below" and rdir == "above" and rvalue >= lvalue:
            relations.append(_relation(
                kind=RelationKind.MUTUALLY_EXCLUSIVE,
                left=left,
                right=right,
                lt=lt,
                rt=rt,
                severity=Severity.INFO,
                title="Mutually exclusive threshold pair",
                detail=f"Both YES outcomes cannot hold if the value must be below {lvalue:g} and above {rvalue:g}.",
            ))
        elif ldir == rdir:
            tighter = max(lvalue, rvalue) if ldir == "above" else min(lvalue, rvalue)
            looser = min(lvalue, rvalue) if ldir == "above" else max(lvalue, rvalue)
            relations.append(_relation(
                kind=RelationKind.IMPLIES,
                left=left,
                right=right,
                lt=lt,
                rt=rt,
                severity=Severity.INFO,
                title="Nested threshold markets",
                detail=f"A YES at the tighter {tighter:g} threshold implies YES at the looser {looser:g} threshold, assuming identical resolution scope.",
            ))
    return relations
