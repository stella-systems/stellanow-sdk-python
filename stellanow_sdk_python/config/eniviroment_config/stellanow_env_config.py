"""
Copyright (C) 2022-2025 Stella Technologies (UK) Limited.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from typing import Optional, Protocol

from stellanow_sdk_python.sinks.mqtt.utils.mqtt_url_parser import MqttUrlConfig, parse_mqtt_url


class StellaNowEnvironmentConfig(Protocol):
    mqtt_url_config: MqttUrlConfig
    api_base_url: Optional[str] = None

    @property
    def authority(self) -> str:
        pass


class _StellaNowEnvironmentConfigImpl:
    def __init__(self, mqtt_url: str, api_base_url: Optional[str] = None):
        self.mqtt_url_config = parse_mqtt_url(mqtt_url)
        self.api_base_url = api_base_url

    @property
    def authority(self) -> str:
        return f"{self.api_base_url}/auth/"


class EnvConfig:
    """Factory for creating environment configurations."""

    @staticmethod
    def stellanow_prod() -> StellaNowEnvironmentConfig:
        """Configuration for the StellaNow production environment."""
        return _StellaNowEnvironmentConfigImpl(
            mqtt_url="wss://ingestor.prod.stella.cloud:8083",
            api_base_url="https://api.prod.stella.cloud",
        )

    @staticmethod
    def stellanow_dev() -> StellaNowEnvironmentConfig:
        """Configuration for the StellaNow dev environment."""
        return _StellaNowEnvironmentConfigImpl(
            mqtt_url="wss://ingestor.dev.stella.cloud:8083",
            api_base_url="https://api.dev.stella.cloud",
        )

    @staticmethod
    def nanomq_local() -> StellaNowEnvironmentConfig:
        """Configuration for the NanoMq local environment."""
        return _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt-tcp://localhost:1883")

    @staticmethod
    def create_custom_env(api_base_url: str, mqtt_broker_url: str) -> StellaNowEnvironmentConfig:
        """Create a custom environment configuration."""
        return _StellaNowEnvironmentConfigImpl(api_base_url=api_base_url, mqtt_url=mqtt_broker_url)
