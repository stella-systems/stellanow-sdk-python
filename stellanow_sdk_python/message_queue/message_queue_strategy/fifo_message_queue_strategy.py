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

from stellanow_sdk_python.message_queue.message_queue_strategy.i_message_queue_strategy import IMessageQueueStrategy
from stellanow_sdk_python.messages.event import StellaNowEventWrapper


class FifoMessageQueueStrategy(IMessageQueueStrategy):
    """
    A first-in, first-out (FIFO) message_queue strategy for storing messages.
    """

    def __init__(self) -> None:
        self._queue: Queue[StellaNowEventWrapper] = queue.Queue()
        self._lock = threading.Lock()

    def enqueue(self, message: StellaNowEventWrapper) -> None:
        with self._lock:
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
