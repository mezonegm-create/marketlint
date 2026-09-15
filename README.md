# MarketLint

**Lint prediction markets before they surprise you.**

MarketLint is an open-source linter and debugger for prediction markets.

Give it a prediction-market URL and MarketLint will analyze the market's rules, resolution conditions, sources, deadlines, and logical structure to uncover potential ambiguity, edge cases, and inconsistencies.

> Think of it like ESLint — but for prediction markets.

## The Idea

Prediction markets can look simple:

**YES — 63%**  
**NO — 37%**

But the contract behind that number may not be simple.

Questions can hide important details:

- What exactly counts as the event occurring?
- Which source determines the outcome?
- What happens at the deadline?
- Which timezone applies?
- What happens at an exact boundary value?
- Are any terms ambiguous?
- Could related markets imply contradictory outcomes?

MarketLint is being built to test these questions systematically.

## Planned Core

### Rule Linting
Analyze resolution rules and identify potentially ambiguous or underspecified conditions.

### Market Unit Tests
Turn market conditions into explicit tests that can be checked and reproduced.

### Counterexample Generation
Try to construct edge cases that stress assumptions in the market's rules.

### Logical Consistency Checks
Analyze relationships between related markets for possible inconsistencies.

### Resolution Source Inspection
Identify what source actually determines the outcome and how it is used.

## First Target

Initial development will focus on **Polymarket**.

Support for additional prediction-market platforms may be explored later.

## Design Principles

MarketLint should be:

- Open source
- Read-only by default
- Reproducible
- Evidence-based
- Auditable
- Useful without connecting a wallet
- Deterministic whenever a rule can be checked programmatically

AI may assist with extracting rules and generating edge cases, but it should not replace verifiable checks where deterministic validation is possible.

## Status

🚧 **Early development**

MarketLint is currently being designed and implemented.

The API, CLI, schemas, and architecture may change significantly during early development.

## What MarketLint Is Not

MarketLint is not a trading bot.

It does not promise profitable trades or attempt to predict market outcomes.

Its purpose is to help inspect and test the structure of prediction markets.

---

**MarketLint**

*Try to break the market before the market breaks your assumptions.*
