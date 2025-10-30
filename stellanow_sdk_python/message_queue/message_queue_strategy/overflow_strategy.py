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

from enum import Enum


class OverflowStrategy(Enum):
    """Strategy for handling queue overflow when max_size is reached."""

    DROP_OLDEST = "drop_oldest"  # Drop oldest message, accept new (default behavior)
    DROP_NEWEST = "drop_newest"  # Reject new message, keep oldest
    RAISE_EXCEPTION = "raise_exception"  # Raise QueueFullError, let application decide


class QueueFullError(Exception):
    """Raised when queue is full and overflow strategy is RAISE_EXCEPTION."""

    def __init__(self, queue_size: int, dropped_count: int, message_id: str):
        self.queue_size = queue_size
        self.dropped_count = dropped_count
        self.message_id = message_id
        super().__init__(
            f"Message queue is full (size: {queue_size}, total dropped: {dropped_count}). "
            f"Cannot accept message {message_id}. Wait for queue to drain or increase max_size."
        )
