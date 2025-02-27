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
import queue
import threading
import time

from loguru import logger


class StellaNowMessageQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.processing = False
        self.message_handler = None
        self.queue_thread = threading.Thread(target=self._process_queue)
        self.queue_thread.daemon = True

    def start_processing(self, message_handler):
        """
        Start processing the queue in a separate thread
        """
        self.message_handler = message_handler
        self.processing = True
        if not self.queue_thread.is_alive():
            self.queue_thread.start()
        logger.info("Message queue processing started...")

    def stop_processing(self):
        """
        Stop the queue processing
        """
        self.processing = False
        if self.queue_thread.is_alive():
            self.queue_thread.join()
        logger.info("Message queue processing stopped.")

    def enqueue(self, message):
        """
        Add a message to the queue
        """
        with self.lock:
            self.queue.put(message)
            logger.info(f"Message queued: {message}")

    def _process_queue(self):
        """
        Process the queue in a separate thread
        """
        while self.processing:
            try:
                if not self.queue.empty():
                    message = self.queue.get()
                    if self.message_handler:
                        asyncio.run(self.message_handler(message))
                    self.queue.task_done()
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

    def is_empty(self):
        """
        Check if the queue is empty
        """
        return self.queue.empty()

    def get_message_count(self):
        """
        Get the number of messages in the queue
        """
        return self.queue.qsize()
