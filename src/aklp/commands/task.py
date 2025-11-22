"""Task subcommands for AKLP CLI."""

import asyncio
from datetime import datetime
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from aklp.models import TaskPriority, TaskResponse, TaskStatus
from aklp.services.task import (
    TaskServiceError,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)

task_app = typer.Typer(
    name="task",
    help="Task 서비스 관리 명령어",
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


def _priority_color(priority: TaskPriority | None) -> str:
    """Get color for task priority."""
    if priority is None:
        return "dim"
    colors = {
        TaskPriority.HIGH: "red",
        TaskPriority.MEDIUM: "yellow",
        TaskPriority.LOW: "green",
    }
    return colors.get(priority, "white")


def _display_task(task: TaskResponse) -> None:
    """Display a single task."""
    status_color = _status_color(task.status)
    priority_str = task.priority.value if task.priority else "없음"
    priority_color = _priority_color(task.priority)

    console.print(f"\n[bold cyan]ID:[/bold cyan] {task.id}")
    console.print(f"[bold cyan]제목:[/bold cyan] {task.title}")
    if task.description:
        console.print(f"[bold cyan]설명:[/bold cyan] {task.description}")
    console.print(f"[bold cyan]상태:[/bold cyan] [{status_color}]{task.status.value}[/{status_color}]")
    console.print(f"[bold cyan]우선순위:[/bold cyan] [{priority_color}]{priority_str}[/{priority_color}]")
    if task.due_date:
        console.print(f"[bold cyan]마감일:[/bold cyan] {task.due_date.strftime('%Y-%m-%d %H:%M')}")
    if task.completed_at:
        console.print(f"[bold cyan]완료일:[/bold cyan] {task.completed_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"[dim]생성일: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print(f"[dim]수정일: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")


def _display_tasks_table(tasks: list[TaskResponse], total: int, page: int, total_pages: int) -> None:
    """Display tasks in a table format."""
    table = Table(title=f"Tasks (Page {page}/{total_pages}, Total: {total})")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("제목", style="cyan")
    table.add_column("상태")
    table.add_column("우선순위")
    table.add_column("마감일", style="dim")

    for task in tasks:
        status_color = _status_color(task.status)
        priority_str = task.priority.value if task.priority else "-"
        priority_color = _priority_color(task.priority)
        due_date_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else "-"

        table.add_row(
            str(task.id),
            task.title,
            f"[{status_color}]{task.status.value}[/{status_color}]",
            f"[{priority_color}]{priority_str}[/{priority_color}]",
            due_date_str,
        )

    console.print(table)


@task_app.command("create")
def create(
    title: Annotated[str, typer.Argument(help="작업 제목")],
    description: Annotated[str | None, typer.Option("--desc", "-d", help="작업 설명")] = None,
    priority: Annotated[str | None, typer.Option("--priority", "-p", help="우선순위 (high/medium/low)")] = None,
    due_date: Annotated[str | None, typer.Option("--due", help="마감일 (YYYY-MM-DD 형식)")] = None,
) -> None:
    """새 작업을 생성합니다."""
    try:
        task_priority = None
        if priority:
            try:
                task_priority = TaskPriority(priority.lower())
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 우선순위입니다: {priority}")
                console.print("[dim]유효한 값: high, medium, low[/dim]")
                raise typer.Exit(code=1)

        task_due_date = None
        if due_date:
            try:
                task_due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 날짜 형식입니다: {due_date}")
                console.print("[dim]형식: YYYY-MM-DD[/dim]")
                raise typer.Exit(code=1)

        task = asyncio.run(
            create_task(
                title=title,
                description=description,
                priority=task_priority,
                due_date=task_due_date,
            )
        )
        console.print("[green]작업이 생성되었습니다.[/green]")
        _display_task(task)
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@task_app.command("list")
def list_cmd(
    page: Annotated[int, typer.Option("--page", "-p", help="페이지 번호")] = 1,
    limit: Annotated[int, typer.Option("--limit", "-l", help="페이지당 항목 수")] = 10,
    status: Annotated[str | None, typer.Option("--status", "-s", help="상태 필터 (pending/in_progress/completed)")] = None,
) -> None:
    """작업 목록을 조회합니다."""
    try:
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 상태입니다: {status}")
                console.print("[dim]유효한 값: pending, in_progress, completed[/dim]")
                raise typer.Exit(code=1)

        result = asyncio.run(list_tasks(page=page, limit=limit, status=task_status))
        if not result.items:
            console.print("[yellow]작업이 없습니다.[/yellow]")
            return
        _display_tasks_table(result.items, result.total, result.page, result.total_pages)
        if result.has_next:
            console.print(f"\n[dim]다음 페이지: aklp task list --page {page + 1}[/dim]")
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@task_app.command("get")
def get_cmd(
    task_id: Annotated[str, typer.Argument(help="작업 UUID")],
) -> None:
    """특정 작업을 조회합니다."""
    try:
        uuid = UUID(task_id)
        task = asyncio.run(get_task(uuid))
        _display_task(task)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {task_id}")
        raise typer.Exit(code=1)
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@task_app.command("update")
def update_cmd(
    task_id: Annotated[str, typer.Argument(help="작업 UUID")],
    title: Annotated[str | None, typer.Option("--title", "-t", help="새 제목")] = None,
    description: Annotated[str | None, typer.Option("--desc", "-d", help="새 설명")] = None,
    status: Annotated[str | None, typer.Option("--status", "-s", help="새 상태 (pending/in_progress/completed)")] = None,
    priority: Annotated[str | None, typer.Option("--priority", "-p", help="새 우선순위 (high/medium/low)")] = None,
    due_date: Annotated[str | None, typer.Option("--due", help="새 마감일 (YYYY-MM-DD 형식)")] = None,
) -> None:
    """작업을 수정합니다."""
    if all(v is None for v in [title, description, status, priority, due_date]):
        console.print("[yellow]수정할 내용을 지정해주세요[/yellow]")
        console.print("[dim]옵션: --title, --desc, --status, --priority, --due[/dim]")
        raise typer.Exit(code=1)

    try:
        uuid = UUID(task_id)

        task_status = None
        if status:
            try:
                task_status = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 상태입니다: {status}")
                raise typer.Exit(code=1)

        task_priority = None
        if priority:
            try:
                task_priority = TaskPriority(priority.lower())
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 우선순위입니다: {priority}")
                raise typer.Exit(code=1)

        task_due_date = None
        if due_date:
            try:
                task_due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                console.print(f"[red]오류:[/red] 유효하지 않은 날짜 형식입니다: {due_date}")
                raise typer.Exit(code=1)

        task = asyncio.run(
            update_task(
                uuid,
                title=title,
                description=description,
                status=task_status,
                priority=task_priority,
                due_date=task_due_date,
            )
        )
        console.print("[green]작업이 수정되었습니다.[/green]")
        _display_task(task)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {task_id}")
        raise typer.Exit(code=1)
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@task_app.command("delete")
def delete_cmd(
    task_id: Annotated[str, typer.Argument(help="작업 UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="확인 없이 삭제")] = False,
) -> None:
    """작업을 삭제합니다."""
    try:
        uuid = UUID(task_id)

        if not force:
            confirm = typer.confirm(f"정말로 작업 {task_id}를 삭제하시겠습니까?")
            if not confirm:
                console.print("[yellow]삭제가 취소되었습니다.[/yellow]")
                return

        asyncio.run(delete_task(uuid))
        console.print(f"[green]작업 {task_id}가 삭제되었습니다.[/green]")
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {task_id}")
        raise typer.Exit(code=1)
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)


@task_app.command("done")
def done_cmd(
    task_id: Annotated[str, typer.Argument(help="작업 UUID")],
) -> None:
    """작업을 완료 상태로 변경합니다."""
    try:
        uuid = UUID(task_id)
        task = asyncio.run(update_task(uuid, status=TaskStatus.COMPLETED))
        console.print("[green]작업이 완료되었습니다.[/green]")
        _display_task(task)
    except ValueError:
        console.print(f"[red]오류:[/red] 유효하지 않은 UUID 형식입니다: {task_id}")
        raise typer.Exit(code=1)
    except TaskServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
