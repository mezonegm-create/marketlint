from marketlint.models import Market, RelationKind, Severity
from marketlint.relations import analyze_relations


def market(market_id: str, question: str, yes_price: float | None = None) -> Market:
    prices = [yes_price, 1 - yes_price] if yes_price is not None else []
    return Market(
        platform="polymarket",
        url="https://polymarket.com/event/example",
        market_id=market_id,
        question=question,
        outcomes=["Yes", "No"],
        prices=prices,
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


def test_flags_inverted_nested_prices():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $100000 by December 31?", 0.40),
        market("2", "Will Bitcoin be above $120000 by December 31?", 0.60),
    ])
    assert relations[0].kind == RelationKind.IMPLIES
    assert relations[0].price_consistent is False
    assert relations[0].severity == Severity.WARNING


def test_accepts_monotonic_nested_prices():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $100000 by December 31?", 0.60),
        market("2", "Will Bitcoin be above $120000 by December 31?", 0.40),
    ])
    assert relations[0].price_consistent is True


def test_flags_mutually_exclusive_prices_over_one():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $120000 by December 31?", 0.65),
        market("2", "Will Bitcoin be below $100000 by December 31?", 0.55),
    ])
    assert relations[0].price_consistent is False
    assert "1.200" in relations[0].price_detail


def test_ignores_unrelated_topics():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $120000 by December 31?"),
        market("2", "Will rainfall be above 120 millimeters by December 31?"),
    ])
    assert relations == []


def test_year_before_threshold_does_not_become_threshold():
    relations = analyze_relations([
        market("1", "In 2026 will Bitcoin be above $100000?"),
        market("2", "In 2026 will Bitcoin be above $120000?"),
    ])
    assert len(relations) == 1
    assert relations[0].kind == RelationKind.IMPLIES


def test_inclusive_and_strict_boundaries_are_not_duplicates():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $100000?"),
        market("2", "Will Bitcoin be at least $100000?"),
    ])
    assert len(relations) == 1
    assert relations[0].kind == RelationKind.IMPLIES


def test_same_boundary_strict_opposites_are_mutually_exclusive():
    relations = analyze_relations([
        market("1", "Will Bitcoin be above $100000?"),
        market("2", "Will Bitcoin be below $100000?"),
    ])
    assert len(relations) == 1
    assert relations[0].kind == RelationKind.MUTUALLY_EXCLUSIVE


def test_same_boundary_inclusive_opposites_are_not_marked_exclusive():
    relations = analyze_relations([
        market("1", "Will Bitcoin be at least $100000?"),
        market("2", "Will Bitcoin be at most $100000?"),
    ])
    assert relations == []


def test_incompatible_units_are_not_related():
    relations = analyze_relations([
        market("1", "Will approval be above 50%?"),
        market("2", "Will approval be above $50?"),
    ])
    assert relations == []
