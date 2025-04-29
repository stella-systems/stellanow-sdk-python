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
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink


class StellaNowMessageQueue:
    def __init__(self, strategy: IMessageQueueStrategy, sink: IStellaNowSink):
        """Initialize the message queue with a strategy and sink."""
        self.strategy = strategy
        self.sink = sink
        self.processing = False
        self._task: Optional[asyncio.Task[None]] = None

    def start_processing(self) -> None:
        """Start processing the queue as an asyncio task."""
        if not self.processing:
            self.processing = True
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._process_queue())
            logger.info("Message queue processing started as asyncio task...")

    async def stop_processing(self, timeout: float = 5.0) -> None:
        """
        Stop the queue processing with an optional timeout.
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

    def enqueue(self, message: StellaNowEventWrapper) -> None:
        """Add a message to the queue."""
        self.strategy.enqueue(message)
        logger.info(f"Message queued with messageId: {message.message_id}, Queue size: {self.get_message_count()}")

    async def _process_queue(self) -> None:
        """Process the queue asynchronously with connection handling."""
        logger.info(f"Starting queue processing with initial queue size: {self.get_message_count()}")
        while self.processing:
            if not self.sink.is_connected():
                logger.warning("Sink is disconnected, pausing queue processing...")
                await self._wait_for_connection()
                logger.info(f"Sink reconnected, resuming queue processing with queue size: {self.get_message_count()}")
            elif not self.strategy.is_empty():
                message = self.strategy.try_dequeue()
                if message:
                    logger.debug(f"Dequeued message {message.message_id}, Queue size: {self.get_message_count()}")
                    await self._send_message_to_sink(message)
            else:
                await asyncio.sleep(0.1)

    async def _send_message_to_sink(self, message: StellaNowEventWrapper) -> None:
        """Send a message to the sink with retry on failure."""
        try:
            await self.sink.send_message(message)
            logger.success(f"Message sent successfully with messageId: {message.message_id}")
        except Exception as e:
            logger.error(f"Failed to send message {message.message_id}: {e}")
            self.strategy.enqueue(message)
            logger.warning(f"Message {message.message_id} re-queued, Queue size: {self.get_message_count()}")
            await asyncio.sleep(1)

    async def _wait_for_connection(self) -> None:
        """Wait for the sink to reconnect."""
        while self.processing and not self.sink.is_connected():
            logger.debug("Waiting for sink to reconnect...")
            await asyncio.sleep(0.5)

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self.strategy.is_empty()

    def get_message_count(self) -> int:
        """Get the number of messages in the queue."""
        return self.strategy.get_message_count()
