"""Configuration management for AKLP CLI Agent."""

from dataclasses import dataclass
from functools import lru_cache

# NodePort mappings for k8s services
AGENT_NODE_PORT = 30001
NOTE_NODE_PORT = 30002
TASK_NODE_PORT = 30003
FILE_NODE_PORT = 30004


@dataclass
class Settings:
    """Application settings loaded from config.toml."""

    cluster_host: str
    agent_service_url: str
    note_service_url: str
    task_service_url: str
    file_service_url: str


def get_settings() -> Settings:
    """Get application settings from config.toml.

    Reads cluster host from ~/.aklp/config.toml and generates
    service URLs using NodePort mappings.

    Returns:
        Settings: Application configuration instance

    Raises:
        RuntimeError: If cluster host is not configured.
    """
    from aklp.secrets import ConfigManager

    config_mgr = ConfigManager()
    host = config_mgr.get_cluster_host()

    if not host:
        raise RuntimeError(
            "클러스터가 설정되지 않았습니다. 'aklp' 명령어로 초기 설정을 진행해주세요."
        )

    return Settings(
        cluster_host=host,
        agent_service_url=f"http://{host}:{AGENT_NODE_PORT}",
        note_service_url=f"http://{host}:{NOTE_NODE_PORT}",
        task_service_url=f"http://{host}:{TASK_NODE_PORT}",
        file_service_url=f"http://{host}:{FILE_NODE_PORT}",
    )


@lru_cache
def get_settings_cached() -> Settings:
    """Get cached application settings.

    Use this for repeated access within same session.
    Use get_settings() directly if config might have changed.

    Returns:
        Settings: Cached application configuration instance
    """
    return get_settings()