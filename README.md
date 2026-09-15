# MarketLint

**Lint prediction markets before they surprise you.**

MarketLint is an open-source, read-only linter and debugger for prediction markets. Give it a Polymarket market or event URL and it turns resolution text and sibling markets into reproducible findings, tests, counterexamples, logical relations, and machine-readable evidence.

> Think of it like ESLint — but for prediction markets.

## What works today

- Fetch a Polymarket market or every child market in an event.
- Validate Polymarket URLs and ingest public Gamma API data without a wallet or API key.
- Normalize resolution rules, deadlines, timezones, sources, and fallback language.
- Run deterministic lint checks with stable finding codes.
- Generate auditable Market Unit Tests.
- Generate counterexamples for exact boundaries, timezone edges, source conflicts, and source outages.
- Compare sibling threshold markets for duplicates, implication, and mutual exclusion.
- Distinguish strict and inclusive threshold semantics (`>`, `>=`, `<`, `<=`).
- Keep currencies and percentages separate when comparing thresholds.
- Detect monotonic price tensions as consistency signals, not trading advice.
- Emit directional implication evidence and JSON output.

## Install

MarketLint requires Python 3.11 or newer.

```bash
git clone https://github.com/mezonegm-create/marketlint.git
cd marketlint
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

Inspect a Polymarket market or event:

```bash
marketlint lint "https://polymarket.com/event/<slug>"
```

Emit a machine-readable report:

```bash
marketlint lint "https://polymarket.com/event/<slug>" --json
```

Exit codes are designed for automation: `0` means no implemented lint/test errors, `1` means the report contains an error/failing test, and `2` means MarketLint could not inspect the input.

## Report model

A report can contain:

- `findings` — lint diagnostics such as missing rules, missing source, or timezone ambiguity.
- `tests` — deterministic Market Unit Tests with pass/warning/fail status.
- `counterexamples` — concrete edge cases worth checking against the contract wording.
- `relations` — cross-market duplicate, implication, and mutual-exclusion relationships.
- `evidence` — parsed facts used to support deterministic relation analysis.
- `price_consistent` / `price_detail` — structural price-consistency signals when comparable YES prices are available.

For implication relations, `antecedent_market_id` identifies the tighter condition and `consequent_market_id` identifies the condition it logically implies, assuming the markets share the same resolution scope.

## Current lint rules

| Code | Meaning |
| --- | --- |
| ML001 | Resolution rules are missing |
| ML002 | Time boundary is present without an explicit timezone |
| ML003 | Resolution source is not explicit |
| ML004 | Outcomes are unavailable |
| ML005 | Outcome/price shapes do not match |
| ML006 | No explicit source fallback is described |

The rule set will grow while keeping codes stable wherever practical.

## Architecture

```text
Market URL
    |
    v
Polymarket Ingestor
    |
    v
Rule Normalizer
    |
    +--> Rule Linter
    +--> Market Unit Tests
    +--> Counterexample Engine
    |
    v
Sibling Relation Engine
    |
    +--> threshold semantics
    +--> implication / exclusivity
    +--> price consistency
    |
    v
CLI Report + JSON
```

## Design principles

MarketLint is intentionally read-only, reproducible, evidence-based, auditable, and useful without connecting a wallet. Deterministic checks are preferred whenever the rules can be verified programmatically. AI may assist future extraction or edge-case generation, but should not replace deterministic validation when deterministic validation is possible.

## Limitations

MarketLint is an analysis tool, not an oracle. Natural-language contracts can contain semantics the current parser does not understand. A detected relationship assumes comparable markets share the same relevant resolution scope. Displayed outcome prices are used only for structural consistency checks; they are not executable order-book quotes and do not establish an arbitrage or expected profit.

Current relation parsing focuses on one-dimensional threshold questions. More complex intervals, categorical relationships, source equivalence, and historical resolution validation are future work.

## Development

Run the quality gates locally:

```bash
ruff check .
pytest -q
```

CI runs Ruff and the test suite on Python 3.11, 3.12, and 3.13.

## What MarketLint is not

MarketLint is not a trading bot and does not tell users what outcome to buy. It does not promise profitable trades or attempt to predict real-world outcomes. Its purpose is to inspect and test the structure of prediction markets.

## License

MIT. See `LICENSE`.

---

*Try to break the market before the market breaks your assumptions.*
