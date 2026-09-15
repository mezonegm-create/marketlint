from marketlint.counterexamples import generate_counterexamples
from marketlint.linter import lint_market
from marketlint.models import Market, TestStatus
from marketlint.normalizer import normalize_rules


def market(**overrides):
    data = {
        "platform": "polymarket",
        "url": "https://polymarket.com/event/example",
        "question": "Will BTC exceed $150,000 before December 31?",
        "description": "Resolution is based on Example Source.",
        "resolution_rules": "BTC must exceed $150,000 before 23:59 UTC on December 31.",
        "resolution_source": "Example Source",
        "end_time": "2026-12-31T23:59:00Z",
        "outcomes": ["Yes", "No"],
        "prices": [0.6, 0.4],
    }
    data.update(overrides)
    return Market(**data)


def test_normalizer_extracts_timezone_and_boundary():
    rules = normalize_rules(market())
    assert rules.timezone == "UTC"
    assert rules.has_boundary_language


def test_counterexample_covers_exact_boundary():
    m = market()
    cases = generate_counterexamples(m, normalize_rules(m))
    assert any(case.code == "CE001" for case in cases)


def test_counterexample_covers_source_unavailable():
    report = lint_market(market())
    assert any(case.code == "CE004" for case in report.counterexamples)


def test_market_tests_are_auditable():
    report = lint_market(market())
    source_test = next(item for item in report.tests if item.code == "MT002")
    assert source_test.status == TestStatus.PASS


def test_missing_timezone_creates_warning_test():
    report = lint_market(market(resolution_rules="BTC must exceed $150,000 before December 31."))
    timezone_test = next(item for item in report.tests if item.code == "MT003")
    assert timezone_test.status == TestStatus.WARNING
