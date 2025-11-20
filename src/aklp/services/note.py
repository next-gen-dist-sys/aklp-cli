"""Note service client for file creation."""

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import NoteRequest, NoteResponse

console = Console()


class NoteServiceError(Exception):
    """Exception raised when Note service fails."""

    pass


async def create_file(filename: str, content: str) -> NoteResponse:
    """Create a file using Note service.

    Args:
        filename: Name of the file to create
        content: Content to write to the file

    Returns:
        NoteResponse: Response from Note service

    Raises:
        NoteServiceError: If the service call fails
    """
    settings = get_settings()
    url = f"{settings.note_service_url}/notes"

    request_data = NoteRequest(filename=filename, content=content)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            data = response.json()
            return NoteResponse.model_validate(data)

    except httpx.TimeoutException as e:
        raise NoteServiceError(
            f"Note 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise NoteServiceError(
            f"Note 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise NoteServiceError(
            f"Note 서비스 연결 실패: {settings.note_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise NoteServiceError(f"예상치 못한 오류: {str(e)}") from e
