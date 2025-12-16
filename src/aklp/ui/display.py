"""Rich UI components for beautiful terminal output."""

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PTStyle
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from aklp.models import (
    AgentResponse,
    AnalysisResult,
    BatchResponse,
    ConversationTurn,
    FileResponse,
    LegacyTaskResponse,
    NoteResponse,
    TaskResponse,
    UsageStats,
)

console = Console()

# prompt_toolkit 설정
_history_file = Path.home() / ".aklp_input_history"
_command_completer = WordCompleter(
    [
        "/help",
        "/history",
        "/clear",
        "/exit",
        "/quit",
        "/notes",
        "/note",
        "/tasks",
        "/task",
        "/files",
        "/file",
        "/batches",
        "/batch",
        "/usage",
    ],
    ignore_case=True,
)
_prompt_style = PTStyle.from_dict(
    {
        "prompt": "ansiblue bold",
    }
)

# PromptSession 초기화 (방향키 히스토리, 한글 입력, 백스페이스 완벽 지원)
_prompt_session: PromptSession[str] | None = None


def _get_prompt_session() -> PromptSession[str]:
    """Get or create the prompt session (lazy initialization)."""
    global _prompt_session
    if _prompt_session is None:
        _prompt_session = PromptSession(
            history=FileHistory(str(_history_file)),
            completer=_command_completer,
            complete_while_typing=True,
            enable_history_search=True,
        )
    return _prompt_session


# Color palette (works well on both light and dark themes)
COLORS = {
    "primary": "blue",
    "secondary": "magenta",
    "success": "green",
    "warning": "dark_orange",
    "error": "red",
    "info": "cyan",
    "muted": "grey50",  # Medium gray works on both light and dark themes
    "accent": "magenta",
    "text": "default",  # Use terminal default for body text
}


def display_agent_result(result: AgentResponse) -> None:
    """Display the Agent service result with rich formatting.

    Args:
        result: Response from Agent service
    """
    console.print()

    if not result.success:
        # Error case
        console.print(
            Panel(
                f"[{COLORS['error']}]{result.error_message or '알 수 없는 오류'}[/{COLORS['error']}]",
                title=f"[{COLORS['error']}]Agent 오류[/{COLORS['error']}]",
                border_style=COLORS["error"],
                padding=(1, 2),
            )
        )
        return

    # Build unified content
    content = Text()

    # Title
    content.append("✨ ", style=COLORS["accent"])
    content.append(result.title or "명령어 생성 완료", style=f"bold {COLORS['primary']}")
    content.append(" ✨\n", style=COLORS["accent"])

    # Reason section
    if result.reason:
        content.append("\n")
        content.append("📋 설명\n", style=f"bold {COLORS['info']}")
        content.append(f"{result.reason}\n", style="")

    # Command section
    if result.command:
        content.append("\n")
        content.append("⚡ 명령어\n", style=f"bold {COLORS['warning']}")
        content.append(result.command, style="bold")

    console.print(
        Panel(
            content,
            border_style=COLORS["primary"],
            padding=(1, 2),
        )
    )
    console.print()


def display_analysis_result(result: AnalysisResult) -> None:
    """Display the LLM analysis result with rich formatting (legacy).

    Args:
        result: Analysis result from LLM service
    """
    console.print()

    # Title with elegant styling
    title_text = Text()
    title_text.append("✨ ", style=COLORS["accent"])
    title_text.append(result.title, style=f"bold {COLORS['primary']}")
    title_text.append(" ✨", style=COLORS["accent"])

    console.print(
        Panel(
            Align.center(title_text),
            border_style=COLORS["primary"],
            padding=(1, 2),
        )
    )

    # Description section
    console.print()
    console.print(
        Panel(
            Markdown(result.description),
            title=f"[{COLORS['info']}]📋 작업 설명[/{COLORS['info']}]",
            title_align="left",
            border_style=COLORS["info"],
            padding=(1, 2),
        )
    )

    # File section
    console.print()
    file_info = Text()
    file_info.append("📄 파일: ", style=f"bold {COLORS['secondary']}")
    file_info.append(result.filename, style=f"{COLORS['primary']}")

    syntax = Syntax(
        result.file_content,
        "markdown",
        theme="ansi_light",
        line_numbers=True,
        background_color="default",
    )

    console.print(
        Panel(
            syntax,
            title=file_info,
            title_align="left",
            border_style=COLORS["secondary"],
            padding=(1, 2),
        )
    )

    # Command section
    console.print()
    cmd_syntax = Syntax(
        result.shell_command,
        "bash",
        theme="ansi_light",
        background_color="default",
    )

    console.print(
        Panel(
            cmd_syntax,
            title=f"[{COLORS['warning']}]⚡ 실행할 명령어[/{COLORS['warning']}]",
            title_align="left",
            border_style=COLORS["warning"],
            padding=(1, 2),
        )
    )
    console.print()


def display_execution_result(note: NoteResponse | None, task: TaskResponse | None) -> None:
    """Display Note and Task creation results.

    Args:
        note: Created note response (optional)
        task: Created task response (optional)
    """
    if not note and not task:
        return

    console.print()

    content = Text()
    content.append("✅ 생성 완료\n", style=f"bold {COLORS['success']}")

    if note:
        content.append("\n")
        content.append("📝 노트: ", style=COLORS["muted"])
        content.append(f"{note.title}\n", style="")
        content.append("   ID: ", style=COLORS["muted"])
        content.append(f"{note.id}", style=COLORS["info"])

    if task:
        content.append("\n")
        content.append("☑️  태스크: ", style=COLORS["muted"])
        content.append(f"{task.title}\n", style="")
        content.append("   ID: ", style=COLORS["muted"])
        content.append(f"{task.id}", style=COLORS["info"])

    console.print(
        Panel(
            content,
            border_style=COLORS["success"],
            padding=(1, 2),
        )
    )


def confirm_execution() -> bool:
    """Ask user to confirm execution.

    Returns:
        bool: True if user confirms, False otherwise
    """
    console.print()
    return Confirm.ask(
        f"[{COLORS['warning']}]🤔 위 작업을 진행하시겠습니까?[/{COLORS['warning']}]",
        default=True,
    )


def display_success(message: str) -> None:
    """Display success message.

    Args:
        message: Success message to display
    """
    console.print(f"  [{COLORS['success']}]✓[/{COLORS['success']}] {message}")


def display_error(message: str) -> None:
    """Display error message.

    Args:
        message: Error message to display
    """
    console.print()
    console.print(
        Panel(
            f"[{COLORS['error']}]{message}[/{COLORS['error']}]",
            title=f"[{COLORS['error']}]✗ 오류[/{COLORS['error']}]",
            border_style=COLORS["error"],
            padding=(1, 2),
        )
    )


def display_task_result(result: LegacyTaskResponse) -> None:
    """Display task execution result.

    Args:
        result: Task execution result
    """
    console.print()

    if result.stdout:
        console.print(
            Panel(
                result.stdout.strip(),
                title=f"[{COLORS['success']}]📤 STDOUT[/{COLORS['success']}]",
                title_align="left",
                border_style=COLORS["success"],
                padding=(1, 2),
            )
        )
        console.print()

    if result.stderr:
        console.print(
            Panel(
                result.stderr.strip(),
                title=f"[{COLORS['error']}]📥 STDERR[/{COLORS['error']}]",
                title_align="left",
                border_style=COLORS["error"],
                padding=(1, 2),
            )
        )
        console.print()

    if result.exit_code == 0:
        console.print(
            f"  [{COLORS['success']}]✓ 명령어 실행 성공[/{COLORS['success']}] "
            f"[{COLORS['muted']}](Exit Code: {result.exit_code})[/{COLORS['muted']}]"
        )
    else:
        console.print(
            f"  [{COLORS['error']}]✗ 명령어 실행 실패[/{COLORS['error']}] "
            f"[{COLORS['muted']}](Exit Code: {result.exit_code})[/{COLORS['muted']}]"
        )


def display_completion_message(elapsed_time: float) -> None:
    """Display final completion message.

    Args:
        elapsed_time: Time taken to complete all tasks in seconds
    """
    console.print()

    completion_text = Text()
    completion_text.append("🎉 ", style=COLORS["success"])
    completion_text.append(
        "모든 작업이 성공적으로 완료되었습니다!", style=f"bold {COLORS['success']}"
    )
    completion_text.append("\n\n", style="")
    completion_text.append("⏱️  소요 시간: ", style=COLORS["muted"])
    completion_text.append(f"{elapsed_time:.2f}초", style=f"bold {COLORS['primary']}")

    console.print(
        Panel(
            Align.center(completion_text),
            border_style=COLORS["success"],
            padding=(1, 2),
        )
    )
    console.print()


def display_cancellation_message() -> None:
    """Display cancellation message when user aborts."""
    console.print(f"\n  [{COLORS['warning']}]⚠️  작업이 취소되었습니다.[/{COLORS['warning']}]")


def display_welcome_message() -> None:
    """Display welcome message for REPL mode."""
    console.print()

    welcome_text = Text()
    welcome_text.append("✨ ", style=COLORS["accent"])
    welcome_text.append("AKLP Interactive Mode", style=f"bold {COLORS['primary']}")
    welcome_text.append(" ✨", style=COLORS["accent"])
    welcome_text.append("\n\n", style="")
    welcome_text.append("자연어로 작업을 요청하세요.\n\n", style=COLORS["muted"])

    # Commands table
    commands_text = Text()
    commands_text.append("💡 명령어\n", style=f"bold {COLORS['info']}")
    commands_text.append("  /help       ", style=f"bold {COLORS['secondary']}")
    commands_text.append("도움말 보기\n", style="")
    commands_text.append("  /notes      ", style=f"bold {COLORS['secondary']}")
    commands_text.append("노트 목록 조회\n", style="")
    commands_text.append("  /tasks      ", style=f"bold {COLORS['secondary']}")
    commands_text.append("작업 목록 조회\n", style="")
    commands_text.append("  /exit       ", style=f"bold {COLORS['secondary']}")
    commands_text.append("종료", style="")

    welcome_text.append_text(commands_text)

    console.print(
        Panel(
            Align.center(welcome_text),
            border_style=COLORS["primary"],
            padding=(2, 4),
            subtitle=f"[{COLORS['muted']}]Ctrl+D로 빠른 종료[/{COLORS['muted']}]",
        )
    )
    console.print()


def display_goodbye_message() -> None:
    """Display goodbye message when exiting REPL."""
    console.print()

    goodbye_text = Text()
    goodbye_text.append("👋 ", style=COLORS["primary"])
    goodbye_text.append("Goodbye!", style=f"bold {COLORS['primary']}")
    goodbye_text.append(" 다음에 또 만나요!", style=COLORS["muted"])

    console.print(Align.center(goodbye_text))
    console.print()


async def get_user_input_async() -> str | None:
    """Get user input from REPL prompt (async version).

    Uses prompt_toolkit for better input handling:
    - Arrow keys: Navigate input history (↑/↓) and cursor (←/→)
    - Backspace/Delete: Proper character deletion
    - Korean/Unicode: Full support for multi-byte characters
    - Tab: Auto-complete commands (/help, /exit, etc.)
    - Ctrl+R: Reverse history search
    - Emacs-style shortcuts: Ctrl+A/E/K/U/W

    Returns:
        User input string, or None if EOF (Ctrl+D)
    """
    try:
        console.print()
        session = _get_prompt_session()
        return await session.prompt_async(
            [("class:prompt", "❯ ")],
            style=_prompt_style,
        )
    except (EOFError, KeyboardInterrupt):
        return None


def get_user_input() -> str | None:
    """Get user input from REPL prompt (sync version).

    Uses prompt_toolkit for better input handling:
    - Arrow keys: Navigate input history (↑/↓) and cursor (←/→)
    - Backspace/Delete: Proper character deletion
    - Korean/Unicode: Full support for multi-byte characters
    - Tab: Auto-complete commands (/help, /exit, etc.)
    - Ctrl+R: Reverse history search
    - Emacs-style shortcuts: Ctrl+A/E/K/U/W

    Returns:
        User input string, or None if EOF (Ctrl+D)
    """
    try:
        console.print()
        session = _get_prompt_session()
        return session.prompt(
            [("class:prompt", "❯ ")],
            style=_prompt_style,
        )
    except (EOFError, KeyboardInterrupt):
        return None


def display_turn_separator() -> None:
    """Display separator between conversation turns."""
    console.print()
    console.print(
        Rule(
            style=Style(color=COLORS["muted"], dim=True),
        )
    )


def display_help() -> None:
    """Display help message with available commands."""
    console.print()

    help_text = Text()
    help_text.append("📚 AKLP Interactive Mode\n\n", style=f"bold {COLORS['primary']}")

    help_text.append("일반 사용\n", style=f"bold {COLORS['info']}")
    help_text.append("  자연어로 작업을 요청하세요.\n", style="")
    help_text.append("  예시: ", style=COLORS["muted"])
    help_text.append("'현재 폴더에 README.md 만들고 ls -al 실행해줘'\n\n", style="italic")

    help_text.append("특수 명령어\n", style=f"bold {COLORS['warning']}")
    help_text.append("  /help      ", style=f"bold {COLORS['secondary']}")
    help_text.append("이 도움말 표시\n", style="")
    help_text.append("  /history   ", style=f"bold {COLORS['secondary']}")
    help_text.append("현재 세션의 대화 히스토리 보기\n", style="")
    help_text.append("  /clear     ", style=f"bold {COLORS['secondary']}")
    help_text.append("현재 세션 히스토리 초기화\n", style="")
    help_text.append("  /exit      ", style=f"bold {COLORS['secondary']}")
    help_text.append("REPL 모드 종료\n", style="")
    help_text.append("  /quit      ", style=f"bold {COLORS['secondary']}")
    help_text.append("REPL 모드 종료\n\n", style="")

    help_text.append("조회 명령어\n", style=f"bold {COLORS['info']}")
    help_text.append("  /notes [page]    ", style=f"bold {COLORS['secondary']}")
    help_text.append("노트 목록 조회\n", style="")
    help_text.append("  /note <id>       ", style=f"bold {COLORS['secondary']}")
    help_text.append("특정 노트 조회\n", style="")
    help_text.append("  /tasks [page]    ", style=f"bold {COLORS['secondary']}")
    help_text.append("작업 목록 조회\n", style="")
    help_text.append("  /task <id>       ", style=f"bold {COLORS['secondary']}")
    help_text.append("특정 작업 조회\n", style="")
    help_text.append("  /files [page]    ", style=f"bold {COLORS['secondary']}")
    help_text.append("파일 목록 조회\n", style="")
    help_text.append("  /file <id>       ", style=f"bold {COLORS['secondary']}")
    help_text.append("특정 파일 조회\n", style="")
    help_text.append("  /batches [page]  ", style=f"bold {COLORS['secondary']}")
    help_text.append("배치 목록 조회\n", style="")
    help_text.append("  /batch <id>      ", style=f"bold {COLORS['secondary']}")
    help_text.append("특정 배치 조회\n", style="")
    help_text.append("  /usage [period]  ", style=f"bold {COLORS['secondary']}")
    help_text.append("API 사용량 조회 (today/month/all)\n\n", style="")

    help_text.append("단축키\n", style=f"bold {COLORS['success']}")
    help_text.append("  Ctrl+D   ", style=f"bold {COLORS['secondary']}")
    help_text.append("종료\n", style="")
    help_text.append("  Ctrl+C   ", style=f"bold {COLORS['secondary']}")
    help_text.append("현재 작업 취소\n", style="")
    help_text.append("  ↑/↓      ", style=f"bold {COLORS['secondary']}")
    help_text.append("이전/다음 입력 히스토리\n", style="")
    help_text.append("  Ctrl+R   ", style=f"bold {COLORS['secondary']}")
    help_text.append("히스토리 검색\n", style="")
    help_text.append("  Tab      ", style=f"bold {COLORS['secondary']}")
    help_text.append("명령어 자동완성", style="")

    console.print(
        Panel(
            help_text,
            border_style=COLORS["info"],
            padding=(2, 3),
        )
    )


def display_history(turns: list[ConversationTurn]) -> None:
    """Display conversation history in a table.

    Args:
        turns: List of conversation turns to display
    """
    if not turns:
        console.print()
        console.print(
            Panel(
                f"[{COLORS['muted']}]히스토리가 비어있습니다.[/{COLORS['muted']}]",
                border_style=COLORS["muted"],
                padding=(1, 2),
            )
        )
        return

    console.print()

    table = Table(
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["primary"],
        title=f"[bold {COLORS['primary']}]📜 세션 히스토리[/bold {COLORS['primary']}]",
        title_style=f"bold {COLORS['primary']}",
        padding=(0, 1),
    )

    table.add_column("#", style=COLORS["muted"], width=4, justify="right")
    table.add_column("시각", style=COLORS["info"], width=19)
    table.add_column("요청", style="default", width=45, no_wrap=False)
    table.add_column("실행", style=COLORS["success"], width=4, justify="center")
    table.add_column("상태", width=10)

    for i, turn in enumerate(turns, 1):
        timestamp = turn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        prompt_preview = (
            turn.user_prompt[:42] + "..." if len(turn.user_prompt) > 45 else turn.user_prompt
        )
        executed = "✓" if turn.executed else "✗"

        if turn.error:
            status = f"[{COLORS['error']}]오류[/{COLORS['error']}]"
            executed_style = COLORS["error"]
        elif turn.executed:
            status = f"[{COLORS['success']}]완료[/{COLORS['success']}]"
            executed_style = COLORS["success"]
        else:
            status = f"[{COLORS['warning']}]취소됨[/{COLORS['warning']}]"
            executed_style = COLORS["warning"]

        table.add_row(
            str(i),
            timestamp,
            prompt_preview,
            f"[{executed_style}]{executed}[/{executed_style}]",
            status,
        )

    console.print(table)
    console.print()
    console.print(Align.center(f"[{COLORS['muted']}]총 {len(turns)}개의 대화[/{COLORS['muted']}]"))
    console.print()


def display_history_cleared() -> None:
    """Display message when history is cleared."""
    console.print()
    console.print(f"  [{COLORS['success']}]✓ 히스토리가 초기화되었습니다.[/{COLORS['success']}]")


def display_notes_list(notes: list[NoteResponse], total: int, page: int, total_pages: int) -> None:
    """Display notes in a table format for interactive mode.

    Args:
        notes: List of notes to display
        total: Total number of notes
        page: Current page number
        total_pages: Total number of pages
    """
    console.print()

    if not notes:
        console.print(
            Panel(
                f"[{COLORS['muted']}]노트가 없습니다.[/{COLORS['muted']}]",
                border_style=COLORS["muted"],
                padding=(1, 2),
            )
        )
        return

    table = Table(
        title=f"[bold {COLORS['primary']}]📝 Notes[/bold {COLORS['primary']}] (Page {page}/{total_pages}, Total: {total})",
        show_header=True,
        header_style=f"bold {COLORS['primary']}",
        border_style=COLORS["primary"],
    )
    table.add_column("ID", style=COLORS["muted"], max_width=36)
    table.add_column("제목", style=COLORS["info"])
    table.add_column("내용", max_width=40)
    table.add_column("생성일", style=COLORS["muted"])

    for note in notes:
        content_preview = note.content[:37] + "..." if len(note.content) > 40 else note.content
        content_preview = content_preview.replace("\n", " ")
        table.add_row(
            str(note.id),
            note.title,
            content_preview,
            note.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)

    if total_pages > 1:
        console.print()
        console.print(
            Align.center(f"[{COLORS['muted']}]페이지 이동: /notes <page>[/{COLORS['muted']}]")
        )


def display_note_detail(note: NoteResponse) -> None:
    """Display a single note in detail.

    Args:
        note: Note to display
    """
    console.print()

    content = Text()
    content.append(f"{note.title}\n\n", style=f"bold {COLORS['primary']}")
    content.append(note.content, style="")
    content.append("\n\n", style="")
    content.append(f"ID: {note.id}\n", style=COLORS["muted"])
    content.append(
        f"생성일: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n", style=COLORS["muted"]
    )
    content.append(
        f"수정일: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}", style=COLORS["muted"]
    )
    if note.session_id:
        content.append(f"\n세션 ID: {note.session_id}", style=COLORS["muted"])

    console.print(
        Panel(
            content,
            title=f"[{COLORS['info']}]📝 Note[/{COLORS['info']}]",
            border_style=COLORS["info"],
            padding=(1, 2),
        )
    )


def display_tasks_list(
    tasks: list[TaskResponse],
    total: int,
    page: int,
    total_pages: int,
) -> None:
    """Display tasks in a table format for interactive mode.

    Args:
        tasks: List of tasks to display
        total: Total number of tasks
        page: Current page number
        total_pages: Total number of pages
    """
    from aklp.models import TaskPriority, TaskStatus

    def _status_color(status: TaskStatus) -> str:
        colors = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.COMPLETED: "green",
        }
        return colors.get(status, "white")

    def _priority_color(priority: TaskPriority | None) -> str:
        if priority is None:
            return COLORS["muted"]
        colors = {
            TaskPriority.HIGH: "red",
            TaskPriority.MEDIUM: "yellow",
            TaskPriority.LOW: "green",
        }
        return colors.get(priority, "white")

    console.print()

    if not tasks:
        console.print(
            Panel(
                f"[{COLORS['muted']}]작업이 없습니다.[/{COLORS['muted']}]",
                border_style=COLORS["muted"],
                padding=(1, 2),
            )
        )
        return

    table = Table(
        title=f"[bold {COLORS['warning']}]☑️  Tasks[/bold {COLORS['warning']}] (Page {page}/{total_pages}, Total: {total})",
        show_header=True,
        header_style=f"bold {COLORS['warning']}",
        border_style=COLORS["warning"],
    )
    table.add_column("ID", style=COLORS["muted"], max_width=36)
    table.add_column("제목", style=COLORS["info"])
    table.add_column("상태")
    table.add_column("우선순위")
    table.add_column("마감일", style=COLORS["muted"])

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

    if total_pages > 1:
        console.print()
        console.print(
            Align.center(f"[{COLORS['muted']}]페이지 이동: /tasks <page>[/{COLORS['muted']}]")
        )


def display_task_detail(task: TaskResponse) -> None:
    """Display a single task in detail.

    Args:
        task: Task to display
    """
    from aklp.models import TaskPriority, TaskStatus

    def _status_color(status: TaskStatus) -> str:
        colors = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.COMPLETED: "green",
        }
        return colors.get(status, "white")

    def _priority_color(priority: TaskPriority | None) -> str:
        if priority is None:
            return COLORS["muted"]
        colors = {
            TaskPriority.HIGH: "red",
            TaskPriority.MEDIUM: "yellow",
            TaskPriority.LOW: "green",
        }
        return colors.get(priority, "white")

    console.print()

    status_color = _status_color(task.status)
    priority_str = task.priority.value if task.priority else "없음"
    priority_color = _priority_color(task.priority)

    content = Text()
    content.append(f"{task.title}\n\n", style=f"bold {COLORS['warning']}")

    if task.description:
        content.append(f"{task.description}\n\n", style="")

    content.append("상태: ", style=COLORS["muted"])
    content.append(f"{task.status.value}\n", style=status_color)
    content.append("우선순위: ", style=COLORS["muted"])
    content.append(f"{priority_str}\n", style=priority_color)

    if task.due_date:
        content.append(
            f"마감일: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n", style=COLORS["muted"]
        )
    if task.completed_at:
        content.append(
            f"완료일: {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n", style=COLORS["success"]
        )

    content.append(f"\nID: {task.id}\n", style=COLORS["muted"])
    content.append(
        f"생성일: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n", style=COLORS["muted"]
    )
    content.append(
        f"수정일: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}", style=COLORS["muted"]
    )

    console.print(
        Panel(
            content,
            title=f"[{COLORS['warning']}]☑️  Task[/{COLORS['warning']}]",
            border_style=COLORS["warning"],
            padding=(1, 2),
        )
    )


def display_usage_stats(stats: UsageStats) -> None:
    """Display API usage statistics.

    Args:
        stats: Usage statistics to display
    """
    period_labels = {
        "today": "오늘",
        "month": "이번 달",
        "all": "전체",
    }
    period_label = period_labels.get(stats.period, stats.period)

    console.print()

    table = Table(
        title=f"[bold {COLORS['info']}]OpenAI API 사용량 ({period_label})[/bold {COLORS['info']}]",
        show_header=True,
        header_style=f"bold {COLORS['info']}",
        border_style=COLORS["info"],
    )
    table.add_column("항목", style=COLORS["muted"])
    table.add_column("값", justify="right")

    table.add_row(
        "Input Tokens", f"[{COLORS['text']}]{stats.total_input_tokens:,}[/{COLORS['text']}]"
    )
    table.add_row(
        "Output Tokens", f"[{COLORS['text']}]{stats.total_output_tokens:,}[/{COLORS['text']}]"
    )
    table.add_row(
        "Cached Tokens", f"[{COLORS['text']}]{stats.total_cached_tokens:,}[/{COLORS['text']}]"
    )
    table.add_row("요청 수", f"[{COLORS['text']}]{stats.request_count:,}[/{COLORS['text']}]")
    table.add_row(
        "총 비용",
        f"[bold {COLORS['success']}]${stats.total_cost_usd:.6f}[/bold {COLORS['success']}]",
    )

    console.print(table)

    # Period info
    if stats.period_start:
        console.print()
        console.print(
            f"[{COLORS['muted']}]기간: {stats.period_start.strftime('%Y-%m-%d %H:%M')} UTC ~[/{COLORS['muted']}]"
        )


def display_files_list(
    files: list[FileResponse],
    total: int,
    page: int,
    total_pages: int,
) -> None:
    """Display files in a table format for interactive mode.

    Args:
        files: List of files to display
        total: Total number of files
        page: Current page number
        total_pages: Total number of pages
    """
    console.print()

    if not files:
        console.print(
            Panel(
                f"[{COLORS['muted']}]파일이 없습니다.[/{COLORS['muted']}]",
                border_style=COLORS["muted"],
                padding=(1, 2),
            )
        )
        return

    table = Table(
        title=f"[bold {COLORS['secondary']}]📁 Files[/bold {COLORS['secondary']}] (Page {page}/{total_pages}, Total: {total})",
        show_header=True,
        header_style=f"bold {COLORS['secondary']}",
        border_style=COLORS["secondary"],
    )
    table.add_column("ID", style=COLORS["muted"], max_width=36)
    table.add_column("파일명", style=COLORS["info"])
    table.add_column("타입", max_width=20)
    table.add_column("크기", justify="right")
    table.add_column("생성일", style=COLORS["muted"])

    for file in files:
        table.add_row(
            str(file.id),
            file.filename,
            file.content_type,
            file.size_human,
            file.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)

    if total_pages > 1:
        console.print()
        console.print(
            Align.center(f"[{COLORS['muted']}]페이지 이동: /files <page>[/{COLORS['muted']}]")
        )


def display_file_detail(file: FileResponse) -> None:
    """Display a single file in detail.

    Args:
        file: File to display
    """
    console.print()

    content = Text()
    content.append(f"{file.filename}\n\n", style=f"bold {COLORS['secondary']}")

    content.append("타입: ", style=COLORS["muted"])
    content.append(f"{file.content_type}\n", style="")
    content.append("크기: ", style=COLORS["muted"])
    content.append(f"{file.size_human}\n", style="")

    if file.description:
        content.append("\n설명: ", style=COLORS["muted"])
        content.append(f"{file.description}\n", style="")

    content.append(f"\nID: {file.id}\n", style=COLORS["muted"])
    content.append(
        f"생성일: {file.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n", style=COLORS["muted"]
    )
    content.append(
        f"수정일: {file.updated_at.strftime('%Y-%m-%d %H:%M:%S')}", style=COLORS["muted"]
    )
    if file.session_id:
        content.append(f"\n세션 ID: {file.session_id}", style=COLORS["muted"])

    console.print(
        Panel(
            content,
            title=f"[{COLORS['secondary']}]📁 File[/{COLORS['secondary']}]",
            border_style=COLORS["secondary"],
            padding=(1, 2),
        )
    )


def display_batches_list(
    batches: list[BatchResponse],
    total: int,
    page: int,
    total_pages: int,
) -> None:
    """Display batches in a table format for interactive mode.

    Args:
        batches: List of batches to display
        total: Total number of batches
        page: Current page number
        total_pages: Total number of pages
    """
    from aklp.models import TaskStatus

    console.print()

    if not batches:
        console.print(
            Panel(
                f"[{COLORS['muted']}]배치가 없습니다.[/{COLORS['muted']}]",
                border_style=COLORS["muted"],
                padding=(1, 2),
            )
        )
        return

    table = Table(
        title=f"[bold {COLORS['accent']}]📦 Batches[/bold {COLORS['accent']}] (Page {page}/{total_pages}, Total: {total})",
        show_header=True,
        header_style=f"bold {COLORS['accent']}",
        border_style=COLORS["accent"],
    )
    table.add_column("ID", style=COLORS["muted"], max_width=36)
    table.add_column("사유", style=COLORS["info"], max_width=40)
    table.add_column("태스크", justify="right")
    table.add_column("생성일", style=COLORS["muted"])

    for batch in batches:
        reason_preview = (
            (batch.reason[:37] + "...")
            if batch.reason and len(batch.reason) > 40
            else (batch.reason or "-")
        )
        table.add_row(
            str(batch.id),
            reason_preview,
            str(len(batch.tasks)),
            batch.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)

    if total_pages > 1:
        console.print()
        console.print(
            Align.center(f"[{COLORS['muted']}]페이지 이동: /batches <page>[/{COLORS['muted']}]")
        )


def display_batch_detail(batch: BatchResponse) -> None:
    """Display a single batch in detail.

    Args:
        batch: Batch to display
    """
    from aklp.models import TaskStatus

    def _status_color(status: TaskStatus) -> str:
        colors = {
            TaskStatus.PENDING: "yellow",
            TaskStatus.IN_PROGRESS: "blue",
            TaskStatus.COMPLETED: "green",
        }
        return colors.get(status, "white")

    console.print()

    content = Text()
    content.append(f"Batch ID: {batch.id}\n\n", style=f"bold {COLORS['accent']}")

    if batch.reason:
        content.append("사유: ", style=COLORS["muted"])
        content.append(f"{batch.reason}\n\n", style="")

    content.append(
        f"생성일: {batch.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n", style=COLORS["muted"]
    )
    if batch.session_id:
        content.append(f"세션 ID: {batch.session_id}", style=COLORS["muted"])

    console.print(
        Panel(
            content,
            title=f"[{COLORS['accent']}]📦 Batch[/{COLORS['accent']}]",
            border_style=COLORS["accent"],
            padding=(1, 2),
        )
    )

    if batch.tasks:
        console.print()
        table = Table(
            title=f"[bold {COLORS['warning']}]태스크 ({len(batch.tasks)}개)[/bold {COLORS['warning']}]",
            show_header=True,
            header_style=f"bold {COLORS['warning']}",
            border_style=COLORS["warning"],
        )
        table.add_column("ID", style=COLORS["muted"], max_width=36)
        table.add_column("제목", style=COLORS["info"])
        table.add_column("상태")

        for task in batch.tasks:
            status_color = _status_color(task.status)
            table.add_row(
                str(task.id),
                task.title,
                f"[{status_color}]{task.status.value}[/{status_color}]",
            )

        console.print(table)
