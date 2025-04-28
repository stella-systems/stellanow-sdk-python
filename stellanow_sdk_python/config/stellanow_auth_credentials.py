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

import os
from typing import Dict, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

from stellanow_sdk_python.config.enums.auth_strategy import AuthStrategyTypes

DEFAULT_OIDC_CLIENT_ID = "event-ingestor"


class CredentialFieldMapping(TypedDict):
    """Defines how env vars map to credential fields and whether they're required."""

    env_var: str
    field: str
    required: bool


# Define config outside the class to avoid Pydantic interference
STRATEGY_CONFIG: Dict[str, list[CredentialFieldMapping]] = {
    AuthStrategyTypes.OIDC.value: [
        {"env_var": "OIDC_USERNAME", "field": "username", "required": True},
        {"env_var": "OIDC_PASSWORD", "field": "password", "required": True},
        {"env_var": "OIDC_CLIENT_ID", "field": "client_id", "required": False},
    ],
    AuthStrategyTypes.BASIC.value: [
        {"env_var": "MQTT_USERNAME", "field": "username", "required": True},
        {"env_var": "MQTT_PASSWORD", "field": "password", "required": True},
    ],
    AuthStrategyTypes.NO_AUTH.value: [],
}


class StellaNowCredentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = DEFAULT_OIDC_CLIENT_ID

    def is_valid(self, auth_strategy: str) -> bool:
        """Validate credentials for the given auth strategy."""
        config = STRATEGY_CONFIG.get(auth_strategy, [])
        return all(getattr(self, mapping["field"]) is not None for mapping in config if mapping["required"])

    @classmethod
    def from_env(cls, auth_strategy: str) -> "StellaNowCredentials":
        """Construct credentials from environment variables based on auth strategy."""
        config = STRATEGY_CONFIG.get(auth_strategy)
        if config is None:
            raise ValueError(f"Unsupported auth strategy: {auth_strategy}")

        env_values = {mapping["env_var"]: os.getenv(mapping["env_var"]) for mapping in config}
        missing_vars = [
            mapping["env_var"] for mapping in config if mapping["required"] and not env_values[mapping["env_var"]]
        ]
        if missing_vars:
            raise ValueError(f"Missing required env vars for '{auth_strategy}': {', '.join(missing_vars)}")

        field_defaults = {field_name: field.default for field_name, field in cls.model_fields.items()}
        kwargs = {
            mapping["field"]: (
                env_values[mapping["env_var"]]
                if env_values[mapping["env_var"]] is not None
                else field_defaults[mapping["field"]]
            )
            for mapping in config
        }
        instance = cls(**kwargs)

        if not instance.is_valid(auth_strategy):
            raise ValueError(f"Invalid credentials for '{auth_strategy}' after env var mapping")

        return instance

    @staticmethod
    def get_required_env_vars(auth_strategy: str) -> list[str]:
        """Return required environment variables for the given auth strategy."""
        config = STRATEGY_CONFIG.get(auth_strategy, [])
        return [mapping["env_var"] for mapping in config if mapping["required"]]


# Backward compatibility
credentials_from_env = StellaNowCredentials.from_env
