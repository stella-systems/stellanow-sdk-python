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
MQTT sink, with support for secure authentication using Username and Password.

Key Features:
- Asynchronous event sending for non-blocking performance.
- Configurable message queue strategies (e.g., FIFO).
- MQTT-based sink with automatic reconnection and Username/Password authentication.
- Graceful shutdown handling for clean exits.

This demo sends two `UserDetailsMessage` events, simulating real-time user data collection, and showcases the SDK's
lifecycle: initialization, event sending, and shutdown.
"""

import asyncio
import sys

from loguru import logger

from stellanow_sdk_python.configure_sdk import configure_dev_oidc_mqtt_fifo_sdk
from stellanow_sdk_python_demo.messages.models.phone_number_model import PhoneNumberModel
from stellanow_sdk_python_demo.messages.user_details_update_message import UserDetailsUpdateMessage


async def main():
    """Main entry point for the StellaNow SDK demo."""
    # sdk = configure_local_nanomq_username_password_mqtt_lifo_sdk()
    sdk = configure_dev_oidc_mqtt_fifo_sdk()
    # sdk = configure_dev_username_password_mqtt_lifo_sdk()
    shutdown_event = asyncio.Event()  # Event to signal shutdown

    try:
        await sdk.start()
        for i in range(10):
            message = UserDetailsUpdateMessage(
                patron="12345", user_id=f"user_{i}", phone_number=PhoneNumberModel(country_code=44, number=753594 + i)
            )
            logger.info(f"Sending message {i + 1}...")
            await sdk.send_message(message)
            await asyncio.sleep(2)
        logger.info("Initial messages sent. Keeping SDK alive...")
        await shutdown_event.wait()  # Wait indefinitely until shutdown

    except KeyboardInterrupt:
        logger.warning("Received Ctrl+C, shutting down gracefully...")
        shutdown_event.set()  # Signal shutdown
        await sdk.stop()
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        await sdk.stop()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as e:
        logger.error(f"Failed to start demo due to configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Program interrupted by user, exiting cleanly.")
    except Exception as e:
        logger.exception(f"Program terminated with unexpected error: {e}")
        sys.exit(1)
