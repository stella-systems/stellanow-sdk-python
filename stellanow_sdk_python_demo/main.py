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
import sys

from loguru import logger

from stellanow_sdk_python.configure_sdk import configure_dev_username_password_mqtt_lifo_sdk
from models.phone_number_model import PhoneNumberModel
from user_details_message import UserDetailsMessage

from stellanow_sdk_python.configure_sdk import configure_dev_oidc_mqtt_fifo_sdk


async def main():
    """Main entry point for the StellaNow SDK demo."""
    # Use pre-defined dev config with OIDC, MQTT, and FIFO
    # sdk = configure_dev_oidc_mqtt_fifo_sdk()
    sdk = configure_dev_username_password_mqtt_lifo_sdk()
    try:
        # Start the SDK
        await sdk.start()
        logger.info("SDK started successfully.")

        # Create and send sample messages
        message = UserDetailsMessage(
            patronEntityId="12345", user_id="user_67890", phone_number=PhoneNumberModel(country_code=44, number=753594)
        )
        message2 = UserDetailsMessage(
            patronEntityId="12345", user_id="user_98888", phone_number=PhoneNumberModel(country_code=48, number=700000)
        )
        logger.info("Sending user detail messages...")
        await sdk.send_message(message)
        await sdk.send_message(message2)
        logger.info("Messages enqueued for processing.")

        # Simulate ongoing work
        await asyncio.sleep(5)
        logger.info("Simulation complete, preparing to shut down.")

    except KeyboardInterrupt:
        logger.warning("Received Ctrl+C, shutting down gracefully...")
        await sdk.stop()
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        await sdk.stop()
    finally:
        await sdk.stop()
        logger.info("Demo completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as e:
        logger.error(f"Failed to start demo due to configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Program interrupted by user, exiting cleanly.")
    except Exception as e:
        logger.error(f"Program terminated with unexpected error: {e}")
        sys.exit(1)
