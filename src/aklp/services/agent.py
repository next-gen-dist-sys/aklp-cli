"""Agent service client for natural language command processing."""

from uuid import UUID

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import AgentRequest, AgentResponse

console = Console()


class AgentServiceError(Exception):
    """Exception raised when Agent service fails."""

    pass


async def execute_command(
    raw_command: str,
    session_id: UUID | None = None,
) -> AgentResponse:
    """Execute natural language command via Agent service.

    Args:
        raw_command: User's natural language command
        session_id: Optional session ID for context

    Returns:
        AgentResponse: Agent service response with generated command

    Raises:
        AgentServiceError: If the service call fails
    """
    settings = get_settings()
    base_url = str(settings.agent_service_url).rstrip("/")
    url = f"{base_url}/api/v1/agent/execute"

    request_data = AgentRequest(
        session_id=session_id,
        raw_command=raw_command,
    )

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                url,
                json=request_data.model_dump(mode="json"),
            )
            response.raise_for_status()

            data = response.json()
            return AgentResponse.model_validate(data)

    except httpx.TimeoutException as e:
        raise AgentServiceError(
            "Agent 서비스 응답 시간 초과 (90초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise AgentServiceError(
            f"Agent 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise AgentServiceError(
            f"Agent 서비스 연결 실패: {settings.agent_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise AgentServiceError(f"예상치 못한 오류: {str(e)}") from e
