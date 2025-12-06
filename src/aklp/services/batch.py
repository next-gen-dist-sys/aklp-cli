"""Batch service client for CRUD operations."""

from uuid import UUID

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import (
    BatchCreate,
    BatchListResponse,
    BatchResponse,
    TaskCreate,
)

console = Console()


class BatchServiceError(Exception):
    """Exception raised when Batch service fails."""

    pass


async def _make_request(
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    """Make HTTP request to Task service (batch endpoints).

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        json_data: JSON body data (optional)
        params: Query parameters (optional)

    Returns:
        dict: Response data

    Raises:
        BatchServiceError: If the service call fails
    """
    settings = get_settings()
    base_url = str(settings.task_service_url).rstrip("/")
    url = f"{base_url}/api/v1{endpoint}"

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
        raise BatchServiceError(
            "Batch 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise BatchServiceError(
            f"Batch 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise BatchServiceError(
            f"Batch 서비스 연결 실패: {settings.task_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise BatchServiceError(f"예상치 못한 오류: {str(e)}") from e


async def create_batch(
    tasks: list[TaskCreate],
    session_id: UUID | None = None,
    reason: str | None = None,
) -> BatchResponse:
    """Create a new batch with tasks.

    Args:
        tasks: List of tasks to create
        session_id: AI session ID (optional)
        reason: AI's reason for creating these tasks (optional)

    Returns:
        BatchResponse: Created batch data

    Raises:
        BatchServiceError: If the service call fails
    """
    request_data = BatchCreate(
        tasks=tasks,
        session_id=session_id,
        reason=reason,
    )
    data = await _make_request("POST", "/batches", json_data=request_data.model_dump(mode="json"))
    return BatchResponse.model_validate(data)


async def list_batches(
    page: int = 1,
    session_id: str | None = None,
) -> BatchListResponse:
    """List batches with pagination.

    Args:
        page: Page number (default: 1)
        session_id: Optional session ID filter

    Returns:
        BatchListResponse: Paginated list of batches

    Raises:
        BatchServiceError: If the service call fails
    """
    params: dict = {"page": page}
    if session_id:
        params["session_id"] = session_id
    data = await _make_request("GET", "/batches", params=params)
    return BatchListResponse.model_validate(data)


async def get_batch(batch_id: UUID) -> BatchResponse:
    """Get a single batch by ID.

    Args:
        batch_id: UUID of the batch

    Returns:
        BatchResponse: Batch data

    Raises:
        BatchServiceError: If the service call fails
    """
    data = await _make_request("GET", f"/batches/{batch_id}")
    return BatchResponse.model_validate(data)


async def get_latest_batch(session_id: str | None = None) -> BatchResponse | None:
    """Get the latest batch.

    Args:
        session_id: Optional session ID filter

    Returns:
        BatchResponse or None: Latest batch data or None if not found

    Raises:
        BatchServiceError: If the service call fails
    """
    params: dict = {}
    if session_id:
        params["session_id"] = session_id
    data = await _make_request("GET", "/batches/latest", params=params if params else None)
    if not data:
        return None
    return BatchResponse.model_validate(data)
