"""Configuration management for IoT device controller."""

import json
import os
from typing import Dict, Any, List


class ConfigManager:
    """Manages device configuration loading and access."""

    DEFAULT_CONFIG_FILE = "config/device.json"
    DEFAULT_HEARTBEAT_INTERVAL = 60

    def __init__(self, config_file: str = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load device configuration from JSON file.

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        with open(self.config_file, 'r') as f:
            config = json.load(f)

        return config

    @property
    def device_id(self) -> str:
        """Get device ID."""
        return self._config.get('deviceId', 'unknown-device')

    @property
    def endpoint(self) -> str:
        """Get AWS IoT endpoint."""
        return self._config['endpoint']

    @property
    def region(self) -> str:
        """Get AWS region."""
        return self._config.get('region', 'us-east-1')

    @property
    def heartbeat_interval(self) -> int:
        """Get heartbeat interval in seconds."""
        return self._config.get('heartbeatInterval', self.DEFAULT_HEARTBEAT_INTERVAL)

    @property
    def cert_path(self) -> str:
        """Get certificate file path."""
        certs = self._config.get('certificates', {})
        return certs.get('certPath', 'certs/device.cert.pem')

    @property
    def private_key_path(self) -> str:
        """Get private key file path."""
        certs = self._config.get('certificates', {})
        return certs.get('privateKeyPath', 'certs/device.private.key')

    @property
    def root_ca_path(self) -> str:
        """Get root CA certificate path."""
        certs = self._config.get('certificates', {})
        return certs.get('rootCAPath', 'certs/AmazonRootCA1.pem')

    @property
    def equipment_config(self) -> List[Dict[str, Any]]:
        """
        Get equipment configuration list.

        Returns:
            List of equipment configurations, or empty list if not present.
        """
        return self._config.get('equipments', [])

    @property
    def plc_config(self) -> Dict[str, Any]:
        """
        Get PLC connection configuration.

        Returns:
            Dictionary containing PLC connection settings, or empty dict if not present.
        """
        return self._config.get('plc', {})

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def __repr__(self) -> str:
        """String representation of config manager."""
        return f"ConfigManager(device_id={self.device_id}, endpoint={self.endpoint})"
