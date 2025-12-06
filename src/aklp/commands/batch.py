"""Batch subcommands for AKLP CLI."""

import asyncio
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from aklp.models import BatchResponse, TaskStatus
from aklp.services.batch import (
    BatchServiceError,
    get_batch,
    get_latest_batch,
    list_batches,
)

batch_app = typer.Typer(
    name="batch",
    help="Batch 서비스 관리 명령어",
    no_args_is_help=True,
)
console = Console()


def _status_color(status: TaskStatus) -> str:
    """Get color for task status."""
    colors = {
        TaskStatus.PENDING: "yellow",
        TaskStatus.IN_PROGRESS: "blue",
        TaskStatus.COMPLETED: "green",
    }
    return colors.get(status, "white")


def _display_batch(batch: BatchResponse) -> None:
    """Display a single batch with its tasks."""
    console.print(f"\n[bold cyan]Batch ID:[/bold cyan] {batch.id}")
    if batch.reason:
        console.print(f"[bold cyan]사유:[/bold cyan] {batch.reason}")
    console.print(f"[dim]생성일: {batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    if batch.session_id:
        console.print(f"[dim]세션 ID: {batch.session_id}[/dim]")

    if batch.tasks:
        console.print(f"\n[bold cyan]태스크 ({len(batch.tasks)}개):[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", max_width=36)
        table.add_column("제목", style="cyan")
        table.add_column("상태")

        for task in batch.tasks:
            status_color = _status_color(task.status)
            table.add_row(
                str(task.id),
                task.title,
                f"[{status_color}]{task.status.value}[/{status_color}]",
            )

        console.print(table)
    else:
        console.print("\n[dim]태스크가 없습니다.[/dim]")


def _display_batches_table(batches: list[BatchResponse], total: int, page: int, total_pages: int) -> None:
    """Display batches in a table format."""
    table = Table(title=f"Batches (Page {page}/{total_pages}, Total: {total})")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("사유", style="cyan", max_width=40)
    table.add_column("태스크 수", justify="right")
    table.add_column("생성일", style="dim")

    for batch in batches:
        reason_preview = (batch.reason[:37] + "...") if batch.reason and len(batch.reason) > 40 else (batch.reason or "-")
        table.add_row(
            str(batch.id),
            reason_preview,
            str(len(batch.tasks)),
            batch.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@batch_app.command("list")
def list_cmd(
    page: Annotated[int, typer.Option("--page", "-p", help="페이지 번호")] = 1,
    session_id: Annotated[str | None, typer.Option("--session", "-s", help="세션 ID로 필터링")] = None,
) -> None:
    """배치 목록을 조회합니다."""
    try:
        result = asyncio.run(list_batches(page=page, session_id=session_id))
        if not result.items:
            console.print("[yellow]배치가 없습니다.[/yellow]")
            return
        _display_batches_table(result.items, result.total, result.page, result.total_pages)
        if result.has_next:
            console.print(f"\n[dim]다음 페이지: aklp batch list --page {page + 1}[/dim]")
    except BatchServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@batch_app.command("get")
def get_cmd(
    batch_id: Annotated[str, typer.Argument(help="배치 UUID")],
) -> None:
    """특정 배치를 조회합니다."""
    try:
        uuid = UUID(batch_id)
        batch = asyncio.run(get_batch(uuid))
        _display_batch(batch)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {batch_id}")
        raise typer.Exit(code=1)
    except BatchServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@batch_app.command("latest")
def latest_cmd(
    session_id: Annotated[str | None, typer.Option("--session", "-s", help="세션 ID로 필터링")] = None,
) -> None:
    """최신 배치를 조회합니다."""
    try:
        batch = asyncio.run(get_latest_batch(session_id=session_id))
        if not batch:
            console.print("[yellow]배치가 없습니다.[/yellow]")
            return
        _display_batch(batch)
    except BatchServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
