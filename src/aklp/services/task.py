"""Task service client for CRUD operations."""

from datetime import datetime
from uuid import UUID

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import (
    TaskBulkDelete,
    TaskBulkDeleteResponse,
    TaskBulkUpdate,
    TaskBulkUpdateItem,
    TaskBulkUpdateResponse,
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)

console = Console()


class TaskServiceError(Exception):
    """Exception raised when Task service fails."""

    pass


async def _make_request(
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    """Make HTTP request to Task service.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        json_data: JSON body data (optional)
        params: Query parameters (optional)

    Returns:
        dict: Response data

    Raises:
        TaskServiceError: If the service call fails
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
        raise TaskServiceError(
            "Task 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
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


async def create_task(
    title: str,
    description: str | None = None,
    status: TaskStatus = TaskStatus.PENDING,
    priority: TaskPriority | None = None,
    due_date: datetime | None = None,
    session_id: UUID | None = None,
) -> TaskResponse:
    """Create a new task.

    Args:
        title: Task title
        description: Task description (optional)
        status: Task status (default: pending)
        priority: Task priority (optional)
        due_date: Due date (optional)
        session_id: AI session ID (optional)

    Returns:
        TaskResponse: Created task data

    Raises:
        TaskServiceError: If the service call fails
    """
    request_data = TaskCreate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
        session_id=session_id,
    )
    data = await _make_request("POST", "/tasks", json_data=request_data.model_dump(mode="json"))
    return TaskResponse.model_validate(data)


async def list_tasks(
    page: int = 1,
    limit: int = 10,
    status: TaskStatus | None = None,
    session_id: str | None = None,
    batch_id: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> TaskListResponse:
    """List tasks with pagination and filtering.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10)
        status: Filter by status (optional)
        session_id: Filter by session ID (optional)
        batch_id: Filter by batch ID (optional)
        sort_by: Sort field (optional)
        sort_order: Sort order - asc or desc (default: desc)

    Returns:
        TaskListResponse: Paginated list of tasks

    Raises:
        TaskServiceError: If the service call fails
    """
    params: dict = {"page": page, "limit": limit, "order": sort_order}
    if status:
        params["status"] = status.value
    if session_id:
        params["session_id"] = session_id
    if batch_id:
        params["batch_id"] = batch_id
    if sort_by:
        params["sort_by"] = sort_by

    data = await _make_request("GET", "/tasks", params=params)
    return TaskListResponse.model_validate(data)


async def get_task(task_id: UUID) -> TaskResponse:
    """Get a single task by ID.

    Args:
        task_id: UUID of the task

    Returns:
        TaskResponse: Task data

    Raises:
        TaskServiceError: If the service call fails
    """
    data = await _make_request("GET", f"/tasks/{task_id}")
    return TaskResponse.model_validate(data)


async def update_task(
    task_id: UUID,
    title: str | None = None,
    description: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due_date: datetime | None = None,
) -> TaskResponse:
    """Update an existing task.

    Args:
        task_id: UUID of the task to update
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        priority: New priority (optional)
        due_date: New due date (optional)

    Returns:
        TaskResponse: Updated task data

    Raises:
        TaskServiceError: If the service call fails
    """
    request_data = TaskUpdate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
    )
    data = await _make_request(
        "PUT",
        f"/tasks/{task_id}",
        json_data=request_data.model_dump(exclude_none=True, mode="json"),
    )
    return TaskResponse.model_validate(data)


async def delete_task(task_id: UUID) -> None:
    """Delete a task.

    Args:
        task_id: UUID of the task to delete

    Raises:
        TaskServiceError: If the service call fails
    """
    await _make_request("DELETE", f"/tasks/{task_id}")


async def bulk_update_tasks(
    updates: list[TaskBulkUpdateItem],
) -> TaskBulkUpdateResponse:
    """Bulk update multiple tasks.

    Args:
        updates: List of task updates with IDs

    Returns:
        TaskBulkUpdateResponse: Updated tasks

    Raises:
        TaskServiceError: If the service call fails
    """
    request_data = TaskBulkUpdate(tasks=updates)
    data = await _make_request(
        "PUT",
        "/tasks/bulk",
        json_data=request_data.model_dump(exclude_none=True, mode="json"),
    )
    return TaskBulkUpdateResponse.model_validate(data)


async def bulk_delete_tasks(task_ids: list[UUID]) -> TaskBulkDeleteResponse:
    """Bulk delete multiple tasks.

    Args:
        task_ids: List of task UUIDs to delete

    Returns:
        TaskBulkDeleteResponse: Delete result with count

    Raises:
        TaskServiceError: If the service call fails
    """
    request_data = TaskBulkDelete(ids=task_ids)
    data = await _make_request(
        "DELETE",
        "/tasks/bulk",
        json_data=request_data.model_dump(mode="json"),
    )
    return TaskBulkDeleteResponse.model_validate(data)
