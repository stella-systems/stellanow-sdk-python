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

import queue
import threading
from queue import Queue
from typing import Optional

from loguru import logger

from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.message_queue.message_queue_strategy.overflow_strategy import OverflowStrategy, QueueFullError
from stellanow_sdk_python.messages.event import StellaNowEventWrapper


class FifoMessageQueueStrategy(IMessageQueueStrategy):
    """
    A first-in, first-out (FIFO) message_queue strategy for storing messages.

    Args:
        max_size: Maximum number of messages in queue. Default is 100,000 (~300 MB for metadata-only messages).
                  Set to 0 for unlimited (not recommended).
        overflow_strategy: Strategy for handling queue overflow. Default is DROP_OLDEST (backward compatible).
                          - DROP_OLDEST: Drop oldest message when full (default)
                          - DROP_NEWEST: Reject new message when full
                          - RAISE_EXCEPTION: Raise QueueFullError for application to handle
    """

    def __init__(
        self, max_size: int = 100_000, overflow_strategy: OverflowStrategy = OverflowStrategy.DROP_OLDEST
    ) -> None:
        if max_size < 0:
            raise ValueError(f"max_size must be non-negative, got {max_size}")
        if max_size > 10_000_000:
            raise ValueError(f"max_size too large (max 10M), got {max_size}")

        self._queue: Queue[StellaNowEventWrapper] = queue.Queue()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._overflow_strategy = overflow_strategy
        self._dropped_count = 0  # Track how many messages were dropped

    def enqueue(self, message: StellaNowEventWrapper) -> None:
        with self._lock:
            # Check if queue is at max capacity (if max_size is set)
            if self._max_size > 0 and self._queue.qsize() >= self._max_size:
                if self._overflow_strategy == OverflowStrategy.RAISE_EXCEPTION:
                    # Raise exception - let application handle it
                    raise QueueFullError(self._queue.qsize(), self._dropped_count, message.message_id)

                elif self._overflow_strategy == OverflowStrategy.DROP_NEWEST:
                    # Reject new message, keep old ones
                    self._dropped_count += 1
                    logger.warning(
                        f"Queue at max capacity ({self._max_size}). "
                        f"Rejecting new message {message.message_id} (DROP_NEWEST strategy). "
                        f"Total rejected: {self._dropped_count}"
                    )
                    return  # Don't enqueue

                elif self._overflow_strategy == OverflowStrategy.DROP_OLDEST:
                    # Drop the oldest message (dequeue) to make room
                    try:
                        dropped_message = self._queue.get_nowait()
                        self._dropped_count += 1
                        logger.warning(
                            f"Queue at max capacity ({self._max_size}). "
                            f"Dropped oldest message {dropped_message.message_id}. "
                            f"Total dropped: {self._dropped_count}"
                        )
                    except queue.Empty:
                        pass  # Race condition, queue became empty

            self._queue.put(message)

    def try_dequeue(self) -> Optional[StellaNowEventWrapper]:
        with self._lock:
            if not self._queue.empty():
                return self._queue.get()
            return None

    def is_empty(self) -> bool:
        with self._lock:
            return self._queue.empty()

    def get_message_count(self) -> int:
        with self._lock:
            return self._queue.qsize()

    def get_dropped_count(self) -> int:
        """Get the total number of messages dropped due to queue being full."""
        with self._lock:
            return self._dropped_count
