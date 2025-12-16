"""Main CLI application using Typer."""

import asyncio
import time
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from aklp.commands.agent import agent_app
from aklp.commands.batch import batch_app
from aklp.commands.config import config_app
from aklp.commands.file import file_app
from aklp.commands.note import note_app
from aklp.commands.task import task_app
from aklp.commands.usage import usage_app
from aklp.config import get_settings
from aklp.executor import (
    InvalidCommandError,
    get_kubeconfig_hint,
    run_kubectl,
    validate_kubectl_command,
)
from aklp.history import HistoryManager
from aklp.models import AgentResponse, ConversationTurn, UsageStats
from aklp.services.agent import AgentServiceError, execute_command
from aklp.services.batch import BatchServiceError, get_batch, list_batches
from aklp.services.file import FileServiceError, get_file as get_file_metadata, list_files
from aklp.services.note import NoteServiceError, create_note, get_note, list_notes
from aklp.services.task import TaskServiceError, create_task, get_task, list_tasks
from aklp.services.usage import UsageServiceError, get_usage
from aklp.ui.display import (
    confirm_execution,
    display_agent_result,
    display_batch_detail,
    display_batches_list,
    display_cancellation_message,
    display_completion_message,
    display_error,
    display_execution_result,
    display_file_detail,
    display_files_list,
    display_goodbye_message,
    display_help,
    display_history,
    display_history_cleared,
    display_kubectl_result,
    display_note_detail,
    display_notes_list,
    display_task_detail,
    display_tasks_list,
    display_turn_separator,
    display_usage_stats,
    display_welcome_message,
    get_user_input_async,
)

app = typer.Typer(
    name="aklp",
    help="MSA CLI Agent - Automate tasks with natural language",
    add_completion=False,
)

# Register subcommands
app.add_typer(agent_app, name="agent")
app.add_typer(batch_app, name="batch")
app.add_typer(config_app, name="config")
app.add_typer(file_app, name="file")
app.add_typer(note_app, name="note")
app.add_typer(task_app, name="task")
app.add_typer(usage_app, name="usage")
console = Console()


def validate_configuration() -> bool:
    """Validate that all required configuration is present.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        settings = get_settings()
        console.print("[dim]서비스 연결 정보:[/dim]")
        console.print(f"[dim]  • Agent: {settings.agent_service_url}[/dim]")
        console.print(f"[dim]  • Note: {settings.note_service_url}[/dim]")
        console.print(f"[dim]  • Task: {settings.task_service_url}[/dim]")
        console.print(f"[dim]  • File: {settings.file_service_url}[/dim]")
        return True
    except RuntimeError as e:
        display_error(str(e))
        return False


async def process_user_request(
    prompt: str,
    history_manager: HistoryManager | None = None,
) -> ConversationTurn:
    """Process a single user request.

    Flow:
    1. User input
    2. Agent service call
    3. Display result
    4. User yes/no confirmation
    5. Note + Task service call
    6. Display result

    Args:
        prompt: User's natural language request
        history_manager: Optional history manager to record turn

    Returns:
        ConversationTurn: Record of this conversation turn
    """
    turn = ConversationTurn(user_prompt=prompt)

    try:
        # Step 1-2: Call Agent service (measure LLM time)
        llm_start_time = time.time()
        with console.status(
            "[bold green]Agent가 요청을 분석하고 있습니다...[/bold green]",
            spinner="dots",
        ):
            agent_response: AgentResponse = await execute_command(prompt)
        turn.llm_elapsed_time = time.time() - llm_start_time

        # Step 3: Display Agent result
        display_agent_result(agent_response)
        console.print(f"[dim]  LLM 응답 시간: {turn.llm_elapsed_time:.2f}초[/dim]")

        # Check if agent returned an error
        if not agent_response.success:
            turn.error = agent_response.error_message
            turn.executed = False
            return turn

        # Step 4: User confirmation
        if not confirm_execution():
            display_cancellation_message()
            turn.executed = False
            return turn

        turn.executed = True

        # Step 5: Validate and execute kubectl command
        kubectl_result = None
        execution_log = ""

        if agent_response.command:
            try:
                validate_kubectl_command(agent_response.command)

                with console.status(
                    "[bold green]kubectl 명령어 실행 중...[/bold green]",
                    spinner="dots",
                ):
                    kubectl_result = run_kubectl(agent_response.command)

                # Display kubectl result
                display_kubectl_result(
                    success=kubectl_result.success,
                    stdout=kubectl_result.stdout,
                    stderr=kubectl_result.stderr,
                    return_code=kubectl_result.return_code,
                    kubeconfig_hint=get_kubeconfig_hint() if not kubectl_result.success else None,
                )

                # Build execution log for Note
                if kubectl_result.stdout:
                    execution_log += f"\n\n## 실행 결과\n```\n{kubectl_result.stdout}\n```"
                if kubectl_result.stderr:
                    execution_log += f"\n\n## 오류 출력\n```\n{kubectl_result.stderr}\n```"
                execution_log += f"\n\n**Exit Code:** {kubectl_result.return_code}"

            except InvalidCommandError as e:
                display_error(str(e))
                turn.error = str(e)
                return turn

        # Step 6: Create Note and Task
        note_response = None
        task_response = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Create Note with execution result
            note_task = progress.add_task("노트 생성 중...", total=1)
            note_content = f"## 명령어\n```bash\n{agent_response.command}\n```\n\n## 설명\n{agent_response.reason or ''}{execution_log}"
            note_response = await create_note(
                title=agent_response.title or "Agent 결과",
                content=note_content,
            )
            progress.update(note_task, completed=1)
            turn.note_response = note_response

            # Create Task
            task_task = progress.add_task("태스크 생성 중...", total=1)
            task_response = await create_task(
                title=agent_response.title or "실행 태스크",
                description=f"명령어: {agent_response.command}\n\n{agent_response.reason or ''}",
            )
            progress.update(task_task, completed=1)
            turn.task_response = task_response

        # Step 7: Display Note/Task creation results
        display_execution_result(note_response, task_response)

    except AgentServiceError as e:
        error_msg = f"Agent 서비스 오류: {str(e)}"
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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Annotated[
        str | None,
        typer.Option(
            "--prompt", "-p", help="자연어로 작성된 작업 요청. 생략 시 대화형 모드로 시작합니다."
        ),
    ] = None,
) -> None:
    """MSA CLI Agent - Automate tasks with natural language.

    If no prompt is provided, starts interactive REPL mode.
    If a prompt is provided, executes it once and exits.

    Args:
        ctx: Typer context
        prompt: Natural language request from user (optional)
    """
    # If a subcommand is invoked, skip main logic
    if ctx.invoked_subcommand is not None:
        return

    # First-time setup: check for cluster host and API key
    from aklp.secrets import ConfigManager
    from aklp.setup import run_first_time_setup

    config_mgr = ConfigManager()
    if not config_mgr.is_configured():
        if not run_first_time_setup():
            raise typer.Exit(code=1)

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


async def handle_notes_command(user_input: str) -> None:
    """Handle /notes [page] command.

    Args:
        user_input: User input string starting with /notes
    """
    parts = user_input.split()
    page = 1
    if len(parts) > 1:
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except ValueError:
            display_error("페이지 번호는 숫자여야 합니다. 예: /notes 2")
            return

    try:
        with console.status("[bold green]노트 목록 조회 중...[/bold green]", spinner="dots"):
            result = await list_notes(page=page)
        display_notes_list(result.items, result.total, result.page, result.total_pages)
    except NoteServiceError as e:
        display_error(f"Note 서비스 오류: {e}")


async def handle_note_command(user_input: str) -> None:
    """Handle /note <id> command.

    Args:
        user_input: User input string starting with /note
    """
    parts = user_input.split()
    if len(parts) < 2:
        display_error("노트 ID를 입력해주세요. 예: /note <uuid>")
        return

    note_id_str = parts[1]
    try:
        note_id = UUID(note_id_str)
    except ValueError:
        display_error(f"유효하지 않은 UUID 형식입니다: {note_id_str}")
        return

    try:
        with console.status("[bold green]노트 조회 중...[/bold green]", spinner="dots"):
            note = await get_note(note_id)
        display_note_detail(note)
    except NoteServiceError as e:
        display_error(f"Note 서비스 오류: {e}")


async def handle_tasks_command(user_input: str) -> None:
    """Handle /tasks [page] command.

    Args:
        user_input: User input string starting with /tasks
    """
    parts = user_input.split()
    page = 1
    if len(parts) > 1:
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except ValueError:
            display_error("페이지 번호는 숫자여야 합니다. 예: /tasks 2")
            return

    try:
        with console.status("[bold green]작업 목록 조회 중...[/bold green]", spinner="dots"):
            result = await list_tasks(page=page)
        display_tasks_list(result.items, result.total, result.page, result.total_pages)
    except TaskServiceError as e:
        display_error(f"Task 서비스 오류: {e}")


async def handle_task_command(user_input: str) -> None:
    """Handle /task <id> command.

    Args:
        user_input: User input string starting with /task
    """
    parts = user_input.split()
    if len(parts) < 2:
        display_error("작업 ID를 입력해주세요. 예: /task <uuid>")
        return

    task_id_str = parts[1]
    try:
        task_id = UUID(task_id_str)
    except ValueError:
        display_error(f"유효하지 않은 UUID 형식입니다: {task_id_str}")
        return

    try:
        with console.status("[bold green]작업 조회 중...[/bold green]", spinner="dots"):
            task = await get_task(task_id)
        display_task_detail(task)
    except TaskServiceError as e:
        display_error(f"Task 서비스 오류: {e}")


async def handle_files_command(user_input: str) -> None:
    """Handle /files [page] command.

    Args:
        user_input: User input string starting with /files
    """
    parts = user_input.split()
    page = 1
    if len(parts) > 1:
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except ValueError:
            display_error("페이지 번호는 숫자여야 합니다. 예: /files 2")
            return

    try:
        with console.status("[bold green]파일 목록 조회 중...[/bold green]", spinner="dots"):
            result = await list_files(page=page)
        display_files_list(result.items, result.total, result.page, result.total_pages)
    except FileServiceError as e:
        display_error(f"File 서비스 오류: {e}")


async def handle_file_command(user_input: str) -> None:
    """Handle /file <id> command.

    Args:
        user_input: User input string starting with /file
    """
    parts = user_input.split()
    if len(parts) < 2:
        display_error("파일 ID를 입력해주세요. 예: /file <uuid>")
        return

    file_id_str = parts[1]
    try:
        file_id = UUID(file_id_str)
    except ValueError:
        display_error(f"유효하지 않은 UUID 형식입니다: {file_id_str}")
        return

    try:
        with console.status("[bold green]파일 조회 중...[/bold green]", spinner="dots"):
            file = await get_file_metadata(file_id)
        display_file_detail(file)
    except FileServiceError as e:
        display_error(f"File 서비스 오류: {e}")


async def handle_batches_command(user_input: str) -> None:
    """Handle /batches [page] command.

    Args:
        user_input: User input string starting with /batches
    """
    parts = user_input.split()
    page = 1
    if len(parts) > 1:
        try:
            page = int(parts[1])
            if page < 1:
                page = 1
        except ValueError:
            display_error("페이지 번호는 숫자여야 합니다. 예: /batches 2")
            return

    try:
        with console.status("[bold green]배치 목록 조회 중...[/bold green]", spinner="dots"):
            result = await list_batches(page=page)
        display_batches_list(result.items, result.total, result.page, result.total_pages)
    except BatchServiceError as e:
        display_error(f"Batch 서비스 오류: {e}")


async def handle_batch_command(user_input: str) -> None:
    """Handle /batch <id> command.

    Args:
        user_input: User input string starting with /batch
    """
    parts = user_input.split()
    if len(parts) < 2:
        display_error("배치 ID를 입력해주세요. 예: /batch <uuid>")
        return

    batch_id_str = parts[1]
    try:
        batch_id = UUID(batch_id_str)
    except ValueError:
        display_error(f"유효하지 않은 UUID 형식입니다: {batch_id_str}")
        return

    try:
        with console.status("[bold green]배치 조회 중...[/bold green]", spinner="dots"):
            batch = await get_batch(batch_id)
        display_batch_detail(batch)
    except BatchServiceError as e:
        display_error(f"Batch 서비스 오류: {e}")


async def handle_usage_command(user_input: str) -> None:
    """Handle /usage [today|month|all] command.

    Args:
        user_input: User input string starting with /usage
    """
    parts = user_input.split()
    period = "all"
    if len(parts) > 1 and parts[1] in ("today", "month", "all"):
        period = parts[1]

    try:
        with console.status("[bold green]사용량 조회 중...[/bold green]", spinner="dots"):
            result = await get_usage(period=period)
        stats = UsageStats.model_validate(result["data"])
        display_usage_stats(stats)
    except UsageServiceError as e:
        display_error(f"사용량 조회 오류: {e}")
    except Exception as e:
        display_error(f"예상치 못한 오류: {e}")


async def interactive_mode() -> None:
    """Start interactive REPL mode."""
    display_welcome_message()

    history_manager = HistoryManager()

    try:
        while True:
            user_input = await get_user_input_async()

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

            # /notes [page] - List notes
            if user_input.lower().startswith("/notes"):
                await handle_notes_command(user_input)
                continue

            # /note <id> - Get single note
            if user_input.lower().startswith("/note "):
                await handle_note_command(user_input)
                continue

            # /tasks [page] - List tasks
            if user_input.lower().startswith("/tasks"):
                await handle_tasks_command(user_input)
                continue

            # /task <id> - Get single task
            if user_input.lower().startswith("/task "):
                await handle_task_command(user_input)
                continue

            # /files [page] - List files
            if user_input.lower().startswith("/files"):
                await handle_files_command(user_input)
                continue

            # /file <id> - Get single file
            if user_input.lower().startswith("/file "):
                await handle_file_command(user_input)
                continue

            # /batches [page] - List batches
            if user_input.lower().startswith("/batches"):
                await handle_batches_command(user_input)
                continue

            # /batch <id> - Get single batch
            if user_input.lower().startswith("/batch "):
                await handle_batch_command(user_input)
                continue

            # /usage [today|month|all] - Get API usage statistics
            if user_input.lower().startswith("/usage"):
                await handle_usage_command(user_input)
                continue

            start_time = time.time()

            turn = await process_user_request(user_input, history_manager)
            history_manager.add_turn(turn)

            if turn.executed and not turn.error:
                elapsed_time = time.time() - start_time
                llm_time = turn.llm_elapsed_time or 0.0
                console.print(f"\n[dim]작업 완료 (전체 {elapsed_time:.2f}초 / LLM {llm_time:.2f}초)[/dim]")

            display_turn_separator()

    except KeyboardInterrupt:
        console.print()

    finally:
        history_manager.save_session()
        display_goodbye_message()


if __name__ == "__main__":
    app()
