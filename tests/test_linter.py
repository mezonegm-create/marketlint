from marketlint.linter import lint_market
from marketlint.models import Market, Severity


def market(**overrides):
    data = {
        "platform": "polymarket",
        "url": "https://polymarket.com/event/example",
        "question": "Will X happen before December 31?",
        "description": "The market resolves based on the stated rules.",
        "resolution_rules": "X must happen before December 31.",
        "resolution_source": None,
        "end_time": "2026-12-31T23:59:00Z",
        "outcomes": ["Yes", "No"],
        "prices": [0.6, 0.4],
    }
    data.update(overrides)
    return Market(**data)


def test_flags_missing_source():
    report = lint_market(market())
    assert any(item.code == "ML003" for item in report.findings)


def test_flags_boundary_without_timezone():
    report = lint_market(market())
    assert any(item.code == "ML002" for item in report.findings)


def test_flags_price_shape_mismatch_as_error():
    report = lint_market(market(prices=[0.6]))
    finding = next(item for item in report.findings if item.code == "ML005")
    assert finding.severity == Severity.ERROR
    assert report.has_errors


def test_clean_structural_market_has_no_errors():
    report = lint_market(
        market(
            resolution_rules="According to Example Source, X must happen before 23:59 UTC on December 31.",
            resolution_source="Example Source",
        )
    )
    assert not report.has_errors
