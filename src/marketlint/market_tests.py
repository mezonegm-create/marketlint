from __future__ import annotations

from marketlint.models import Market, MarketTest, NormalizedRules, TestStatus


def build_market_tests(market: Market, rules: NormalizedRules) -> list[MarketTest]:
    tests = [
        MarketTest(
            code="MT001",
            name="Resolution rules present",
            status=TestStatus.PASS if market.resolution_rules or market.description else TestStatus.FAIL,
            detail="Resolution text is available." if market.resolution_rules or market.description else "No resolution text is available.",
        ),
        MarketTest(
            code="MT002",
            name="Resolution source explicit",
            status=TestStatus.PASS if market.resolution_source else TestStatus.WARNING,
            detail=f"Named source: {market.resolution_source}" if market.resolution_source else "No structured resolution source was found.",
        ),
        MarketTest(
            code="MT003",
            name="Deadline timezone explicit",
            status=(TestStatus.PASS if rules.timezone else TestStatus.WARNING) if market.end_time and rules.has_boundary_language else TestStatus.NOT_APPLICABLE,
            detail=f"Timezone: {rules.timezone}" if rules.timezone else "A deadline/boundary exists without an explicit timezone in the inspected text.",
        ),
        MarketTest(
            code="MT004",
            name="Outcome/price shape",
            status=TestStatus.PASS if (not market.prices or len(market.prices) == len(market.outcomes)) else TestStatus.FAIL,
            detail=f"{len(market.outcomes)} outcomes; {len(market.prices)} prices.",
        ),
    ]
    return tests
