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


def test_flags_undefined_subjective_resolution_language():
    report = lint_market(
        market(
            question="Will there be a major disruption before December 31?",
            resolution_rules=(
                "According to Example Source, the market resolves Yes if a major disruption "
                "occurs before 23:59 UTC on December 31."
            ),
            resolution_source="Example Source",
        )
    )
    finding = next(item for item in report.findings if item.code == "ML007")
    assert finding.severity == Severity.WARNING
    assert "subjective term: major" in finding.evidence


def test_subjective_term_with_objective_definition_is_not_flagged():
    report = lint_market(
        market(
            question="Will there be a major disruption before December 31?",
            resolution_rules=(
                "According to Example Source, major is defined as an outage affecting at least "
                "1,000,000 users before 23:59 UTC on December 31."
            ),
            resolution_source="Example Source",
        )
    )
    assert not any(item.code == "ML007" for item in report.findings)


def test_subjective_terms_are_deduplicated_in_evidence():
    report = lint_market(
        market(
            question="Will a significant event occur?",
            resolution_rules="A significant event must be reported by Example Source. Significant events qualify.",
            resolution_source="Example Source",
        )
    )
    finding = next(item for item in report.findings if item.code == "ML007")
    assert finding.evidence == ["subjective term: significant"]


def test_flags_revision_sensitive_data_without_policy():
    report = lint_market(
        market(
            resolution_rules=(
                "According to Example Source, this resolves using the preliminary GDP estimate "
                "published before 23:59 UTC on December 31."
            ),
            resolution_source="Example Source",
        )
    )
    finding = next(item for item in report.findings if item.code == "ML008")
    assert finding.severity == Severity.WARNING
    assert "revision-sensitive term: preliminary" in finding.evidence


def test_revision_sensitive_data_with_policy_is_not_flagged():
    report = lint_market(
        market(
            resolution_rules=(
                "According to Example Source, this resolves using the preliminary GDP estimate. "
                "The first release controls resolution and later revisions will not count."
            ),
            resolution_source="Example Source",
        )
    )
    assert not any(item.code == "ML008" for item in report.findings)


def test_risk_summary_is_machine_readable():
    report = lint_market(market())
    assert report.risk_summary is not None
    assert report.risk_summary.warnings >= 1
    dumped = report.model_dump(mode="json")
    assert dumped["risk_summary"]["level"] in {"low", "review", "elevated", "high"}
