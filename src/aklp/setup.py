"""First-time setup wizard for AKLP CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def prompt_cluster_host() -> str:
    """Prompt user for cluster host (IP or hostname).

    Returns:
        str: The cluster host entered by user.
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold]클러스터 연결 설정[/bold]\n\n"
            "AKLP 서비스가 배포된 Kubernetes 클러스터의\n"
            "IP 주소 또는 호스트명을 입력해주세요.\n\n"
            "[dim]예: 192.168.1.100, k3s.local[/dim]",
            title="첫 실행 설정 (1/2)",
        )
    )
    console.print()

    return Prompt.ask("클러스터 주소")


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
            "API 키를 입력해주세요.\n\n"
            "[dim]키는 클러스터의 Secret으로 안전하게 저장됩니다.[/dim]",
            title="첫 실행 설정 (2/2)",
        )
    )
    console.print()

    return Prompt.ask("OpenAI API Key", password=True)


def validate_cluster_host(host: str) -> bool:
    """Validate cluster host format.

    Args:
        host: Cluster host to validate.

    Returns:
        bool: True if host format appears valid.
    """
    if not host:
        return False
    # Basic validation: not empty and no spaces
    return len(host.strip()) > 0 and " " not in host


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

    Flow:
    1. Prompt for cluster host
    2. Test cluster connection (check aklp namespace)
    3. Prompt for API key
    4. Create/update Kubernetes Secret
    5. Save to config.toml
    6. Done

    Returns:
        bool: True if setup completed successfully, False otherwise.
    """
    from aklp.k8s import KubernetesError, KubernetesManager
    from aklp.secrets import ConfigManager

    config_mgr = ConfigManager()
    k8s_mgr = KubernetesManager()

    # Step 1: Cluster host
    while True:
        host = prompt_cluster_host()

        if not validate_cluster_host(host):
            console.print("\n[red]유효하지 않은 주소 형식입니다.[/red]")
            continue

        # Step 2: Test connection
        console.print(f"\n[dim]클러스터 연결 테스트 중... ({host})[/dim]")

        try:
            k8s_mgr.test_connection()
            console.print("[green]클러스터 연결 성공![/green]")
            break
        except KubernetesError as e:
            console.print(f"\n[red]연결 실패:[/red] {e}")
            console.print("[dim]다시 시도해주세요.[/dim]")
            continue

    # Step 3: API key
    while True:
        api_key = prompt_api_key()

        if not validate_api_key(api_key):
            console.print("\n[red]유효하지 않은 API 키 형식입니다.[/red]")
            console.print("[dim]OpenAI API 키는 'sk-'로 시작해야 합니다.[/dim]")
            continue

        # Step 4: Create Secret and restart Agent
        console.print("\n[dim]Kubernetes Secret 생성 중...[/dim]")

        try:
            k8s_mgr.create_or_update_secret(api_key)
            console.print("[green]Secret 생성 성공![/green]")

            console.print("[dim]Agent 서비스 재시작 중...[/dim]")
            k8s_mgr.restart_agent_deployment()
            console.print("[green]Agent 재시작 완료![/green]")
            break
        except KubernetesError as e:
            console.print(f"\n[red]실패:[/red] {e}")
            console.print("[dim]다시 시도해주세요.[/dim]")
            continue

    # Step 5: Save config
    config_mgr.set_cluster_host(host)
    config_mgr.set_api_key(api_key)

    # Step 6: Done
    console.print()
    console.print(
        Panel.fit(
            "[bold green]설정 완료![/bold green]\n\n"
            f"클러스터: {host}\n"
            f"설정 파일: {config_mgr.config_file}\n\n"
            "[dim]이제 AKLP CLI를 사용할 수 있습니다.[/dim]",
            title="Setup Complete",
        )
    )
    console.print()

    # KUBECONFIG tip
    console.print(
        Panel.fit(
            "[bold cyan]Tip: kubectl 설정[/bold cyan]\n\n"
            "kubectl 명령어 실행 시 kubeconfig를 자동으로 인식하려면\n"
            "아래 명령어를 셸 설정 파일에 추가하세요:\n\n"
            "[bold]export KUBECONFIG=~/.kube/config[/bold]\n\n"
            "[dim]bash: ~/.bashrc | zsh: ~/.zshrc[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    return True