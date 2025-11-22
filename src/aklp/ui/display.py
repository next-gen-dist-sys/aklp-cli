"""Rich UI components for beautiful terminal output."""

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

from aklp.models import AnalysisResult, ConversationTurn, LegacyTaskResponse

console = Console()

# Modern color palette
COLORS = {
    "primary": "bright_blue",
    "secondary": "bright_magenta",
    "success": "bright_green",
    "warning": "bright_yellow",
    "error": "bright_red",
    "info": "bright_cyan",
    "muted": "bright_black",
    "accent": "magenta",
}


def display_analysis_result(result: AnalysisResult) -> None:
    """Display the LLM analysis result with rich formatting.

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
        theme="monokai",
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
        theme="monokai",
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


def confirm_execution() -> bool:
    """Ask user to confirm execution.

    Returns:
        bool: True if user confirms, False otherwise
    """
    console.print()
    return Confirm.ask(
        f"[{COLORS['warning']}]🤔 위 작업을 진행하시겠습니까?[/{COLORS['warning']}]",
        default=False,
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
    completion_text.append("모든 작업이 성공적으로 완료되었습니다!", style=f"bold {COLORS['success']}")
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
    commands_text.append("  /help      ", style=f"bold {COLORS['secondary']}")
    commands_text.append("도움말 보기\n", style="")
    commands_text.append("  /history   ", style=f"bold {COLORS['secondary']}")
    commands_text.append("세션 히스토리 보기\n", style="")
    commands_text.append("  /clear     ", style=f"bold {COLORS['secondary']}")
    commands_text.append("히스토리 초기화\n", style="")
    commands_text.append("  /exit      ", style=f"bold {COLORS['secondary']}")
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


def get_user_input() -> str | None:
    """Get user input from REPL prompt.

    Returns:
        User input string, or None if EOF (Ctrl+D)
    """
    try:
        console.print()
        return Prompt.ask(
            f"[{COLORS['primary']}]❯[/{COLORS['primary']}]",
            console=console,
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

    help_text.append("단축키\n", style=f"bold {COLORS['success']}")
    help_text.append("  Ctrl+D   ", style=f"bold {COLORS['secondary']}")
    help_text.append("종료\n", style="")
    help_text.append("  Ctrl+C   ", style=f"bold {COLORS['secondary']}")
    help_text.append("현재 작업 취소", style="")

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
    table.add_column("요청", style="white", width=45, no_wrap=False)
    table.add_column("실행", style=COLORS["success"], width=4, justify="center")
    table.add_column("상태", width=10)

    for i, turn in enumerate(turns, 1):
        timestamp = turn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        prompt_preview = (
            turn.user_prompt[:42] + "..."
            if len(turn.user_prompt) > 45
            else turn.user_prompt
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
    console.print(
        Align.center(
            f"[{COLORS['muted']}]총 {len(turns)}개의 대화[/{COLORS['muted']}]"
        )
    )
    console.print()


def display_history_cleared() -> None:
    """Display message when history is cleared."""
    console.print()
    console.print(f"  [{COLORS['success']}]✓ 히스토리가 초기화되었습니다.[/{COLORS['success']}]")
