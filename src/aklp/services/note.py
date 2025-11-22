"""Note service client for CRUD operations."""

from uuid import UUID

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate

console = Console()


class NoteServiceError(Exception):
    """Exception raised when Note service fails."""

    pass


async def _make_request(
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    """Make HTTP request to Note service.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        json_data: JSON body data (optional)
        params: Query parameters (optional)

    Returns:
        dict: Response data

    Raises:
        NoteServiceError: If the service call fails
    """
    settings = get_settings()
    url = f"{settings.note_service_url}/api/v1{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return {}
            return response.json()

    except httpx.TimeoutException as e:
        raise NoteServiceError(
            "Note 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
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


async def create_note(
    title: str,
    content: str,
    session_id: UUID | None = None,
) -> NoteResponse:
    """Create a new note.

    Args:
        title: Title of the note
        content: Content of the note
        session_id: Optional session ID

    Returns:
        NoteResponse: Created note data

    Raises:
        NoteServiceError: If the service call fails
    """
    request_data = NoteCreate(title=title, content=content, session_id=session_id)
    data = await _make_request("POST", "/notes", json_data=request_data.model_dump(mode="json"))
    return NoteResponse.model_validate(data)


async def list_notes(
    page: int = 1,
    limit: int = 10,
) -> NoteListResponse:
    """List notes with pagination.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10)

    Returns:
        NoteListResponse: Paginated list of notes

    Raises:
        NoteServiceError: If the service call fails
    """
    params = {"page": page, "limit": limit}
    data = await _make_request("GET", "/notes", params=params)
    return NoteListResponse.model_validate(data)


async def get_note(note_id: UUID) -> NoteResponse:
    """Get a single note by ID.

    Args:
        note_id: UUID of the note

    Returns:
        NoteResponse: Note data

    Raises:
        NoteServiceError: If the service call fails
    """
    data = await _make_request("GET", f"/notes/{note_id}")
    return NoteResponse.model_validate(data)


async def update_note(
    note_id: UUID,
    title: str | None = None,
    content: str | None = None,
) -> NoteResponse:
    """Update an existing note.

    Args:
        note_id: UUID of the note to update
        title: New title (optional)
        content: New content (optional)

    Returns:
        NoteResponse: Updated note data

    Raises:
        NoteServiceError: If the service call fails
    """
    request_data = NoteUpdate(title=title, content=content)
    data = await _make_request(
        "PUT",
        f"/notes/{note_id}",
        json_data=request_data.model_dump(exclude_none=True),
    )
    return NoteResponse.model_validate(data)


async def delete_note(note_id: UUID) -> None:
    """Delete a note.

    Args:
        note_id: UUID of the note to delete

    Raises:
        NoteServiceError: If the service call fails
    """
    await _make_request("DELETE", f"/notes/{note_id}")
