"""File service client for CRUD operations."""

from pathlib import Path
from uuid import UUID

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import FileListResponse, FileResponse, FileUpdate

console = Console()


class FileServiceError(Exception):
    """Exception raised when File service fails."""

    pass


async def _make_request(
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    params: dict | None = None,
    files: dict | None = None,
    data: dict | None = None,
) -> dict:
    """Make HTTP request to File service.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        endpoint: API endpoint path
        json_data: JSON body data (optional)
        params: Query parameters (optional)
        files: Files to upload (optional)
        data: Form data (optional)

    Returns:
        dict: Response data

    Raises:
        FileServiceError: If the service call fails
    """
    settings = get_settings()
    base_url = str(settings.file_service_url).rstrip("/")
    url = f"{base_url}/api/v1{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                files=files,
                data=data,
            )
            response.raise_for_status()

            if response.status_code == 204:
                return {}
            return response.json()

    except httpx.TimeoutException as e:
        raise FileServiceError(
            "File 서비스 응답 시간 초과 (60초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise FileServiceError(
            f"File 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise FileServiceError(
            f"File 서비스 연결 실패: {settings.file_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise FileServiceError(f"예상치 못한 오류: {str(e)}") from e


async def upload_file(
    file_path: Path,
    description: str | None = None,
    session_id: UUID | None = None,
) -> FileResponse:
    """Upload a file.

    Args:
        file_path: Path to the file to upload
        description: Optional file description
        session_id: Optional session ID

    Returns:
        FileResponse: Uploaded file data

    Raises:
        FileServiceError: If the service call fails
    """
    if not file_path.exists():
        raise FileServiceError(f"파일을 찾을 수 없습니다: {file_path}")

    if not file_path.is_file():
        raise FileServiceError(f"파일이 아닙니다: {file_path}")

    # Read file content
    content = file_path.read_bytes()
    filename = file_path.name

    # Prepare multipart form data
    files = {"file": (filename, content)}
    data = {}
    if description:
        data["description"] = description
    if session_id:
        data["session_id"] = str(session_id)

    response_data = await _make_request("POST", "/files", files=files, data=data if data else None)
    return FileResponse.model_validate(response_data)


async def list_files(
    page: int = 1,
    session_id: str | None = None,
) -> FileListResponse:
    """List files with pagination.

    Args:
        page: Page number (default: 1)
        session_id: Optional session ID filter

    Returns:
        FileListResponse: Paginated list of files

    Raises:
        FileServiceError: If the service call fails
    """
    params: dict = {"page": page}
    if session_id:
        params["session_id"] = session_id
    data = await _make_request("GET", "/files", params=params)
    return FileListResponse.model_validate(data)


async def get_file(file_id: UUID) -> FileResponse:
    """Get file metadata by ID.

    Args:
        file_id: UUID of the file

    Returns:
        FileResponse: File metadata

    Raises:
        FileServiceError: If the service call fails
    """
    data = await _make_request("GET", f"/files/{file_id}")
    return FileResponse.model_validate(data)


async def download_file(file_id: UUID) -> tuple[bytes, str, str]:
    """Download file content.

    Args:
        file_id: UUID of the file

    Returns:
        tuple: (file content bytes, filename, content_type)

    Raises:
        FileServiceError: If the service call fails
    """
    settings = get_settings()
    base_url = str(settings.file_service_url).rstrip("/")
    url = f"{base_url}/api/v1/files/{file_id}/download"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Extract filename from Content-Disposition header
            content_disposition = response.headers.get("content-disposition", "")
            filename = "download"
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

            content_type = response.headers.get("content-type", "application/octet-stream")

            return response.content, filename, content_type

    except httpx.TimeoutException as e:
        raise FileServiceError(
            "File 서비스 응답 시간 초과 (60초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise FileServiceError(
            f"File 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise FileServiceError(
            f"File 서비스 연결 실패: {settings.file_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise FileServiceError(f"예상치 못한 오류: {str(e)}") from e


async def update_file_metadata(
    file_id: UUID,
    filename: str | None = None,
    description: str | None = None,
) -> FileResponse:
    """Update file metadata.

    Args:
        file_id: UUID of the file to update
        filename: New filename (optional)
        description: New description (optional)

    Returns:
        FileResponse: Updated file metadata

    Raises:
        FileServiceError: If the service call fails
    """
    request_data = FileUpdate(filename=filename, description=description)
    data = await _make_request(
        "PATCH",
        f"/files/{file_id}",
        json_data=request_data.model_dump(exclude_none=True),
    )
    return FileResponse.model_validate(data)


async def replace_file(
    file_id: UUID,
    file_path: Path,
) -> FileResponse:
    """Replace file content.

    Args:
        file_id: UUID of the file to replace
        file_path: Path to the new file

    Returns:
        FileResponse: Updated file metadata

    Raises:
        FileServiceError: If the service call fails
    """
    if not file_path.exists():
        raise FileServiceError(f"파일을 찾을 수 없습니다: {file_path}")

    if not file_path.is_file():
        raise FileServiceError(f"파일이 아닙니다: {file_path}")

    content = file_path.read_bytes()
    filename = file_path.name

    files = {"file": (filename, content)}

    data = await _make_request("PUT", f"/files/{file_id}", files=files)
    return FileResponse.model_validate(data)


async def delete_file(file_id: UUID) -> None:
    """Delete a file.

    Args:
        file_id: UUID of the file to delete

    Raises:
        FileServiceError: If the service call fails
    """
    await _make_request("DELETE", f"/files/{file_id}")
