from marketlint.linter import lint_market
from marketlint.models import Market


def case(rules: str, source: str | None = "Official Source") -> Market:
    return Market(
        platform="polymarket",
        url="https://polymarket.com/event/regression-case",
        question="Will the event condition be met?",
        resolution_rules=rules,
        resolution_source=source,
        outcomes=["Yes", "No"],
        prices=[0.5, 0.5],
    )


REGRESSION_CASES = [
    (
        "ambiguous-source-priority",
        "According to Official Source or other reliable sources, the published result controls.",
        "ML009",
    ),
    (
        "vague-friday-deadline",
        "According to Official Source, the announcement must happen by Friday.",
        "ML010",
    ),
    (
        "unhandled-postponement",
        "According to Official Source, the event may be postponed and results are checked later.",
        "ML011",
    ),
    (
        "revision-sensitive-release",
        "According to Official Source, use the preliminary estimate published for the period.",
        "ML008",
    ),
]


def test_realistic_resolution_regression_cases_remain_detected():
    for name, rules, expected_code in REGRESSION_CASES:
        report = lint_market(case(rules))
        codes = {item.code for item in report.findings}
        assert expected_code in codes, f"{name}: expected {expected_code}, got {sorted(codes)}"
