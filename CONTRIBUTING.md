# Contributing to MarketLint

Thanks for helping make prediction-market contracts easier to inspect and test.

## Development setup

MarketLint requires Python 3.11+.

```bash
git clone https://github.com/mezonegm-create/marketlint.git
cd marketlint
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Before submitting a change, run:

```bash
ruff check .
pytest -q
```

## Contribution principles

- Prefer deterministic, reproducible checks over opaque judgments.
- Include evidence with diagnostics when practical.
- Add tests for every parser or lint-rule behavior change.
- Keep existing diagnostic codes stable unless there is a strong compatibility reason to change them.
- Treat price checks as structural consistency signals, not profit claims or trading recommendations.
- Do not require wallet credentials for analysis features.
- Keep platform adapters separated from the core analysis engine.

## Adding a lint rule

A useful lint rule should have a stable code, a clear severity, a concise explanation, reproducible evidence where possible, and tests for both positive and negative cases.

## Adding relation semantics

Relation logic should only compare markets when the parser has enough evidence that their units and topics are compatible. If the relationship depends on an assumption, expose that assumption in the report instead of silently treating it as fact.

## Pull requests

Keep pull requests focused. Explain the behavior change, add or update tests, and make sure CI is green on every supported Python version.
