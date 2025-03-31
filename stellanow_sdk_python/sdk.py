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

import time
from typing import Optional

from loguru import logger

from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.message_queue.message_queue import StellaNowMessageQueue
from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.messages.message import StellaNowMessageBase, StellaNowMessageWrapper
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink


class StellaNowSDK:
    def __init__(self, project_info: StellaProjectInfo, sink: IStellaNowSink, queue_strategy: IMessageQueueStrategy):
        """Initialize the SDK with project info, sink, and queue strategy."""
        self.__project_info = project_info
        self.__sink = sink
        self.__message_queue = StellaNowMessageQueue(strategy=queue_strategy, sink=sink)

        self.__started = False

    async def start(self) -> None:
        """
        Starts the SDK and connects to the sink.
        """
        await self.__sink.connect()  # Blocks until connected
        self.__message_queue.start_processing()
        self.__started = True

        logger.info("SDK started successfully")

    async def send_message(self, message: StellaNowMessageBase | StellaNowMessageWrapper) -> None:
        """
        Sends a message through the sink.
        :param message: The message to send, either as a StellaNowMessageBase or StellaNowMessageWrapper.
        """
        if isinstance(message, StellaNowMessageBase):
            # If the message is a StellaNowMessageBase, wrap it and call send_message recursively
            wrapped_message = StellaNowMessageWrapper.create(message=message)
            await self.send_message(wrapped_message)
        elif isinstance(message, StellaNowMessageWrapper):
            # If the message is already a StellaNowMessageWrapper, enqueue it
            self.__message_queue.enqueue(
                StellaNowEventWrapper.create(
                    message=message,
                    organization_id=self.__project_info.organization_id,
                    project_id=self.__project_info.project_id,
                )
            )
        else:
            raise ValueError(f"Expected StellaNowMessageBase or StellaNowMessageWrapper, got {type(message)}")

    def wait_for_queue_to_empty(self, timeout: Optional[float] = None) -> bool:
        """
        Waits for the message queue to be empty before proceeding.
        :param timeout: Maximum time to wait (in seconds). If None, waits indefinitely.
        :return: True if the queue is empty, False if timeout is reached and queue is not empty.
        """
        start_time = time.time()
        while not self.__message_queue.is_empty():
            if timeout is not None and (time.time() - start_time) > timeout:
                logger.warning("Timeout reached while waiting for the message queue to empty.")
                return False
            time.sleep(0.1)
        logger.info("Message queue is empty.")
        return True

    async def stop(self) -> None:
        """Stops the SDK after ensuring the message queue is empty."""
        self.wait_for_queue_to_empty(timeout=10)
        await self.__message_queue.stop_processing(timeout=5.0)
        await self.__sink.disconnect()
        logger.info("SDK stopped successfully")
