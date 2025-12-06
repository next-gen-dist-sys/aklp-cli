"""Usage service client for API usage statistics."""

import httpx

from aklp.config import get_settings


class UsageServiceError(Exception):
    """Exception raised when Usage service fails."""

    pass


async def get_usage(period: str = "all") -> dict:
    """Get API usage statistics from Agent service.

    Args:
        period: Period to query - "today", "month", or "all"

    Returns:
        dict: Usage statistics response

    Raises:
        UsageServiceError: If the service call fails
    """
    settings = get_settings()
    base_url = str(settings.agent_service_url).rstrip("/")
    url = f"{base_url}/api/v1/usage"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params={"period": period})
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as e:
        raise UsageServiceError(
            "사용량 조회 응답 시간 초과 (30초). 서비스 상태를 확인하세요."
        ) from e
    except httpx.HTTPStatusError as e:
        raise UsageServiceError(
            f"사용량 조회 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise UsageServiceError(
            f"서비스 연결 실패: {settings.agent_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise UsageServiceError(f"예상치 못한 오류: {str(e)}") from e
