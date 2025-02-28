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

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.message_queue.message_queue import StellaNowMessageQueue
from stellanow_sdk_python.settings import MQTT_BROKER_PORT, MQTT_BROKER_URL, MQTT_CLIENT_ID, MQTT_KEEP_ALIVE, MQTT_TOPIC


class StellaNowMQTTClient:
    def __init__(self):
        self.auth_service = StellaNowAuthenticationService()
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # noqa
            transport="websockets",
            protocol=mqtt.MQTTv5,
            client_id=MQTT_CLIENT_ID,  # noqa
        )
        self.is_connected = asyncio.Event()
        self.reconnect_attempts = 0

        # Initialize the Message Queue
        self.message_queue = StellaNowMessageQueue()

    async def connect(self):
        """
        Asynchronously connect to the MQTT broker
        """
        try:
            access_token = await self.auth_service.get_access_token()
            self.client.username_pw_set(access_token, password=None)
            self.client.tls_set()

            # Assign all necessary callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish

            logger.info("Connecting to MQTT broker...")
            self.client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE)
            self.client.loop_start()

            # Start processing the message queue
            self.message_queue.start_processing(self._process_message)

            # Wait until connected
            await self.wait_for_connection()

        except Exception as e:
            logger.error(f"Unexpected error during MQTT connection: {e}")
            await self.handle_connection_error(e)

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

    def on_publish(self, client, userdata, mid, reason_code, properties):  # noqa
        """
        Callback when a message has been published
        """
        logger.success(f"Message published successfully with mid: {mid}")

    async def wait_for_connection(self):
        """
        Wait until the client is connected
        """
        while not self.is_connected.is_set():
            await asyncio.sleep(0.5)

    async def publish_message(self, message):
        """
        Queue the message for publishing
        """
        logger.info(f"Queueing message: {message}")
        self.message_queue.enqueue(message)

    async def _process_message(self, message):
        """
        Process and publish a message from the queue
        """
        await self.wait_for_connection()
        result = self.client.publish(MQTT_TOPIC, message)
        status = result.rc

        if status == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Message sent: {message}")
        else:
            logger.error(f"Failed to send message. Status: {status}")

    async def handle_connection_error(self, error):
        """
        Handle connection errors with retry logic
        """
        logger.error(f"Handling connection error: {error}")
        backoff = min(2**self.reconnect_attempts, 60)
        self.reconnect_attempts += 1

        logger.info(f"Retrying connection in {backoff} seconds...")
        await asyncio.sleep(backoff)
        await self.connect()

    async def handle_publish_error(self, error):
        """
        Handle publish errors and retry
        """
        logger.error(f"Handling publish error: {error}")
        await self.wait_for_connection()
        logger.info("Retrying message publish...")

    def stop(self):
        """
        Stop the MQTT client and message queue
        """
        self.message_queue.stop_processing()
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT client stopped.")
