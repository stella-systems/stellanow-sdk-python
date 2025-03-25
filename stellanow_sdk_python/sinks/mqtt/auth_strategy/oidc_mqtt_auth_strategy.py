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

    async def authenticate(self, client: mqtt.Client) -> None:
        """
        Authenticates the MQTT client using OIDC.
        """
        logger.info("Authenticating MQTT client using OIDC.")
        try:
            access_token = await self.auth_service.get_access_token()
            client.username_pw_set(access_token, password=None)
        except Exception as e:
            logger.error(f"OIDC authentication failed: {e}")
            raise Exception("Failed to authenticate MQTT client using OIDC.")
