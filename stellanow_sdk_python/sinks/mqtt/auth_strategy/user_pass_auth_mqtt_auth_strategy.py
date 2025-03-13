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

import paho.mqtt.client as mqtt
from loguru import logger

from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy


class UserPassAuthMqttAuthStrategy(IMqttAuthStrategy):
    """
    Username/password authentication strategy for MQTT connections.
    """

    def __init__(self, username: str, password: str):
        """
        Authentication strategy using a simple username and password.
        :param username: The username for MQTT authentication.
        :param password: The password for MQTT authentication.
        """
        self.username = username
        self.password = password

    async def authenticate(self, client: mqtt.Client) -> None:
        """
        Authenticates the MQTT client using a username and password.
        """
        logger.info("Authenticating MQTT client using username/password.")

        try:
            client.username_pw_set(self.username, self.password)

        except Exception as e:
            logger.error(f"Username/password authentication failed: {e}")
            raise Exception("Failed to authenticate MQTT client using username/password.")

    def get_required_env_vars(self) -> list[str]:
        """Return required environment variables for username/password authentication."""
        return ["MQTT_USERNAME", "MQTT_PASSWORD"]
