from marketlint.models import Market, RelationKind
from marketlint.relations import analyze_relations


def market(market_id: str, question: str) -> Market:
    return Market(
        platform="polymarket",
        url="https://polymarket.com/event/example",
        market_id=market_id,
        question=question,
        outcomes=["Yes", "No"],
    )


def test_detects_nested_thresholds():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $100000 by December 31?"),
        market("2", "Will Bitcoin be above $120000 by December 31?"),
    ])
    assert len(relations) == 1
    assert relations[0].kind == RelationKind.IMPLIES


def test_detects_mutually_exclusive_thresholds():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $120000 by December 31?"),
        market("2", "Will Bitcoin be below $100000 by December 31?"),
    ])
    assert len(relations) == 1
    assert relations[0].kind == RelationKind.MUTUALLY_EXCLUSIVE


def test_ignores_unrelated_topics():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $120000 by December 31?"),
        market("2", "Will rainfall be above 120 millimeters by December 31?"),
    ])
    assert relations == []
