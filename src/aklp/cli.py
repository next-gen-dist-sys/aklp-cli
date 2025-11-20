"""Main CLI application using Typer."""

import asyncio
import sys
import time
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from aklp.config import get_settings
from aklp.history import HistoryManager
from aklp.models import ConversationTurn
from aklp.services.llm import LLMServiceError, analyze_prompt
from aklp.services.note import NoteServiceError, create_file
from aklp.services.task import TaskServiceError, execute_command
from aklp.ui.display import (
    confirm_execution,
    display_analysis_result,
    display_cancellation_message,
    display_completion_message,
    display_error,
    display_goodbye_message,
    display_help,
    display_history,
    display_history_cleared,
    display_success,
    display_task_result,
    display_turn_separator,
    display_welcome_message,
    get_user_input,
)

app = typer.Typer(
    name="aklp",
    help="MSA CLI Agent - Automate tasks with natural language",
    add_completion=False,
)
console = Console()


def validate_configuration() -> bool:
    """Validate that all required configuration is present.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        settings = get_settings()
        console.print("[dim]서비스 연결 정보:[/dim]")
        console.print(f"[dim]  • LLM: {settings.llm_service_url}[/dim]")
        console.print(f"[dim]  • Note: {settings.note_service_url}[/dim]")
        console.print(f"[dim]  • Task: {settings.task_service_url}[/dim]")
        return True
    except ValidationError:
        display_error("환경 설정 오류")
        console.print("\n필요한 환경 변수가 설정되지 않았습니다:")
        console.print("  • LLM_SERVICE_URL")
        console.print("  • NOTE_SERVICE_URL")
        console.print("  • TASK_SERVICE_URL")
        console.print("\n.env 파일을 생성하거나 환경 변수를 설정해주세요.")
        console.print("예시: .env.example 파일을 참조하세요.")
        return False


async def process_user_request(
    prompt: str,
    history_manager: HistoryManager | None = None,
) -> ConversationTurn:
    """Process a single user request.

    Args:
        prompt: User's natural language request
        history_manager: Optional history manager to record turn

    Returns:
        ConversationTurn: Record of this conversation turn
    """
    turn = ConversationTurn(user_prompt=prompt)

    try:
        with console.status(
            "[bold green]AI가 요청을 분석하고 있습니다...[/bold green]",
            spinner="dots",
        ):
            analysis_result = await analyze_prompt(prompt)

        turn.analysis = analysis_result
        display_analysis_result(analysis_result)

        if not confirm_execution():
            display_cancellation_message()
            turn.executed = False
            return turn

        turn.executed = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("파일 생성 중...", total=1)

            note_response = await create_file(
                filename=analysis_result.filename,
                content=analysis_result.file_content,
            )

            turn.note_response = note_response

            if note_response.success:
                display_success(
                    f"파일 생성 완료: {note_response.filepath or analysis_result.filename}"
                )
            else:
                display_error(f"파일 생성 실패: {note_response.message}")
                turn.error = note_response.message
                return turn

            progress.update(task1, completed=1)

            task2 = progress.add_task("명령어 실행 중...", total=1)

            task_response = await execute_command(analysis_result.shell_command)
            turn.task_response = task_response

            progress.update(task2, completed=1)

        display_task_result(task_response)

    except LLMServiceError as e:
        error_msg = f"LLM 서비스 오류: {str(e)}"
        display_error(error_msg)
        turn.error = error_msg
    except NoteServiceError as e:
        error_msg = f"Note 서비스 오류: {str(e)}"
        display_error(error_msg)
        turn.error = error_msg
    except TaskServiceError as e:
        error_msg = f"Task 서비스 오류: {str(e)}"
        display_error(error_msg)
        turn.error = error_msg
    except KeyboardInterrupt:
        console.print("\n\n[bold red]사용자에 의해 중단되었습니다.[/bold red]")
        turn.error = "사용자 중단"
        turn.executed = False
    except Exception as e:
        error_msg = f"예상치 못한 오류: {str(e)}"
        display_error(error_msg)
        turn.error = error_msg

    return turn


@app.command()
def main(
    prompt: Annotated[
        str | None,
        typer.Argument(
            help="자연어로 작성된 작업 요청. 생략 시 대화형 모드로 시작합니다."
        ),
    ] = None,
) -> None:
    """Process user's natural language request.

    If no prompt is provided, starts interactive REPL mode.
    If a prompt is provided, executes it once and exits.

    Args:
        prompt: Natural language request from user (optional)
    """
    if not validate_configuration():
        raise typer.Exit(code=1)

    if prompt is None:
        asyncio.run(interactive_mode())
    else:
        asyncio.run(single_shot_mode(prompt))


async def single_shot_mode(prompt: str) -> None:
    """Execute a single prompt and exit.

    Args:
        prompt: Natural language request from user
    """
    start_time = time.time()

    console.print(
        f"\n[bold cyan]요청 처리 중:[/bold cyan] {prompt}\n",
    )

    turn = await process_user_request(prompt)

    if turn.error:
        raise typer.Exit(code=1)

    if turn.executed:
        elapsed_time = time.time() - start_time
        display_completion_message(elapsed_time)
    else:
        raise typer.Exit(code=0)


async def interactive_mode() -> None:
    """Start interactive REPL mode."""
    display_welcome_message()

    history_manager = HistoryManager()

    try:
        while True:
            user_input = get_user_input()

            if user_input is None:
                break

            user_input = user_input.strip()

            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit"]:
                break

            if user_input.lower() == "/help":
                display_help()
                continue

            if user_input.lower() == "/history":
                display_history(history_manager.get_turns())
                continue

            if user_input.lower() == "/clear":
                history_manager.clear_history()
                display_history_cleared()
                continue

            start_time = time.time()

            turn = await process_user_request(user_input, history_manager)
            history_manager.add_turn(turn)

            if turn.executed and not turn.error:
                elapsed_time = time.time() - start_time
                console.print(
                    f"\n[dim]작업 완료 (소요 시간: {elapsed_time:.2f}초)[/dim]"
                )

            display_turn_separator()

    except KeyboardInterrupt:
        console.print()

    finally:
        history_manager.save_session()
        display_goodbye_message()


if __name__ == "__main__":
    app()
