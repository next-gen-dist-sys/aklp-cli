"""First-time setup wizard for AKLP CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def prompt_api_key() -> str:
    """Prompt user for OpenAI API key with hidden input.

    Returns:
        str: The API key entered by user.
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold]OpenAI API Key 설정[/bold]\n\n"
            "AKLP Agent 서비스는 OpenAI API를 사용합니다.\n"
            "API 키를 입력해주세요.",
            title="첫 실행 설정",
        )
    )
    console.print()

    return Prompt.ask("OpenAI API Key", password=True)


def validate_api_key(api_key: str) -> bool:
    """Validate OpenAI API key format.

    Args:
        api_key: API key to validate.

    Returns:
        bool: True if key format appears valid.
    """
    if not api_key:
        return False
    # OpenAI keys start with "sk-" and are typically 50+ characters
    return api_key.startswith("sk-") and len(api_key) > 20


def run_first_time_setup() -> bool:
    """Run first-time setup wizard.

    Prompts for OpenAI API key, validates it, and saves to config.

    Returns:
        bool: True if setup completed successfully, False otherwise.
    """
    from aklp.secrets import ConfigManager

    api_key = prompt_api_key()

    if not validate_api_key(api_key):
        console.print("\n[red]유효하지 않은 API 키 형식입니다.[/red]")
        console.print("[dim]OpenAI API 키는 'sk-'로 시작해야 합니다.[/dim]")
        return False

    config_mgr = ConfigManager()
    config_mgr.set_api_key(api_key)

    console.print("\n[green]API 키가 저장되었습니다.[/green]")
    console.print(f"[dim]설정 파일: {config_mgr.config_file}[/dim]\n")

    return True
