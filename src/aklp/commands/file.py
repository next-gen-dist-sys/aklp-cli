"""File subcommands for AKLP CLI."""

import asyncio
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from aklp.models import FileResponse
from aklp.services.file import (
    FileServiceError,
    delete_file,
    download_file,
    get_file,
    list_files,
    replace_file,
    update_file_metadata,
    upload_file,
)

file_app = typer.Typer(
    name="file",
    help="File 서비스 관리 명령어",
    no_args_is_help=True,
)
console = Console()


def _display_file(file: FileResponse) -> None:
    """Display a single file metadata."""
    console.print(f"\n[bold cyan]ID:[/bold cyan] {file.id}")
    console.print(f"[bold cyan]파일명:[/bold cyan] {file.filename}")
    console.print(f"[bold cyan]타입:[/bold cyan] {file.content_type}")
    console.print(f"[bold cyan]크기:[/bold cyan] {file.size_human}")
    if file.description:
        console.print(f"[bold cyan]설명:[/bold cyan] {file.description}")
    console.print(f"[dim]생성일: {file.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print(f"[dim]수정일: {file.updated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    if file.session_id:
        console.print(f"[dim]세션 ID: {file.session_id}[/dim]")


def _display_files_table(
    files: list[FileResponse], total: int, page: int, total_pages: int
) -> None:
    """Display files in a table format."""
    table = Table(title=f"Files (Page {page}/{total_pages}, Total: {total})")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("파일명", style="cyan")
    table.add_column("타입", max_width=20)
    table.add_column("크기", justify="right")
    table.add_column("생성일", style="dim")

    for file in files:
        table.add_row(
            str(file.id),
            file.filename,
            file.content_type,
            file.size_human,
            file.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@file_app.command("upload")
def upload_cmd(
    file_path: Annotated[Path, typer.Argument(help="업로드할 파일 경로")],
    description: Annotated[str | None, typer.Option("--desc", "-d", help="파일 설명")] = None,
) -> None:
    """파일을 업로드합니다."""
    try:
        file = asyncio.run(upload_file(file_path=file_path, description=description))
        console.print("[green]파일이 업로드되었습니다.[/green]")
        _display_file(file)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@file_app.command("list")
def list_cmd(
    page: Annotated[int, typer.Option("--page", "-p", help="페이지 번호")] = 1,
    session_id: Annotated[
        str | None, typer.Option("--session", "-s", help="세션 ID로 필터링")
    ] = None,
) -> None:
    """파일 목록을 조회합니다."""
    try:
        result = asyncio.run(list_files(page=page, session_id=session_id))
        if not result.items:
            console.print("[yellow]파일이 없습니다.[/yellow]")
            return
        _display_files_table(result.items, result.total, result.page, result.total_pages)
        if result.has_next:
            console.print(f"\n[dim]다음 페이지: aklp file list --page {page + 1}[/dim]")
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@file_app.command("get")
def get_cmd(
    file_id: Annotated[str, typer.Argument(help="파일 UUID")],
) -> None:
    """특정 파일의 메타데이터를 조회합니다."""
    try:
        uuid = UUID(file_id)
        file = asyncio.run(get_file(uuid))
        _display_file(file)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {file_id}")
        raise typer.Exit(code=1)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@file_app.command("download")
def download_cmd(
    file_id: Annotated[str, typer.Argument(help="파일 UUID")],
    output: Annotated[Path | None, typer.Option("--output", "-o", help="저장할 경로")] = None,
) -> None:
    """파일을 다운로드합니다."""
    try:
        uuid = UUID(file_id)
        content, filename, content_type = asyncio.run(download_file(uuid))

        # Determine output path
        if output:
            output_path = output
        else:
            output_path = Path.cwd() / filename

        # Write file
        output_path.write_bytes(content)
        console.print(f"[green]파일이 다운로드되었습니다:[/green] {output_path}")
        console.print(f"[dim]크기: {len(content):,} bytes, 타입: {content_type}[/dim]")

    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {file_id}")
        raise typer.Exit(code=1)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
    except OSError as e:
        console.print(f"[red]오류:[/red] 파일 저장 실패: {e}")
        raise typer.Exit(code=1)


@file_app.command("update")
def update_cmd(
    file_id: Annotated[str, typer.Argument(help="파일 UUID")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="새 파일명")] = None,
    description: Annotated[str | None, typer.Option("--desc", "-d", help="새 설명")] = None,
) -> None:
    """파일 메타데이터를 수정합니다."""
    if name is None and description is None:
        console.print("[yellow]수정할 내용을 지정해주세요 (--name 또는 --desc)[/yellow]")
        raise typer.Exit(code=1)

    try:
        uuid = UUID(file_id)
        file = asyncio.run(update_file_metadata(uuid, filename=name, description=description))
        console.print("[green]파일 메타데이터가 수정되었습니다.[/green]")
        _display_file(file)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {file_id}")
        raise typer.Exit(code=1)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@file_app.command("replace")
def replace_cmd(
    file_id: Annotated[str, typer.Argument(help="파일 UUID")],
    file_path: Annotated[Path, typer.Argument(help="새 파일 경로")],
) -> None:
    """파일 내용을 교체합니다."""
    try:
        uuid = UUID(file_id)
        file = asyncio.run(replace_file(uuid, file_path))
        console.print("[green]파일이 교체되었습니다.[/green]")
        _display_file(file)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {file_id}")
        raise typer.Exit(code=1)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@file_app.command("delete")
def delete_cmd(
    file_id: Annotated[str, typer.Argument(help="파일 UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="확인 없이 삭제")] = False,
) -> None:
    """파일을 삭제합니다."""
    try:
        uuid = UUID(file_id)

        if not force:
            confirm = typer.confirm(f"정말로 파일 {file_id}를 삭제하시겠습니까?")
            if not confirm:
                console.print("[yellow]삭제가 취소되었습니다.[/yellow]")
                return

        asyncio.run(delete_file(uuid))
        console.print(f"[green]파일 {file_id}가 삭제되었습니다.[/green]")
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {file_id}")
        raise typer.Exit(code=1)
    except FileServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
