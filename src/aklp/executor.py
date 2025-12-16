"""kubectl command executor for AKLP CLI."""

import subprocess
from dataclasses import dataclass


class InvalidCommandError(Exception):
    """Raised when command is not a valid kubectl command."""

    pass


def validate_kubectl_command(command: str) -> bool:
    """Validate that the command is a kubectl command.

    Args:
        command: Command string to validate

    Returns:
        True if valid kubectl command

    Raises:
        InvalidCommandError: If command is not a kubectl command
    """
    stripped = command.strip()

    if not stripped.startswith("kubectl "):
        raise InvalidCommandError(
            f"kubectl 명령어가 아닙니다: {stripped[:50]}..."
            if len(stripped) > 50
            else f"kubectl 명령어가 아닙니다: {stripped}"
        )

    return True


@dataclass
class ExecutionResult:
    """Result of kubectl command execution."""

    success: bool
    stdout: str
    stderr: str
    return_code: int


def run_kubectl(command: str, timeout: int = 60) -> ExecutionResult:
    """Execute a kubectl command and return the result.

    Args:
        command: Full kubectl command string (e.g., "kubectl get pods -A")
        timeout: Timeout in seconds (default: 60)

    Returns:
        ExecutionResult with success status, stdout, stderr, and return code
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"명령어 실행 시간 초과 ({timeout}초)",
            return_code=-1,
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            return_code=-1,
        )


def get_kubeconfig_hint() -> str:
    """Return a hint message about KUBECONFIG setup."""
    return (
        "KUBECONFIG 설정을 확인해주세요:\n"
        "  1. ~/.kube/config 파일이 존재하는지 확인\n"
        "  2. 또는 환경변수 설정: export KUBECONFIG=~/.kube/config\n"
        "  3. kubeconfig의 server 주소가 올바른지 확인"
    )