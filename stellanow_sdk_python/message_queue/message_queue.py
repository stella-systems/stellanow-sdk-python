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
import threading

from loguru import logger

from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink


class StellaNowMessageQueue:
    def __init__(self, strategy: IMessageQueueStrategy, sink: IStellaNowSink):
        self.strategy = strategy
        self.sink = sink
        self.processing = False
        self.queue_thread = threading.Thread(target=self._process_queue)
        self.queue_thread.daemon = True

    def start_processing(self):
        """
        Start processing the queue in a separate thread.
        """
        self.processing = True
        if not self.queue_thread.is_alive():
            self.queue_thread.start()
        logger.info("Message queue processing started...")

    def stop_processing(self):
        """
        Stop the queue processing.
        """
        self.processing = False
        if self.queue_thread.is_alive():
            self.queue_thread.join()
        logger.info("Message queue processing stopped.")

    def enqueue(self, message: str):
        """
        Add a message to the queue.
        """
        self.strategy.enqueue(message)
        logger.info(f"Message queued: {message}")

    def _process_queue(self):
        """
        Process the queue in a separate thread.
        """
        while self.processing or not self.strategy.is_empty():
            try:
                message = self.strategy.try_dequeue()
                if message:
                    asyncio.run(self._send_message_to_sink(message))
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

    async def _send_message_to_sink(self, message: str):
        """
        Send a message to the sink.
        """
        try:
            await self.sink.send_message(message)
            logger.info(f"Message sent to sink: {message}")
        except Exception as e:
            logger.error(f"Failed to send message to sink: {e}")

    def is_empty(self) -> bool:
        """
        Check if the queue is empty.
        """
        return self.strategy.is_empty()

    def get_message_count(self) -> int:
        """
        Get the number of messages in the queue.
        """
        return self.strategy.get_message_count()
