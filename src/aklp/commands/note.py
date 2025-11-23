"""Note subcommands for AKLP CLI."""

import asyncio
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from aklp.models import NoteResponse
from aklp.services.note import (
    NoteServiceError,
    create_note,
    delete_note,
    get_note,
    list_notes,
    update_note,
)

note_app = typer.Typer(
    name="note",
    help="Note 서비스 관리 명령어",
    no_args_is_help=True,
)
console = Console()


def _display_note(note: NoteResponse) -> None:
    """Display a single note."""
    console.print(f"\n[bold cyan]ID:[/bold cyan] {note.id}")
    console.print(f"[bold cyan]제목:[/bold cyan] {note.title}")
    console.print(f"[bold cyan]내용:[/bold cyan]\n{note.content}")
    console.print(f"[dim]생성일: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print(f"[dim]수정일: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    if note.session_id:
        console.print(f"[dim]세션 ID: {note.session_id}[/dim]")


def _display_notes_table(notes: list[NoteResponse], total: int, page: int, total_pages: int) -> None:
    """Display notes in a table format."""
    table = Table(title=f"Notes (Page {page}/{total_pages}, Total: {total})")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("제목", style="cyan")
    table.add_column("내용", max_width=40)
    table.add_column("생성일", style="dim")

    for note in notes:
        content_preview = note.content[:40] + "..." if len(note.content) > 40 else note.content
        table.add_row(
            str(note.id),
            note.title,
            content_preview,
            note.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@note_app.command("create")
def create(
    title: Annotated[str, typer.Argument(help="노트 제목")],
    content: Annotated[str, typer.Argument(help="노트 내용")],
) -> None:
    """새 노트를 생성합니다."""
    try:
        note = asyncio.run(create_note(title=title, content=content))
        console.print("[green]노트가 생성되었습니다.[/green]")
        _display_note(note)
    except NoteServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@note_app.command("list")
def list_cmd(
    page: Annotated[int, typer.Option("--page", "-p", help="페이지 번호")] = 1,
    session_id: Annotated[str | None, typer.Option("--session", "-s", help="세션 ID로 필터링")] = None,
) -> None:
    """노트 목록을 조회합니다."""
    try:
        result = asyncio.run(list_notes(page=page, session_id=session_id))
        if not result.items:
            console.print("[yellow]노트가 없습니다.[/yellow]")
            return
        _display_notes_table(result.items, result.total, result.page, result.total_pages)
        if result.has_next:
            console.print(f"\n[dim]다음 페이지: aklp note list --page {page + 1}[/dim]")
    except NoteServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@note_app.command("get")
def get_cmd(
    note_id: Annotated[str, typer.Argument(help="노트 UUID")],
) -> None:
    """특정 노트를 조회합니다."""
    try:
        uuid = UUID(note_id)
        note = asyncio.run(get_note(uuid))
        _display_note(note)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {note_id}")
        raise typer.Exit(code=1)
    except NoteServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@note_app.command("update")
def update_cmd(
    note_id: Annotated[str, typer.Argument(help="노트 UUID")],
    title: Annotated[str | None, typer.Option("--title", "-t", help="새 제목")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="새 내용")] = None,
) -> None:
    """노트를 수정합니다."""
    if title is None and content is None:
        console.print("[yellow]수정할 내용을 지정해주세요 (--title 또는 --content)[/yellow]")
        raise typer.Exit(code=1)

    try:
        uuid = UUID(note_id)
        note = asyncio.run(update_note(uuid, title=title, content=content))
        console.print("[green]노트가 수정되었습니다.[/green]")
        _display_note(note)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {note_id}")
        raise typer.Exit(code=1)
    except NoteServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@note_app.command("delete")
def delete_cmd(
    note_id: Annotated[str, typer.Argument(help="노트 UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="확인 없이 삭제")] = False,
) -> None:
    """노트를 삭제합니다."""
    try:
        uuid = UUID(note_id)

        if not force:
            confirm = typer.confirm(f"정말로 노트 {note_id}를 삭제하시겠습니까?")
            if not confirm:
                console.print("[yellow]삭제가 취소되었습니다.[/yellow]")
                return

        asyncio.run(delete_note(uuid))
        console.print(f"[green]노트 {note_id}가 삭제되었습니다.[/green]")
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {note_id}")
        raise typer.Exit(code=1)
    except NoteServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
