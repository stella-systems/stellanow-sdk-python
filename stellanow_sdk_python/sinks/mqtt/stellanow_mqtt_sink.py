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
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt
from loguru import logger
from nanoid import generate

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy


class StellaNowMqttSink(IStellaNowSink):
    def __init__(
        self,
        auth_strategy: IMqttAuthStrategy,
        env_config: StellaNowEnvironmentConfig,
        project_info: StellaProjectInfo,
    ):
        self.auth_strategy = auth_strategy
        self.env_config = env_config
        self.project_info = project_info
        self.default_qos = 1
        self.client_id = f"StellaNowSDKPython_{generate(size=10)}"
        mqtt_config = env_config.mqtt_url_config

        self.client: Optional[mqtt.Client] = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
            protocol=mqtt.MQTTv5,
            transport=mqtt_config.transport,
            client_id=self.client_id,
        )
        self.client.keepalive = 5
        if mqtt_config.use_tls:
            self.client.tls_set()

        self._is_connected_event = asyncio.Event()
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task[None]] = None

        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect  # type: ignore[assignment]

        # Start the loop once during initialization
        self.client.loop_start()

        logger.info(f'SDK Client ID is "{self.client_id}"')

    async def connect(self) -> None:
        if self._shutdown:
            logger.info("Shutdown requested, skipping connection attempt.")
            return
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._connection_monitor())
            try:
                await asyncio.wait_for(self._is_connected_event.wait(), timeout=None)
                logger.info("Initial connection established")
            except asyncio.TimeoutError:
                logger.warning("Initial connection timed out after 30s, but monitor continues in background")

    async def disconnect(self) -> None:
        logger.info("Disconnecting from MQTT broker...")
        self._shutdown = True
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if isinstance(self.auth_strategy, OidcMqttAuthStrategy):
            await self.auth_strategy.auth_service.stop_refresh_task()
        if self.client is not None:
            self.client.disconnect()
            self.client.loop_stop()
            self._is_connected_event.clear()

    async def send_message(self, message: StellaNowEventWrapper) -> None:
        if not self.is_connected() or self.client is None:
            logger.warning(
                f"Cannot send message {message.message_id}: MQTT sink is disconnected. Awaiting reconnection..."
            )
            raise Exception("MQTT sink is disconnected; connection monitor is attempting to reconnect.")
        mqtt_topic = f"in/{self.project_info.organization_id}"
        result = self.client.publish(mqtt_topic, message.model_dump_json(by_alias=True), qos=self.default_qos)
        logger.debug(f"Publish result: {result.rc}, MID: {result.mid}")
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to send message {message.message_id}. Status: {result.rc}")
            raise Exception(f"Publish failed with status: {result.rc}")
        logger.debug(f"Message sent to with messageId: {message.message_id}")

    def is_connected(self) -> bool:
        if not self._is_connected_event.is_set():
            return False
        # Ensure the client is still functional
        return self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS

    def on_connect(
        self,
        client: mqtt.Client,  # noqa
        userdata: Any,  # noqa
        flags: Dict[str, Any],  # noqa
        reason_code: mqtt.ReasonCode,  # type: ignore # noqa
        properties: Optional[mqtt.Properties],  # type: ignore # noqa
    ) -> None:
        if reason_code == 0:
            logger.info("Connected to MQTT broker")
            self._is_connected_event.set()
        else:
            logger.error(f"Connection failed with code {reason_code}")
            self._is_connected_event.clear()

    def on_publish(  # noqa
        self,
        client: mqtt.Client,  # noqa
        userdata: Any,  # noqa
        mid: int,
        reason_code: mqtt.ReasonCode,  # type: ignore # noqa
        properties: Optional[mqtt.Properties],  # type: ignore # noqa
    ) -> None:
        logger.success(f"Message published with MID: {mid}")

    def on_disconnect(
        self,
        client: mqtt.Client,  # noqa
        userdata: Any,  # noqa
        flags: Dict[str, int],  # noqa
        rc: int,
        properties: Optional[Any] = None,  # noqa
    ) -> None:
        reason_str = mqtt.error_string(rc)
        logger.warning(f"Disconnected from MQTT broker with reason code {rc}: {reason_str}")
        self._is_connected_event.clear()

    async def _connection_monitor(self) -> None:
        logger.info("Started connection monitor")
        attempt = 1
        while True:
            is_connected = self.is_connected()
            if not is_connected:
                mqtt_config = self.env_config.mqtt_url_config
                logger.info(f"Attempting connection (Attempt {attempt}) to {mqtt_config.hostname}:{mqtt_config.port}")

                logger.debug("Initializing fresh MQTT client")
                if hasattr(self, "client") and self.client is not None:
                    try:
                        self.client.loop_stop()
                    except Exception as e:
                        logger.debug(f"Error stopping previous client: {e}")
                    self.client = None

                self.client: Optional[mqtt.Client] = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
                    protocol=mqtt.MQTTv5,
                    transport=mqtt_config.transport,
                    client_id=self.client_id,
                )
                if mqtt_config.use_tls:
                    self.client.tls_set()
                self.client.on_connect = self.on_connect
                self.client.on_publish = self.on_publish
                self.client.on_disconnect = self.on_disconnect  # type: ignore[assignment]

                # Authenticate and connect
                try:
                    await self.auth_strategy.authenticate(self.client)
                    self.client.connect_async(mqtt_config.hostname, mqtt_config.port, keepalive=5)
                    self.client.loop_start()
                    await asyncio.wait_for(self._is_connected_event.wait(), timeout=5.0)
                    logger.info("Successfully connected to MQTT broker")
                except Exception as e:
                    logger.error(f"Connection attempt {attempt} failed: {e}", exc_info=True)
                    try:
                        self.client.loop_stop()
                    except Exception as stop_e:
                        logger.debug(f"Error stopping loop: {stop_e}")
                    self.client = None
                    attempt += 1
                    retry_delay = min(attempt * 10, 60)
                    logger.info(f"Retrying connection in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            await asyncio.sleep(2.5)
