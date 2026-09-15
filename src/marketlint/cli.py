from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from marketlint.adapters.polymarket import fetch_market
from marketlint.linter import lint_market

app = typer.Typer(no_args_is_help=True, help="Lint and debug prediction markets.")
console = Console()


@app.command()
def lint(url: str, json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON.")) -> None:
    """Inspect a Polymarket market URL using deterministic checks."""
    try:
        market = fetch_market(url)
        report = lint_market(market)
    except Exception as exc:
        console.print(f"[red]MarketLint failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
        raise typer.Exit(code=1 if report.has_errors else 0)

    console.print(f"\n[bold]{market.question}[/bold]")
    console.print(f"Platform: {market.platform}  |  Market ID: {market.market_id or '-'}")
    table = Table("Code", "Severity", "Finding")
    for item in report.findings:
        table.add_row(item.code, item.severity.value.upper(), item.title)
    if report.findings:
        console.print(table)
    else:
        console.print("[green]No findings from the currently implemented rules.[/green]")
    raise typer.Exit(code=1 if report.has_errors else 0)


if __name__ == "__main__":
    app()
