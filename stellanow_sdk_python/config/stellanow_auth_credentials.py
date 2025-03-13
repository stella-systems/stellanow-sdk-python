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

from typing import Optional

from stellanow_sdk_python.config.stellanow_config import read_env


class StellaNowCredentials:
    """Holds authentication credentials for the StellaNow SDK."""

    DEFAULT_OIDC_CLIENT_ID = "event-ingestor"

    def __init__(
        self,
        oidc_username: Optional[str] = None,
        oidc_password: Optional[str] = None,
        oidc_client_id: str = DEFAULT_OIDC_CLIENT_ID,
        mqtt_username: Optional[str] = None,
        mqtt_password: Optional[str] = None,
    ):
        self.oidc_username = oidc_username
        self.oidc_password = oidc_password
        self.oidc_client_id = oidc_client_id
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password


def credentials_from_env(auth_strategy: str = "oidc") -> StellaNowCredentials:
    """
    Create a StellaNowCredentials instance from environment variables based on auth strategy.

    Args:
        auth_strategy (str): The authentication strategy ("oidc", "username_password", "none").

    Returns:
        StellaNowCredentials: Configured credentials for the specified strategy.
    """
    if auth_strategy == "oidc":
        return StellaNowCredentials(
            oidc_username=read_env("OIDC_USERNAME"),
            oidc_password=read_env("OIDC_PASSWORD"),
            oidc_client_id=read_env("OIDC_CLIENT_ID", StellaNowCredentials.DEFAULT_OIDC_CLIENT_ID),
        )
    elif auth_strategy == "username_password":
        return StellaNowCredentials(mqtt_username=read_env("MQTT_USERNAME"), mqtt_password=read_env("MQTT_PASSWORD"))
    elif auth_strategy == "none":
        return StellaNowCredentials()
    else:
        raise ValueError(f"Unknown auth strategy: {auth_strategy}")
