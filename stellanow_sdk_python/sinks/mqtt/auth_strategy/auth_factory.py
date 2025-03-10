"""
Factory for creating MQTT authentication strategies.
"""

from loguru import logger

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.no_auth_mqtt_auth_strategy import NoAuthMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.user_pass_auth_mqtt_auth_strategy import UserPassAuthMqttAuthStrategy


def create_auth_strategy(
    auth_type: str,
    project_info: StellaProjectInfo,
    credentials: StellaNowCredentials,
    env_config: StellaNowEnvironmentConfig,
) -> IMqttAuthStrategy:
    """
    Create an authentication strategy based on the specified type.

    Args:
        auth_type (str): The type of authentication ("oidc", "username_password", "none").
        project_info (StellaProjectInfo): Project information including organization_id.
        credentials (StellaNowCredentials): The credentials object containing auth details.
        env_config (StellaNowEnvironmentConfig): The environment configuration.

    Returns:
        IMqttAuthStrategy: The instantiated authentication strategy.

    Raises:
        ValueError: If the auth_type is unsupported or required credentials are missing.
    """
    if auth_type == "oidc":
        if not (credentials.oidc_username and credentials.oidc_password and credentials.oidc_client_id):
            raise ValueError("OIDC requires STELLA_USERNAME, STELLA_PASSWORD, and OIDC_CLIENT_ID")
        auth_strategy = OidcMqttAuthStrategy(StellaNowAuthenticationService(project_info, credentials, env_config))
        logger.info(
            f"Loaded OIDC credentials - Username: {credentials.oidc_username}, Client ID: {credentials.oidc_client_id}"
        )
        return auth_strategy

    elif auth_type == "username_password":
        if not (credentials.mqtt_username and credentials.mqtt_password):
            raise ValueError("Username/password auth requires MQTT_USERNAME and MQTT_PASSWORD")
        auth_strategy = UserPassAuthMqttAuthStrategy(credentials.mqtt_username, credentials.mqtt_password)
        logger.info(f"Loaded username/password credentials - Username: {credentials.mqtt_username}")
        return auth_strategy

    elif auth_type == "none":
        auth_strategy = NoAuthMqttAuthStrategy()
        logger.info("Using no-auth strategy - no credentials required")
        return auth_strategy

    else:
        raise ValueError(f"Unsupported auth strategy: {auth_type}")
