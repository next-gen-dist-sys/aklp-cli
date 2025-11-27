"""Configuration and secrets management for AKLP CLI."""

import tomllib
from pathlib import Path

import tomli_w

AKLP_DIR = Path.home() / ".aklp"
CONFIG_FILE = AKLP_DIR / "config.toml"


class ConfigManager:
    """Manage AKLP CLI configuration and secrets."""

    def __init__(self) -> None:
        """Initialize config manager."""
        self.config_dir = AKLP_DIR
        self.config_file = CONFIG_FILE

    def ensure_config_dir(self) -> None:
        """Create ~/.aklp directory with secure permissions (0700)."""
        self.config_dir.mkdir(mode=0o700, exist_ok=True)

    def _load_config(self) -> dict:
        """Load configuration from TOML file.

        Returns:
            dict: Configuration dictionary, empty if file doesn't exist.
        """
        if not self.config_file.exists():
            return {}
        return tomllib.loads(self.config_file.read_text())

    def _save_config(self, config: dict) -> None:
        """Save configuration to TOML file with secure permissions.

        Args:
            config: Configuration dictionary to save.
        """
        self.ensure_config_dir()
        self.config_file.write_text(tomli_w.dumps(config))
        self.config_file.chmod(0o600)  # Read/write owner only

    def has_api_key(self) -> bool:
        """Check if OpenAI API key is configured.

        Returns:
            bool: True if API key exists and is non-empty.
        """
        config = self._load_config()
        api_key = config.get("openai", {}).get("api_key", "")
        return bool(api_key)

    def get_api_key(self) -> str | None:
        """Get stored OpenAI API key.

        Returns:
            str | None: API key if exists, None otherwise.
        """
        config = self._load_config()
        return config.get("openai", {}).get("api_key")

    def set_api_key(self, api_key: str) -> None:
        """Store OpenAI API key to config file.

        Args:
            api_key: OpenAI API key to store.
        """
        config = self._load_config()
        if "openai" not in config:
            config["openai"] = {}
        config["openai"]["api_key"] = api_key
        self._save_config(config)
