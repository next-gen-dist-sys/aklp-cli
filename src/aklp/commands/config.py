"""Config subcommands for AKLP CLI."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from aklp.k8s import KubernetesError, KubernetesManager
from aklp.secrets import ConfigManager

config_app = typer.Typer(
    name="config",
    help="CLI 설정 관리 명령어",
    invoke_without_command=True,
)
console = Console()


@config_app.callback(invoke_without_command=True)
def show_config(ctx: typer.Context) -> None:
    """현재 설정을 표시합니다."""
    if ctx.invoked_subcommand is not None:
        return

    config_mgr = ConfigManager()

    if not config_mgr.is_configured():
        console.print("[yellow]설정이 완료되지 않았습니다.[/yellow]")
        console.print("[dim]'aklp' 명령어로 초기 설정을 진행해주세요.[/dim]")
        raise typer.Exit(code=1)

    table = Table(title="AKLP 설정", show_header=True, header_style="bold cyan")
    table.add_column("항목", style="dim")
    table.add_column("값")

    host = config_mgr.get_cluster_host()
    api_key = config_mgr.get_api_key()

    table.add_row("클러스터 주소", host or "-")
    table.add_row("API 키", f"{api_key[:10]}...{api_key[-4:]}" if api_key else "-")
    table.add_row("설정 파일", str(config_mgr.config_file))

    console.print()
    console.print(table)
    console.print()

    # Show service URLs
    from aklp.config import (
        AGENT_NODE_PORT,
        FILE_NODE_PORT,
        NOTE_NODE_PORT,
        TASK_NODE_PORT,
    )

    url_table = Table(title="서비스 URL", show_header=True, header_style="bold cyan")
    url_table.add_column("서비스", style="dim")
    url_table.add_column("URL")

    url_table.add_row("Agent", f"http://{host}:{AGENT_NODE_PORT}")
    url_table.add_row("Note", f"http://{host}:{NOTE_NODE_PORT}")
    url_table.add_row("Task", f"http://{host}:{TASK_NODE_PORT}")
    url_table.add_row("File", f"http://{host}:{FILE_NODE_PORT}")

    console.print(url_table)
    console.print()


@config_app.command("cluster")
def set_cluster(
    host: Annotated[str, typer.Argument(help="클러스터 IP 또는 호스트명")],
) -> None:
    """클러스터 주소를 변경합니다."""
    config_mgr = ConfigManager()
    k8s_mgr = KubernetesManager()

    console.print(f"\n[dim]클러스터 연결 테스트 중... ({host})[/dim]")

    try:
        k8s_mgr.test_connection()
        console.print("[green]클러스터 연결 성공![/green]")
    except KubernetesError as e:
        console.print(f"\n[red]연결 실패:[/red] {e}")
        raise typer.Exit(code=1)

    config_mgr.set_cluster_host(host)
    console.print(f"\n[green]클러스터 주소가 변경되었습니다:[/green] {host}")


@config_app.command("apikey")
def set_apikey() -> None:
    """OpenAI API 키를 변경합니다."""
    config_mgr = ConfigManager()
    k8s_mgr = KubernetesManager()

    # Check cluster connection first
    if not config_mgr.has_cluster_host():
        console.print("[red]클러스터가 설정되지 않았습니다.[/red]")
        console.print("[dim]먼저 'aklp config cluster <IP>'로 클러스터를 설정해주세요.[/dim]")
        raise typer.Exit(code=1)

    console.print()
    api_key = Prompt.ask("새 OpenAI API Key", password=True)

    if not api_key or not api_key.startswith("sk-") or len(api_key) <= 20:
        console.print("\n[red]유효하지 않은 API 키 형식입니다.[/red]")
        console.print("[dim]OpenAI API 키는 'sk-'로 시작해야 합니다.[/dim]")
        raise typer.Exit(code=1)

    console.print("\n[dim]Kubernetes Secret 업데이트 중...[/dim]")

    try:
        k8s_mgr.create_or_update_secret(api_key)
        console.print("[green]Secret 업데이트 성공![/green]")

        console.print("[dim]Agent 서비스 재시작 중...[/dim]")
        k8s_mgr.restart_agent_deployment()
        console.print("[green]Agent 재시작 완료![/green]")
    except KubernetesError as e:
        console.print(f"\n[red]실패:[/red] {e}")
        raise typer.Exit(code=1)

    config_mgr.set_api_key(api_key)
    console.print("\n[green]API 키가 변경되었습니다.[/green]")


@config_app.command("reset")
def reset_config() -> None:
    """모든 설정을 초기화합니다."""
    config_mgr = ConfigManager()

    if not config_mgr.config_file.exists():
        console.print("[yellow]초기화할 설정이 없습니다.[/yellow]")
        return

    console.print()
    console.print(
        Panel(
            "[bold yellow]경고[/bold yellow]\n\n"
            "모든 설정이 삭제됩니다.\n"
            "Kubernetes Secret은 삭제되지 않습니다.",
            border_style="yellow",
        )
    )

    if not Confirm.ask("\n정말 초기화하시겠습니까?", default=False):
        console.print("[dim]취소되었습니다.[/dim]")
        return

    config_mgr.reset()
    console.print("\n[green]설정이 초기화되었습니다.[/green]")
    console.print("[dim]'aklp' 명령어로 다시 설정을 진행해주세요.[/dim]")