"""Agent subcommands for AKLP CLI."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from aklp.services.agent import AgentServiceError, execute_command

agent_app = typer.Typer(
    name="agent",
    help="Agent 서비스 관리 명령어",
    no_args_is_help=True,
)
console = Console()


def _display_agent_result(result) -> None:
    """Display agent result."""
    if not result.success:
        console.print(
            Panel(
                f"[red]{result.error_message or '알 수 없는 오류'}[/red]",
                title="[red]Agent 오류[/red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        return

    content = Text()

    if result.title:
        content.append(f"{result.title}\n\n", style="bold blue")

    if result.reason:
        content.append("설명: ", style="dim")
        content.append(f"{result.reason}\n\n", style="")

    if result.command:
        content.append("명령어:\n", style="bold yellow")
        content.append(result.command, style="bold")

    console.print(
        Panel(
            content,
            border_style="blue",
            padding=(1, 2),
        )
    )


@agent_app.command("execute")
def execute_cmd(
    prompt: Annotated[str, typer.Argument(help="자연어 명령어")],
) -> None:
    """자연어를 kubectl 명령어로 변환합니다."""
    try:
        with console.status("[bold green]Agent가 명령어를 분석하고 있습니다...[/bold green]"):
            result = asyncio.run(execute_command(prompt))
        _display_agent_result(result)

        if result.success and result.command:
            console.print()
            if typer.confirm("이 명령어를 클립보드에 복사하시겠습니까?", default=False):
                try:
                    import pyperclip
                    pyperclip.copy(result.command)
                    console.print("[green]명령어가 클립보드에 복사되었습니다.[/green]")
                except ImportError:
                    console.print("[yellow]pyperclip이 설치되지 않아 클립보드 복사가 불가능합니다.[/yellow]")
                except Exception:
                    console.print("[yellow]클립보드 복사에 실패했습니다.[/yellow]")

    except AgentServiceError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
