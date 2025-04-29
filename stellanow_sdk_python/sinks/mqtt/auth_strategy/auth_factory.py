"""
Factory for creating MQTT authentication strategies.
"""

from loguru import logger

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.enums.auth_strategy import AuthStrategyTypes
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.no_auth_mqtt_auth_strategy import NoAuthMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.user_pass_auth_mqtt_auth_strategy import UserPassAuthMqttAuthStrategy


def create_auth_strategy(
    auth_strategy_type: str,
    project_info: StellaProjectInfo,
    credentials: StellaNowCredentials,
    env_config: StellaNowEnvironmentConfig,
) -> IMqttAuthStrategy:
    """
    Create an authentication strategy based on the specified type.

    Args:
        auth_strategy_type (str): The type of authentication ("oidc", "basic", "none").
        project_info (StellaProjectInfo): Project information including organization_id.
        credentials (StellaNowCredentials): The credentials object containing auth details.
        env_config (StellaNowEnvironmentConfig): The environment configuration.

    Returns:
        IMqttAuthStrategy: The instantiated authentication strategy.

    Raises:
        ValueError: If the auth_type is unsupported or required credentials are missing.
    """

    if not credentials.is_valid(auth_strategy_type):
        raise ValueError(f"Invalid or missing credentials for '{auth_strategy_type}'")

    logger.info(f"Creating auth strategy: {auth_strategy_type}")
    if auth_strategy_type == AuthStrategyTypes.OIDC.value:
        return OidcMqttAuthStrategy(project_info, credentials, env_config)
    elif auth_strategy_type == AuthStrategyTypes.BASIC.value:
        return UserPassAuthMqttAuthStrategy(credentials)
    elif auth_strategy_type == AuthStrategyTypes.NO_AUTH.value:
        return NoAuthMqttAuthStrategy()
    else:
        raise ValueError(f"Unknown auth strategy type: {auth_strategy_type}")
