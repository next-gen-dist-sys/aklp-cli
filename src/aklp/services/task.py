"""Task service client for shell command execution."""

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import TaskRequest, TaskResponse

console = Console()


class TaskServiceError(Exception):
    """Exception raised when Task service fails."""

    pass


async def execute_command(command: str) -> TaskResponse:
    """Execute a shell command using Task service.

    Args:
        command: Shell command to execute

    Returns:
        TaskResponse: Response from Task service with stdout/stderr

    Raises:
        TaskServiceError: If the service call fails
    """
    settings = get_settings()
    url = f"{settings.task_service_url}/tasks/execute"

    request_data = TaskRequest(command=command)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            data = response.json()
            return TaskResponse.model_validate(data)

    except httpx.TimeoutException as e:
        raise TaskServiceError(
            f"Task 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise TaskServiceError(
            f"Task 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise TaskServiceError(
            f"Task 서비스 연결 실패: {settings.task_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise TaskServiceError(f"예상치 못한 오류: {str(e)}") from e
