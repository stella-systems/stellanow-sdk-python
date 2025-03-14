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
from typing import Optional

from loguru import logger

from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink


class StellaNowMessageQueue:
    def __init__(self, strategy: IMessageQueueStrategy, sink: IStellaNowSink):
        """Initialize the message queue with a strategy and sink."""
        self.strategy = strategy
        self.sink = sink
        self.processing = False
        self._task: Optional[asyncio.Task] = None  # Store the asyncio task

    def start_processing(self):
        """Start processing the queue as an asyncio task."""
        if not self.processing:
            self.processing = True
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._process_queue())
            logger.info("Message queue processing started as asyncio task...")

    async def stop_processing(self, timeout: float = 5.0):
        """
        Stop the queue processing with an optional timeout.

        Args:
            timeout (float): Maximum time in seconds to wait for shutdown. Defaults to 5.0.
        """
        if self.processing:
            self.processing = False
            if self._task:
                try:
                    await asyncio.wait_for(self._task, timeout=timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"Queue processing did not stop within {timeout} seconds, forcing shutdown.")
                    self._task.cancel()
                    try:
                        await self._task
                    except asyncio.CancelledError:
                        pass
                finally:
                    self._task = None
            logger.info("Message queue processing stopped.")

    def enqueue(self, message: StellaNowMessageWrapper):
        """Add a message to the queue."""
        self.strategy.enqueue(message)
        logger.info(f"Message queued with messageId:{message.message_id}")
        logger.debug(f"Message queued: {message}")

    async def _process_queue(self):
        """Process the queue asynchronously using the existing event loop."""
        while self.processing or not self.strategy.is_empty():
            try:
                message = self.strategy.try_dequeue()
                if message:
                    await self._send_message_to_sink(message)
                else:
                    await asyncio.sleep(0.1)  # Brief pause to avoid tight loop
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
                await asyncio.sleep(1)  # Back off on error

    async def _send_message_to_sink(self, message: StellaNowMessageWrapper):
        """Send a message to the sink."""
        try:
            await self.sink.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send message to sink: {e}")

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self.strategy.is_empty()

    def get_message_count(self) -> int:
        """Get the number of messages in the queue."""
        return self.strategy.get_message_count()
