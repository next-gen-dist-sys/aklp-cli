"""Kubernetes cluster management for AKLP CLI."""

from pathlib import Path

import urllib3
from kubernetes import client, config
from kubernetes.client.rest import ApiException

NAMESPACE = "aklp"
SECRET_NAME = "openai-secret"
KUBECONFIG_PATH = Path.home() / ".kube" / "config"
API_TIMEOUT = 10  # seconds


class KubernetesError(Exception):
    """Exception raised for Kubernetes operations."""

    pass


class KubernetesManager:
    """Manage Kubernetes cluster connection and secrets."""

    def __init__(self, kubeconfig_path: Path | None = None) -> None:
        """Initialize Kubernetes manager.

        Args:
            kubeconfig_path: Path to kubeconfig file. Defaults to ~/.kube/config.
        """
        self.kubeconfig_path = kubeconfig_path or KUBECONFIG_PATH
        self._core_api: client.CoreV1Api | None = None

    def _load_config(self) -> None:
        """Load kubeconfig and initialize API client."""
        if not self.kubeconfig_path.exists():
            raise KubernetesError(
                f"kubeconfig 파일을 찾을 수 없습니다: {self.kubeconfig_path}\n"
                "k3s 클러스터의 kubeconfig를 ~/.kube/config에 복사해주세요."
            )

        try:
            config.load_kube_config(config_file=str(self.kubeconfig_path))
            self._core_api = client.CoreV1Api()
        except Exception as e:
            raise KubernetesError(f"kubeconfig 로드 실패: {e}") from e

    @property
    def core_api(self) -> client.CoreV1Api:
        """Get CoreV1Api client, loading config if needed."""
        if self._core_api is None:
            self._load_config()
        return self._core_api  # type: ignore[return-value]

    def test_connection(self) -> bool:
        """Test cluster connection by checking if aklp namespace exists.

        Returns:
            bool: True if connection successful and namespace exists.

        Raises:
            KubernetesError: If connection fails or namespace doesn't exist.
        """
        try:
            self.core_api.read_namespace(name=NAMESPACE, _request_timeout=API_TIMEOUT)
            return True
        except ApiException as e:
            if e.status == 404:
                raise KubernetesError(
                    f"'{NAMESPACE}' namespace가 존재하지 않습니다.\n"
                    "먼저 AKLP 서비스를 클러스터에 배포해주세요."
                ) from e
            raise KubernetesError(f"클러스터 연결 실패: {e.reason}") from e
        except urllib3.exceptions.MaxRetryError as e:
            raise KubernetesError(
                f"클러스터 연결 실패: 서버에 연결할 수 없습니다.\n"
                f"kubeconfig의 서버 주소를 확인해주세요: {self.kubeconfig_path}"
            ) from e
        except Exception as e:
            raise KubernetesError(f"클러스터 연결 실패: {e}") from e

    def create_or_update_secret(self, api_key: str) -> bool:
        """Create or update OpenAI API key secret.

        Args:
            api_key: OpenAI API key to store.

        Returns:
            bool: True if operation successful.

        Raises:
            KubernetesError: If secret creation/update fails.
        """
        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(
                name=SECRET_NAME,
                namespace=NAMESPACE,
            ),
            string_data={"api-key": api_key},
            type="Opaque",
        )

        try:
            # Try to read existing secret
            self.core_api.read_namespaced_secret(name=SECRET_NAME, namespace=NAMESPACE)
            # Secret exists, update it
            self.core_api.replace_namespaced_secret(
                name=SECRET_NAME, namespace=NAMESPACE, body=secret
            )
        except ApiException as e:
            if e.status == 404:
                # Secret doesn't exist, create it
                try:
                    self.core_api.create_namespaced_secret(namespace=NAMESPACE, body=secret)
                except ApiException as create_error:
                    raise KubernetesError(
                        f"Secret 생성 실패: {create_error.reason}"
                    ) from create_error
            else:
                raise KubernetesError(f"Secret 업데이트 실패: {e.reason}") from e

        return True

    def secret_exists(self) -> bool:
        """Check if OpenAI secret exists.

        Returns:
            bool: True if secret exists.
        """
        try:
            self.core_api.read_namespaced_secret(name=SECRET_NAME, namespace=NAMESPACE)
            return True
        except ApiException:
            return False