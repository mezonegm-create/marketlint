# Security Policy

## Supported version

MarketLint is currently pre-1.0. Security fixes are applied to the latest code on `main`.

## Reporting a vulnerability

Please do not publish exploitable details in a public issue before a fix is available. Use GitHub's private vulnerability reporting feature for this repository when available.

A useful report includes the affected version or commit, reproduction steps, impact, and any suggested mitigation.

## Security model

MarketLint is designed as a read-only analysis tool. It should not require wallet seed phrases, private keys, trading credentials, or custody of user funds. Treat any change that introduces credential handling, transaction signing, or write access to a prediction-market account as a security-sensitive architectural change requiring explicit review.

Remote market data is untrusted input. Adapters and parsers should validate URLs, bound network behavior, avoid executing remote content, and fail clearly when upstream responses do not match expected structures.
