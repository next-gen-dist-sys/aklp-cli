"""LLM service client for natural language analysis."""

import httpx
from rich.console import Console

from aklp.config import get_settings
from aklp.models import AnalysisRequest, AnalysisResult

console = Console()


class LLMServiceError(Exception):
    """Exception raised when LLM service fails."""

    pass


async def analyze_prompt(prompt: str) -> AnalysisResult:
    """Analyze user's natural language prompt using LLM service.

    Args:
        prompt: User's natural language request

    Returns:
        AnalysisResult: Structured analysis result

    Raises:
        LLMServiceError: If the service call fails
    """
    settings = get_settings()
    url = f"{settings.llm_service_url}/analyze"

    request_data = AnalysisRequest(prompt=prompt)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            data = response.json()
            return AnalysisResult.model_validate(data)

    except httpx.TimeoutException as e:
        raise LLMServiceError(f"LLM 서비스 응답 시간 초과 (30초). 서비스 상태를 확인하세요.") from e
    except httpx.HTTPStatusError as e:
        raise LLMServiceError(
            f"LLM 서비스 오류 (HTTP {e.response.status_code}): {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise LLMServiceError(
            f"LLM 서비스 연결 실패: {settings.llm_service_url}\n오류: {str(e)}"
        ) from e
    except Exception as e:
        raise LLMServiceError(f"예상치 못한 오류: {str(e)}") from e
