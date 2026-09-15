from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations

from marketlint.models import Market, MarketRelation, RelationKind, Severity

PRICE_TOLERANCE = 0.02


class Comparator(StrEnum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


@dataclass(frozen=True)
class Threshold:
    comparator: Comparator
    value: float
    unit: str | None = None


_COMPARATOR = (
    r"(?P<comparator>above|over|more than|exceed(?:s|ed|ing)?|at least|greater than|"
    r"below|under|less than|at most|fewer than|lower than)"
)
_VALUE = (
    r"(?P<currency>[$€£])?\s*(?P<number>[0-9]+(?:\.[0-9]+)?)\s*"
    r"(?P<suffix>%|percent|million|billion|k|m|b)?"
)
_THRESHOLD = re.compile(rf"\b{_COMPARATOR}\b\s*{_VALUE}", re.IGNORECASE)

_COMPARATORS = {
    "above": Comparator.GT,
    "over": Comparator.GT,
    "more than": Comparator.GT,
    "exceed": Comparator.GT,
    "exceeds": Comparator.GT,
    "exceeded": Comparator.GT,
    "exceeding": Comparator.GT,
    "greater than": Comparator.GT,
    "at least": Comparator.GTE,
    "below": Comparator.LT,
    "under": Comparator.LT,
    "less than": Comparator.LT,
    "fewer than": Comparator.LT,
    "lower than": Comparator.LT,
    "at most": Comparator.LTE,
}


def _threshold(question: str) -> Threshold | None:
    match = _THRESHOLD.search(question)
    if not match:
        return None
    value = float(match.group("number"))
    suffix = (match.group("suffix") or "").lower()
    if suffix in {"million", "m"}:
        value *= 1_000_000
    elif suffix in {"billion", "b"}:
        value *= 1_000_000_000
    elif suffix == "k":
        value *= 1_000

    currency = match.group("currency")
    if currency:
        unit = currency
    elif suffix in {"%", "percent"}:
        unit = "%"
    else:
        unit = None
    return Threshold(_COMPARATORS[match.group("comparator").lower()], value, unit)


def _topic(question: str) -> str:
    text = _THRESHOLD.sub(" ", question.lower())
    text = re.sub(
        r"\b(will|be|by|before|after|on|in|at|the|a|an|is|does|do|of|to)\b",
        " ",
        text,
    )
    return " ".join(re.findall(r"[a-z]{3,}", text))


def _similar_topic(left: Market, right: Market) -> bool:
    a = set(_topic(left.question).split())
    b = set(_topic(right.question).split())
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= 0.6


def _compatible_units(left: Threshold, right: Threshold) -> bool:
    return left.unit == right.unit


def _yes_price(market: Market) -> float | None:
    for index, outcome in enumerate(market.outcomes):
        if outcome.strip().lower() == "yes" and index < len(market.prices):
            return market.prices[index]
    return None


def _direction(threshold: Threshold) -> str:
    return "above" if threshold.comparator in {Comparator.GT, Comparator.GTE} else "below"


def _strictness_key(threshold: Threshold) -> tuple[float, int]:
    if _direction(threshold) == "above":
        return threshold.value, int(threshold.comparator == Comparator.GT)
    return -threshold.value, int(threshold.comparator == Comparator.LT)


def _threshold_evidence(threshold: Threshold) -> str:
    unit = threshold.unit or "unitless"
    return f"comparator={threshold.comparator.value}, value={threshold.value:g}, unit={unit}"


def _price_check(
    kind: RelationKind,
    left: Market,
    right: Market,
    lt: Threshold,
    rt: Threshold,
) -> tuple[bool | None, str | None]:
    lp = _yes_price(left)
    rp = _yes_price(right)
    if lp is None or rp is None:
        return None, None

    if kind == RelationKind.DUPLICATE:
        difference = abs(lp - rp)
        detail = (
            f"YES prices are {lp:.3f} and {rp:.3f}; duplicate markets differ by "
            f"{difference:.3f}."
        )
        return difference <= PRICE_TOLERANCE, detail

    if kind == RelationKind.MUTUALLY_EXCLUSIVE:
        total = lp + rp
        return total <= 1 + PRICE_TOLERANCE, f"Mutually exclusive YES prices sum to {total:.3f}."

    left_is_tighter = _strictness_key(lt) > _strictness_key(rt)
    tighter_price, looser_price = (lp, rp) if left_is_tighter else (rp, lp)
    ok = tighter_price <= looser_price + PRICE_TOLERANCE
    detail = (
        f"Tighter-threshold YES price is {tighter_price:.3f}; "
        f"looser-threshold YES price is {looser_price:.3f}."
    )
    return ok, detail


def _relation(
    *,
    kind: RelationKind,
    left: Market,
    right: Market,
    lt: Threshold,
    rt: Threshold,
    severity: Severity,
    title: str,
    detail: str,
    antecedent: Market | None = None,
    consequent: Market | None = None,
) -> MarketRelation:
    price_consistent, price_detail = _price_check(kind, left, right, lt, rt)
    if price_consistent is False:
        severity = Severity.WARNING
    return MarketRelation(
        kind=kind,
        severity=severity,
        left_market_id=left.market_id,
        right_market_id=right.market_id,
        antecedent_market_id=antecedent.market_id if antecedent else None,
        consequent_market_id=consequent.market_id if consequent else None,
        title=title,
        detail=detail,
        evidence=[
            f"left: {_threshold_evidence(lt)}",
            f"right: {_threshold_evidence(rt)}",
        ],
        price_consistent=price_consistent,
        price_detail=price_detail,
    )


def _mutually_exclusive(lt: Threshold, rt: Threshold) -> bool:
    ld, rd = _direction(lt), _direction(rt)
    if ld == rd:
        return False
    above, below = (lt, rt) if ld == "above" else (rt, lt)
    if above.value > below.value:
        return True
    if above.value < below.value:
        return False
    return not (
        above.comparator == Comparator.GTE and below.comparator == Comparator.LTE
    )


def analyze_relations(markets: list[Market]) -> list[MarketRelation]:
    """Find deterministic logical relations and price tensions among siblings."""
    relations: list[MarketRelation] = []
    for left, right in combinations(markets, 2):
        if not _similar_topic(left, right):
            continue
        lt = _threshold(left.question)
        rt = _threshold(right.question)
        if not lt or not rt or not _compatible_units(lt, rt):
            continue

        ld, rd = _direction(lt), _direction(rt)
        if lt == rt:
            relations.append(
                _relation(
                    kind=RelationKind.DUPLICATE,
                    left=left,
                    right=right,
                    lt=lt,
                    rt=rt,
                    severity=Severity.WARNING,
                    title="Potential duplicate threshold markets",
                    detail="Sibling markets appear to ask the same threshold question.",
                )
            )
        elif _mutually_exclusive(lt, rt):
            relations.append(
                _relation(
                    kind=RelationKind.MUTUALLY_EXCLUSIVE,
                    left=left,
                    right=right,
                    lt=lt,
                    rt=rt,
                    severity=Severity.INFO,
                    title="Mutually exclusive threshold pair",
                    detail="Both YES outcomes cannot hold under the parsed threshold semantics.",
                )
            )
        elif ld == rd:
            tighter = left if _strictness_key(lt) > _strictness_key(rt) else right
            looser = right if tighter is left else left
            relations.append(
                _relation(
                    kind=RelationKind.IMPLIES,
                    left=left,
                    right=right,
                    lt=lt,
                    rt=rt,
                    severity=Severity.INFO,
                    title="Nested threshold markets",
                    detail=(
                        f"YES on market {tighter.market_id or 'tighter'} implies YES on market "
                        f"{looser.market_id or 'looser'}, assuming identical resolution scope."
                    ),
                    antecedent=tighter,
                    consequent=looser,
                )
            )
    return relations
