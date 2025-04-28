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

import sys

from loguru import logger

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig, StellaNowEnvironmentConfig
from stellanow_sdk_python.config.enums.auth_strategy import AuthStrategyTypes
from stellanow_sdk_python.config.enums.logger_config import LoggerLevel
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import project_info_from_env
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_message_queue_strategy import (
    FifoMessageQueueStrategy,
)
from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import MessageQueueType
from stellanow_sdk_python.message_queue.message_queue_strategy.lifo_message_queue_strategy import (
    LifoMessageQueueStrategy,
)
from stellanow_sdk_python.sdk import StellaNowSDK
from stellanow_sdk_python.sinks.mqtt.auth_strategy.auth_factory import create_auth_strategy
from stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink import StellaNowMqttSink


def configure_sdk(
    auth_strategy_type: str,
    env_config: StellaNowEnvironmentConfig,
    queue_strategy_type: str = MessageQueueType.FIFO.value,
    logger_level: LoggerLevel = LoggerLevel.INFO,
) -> StellaNowSDK:
    """
    Generic method to configure and return a StellaNowSDK instance.

    Args:
        auth_strategy_type (str): Authentication strategy ("oidc", "basic", "none").
        env_config (StellaNowEnvironmentConfig): Environment configuration (e.g., from EnvConfig).
        queue_strategy_type (str, optional): Queue strategy ("fifo" or "lifo"). Defaults to "fifo".
        logger_level (LoggerLevel, optional): Logging level for the SDK. Defaults to LoggerLevel.INFO.

    Returns:
        StellaNowSDK: A configured SDK instance.

    Raises:
        ValueError: If required environment variables are missing or invalid.
    """
    try:
        logger.remove()
        logger.add(sys.stderr, level=logger_level.value)
        logger.info("Starting StellaNow SDK demo...")

        # Load project info
        project_info = project_info_from_env()
        logger.info(
            f"Loaded project info - Organization ID: {project_info.organization_id}, Project ID: {project_info.project_id}"
        )

        # Load credentials
        credentials = StellaNowCredentials.from_env(auth_strategy=auth_strategy_type)

        # Create auth strategy
        auth_strategy = create_auth_strategy(auth_strategy_type, project_info, credentials, env_config)

        # Initialize components
        queue_strategies = {
            MessageQueueType.FIFO.value: FifoMessageQueueStrategy,
            MessageQueueType.LIFO.value: LifoMessageQueueStrategy,
        }
        queue_strategy_class = queue_strategies.get(queue_strategy_type, FifoMessageQueueStrategy)
        queue_strategy = queue_strategy_class()
        mqtt_sink = StellaNowMqttSink(auth_strategy=auth_strategy, env_config=env_config, project_info=project_info)
        sdk = StellaNowSDK(project_info=project_info, sink=mqtt_sink, queue_strategy=queue_strategy)
        logger.info(f"SDK initialized with MQTT sink and {queue_strategy_type.upper()} queue strategy.")

        return sdk

    except ValueError as e:
        required_vars = ["ORGANIZATION_ID", "PROJECT_ID"] + StellaNowCredentials.get_required_env_vars(
            auth_strategy_type
        )
        logger.error(f"Configuration error: {e}")
        logger.info(
            f"Please set required environment variables for '{auth_strategy_type}' auth: {', '.join(required_vars)}"
        )
        raise


# Pre-defined configurations
def configure_dev_oidc_mqtt_fifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_dev env with OIDC auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.OIDC.value,
        env_config=EnvConfig.stellanow_dev(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )


def configure_dev_no_auth_mqtt_fifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_dev env with NO auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.NO_AUTH.value,
        env_config=EnvConfig.stellanow_dev(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )


def configure_dev_basic_mqtt_lifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_dev env with basic auth, MQTT sink, and LIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.BASIC.value,
        env_config=EnvConfig.stellanow_dev(),
        queue_strategy_type=MessageQueueType.LIFO.value,
        logger_level=logger_level,
    )


def configure_local_nanomq_basic_mqtt_fifo_sdk(
    logger_level: LoggerLevel = LoggerLevel.INFO,
) -> StellaNowSDK:
    """Configure SDK for local NanoMQ env with basic auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.BASIC.value,
        env_config=EnvConfig.nanomq_local(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )


def configure_local_nanomq_basic_mqtt_lifo_sdk(
    logger_level: LoggerLevel = LoggerLevel.INFO,
) -> StellaNowSDK:
    """Configure SDK for local NanoMQ env with basic auth, MQTT sink, and LIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.BASIC.value,
        env_config=EnvConfig.nanomq_local(),
        queue_strategy_type=MessageQueueType.LIFO.value,
        logger_level=logger_level,
    )


def configure_prod_oidc_mqtt_fifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_prod env with OIDC auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.OIDC.value,
        env_config=EnvConfig.stellanow_prod(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )


def configure_prod_no_auth_mqtt_fifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_prod env with no auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.NO_AUTH.value,
        env_config=EnvConfig.stellanow_prod(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )


def configure_prod_basic_mqtt_fifo_sdk(logger_level: LoggerLevel = LoggerLevel.INFO) -> StellaNowSDK:
    """Configure SDK for stellanow_prod env with basic auth, MQTT sink, and FIFO queue."""
    return configure_sdk(
        auth_strategy_type=AuthStrategyTypes.BASIC.value,
        env_config=EnvConfig.stellanow_prod(),
        queue_strategy_type=MessageQueueType.FIFO.value,
        logger_level=logger_level,
    )
