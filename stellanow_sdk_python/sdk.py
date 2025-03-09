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

import time
import uuid

from loguru import logger

from stellanow_sdk_python.message_queue.message_queue import StellaNowMessageQueue
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_messsage_queue_strategy import (
    FifoMessageQueueStrategy,
)
from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper
from stellanow_sdk_python.settings import ORGANIZATION_ID, PROJECT_ID
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink


class StellaNowSDK:
    def __init__(self, sink: IStellaNowSink, queue_strategy: IMessageQueueStrategy = None):
        self.queue_strategy = queue_strategy or FifoMessageQueueStrategy()
        self.message_queue = StellaNowMessageQueue(strategy=self.queue_strategy, sink=sink)
        self.sink = sink

    async def start(self):
        """
        Starts the SDK and connects to the sink.
        """
        await self.sink.connect()
        self.message_queue.start_processing()

    async def send_message(self, message):
        """
        Sends a message through the sink.
        :param message: The message to send.
        """
        wrapped_message = StellaNowMessageWrapper.create(
            message=message,
            organization_id=ORGANIZATION_ID,
            project_id=PROJECT_ID,
            event_id=str(uuid.uuid4()),
        )
        self.message_queue.enqueue(wrapped_message.model_dump_json())

    def wait_for_queue_to_empty(self, timeout: float = None):
        """
        Waits for the message message_queue to be empty before proceeding.
        :param timeout: Maximum time to wait (in seconds). If None, waits indefinitely.
        """
        start_time = time.time()
        while not self.message_queue.is_empty():
            if timeout and (time.time() - start_time) > timeout:
                logger.warning("Timeout reached while waiting for the message_queue to empty.")
                break
            time.sleep(0.1)
        logger.info("message_queue is empty.")

    async def stop(self):
        """
        Stops the SDK after ensuring the message queue is empty.
        """
        self.wait_for_queue_to_empty()
        await self.sink.disconnect()
        self.message_queue.stop_processing()
        logger.info("SDK stopped successfully.")
