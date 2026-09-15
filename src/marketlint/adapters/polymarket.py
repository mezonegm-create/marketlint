from __future__ import annotations

import json
from urllib.parse import urlparse

import httpx

from marketlint.models import Market

GAMMA_API = "https://gamma-api.polymarket.com"


def _slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError("Polymarket URL has no market/event slug")
    if "event" in parts:
        idx = parts.index("event")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    if "market" in parts:
        idx = parts.index("market")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return parts[-1]


def _is_event_url(url: str) -> bool:
    return "event" in [part for part in urlparse(url).path.split("/") if part]


def _json_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _market_from_row(url: str, slug: str, row: dict) -> Market:
    outcomes = [str(x) for x in _json_list(row.get("outcomes"))]
    prices = []
    for value in _json_list(row.get("outcomePrices")):
        try:
            prices.append(float(value))
        except (TypeError, ValueError):
            pass
    return Market(
        platform="polymarket",
        url=url,
        market_id=str(row.get("id")) if row.get("id") is not None else None,
        question=row.get("question") or row.get("title") or slug,
        description=row.get("description"),
        resolution_rules=row.get("rules") or row.get("description"),
        resolution_source=row.get("resolutionSource") or row.get("source"),
        end_time=row.get("endDate") or row.get("endDateIso"),
        outcomes=outcomes,
        prices=prices,
        raw=row,
    )


def fetch_markets(url: str, client: httpx.Client | None = None) -> list[Market]:
    """Fetch one market or every child market belonging to a Polymarket event."""
    slug = _slug_from_url(url)
    owns_client = client is None
    client = client or httpx.Client(timeout=15, follow_redirects=True)
    try:
        rows: list[dict] = []
        if _is_event_url(url):
            response = client.get(f"{GAMMA_API}/events", params={"slug": slug})
            response.raise_for_status()
            events = response.json()
            rows = events[0].get("markets", []) if events else []
        else:
            response = client.get(f"{GAMMA_API}/markets", params={"slug": slug})
            response.raise_for_status()
            rows = response.json()
            if not rows:
                event_response = client.get(f"{GAMMA_API}/events", params={"slug": slug})
                event_response.raise_for_status()
                events = event_response.json()
                rows = events[0].get("markets", []) if events else []
        if not rows:
            raise ValueError(f"No Polymarket market found for slug: {slug}")
        return [_market_from_row(url, slug, row) for row in rows]
    finally:
        if owns_client:
            client.close()


def fetch_market(url: str, client: httpx.Client | None = None) -> Market:
    """Backward-compatible single-market fetch.

    Event URLs return their first child market. New callers that want complete
    event coverage should use fetch_markets().
    """
    return fetch_markets(url, client=client)[0]
