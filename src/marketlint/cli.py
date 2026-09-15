from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from marketlint.adapters.polymarket import fetch_markets, parse_polymarket_url
from marketlint.linter import lint_market
from marketlint.models import EventReport, LintReport
from marketlint.relations import analyze_relations

app = typer.Typer(no_args_is_help=True, help="Lint and debug prediction markets.")
console = Console()


def _render_market(report: LintReport) -> None:
    market = report.market
    console.print(f"\n[bold]{market.question}[/bold]")
    console.print(f"Platform: {market.platform}  |  Market ID: {market.market_id or '-'}")

    findings = Table("Code", "Severity", "Finding")
    for item in report.findings:
        findings.add_row(item.code, item.severity.value.upper(), item.title)
    if report.findings:
        console.print("\n[bold]Findings[/bold]")
        console.print(findings)

    tests = Table("Test", "Status", "Detail")
    for item in report.tests:
        tests.add_row(item.code, item.status.value.upper(), item.detail)
    console.print("\n[bold]Market Unit Tests[/bold]")
    console.print(tests)

    if report.counterexamples:
        console.print("\n[bold]Counterexamples to inspect[/bold]")
        for case in report.counterexamples:
            console.print(f"[bold]{case.code} — {case.title}[/bold]")
            console.print(f"  Scenario: {case.scenario}")
            console.print(f"  Question: {case.question}")

    if not report.findings:
        console.print("\n[green]No findings from the currently implemented lint rules.[/green]")


def _build_report(url: str) -> EventReport:
    markets = fetch_markets(url)
    reports = [lint_market(market) for market in markets]
    _, slug = parse_polymarket_url(url)
    return EventReport(
        url=url,
        slug=slug,
        markets=reports,
        relations=analyze_relations(markets),
    )


def _run(url: str, json_output: bool) -> None:
    try:
        event = _build_report(url)
    except Exception as exc:
        console.print(f"[red]MarketLint failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(event.model_dump(mode="json"), indent=2, ensure_ascii=False))
        raise typer.Exit(code=1 if event.has_errors else 0)

    if len(event.markets) > 1:
        console.print(f"\n[bold]Event: {event.slug}[/bold] — {len(event.markets)} child markets")
    for report in event.markets:
        _render_market(report)

    if event.relations:
        relations = Table("Kind", "Markets", "Price check", "Relation")
        for item in event.relations:
            if item.kind.value == "implies" and item.antecedent_market_id:
                pair = f"{item.antecedent_market_id} → {item.consequent_market_id or '-'}"
            else:
                pair = f"{item.left_market_id or '-'} ↔ {item.right_market_id or '-'}"
            if item.price_consistent is True:
                price_check = "PASS"
            elif item.price_consistent is False:
                price_check = "TENSION"
            else:
                price_check = "N/A"
            detail = item.detail
            if item.price_detail:
                detail = f"{detail} {item.price_detail}"
            relations.add_row(item.kind.value.upper(), pair, price_check, detail)
        console.print("\n[bold]Cross-market relations[/bold]")
        console.print(relations)

    raise typer.Exit(code=1 if event.has_errors else 0)


@app.command()
def lint(
    url: str,
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Lint a Polymarket market or all child markets in an event."""
    _run(url, json_output)


@app.command()
def inspect(
    url: str,
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Inspect a Polymarket market or event; alias for lint."""
    _run(url, json_output)


if __name__ == "__main__":
    app()
