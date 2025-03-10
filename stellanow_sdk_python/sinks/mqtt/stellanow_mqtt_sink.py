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

import asyncio

import paho.mqtt.client as mqtt
from loguru import logger

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy


class StellaNowMqttSink(IStellaNowSink):
    """
    MQTT implementation of the StellaNow Sink.
    """

    def __init__(
        self, auth_strategy: IMqttAuthStrategy, env_config: StellaNowEnvironmentConfig, project_info: StellaProjectInfo
    ):
        self.auth_strategy = auth_strategy
        self.env_config = env_config
        self.project_info = project_info
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # noqa
            transport="websockets",
            protocol=mqtt.MQTTv5,
            client_id="StellaNowSDKPython",  # noqa
        )
        self.is_connected = asyncio.Event()
        self.reconnect_attempts = 0
        self._shutdown = False

    async def connect(self) -> None:
        """
        Connects to the MQTT broker.
        """
        if self._shutdown:
            logger.info("Shutdown requested, skipping connection attempt.")
            return
        try:
            # TODO Check if 'start_refresh_task' is valid
            # Start token refresh if using OIDC
            # if isinstance(self.auth_strategy, OidcMqttAuthStrategy):
            #     await self.auth_strategy.auth_service.start_refresh_task()
            await self.auth_strategy.authenticate(self.client)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            logger.info("Connecting to MQTT broker...")
            # TODO Add port to env_config
            self.client.connect(self.env_config.broker_url, 8083, 60)
            self.client.loop_start()
            await self.wait_for_connection()
        except Exception as e:
            logger.error(f"Unexpected error during MQTT connection: {e}")
            if not self._shutdown:
                await self.handle_connection_error(e)

    async def disconnect(self) -> None:
        """
        Disconnects from the MQTT broker.
        """
        logger.info("Disconnecting from MQTT broker...")
        self._shutdown = True
        if isinstance(self.auth_strategy, OidcMqttAuthStrategy):
            await self.auth_strategy.auth_service.stop_refresh_task()
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected.clear()

    async def send_message(self, message: str) -> None:
        """
        Sends a message to the MQTT broker.
        :param message: The message to send.
        """
        if not self.is_connected.is_set():
            raise Exception("MQTT sink is not connected.")

        await self.wait_for_connection()
        mqtt_topic = f"in/{self.project_info.organization_id}"
        result = self.client.publish(mqtt_topic, message)
        status = result.rc

        if status == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Message sent: {message}")
        else:
            logger.error(f"Failed to send message. Status: {status}")
            await self.handle_publish_error(status)

    def is_connected(self) -> bool:
        """
        Checks if the MQTT sink is connected.
        :return: True if connected; otherwise, False.
        """
        return self.is_connected.is_set()

    def on_connect(self, client, userdata, flags, reason_code, properties):  # noqa
        if reason_code == 0:
            logger.info("Connected to MQTT broker")
            self.is_connected.set()
            self.reconnect_attempts = 0
        else:
            logger.error(f"Connection failed with code {reason_code}")

    def on_disconnect(self, client, userdata, reason_code, properties, x):  # noqa
        logger.warning("Disconnected from MQTT broker")
        self.is_connected.clear()
        self.client.disconnect()
        if reason_code == mqtt.MQTT_ERR_CONN_LOST:
            logger.error("Unexpected disconnection.")
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.handle_connection_error(reason_code))
            else:
                asyncio.run(self.handle_connection_error(reason_code))

    def on_publish(self, client, userdata, mid, reason_code, properties):  # noqa
        """Callback when a message is published."""
        if reason_code == mqtt.MQTT_ERR_SUCCESS:
            logger.success(f"Message published successfully with mid: {mid}")
        else:
            logger.error(f"Failed to publish message with mid: {mid}, reason_code: {reason_code}")
            if not self._shutdown:
                asyncio.create_task(self.handle_publish_error(reason_code))

    async def wait_for_connection(self):
        """
        Wait until the client is connected
        """
        while not self.is_connected.is_set():
            await asyncio.sleep(0.5)

    async def handle_connection_error(self, error):
        """
        Handle connection errors with retry logic
        """
        logger.error(f"Handling connection error: {error}")
        backoff = min(2**self.reconnect_attempts, 60)
        self.reconnect_attempts += 1

        logger.info(f"Retrying connection in {backoff} seconds...")
        await asyncio.sleep(backoff)
        if not self._shutdown:
            await self.connect()
        else:
            logger.info("Shutdown detected, aborting retry.")

    async def handle_publish_error(self, error):
        """
        Handle publish errors and retry
        """
        logger.error(f"Handling publish error: {error}")
        await self.wait_for_connection()
        logger.info("Retrying message publish...")
