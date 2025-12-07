"""Usage subcommands for AKLP CLI."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from aklp.models import UsageStats
from aklp.services.usage import UsageServiceError, get_usage

usage_app = typer.Typer(
    name="usage",
    help="API 사용량 조회 명령어",
    no_args_is_help=False,
)
console = Console()


def _display_usage_stats(stats: UsageStats) -> None:
    """Display usage statistics."""
    period_labels = {
        "today": "오늘",
        "month": "이번 달",
        "all": "전체",
    }
    period_label = period_labels.get(stats.period, stats.period)

    console.print()

    table = Table(
        title=f"[bold cyan]OpenAI API 사용량 ({period_label})[/bold cyan]",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    table.add_column("항목", style="dim")
    table.add_column("값", justify="right")

    table.add_row("Input Tokens", f"{stats.total_input_tokens:,}")
    table.add_row("Output Tokens", f"{stats.total_output_tokens:,}")
    table.add_row("Cached Tokens", f"{stats.total_cached_tokens:,}")
    table.add_row("요청 수", f"{stats.request_count:,}")
    table.add_row("총 비용", f"[bold green]${stats.total_cost_usd:.6f}[/bold green]")

    console.print(table)

    if stats.period_start:
        console.print()
        console.print(f"[dim]기간: {stats.period_start.strftime('%Y-%m-%d %H:%M')} UTC ~[/dim]")


@usage_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    period: Annotated[
        str, typer.Option("--period", "-p", help="조회 기간 (today/month/all)")
    ] = "all",
) -> None:
    """API 사용량을 조회합니다."""
    if ctx.invoked_subcommand is not None:
        return

    if period not in ("today", "month", "all"):
        console.print(f"[red]오류:[/red] 유효하지 않은 기간입니다: {period}")
        console.print("[dim]유효한 값: today, month, all[/dim]")
        raise typer.Exit(code=1)

    try:
        with console.status("[bold green]사용량 조회 중...[/bold green]"):
            result = asyncio.run(get_usage(period=period))
        stats = UsageStats.model_validate(result["data"])
        _display_usage_stats(stats)
    except UsageServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]오류:[/red] 예상치 못한 오류: {e}")
        raise typer.Exit(code=1)


@usage_app.command("today")
def today_cmd() -> None:
    """오늘의 API 사용량을 조회합니다."""
    try:
        with console.status("[bold green]사용량 조회 중...[/bold green]"):
            result = asyncio.run(get_usage(period="today"))
        stats = UsageStats.model_validate(result["data"])
        _display_usage_stats(stats)
    except UsageServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@usage_app.command("month")
def month_cmd() -> None:
    """이번 달 API 사용량을 조회합니다."""
    try:
        with console.status("[bold green]사용량 조회 중...[/bold green]"):
            result = asyncio.run(get_usage(period="month"))
        stats = UsageStats.model_validate(result["data"])
        _display_usage_stats(stats)
    except UsageServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
