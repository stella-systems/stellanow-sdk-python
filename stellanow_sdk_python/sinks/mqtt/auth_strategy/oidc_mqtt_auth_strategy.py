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

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy


class OidcMqttAuthStrategy(IMqttAuthStrategy):
    """Authentication strategy using OpenID Connect (OIDC)."""

    def __init__(
        self, project_info: StellaProjectInfo, credentials: StellaNowCredentials, env_config: StellaNowEnvironmentConfig
    ) -> None:
        self.project_info = project_info
        self.credentials = credentials
        self.env_config = env_config
        self.auth_service = StellaNowAuthenticationService(
            project_info=self.project_info,
            credentials=self.credentials,
            env_config=self.env_config,
        )
        self.client = None
        self.auth_service.register_token_update_callback(self._update_token)
        logger.debug("Initialized OidcMqttAuthStrategy and registered callback")

    async def _update_token(self, new_token: str) -> None:
        """Update MQTT client credentials with new token and reconnect."""
        logger.info(f"Received token update callback with new token: {new_token[:20]}...")
        if self.client:
            logger.debug("Updating MQTT client credentials and forcing reconnect")
            self.client.username_pw_set(username=new_token, password=None)
            try:
                self.client.disconnect()
                logger.debug("Disconnected MQTT client for token update")
                self.client.reconnect()
                logger.info("Reconnected MQTT client after token update")
            except Exception as e:
                logger.error(f"Failed to reconnect after token update: {e}")
        else:
            logger.warning("No MQTT client available to update token")

    async def authenticate(self, client: mqtt.Client) -> None:
        """Authenticate the MQTT client using OIDC."""
        self.client = client
        access_token = await self.auth_service.get_access_token()
        logger.info("Authenticating MQTT client using OIDC.")
        logger.debug(f"Using token: {access_token[:20]}...")
        client.username_pw_set(username=access_token, password=None)
