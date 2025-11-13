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

import threading
from abc import abstractmethod
from collections import deque

from loguru import logger

from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.message_queue.message_queue_strategy.overflow_strategy import OverflowStrategy, QueueFullError
from stellanow_sdk_python.messages.event import StellaNowEventWrapper


class BaseDequeStrategy(IMessageQueueStrategy):
    """
    Base class for deque-based queue strategies with common overflow handling.

    Subclasses must implement _drop_oldest() to define how the oldest message is removed.
    """

    def __init__(
        self, max_size: int = 100_000, overflow_strategy: OverflowStrategy = OverflowStrategy.DROP_OLDEST
    ) -> None:
        if max_size < 0:
            raise ValueError(f"max_size must be non-negative, got {max_size}")
        if max_size > 10_000_000:
            raise ValueError(f"max_size too large (max 10M), got {max_size}")

        self._queue: deque[StellaNowEventWrapper] = deque()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._overflow_strategy = overflow_strategy
        self._dropped_count = 0

    @abstractmethod
    def _drop_oldest(self) -> StellaNowEventWrapper:
        """
        Remove and return the oldest message from the queue.
        Must be implemented by subclasses to define FIFO/LIFO behavior.
        """

    def _handle_overflow(self, message: StellaNowEventWrapper) -> bool:
        """
        Handle queue overflow according to the configured strategy.

        Returns:
            True if message should be enqueued, False if it should be rejected.

        Raises:
            QueueFullError: If overflow_strategy is RAISE_EXCEPTION.
        """
        if self._max_size > 0 and len(self._queue) >= self._max_size:
            match self._overflow_strategy:
                case OverflowStrategy.RAISE_EXCEPTION:
                    raise QueueFullError(len(self._queue), self._dropped_count, message.message_id)

                case OverflowStrategy.DROP_NEWEST:
                    self._dropped_count += 1
                    logger.warning(
                        f"Queue at max capacity ({self._max_size}). "
                        f"Rejecting new message {message.message_id} (DROP_NEWEST strategy). "
                        f"Total rejected: {self._dropped_count}"
                    )
                    return False  # Don't enqueue

                case OverflowStrategy.DROP_OLDEST:
                    dropped_message = self._drop_oldest()
                    self._dropped_count += 1
                    logger.warning(
                        f"Queue at max capacity ({self._max_size}). "
                        f"Dropped oldest message {dropped_message.message_id}. "
                        f"Total dropped: {self._dropped_count}"
                    )

        return True  # Enqueue the message

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0

    def get_message_count(self) -> int:
        with self._lock:
            return len(self._queue)

    def get_dropped_count(self) -> int:
        """Get the total number of messages dropped due to queue being full."""
        with self._lock:
            return self._dropped_count
