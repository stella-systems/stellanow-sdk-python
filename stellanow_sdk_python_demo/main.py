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
---

StellaNow SDK Python Demo
=========================

This script demonstrates the usage of the StellaNow SDK for Python, a powerful tool for real-time analytics.
The SDK enables developers to send event data (e.g., user details) to a StellaNow backend via a message queue and
MQTT sink, with support for secure authentication using OpenID Connect (OIDC).

Key Features:
- Asynchronous event sending for non-blocking performance.
- Configurable message queue strategies (e.g., FIFO).
- MQTT-based sink with automatic reconnection and OIDC authentication.
- Graceful shutdown handling for clean exits.

This demo sends two `UserDetailsMessage` events, simulating real-time user data collection, and showcases the SDK's
lifecycle: initialization, event sending, and shutdown.
"""
import asyncio
import uuid

import sys
from loguru import logger
from stellanow_sdk_python.sinks.mqtt.auth_strategy.oidc_mqtt_auth_strategy import OidcMqttAuthStrategy
from stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink import StellaNowMqttSink
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_messsage_queue_strategy import FifoMessageQueueStrategy

from models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python.sdk import StellaNowSDK
from user_details_message import UserDetailsMessage


async def main():
    """
        Main entry point for the StellaNow SDK demo.

        This function initializes the SDK with an MQTT sink and FIFO queue, sends sample user detail messages,
        and ensures graceful shutdown on interruption or error.

        Steps:
        1. Configure logging with loguru for INFO-level output.
        2. Set up the SDK with an MQTT sink (using OIDC auth) and FIFO message queue.
        3. Start the SDK, connecting to the MQTT broker.
        4. Send two sample `UserDetailsMessage` events.
        5. Simulate work with a 5-second delay.
        6. Handle interruptions (Ctrl+C) or errors, ensuring clean shutdown.
    def __init__(self, sink: IStellaNowSink, queue_strategy: IMessageQueueStrategy):
        self.queue_strategy = queue_strategy
        self.message_queue = StellaNowMessageQueue(strategy=self.queue_strategy, sink=sink)
        self.sink = sink
"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    # Initialize SDK components
    queue_strategy = FifoMessageQueueStrategy()  # First-in, first-out queue for ordered message processing
    auth_strategy = OidcMqttAuthStrategy()  # OIDC-based authentication for secure MQTT communication
    mqtt_sink = StellaNowMqttSink(auth_strategy=auth_strategy)  # MQTT sink for sending messages to the broker

    # Create the SDK instance
    sdk = StellaNowSDK(sink=mqtt_sink, queue_strategy=queue_strategy)
    logger.info("SDK initialized with MQTT sink and FIFO queue strategy.")

    try:
        # Start the SDK, establishing the MQTT connection and queue processing
        await sdk.start()
        logger.info("SDK started successfully.")

        # Create sample messages representing user details
        message = UserDetailsMessage(
            patronEntityId="12345",
            user_id="user_67890",
            phone_number=PhoneNumberModel(country_code=44, number=753594)
        )
        message2 = UserDetailsMessage(
            patronEntityId="12345",
            user_id="user_98888",
            phone_number=PhoneNumberModel(country_code=48, number=700000)
        )

        # Send messages asynchronously to the StellaNow backend
        logger.info("Sending user detail messages...")
        await sdk.send_message(message)
        await sdk.send_message(message2)
        logger.info("Messages enqueued for processing.")

        # Simulate ongoing work (e.g., waiting for more events)
        await asyncio.sleep(5)
        logger.info("Simulation complete, preparing to shut down.")

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger.warning("Received Ctrl+C, shutting down gracefully...")
        await sdk.stop()
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error occurred: {e}")
        await sdk.stop()
    finally:
        # Ensure the SDK shuts down cleanly, even on failure
        await sdk.stop()
        logger.info("Demo completed.")


if __name__ == "__main__":
    """
    Program entry point. Runs the demo within an asyncio event loop and handles top-level exceptions.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user, exiting cleanly.")
    except Exception as e:
        logger.error(f"Program terminated with unexpected error: {e}")
