from __future__ import annotations

import re
from itertools import combinations

from marketlint.models import Market, MarketRelation, RelationKind, Severity

_NUMBER = re.compile(r"(?:\$|€|£)?\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|million|billion|k|m|b)?", re.I)
_ABOVE = re.compile(r"\b(above|over|more than|exceed(?:s|ed|ing)?|at least|greater than)\b", re.I)
_BELOW = re.compile(r"\b(below|under|less than|at most|fewer than|lower than)\b", re.I)


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


def analyze_relations(markets: list[Market]) -> list[MarketRelation]:
    """Find deterministic logical tensions among sibling markets.

    This intentionally handles only relations that can be justified without an
    LLM. Unknown relationships are left unclassified rather than guessed.
    """
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
            relations.append(MarketRelation(
                kind=RelationKind.DUPLICATE,
                severity=Severity.WARNING,
                left_market_id=left.market_id,
                right_market_id=right.market_id,
                title="Potential duplicate threshold markets",
                detail="Sibling markets appear to ask the same directional threshold question.",
            ))
        elif ldir == "above" and rdir == "below" and lvalue >= rvalue:
            relations.append(MarketRelation(
                kind=RelationKind.MUTUALLY_EXCLUSIVE,
                severity=Severity.INFO,
                left_market_id=left.market_id,
                right_market_id=right.market_id,
                title="Mutually exclusive threshold pair",
                detail=f"Both YES outcomes cannot hold if the value must be above {lvalue:g} and below {rvalue:g}.",
            ))
        elif ldir == "below" and rdir == "above" and rvalue >= lvalue:
            relations.append(MarketRelation(
                kind=RelationKind.MUTUALLY_EXCLUSIVE,
                severity=Severity.INFO,
                left_market_id=left.market_id,
                right_market_id=right.market_id,
                title="Mutually exclusive threshold pair",
                detail=f"Both YES outcomes cannot hold if the value must be below {lvalue:g} and above {rvalue:g}.",
            ))
        elif ldir == rdir:
            tighter = max(lvalue, rvalue) if ldir == "above" else min(lvalue, rvalue)
            looser = min(lvalue, rvalue) if ldir == "above" else max(lvalue, rvalue)
            relations.append(MarketRelation(
                kind=RelationKind.IMPLIES,
                severity=Severity.INFO,
                left_market_id=left.market_id,
                right_market_id=right.market_id,
                title="Nested threshold markets",
                detail=f"A YES at the tighter {tighter:g} threshold implies YES at the looser {looser:g} threshold, assuming identical resolution scope.",
            ))
    return relations
