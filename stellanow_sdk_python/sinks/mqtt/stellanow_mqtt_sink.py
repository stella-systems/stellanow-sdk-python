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

from stellanow_sdk_python.authentication.exceptions import AuthenticationError
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink
from stellanow_sdk_python.sinks.mqtt.auth_strategy.i_mqtt_auth_strategy import IMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.exceptions import MqttPublishError, MqttSinkDisconnectedError


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

        self._is_connected_event = asyncio.Event()
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task[None]] = None
        self._client_lock = asyncio.Lock()  # Protects concurrent access to self.client

        self.client: Optional[mqtt.Client] = self._create_mqtt_client()

        if isinstance(self.auth_strategy, OidcMqttAuthStrategy):
            self.auth_strategy.set_client_lock(self._client_lock)

        self.client.loop_start()

        logger.info(f'SDK Client ID is "{self.client_id}"')

    def _create_mqtt_client(self) -> mqtt.Client:
        """
        Create and configure a new MQTT client instance.

        Returns:
            mqtt.Client: Configured MQTT client ready for connection
        """
        mqtt_config = self.env_config.mqtt_url_config

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
            protocol=mqtt.MQTTv5,
            transport=mqtt_config.transport,
            client_id=self.client_id,
        )
        client.keepalive = 5

        if mqtt_config.use_tls:
            client.tls_set()

        client.on_connect = self.on_connect
        client.on_publish = self.on_publish
        client.on_disconnect = self.on_disconnect  # type: ignore[assignment]

        return client

    async def connect(self) -> None:
        if self._shutdown:
            logger.info("Shutdown requested, skipping connection attempt.")
            return

        async with self._client_lock:
            if not self._monitor_task:
                self._monitor_task = asyncio.create_task(self._connection_monitor())

        # Wait for either connection or monitor task failure
        # If monitor task fails (e.g., permanent auth error), propagate the exception
        connection_wait = asyncio.create_task(self._is_connected_event.wait())
        done, pending = await asyncio.wait([connection_wait, self._monitor_task], return_when=asyncio.FIRST_COMPLETED)

        # If monitor task completed, check if it failed
        if self._monitor_task in done:
            # Monitor task finished - check for exception
            try:
                self._monitor_task.result()
            except Exception as e:
                logger.error(f"Connection monitor failed with permanent error: {e}")
                connection_wait.cancel()  # Cancel the wait task
                raise

        # If connection succeeded
        if connection_wait in done:
            logger.info("Initial connection established")
            return

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
        async with self._client_lock:
            if self.client is not None:
                self.client.disconnect()
                self.client.loop_stop()
                self._is_connected_event.clear()

    async def send_message(self, message: StellaNowEventWrapper) -> None:
        async with self._client_lock:
            if not self.is_connected() or self.client is None:
                logger.warning(
                    f"Cannot send message {message.message_id}: MQTT sink is disconnected. Awaiting reconnection..."
                )
                raise MqttSinkDisconnectedError(
                    "MQTT sink is disconnected; connection monitor is attempting to reconnect."
                )
            if not self.project_info.organization_id:
                raise ValueError("Organization ID is empty")

            mqtt_topic = f"in/{self.project_info.organization_id}"
            if len(mqtt_topic) > 65535:  # MQTT topic length limit
                raise ValueError(f"MQTT topic too long: {len(mqtt_topic)} bytes (max 65535)")

            payload_json = message.model_dump_json(by_alias=True)
            payload_size = len(payload_json.encode("utf-8"))
            if payload_size > 268_435_455:  # MQTT v5 max payload size
                raise ValueError(
                    f"Message payload too large: {payload_size} bytes (max 268,435,455). "
                    f"Message ID: {message.message_id}"
                )

            if self.default_qos not in [0, 1, 2]:
                raise ValueError(f"Invalid QoS level: {self.default_qos} (must be 0, 1, or 2)")

            result = self.client.publish(mqtt_topic, payload_json, qos=self.default_qos)
            logger.debug(f"Publish result: {result.rc}, MID: {result.mid}")
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to send message {message.message_id}. Status: {result.rc}")
                raise MqttPublishError(f"Publish failed with status: {result.rc}")
            logger.debug(f"Message sent to with messageId: {message.message_id}")

    def is_connected(self) -> bool:
        if not self._is_connected_event.is_set():
            return False
        if self.client is None:
            return False
        try:
            return self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS
        except (AttributeError, RuntimeError):
            return False

    def on_connect(
        self,
        client: mqtt.Client,  # noqa
        userdata: Any,  # noqa
        flags: Dict[str, Any],  # noqa
        reason_code: mqtt.ReasonCode,  # type: ignore # noqa
        properties: Optional[mqtt.Properties],  # type: ignore # noqa
    ) -> None:
        """
        MQTT callback invoked when the client successfully connects to the broker.

        This callback is automatically called by the Paho MQTT client when a
        connection is established. It sets the internal connection event flag
        to signal that the sink is ready to send messages.

        Args:
            client: The MQTT client instance that triggered the callback
            userdata: User data of any type (unused)
            flags: Connection response flags from the broker
            reason_code: Connection result code (0 indicates success)
            properties: MQTT v5 properties (optional)

        Note:
            A reason_code of 0 indicates successful connection. Any other value
            indicates a connection failure.
        """
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
        """
        MQTT callback invoked when a message is successfully published to the broker.

        This callback is automatically called by the Paho MQTT client after a
        message publish operation completes. It's used for logging and tracking
        message delivery confirmation.

        Args:
            client: The MQTT client instance that triggered the callback
            userdata: User data of any type (unused)
            mid: Message ID assigned to the published message
            reason_code: Publish result code
            properties: MQTT v5 properties (optional)

        Note:
            This callback is triggered for QoS 1 messages after the broker
            acknowledges receipt.
        """
        logger.success(f"Message published with MID: {mid}")

    def on_disconnect(
        self,
        client: mqtt.Client,  # noqa
        userdata: Any,  # noqa
        flags: Dict[str, int],  # noqa
        rc: int,
        properties: Optional[Any] = None,  # noqa
    ) -> None:
        """
        MQTT callback invoked when the client disconnects from the broker.

        This callback is automatically called by the Paho MQTT client when the
        connection to the broker is lost. It clears the internal connection event
        flag, signaling the message queue to pause processing until reconnection.

        Args:
            client: The MQTT client instance that triggered the callback
            userdata: User data of any type (unused)
            flags: Disconnection flags
            rc: Disconnection reason code (0 = clean disconnect)
            properties: MQTT v5 properties (optional)

        Note:
            The _connection_monitor() background task will automatically attempt
            to reconnect after a disconnection is detected.
        """
        reason_str = mqtt.error_string(rc)
        logger.warning(f"Disconnected from MQTT broker with reason code {rc}: {reason_str}")
        self._is_connected_event.clear()

    async def _connection_monitor(self) -> None:
        """
        Background task that monitors MQTT connection status and attempts reconnection.

        This method runs continuously in the background, checking the connection status
        every 2.5 seconds. If disconnected, it will:
        1. Stop and clean up the old client
        2. Create a new MQTT client
        3. Authenticate with the configured strategy
        4. Attempt to connect with exponential backoff on failure

        The reconnection attempts have exponential backoff with a maximum delay of 60 seconds.
        """
        logger.info("Started connection monitor")
        attempt = 1
        while True:
            is_connected = self.is_connected()
            if not is_connected:
                mqtt_config = self.env_config.mqtt_url_config
                logger.info(f"Attempting connection (Attempt {attempt}) to {mqtt_config.hostname}:{mqtt_config.port}")

                # Acquire lock to safely recreate client
                async with self._client_lock:
                    logger.debug("Initializing fresh MQTT client")
                    if hasattr(self, "client") and self.client is not None:
                        try:
                            self.client.loop_stop()
                        except (RuntimeError, OSError) as e:
                            logger.warning(f"Error stopping previous client: {e}")
                        self.client = None

                    self.client = self._create_mqtt_client()

                    try:
                        await self.auth_strategy.authenticate(self.client)
                        self.client.connect_async(mqtt_config.hostname, mqtt_config.port, keepalive=5)
                        self.client.loop_start()
                        await asyncio.wait_for(self._is_connected_event.wait(), timeout=5.0)
                        logger.info("Successfully connected to MQTT broker")
                        attempt = 1  # Reset attempt counter on success
                    except AuthenticationError as e:
                        # Permanent authentication error - stop retrying
                        logger.critical(
                            f"Permanent authentication error: {e}. "
                            "SDK cannot connect due to invalid credentials or account issues. "
                            "Connection monitor is stopping. Please fix credentials and restart SDK."
                        )
                        try:
                            self.client.loop_stop()
                        except (RuntimeError, OSError) as stop_e:
                            logger.warning(f"Error stopping loop: {stop_e}")
                        self.client = None
                        self._shutdown = True  # Stop connection monitor
                        raise  # Re-raise to propagate error to SDK
                    except (ConnectionError, RuntimeError, OSError, asyncio.TimeoutError, ValueError) as e:
                        logger.error(f"Connection attempt {attempt} failed: {e}", exc_info=True)
                        try:
                            self.client.loop_stop()
                        except (RuntimeError, OSError) as stop_e:
                            logger.warning(f"Error stopping loop: {stop_e}")
                        self.client = None
                        attempt += 1
                        retry_delay = min(attempt * 10, 60)
                        logger.info(f"Retrying connection in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
            await asyncio.sleep(2.5)
