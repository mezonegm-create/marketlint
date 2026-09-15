from __future__ import annotations

import json
from urllib.parse import urlparse

import httpx

from marketlint.models import Market

GAMMA_API = "https://gamma-api.polymarket.com"
_ALLOWED_HOSTS = {"polymarket.com", "www.polymarket.com"}


def _parse_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("Expected a polymarket.com market or event URL")
    parts = [part for part in parsed.path.split("/") if part]
    for kind in ("event", "market"):
        if kind in parts:
            idx = parts.index(kind)
            if idx + 1 < len(parts):
                return kind, parts[idx + 1]
    raise ValueError("Polymarket URL must contain /event/<slug> or /market/<slug>")


def _slug_from_url(url: str) -> str:
    return _parse_url(url)[1]


def _is_event_url(url: str) -> bool:
    return _parse_url(url)[0] == "event"


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


def _market_from_row(url: str, slug: str, row: dict, event: dict | None = None) -> Market:
    outcomes = [str(x) for x in _json_list(row.get("outcomes"))]
    prices = []
    for value in _json_list(row.get("outcomePrices")):
        try:
            prices.append(float(value))
        except (TypeError, ValueError):
            pass

    event = event or {}
    description = row.get("description") or event.get("description")
    source = row.get("resolutionSource") or event.get("resolutionSource")
    return Market(
        platform="polymarket",
        url=url,
        market_id=str(row.get("id")) if row.get("id") is not None else None,
        question=row.get("question") or row.get("title") or slug,
        description=description,
        resolution_rules=row.get("rules") or description,
        resolution_source=source,
        end_time=row.get("endDate") or event.get("endDate"),
        outcomes=outcomes,
        prices=prices,
        raw=row,
    )


def _get_event(client: httpx.Client, slug: str) -> dict | None:
    response = client.get(f"{GAMMA_API}/events/slug/{slug}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else None


def _get_market(client: httpx.Client, slug: str) -> dict | None:
    response = client.get(f"{GAMMA_API}/markets/slug/{slug}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else None


def fetch_markets(url: str, client: httpx.Client | None = None) -> list[Market]:
    """Fetch one market or every child market belonging to a Polymarket event."""
    kind, slug = _parse_url(url)
    owns_client = client is None
    client = client or httpx.Client(timeout=15, follow_redirects=True)
    try:
        if kind == "event":
            event = _get_event(client, slug)
            rows = event.get("markets", []) if event else []
            if not rows:
                raise ValueError(f"No Polymarket markets found for event slug: {slug}")
            return [_market_from_row(url, slug, row, event) for row in rows]

        row = _get_market(client, slug)
        if not row:
            raise ValueError(f"No Polymarket market found for slug: {slug}")
        return [_market_from_row(url, slug, row)]
    finally:
        if owns_client:
            client.close()


def fetch_market(url: str, client: httpx.Client | None = None) -> Market:
    """Fetch exactly one market URL, or the first child of an event for compatibility."""
    return fetch_markets(url, client=client)[0]
