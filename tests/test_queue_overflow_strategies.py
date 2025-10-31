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

from uuid import UUID

import pytest

from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_message_queue_strategy import (
    FifoMessageQueueStrategy,
)
from stellanow_sdk_python.message_queue.message_queue_strategy.lifo_message_queue_strategy import (
    LifoMessageQueueStrategy,
)
from stellanow_sdk_python.message_queue.message_queue_strategy.overflow_strategy import OverflowStrategy, QueueFullError
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase, StellaNowMessageWrapper


class SampleMessage(StellaNowMessageBase):
    """Simple test message class."""

    test_field: str


def create_test_message(message_id: str) -> StellaNowEventWrapper:
    """Helper to create test messages wrapped for queue."""
    msg = SampleMessage(
        event_name="test_event",
        entities=[Entity(entity_type_definition_id="test", entity_id="test_entity")],
        test_field=f"data_{message_id}",
    )
    wrapper = StellaNowMessageWrapper.create(msg)
    # Override the auto-generated message_id for testing
    wrapper.metadata.message_id = message_id

    return StellaNowEventWrapper.create(
        message=wrapper,
        organization_id=UUID("00000000-0000-0000-0000-000000000000"),
        project_id=UUID("00000000-0000-0000-0000-000000000000"),
    )


class TestFifoDropOldest:
    """Tests for FIFO queue with DROP_OLDEST strategy."""

    def test_drop_oldest_when_full(self):
        """Test that oldest messages are dropped when queue is full."""
        queue = FifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_OLDEST)

        # Fill queue to capacity
        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        msg3 = create_test_message("msg3")
        queue.enqueue(msg1)
        queue.enqueue(msg2)
        queue.enqueue(msg3)

        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 0

        # Add 4th message - should drop msg1
        msg4 = create_test_message("msg4")
        queue.enqueue(msg4)

        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 1

        # Dequeue and verify msg1 was dropped, msg2 is now first
        dequeued = queue.try_dequeue()
        assert dequeued.message_id == "msg2"

    def test_multiple_drops(self):
        """Test multiple messages being dropped."""
        queue = FifoMessageQueueStrategy(max_size=2, overflow_strategy=OverflowStrategy.DROP_OLDEST)

        for i in range(10):
            queue.enqueue(create_test_message(f"msg{i}"))

        assert queue.get_message_count() == 2
        assert queue.get_dropped_count() == 8

        # Should have msg8 and msg9
        assert queue.try_dequeue().message_id == "msg8"
        assert queue.try_dequeue().message_id == "msg9"


class TestFifoDropNewest:
    """Tests for FIFO queue with DROP_NEWEST strategy."""

    def test_drop_newest_when_full(self):
        """Test that newest messages are rejected when queue is full."""
        queue = FifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_NEWEST)

        # Fill queue to capacity
        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        msg3 = create_test_message("msg3")
        queue.enqueue(msg1)
        queue.enqueue(msg2)
        queue.enqueue(msg3)

        assert queue.get_message_count() == 3

        # Try to add 4th message - should be rejected
        msg4 = create_test_message("msg4")
        queue.enqueue(msg4)

        assert queue.get_message_count() == 3  # Still 3
        assert queue.get_dropped_count() == 1

        # Dequeue and verify msg1, msg2, msg3 are preserved
        assert queue.try_dequeue().message_id == "msg1"
        assert queue.try_dequeue().message_id == "msg2"
        assert queue.try_dequeue().message_id == "msg3"
        assert queue.try_dequeue() is None


class TestFifoRaiseException:
    """Tests for FIFO queue with RAISE_EXCEPTION strategy."""

    def test_raise_exception_when_full(self):
        """Test that QueueFullError is raised when queue is full."""
        queue = FifoMessageQueueStrategy(max_size=2, overflow_strategy=OverflowStrategy.RAISE_EXCEPTION)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        queue.enqueue(msg1)
        queue.enqueue(msg2)

        # 3rd message should raise exception
        msg3 = create_test_message("msg3")
        with pytest.raises(QueueFullError) as exc_info:
            queue.enqueue(msg3)

        assert exc_info.value.queue_size == 2
        assert exc_info.value.dropped_count == 0
        assert exc_info.value.message_id == "msg3"
        assert "Cannot accept message msg3" in str(exc_info.value)

    def test_exception_preserves_queue(self):
        """Test that queue state is preserved when exception is raised."""
        queue = FifoMessageQueueStrategy(max_size=2, overflow_strategy=OverflowStrategy.RAISE_EXCEPTION)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        queue.enqueue(msg1)
        queue.enqueue(msg2)

        # Try to add 3rd message
        msg3 = create_test_message("msg3")
        try:
            queue.enqueue(msg3)
        except QueueFullError:
            pass

        # Queue should still have original 2 messages
        assert queue.get_message_count() == 2
        assert queue.try_dequeue().message_id == "msg1"
        assert queue.try_dequeue().message_id == "msg2"


class TestLifoDropOldest:
    """Tests for LIFO queue with DROP_OLDEST strategy."""

    def test_drop_oldest_when_full(self):
        """Test that oldest messages are dropped when LIFO queue is full."""
        queue = LifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_OLDEST)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        msg3 = create_test_message("msg3")
        queue.enqueue(msg1)
        queue.enqueue(msg2)
        queue.enqueue(msg3)

        assert queue.get_message_count() == 3

        # Add 4th message - should drop msg1 (oldest)
        msg4 = create_test_message("msg4")
        queue.enqueue(msg4)

        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 1

        # LIFO: should get msg4, msg3, msg2 (msg1 was dropped)
        assert queue.try_dequeue().message_id == "msg4"
        assert queue.try_dequeue().message_id == "msg3"
        assert queue.try_dequeue().message_id == "msg2"


class TestLifoRaiseException:
    """Tests for LIFO queue with RAISE_EXCEPTION strategy."""

    def test_raise_exception_when_full(self):
        """Test that QueueFullError is raised when LIFO queue is full."""
        queue = LifoMessageQueueStrategy(max_size=2, overflow_strategy=OverflowStrategy.RAISE_EXCEPTION)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        queue.enqueue(msg1)
        queue.enqueue(msg2)

        msg3 = create_test_message("msg3")
        with pytest.raises(QueueFullError) as exc_info:
            queue.enqueue(msg3)

        assert exc_info.value.message_id == "msg3"


class TestQueueValidation:
    """Tests for queue size validation."""

    def test_negative_max_size_raises_error(self):
        """Test that negative max_size raises ValueError."""
        with pytest.raises(ValueError, match="max_size must be non-negative"):
            FifoMessageQueueStrategy(max_size=-1)

    def test_excessive_max_size_raises_error(self):
        """Test that excessive max_size raises ValueError."""
        with pytest.raises(ValueError, match="max_size too large"):
            FifoMessageQueueStrategy(max_size=20_000_000)

    def test_zero_max_size_is_unlimited(self):
        """Test that max_size=0 means unlimited queue."""
        queue = FifoMessageQueueStrategy(max_size=0)

        # Add many messages - should not drop any
        for i in range(1000):
            queue.enqueue(create_test_message(f"msg{i}"))

        assert queue.get_message_count() == 1000
        assert queue.get_dropped_count() == 0


class TestDefaultBehavior:
    """Tests for default queue behavior (backward compatibility)."""

    def test_default_max_size(self):
        """Test that default max_size is 100,000."""
        queue = FifoMessageQueueStrategy()
        # Just verify it's created successfully with default
        assert queue.get_message_count() == 0

    def test_default_overflow_strategy(self):
        """Test that default overflow strategy is DROP_OLDEST."""
        queue = FifoMessageQueueStrategy(max_size=2)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        msg3 = create_test_message("msg3")
        queue.enqueue(msg1)
        queue.enqueue(msg2)
        queue.enqueue(msg3)

        # Should have dropped msg1, kept msg2 and msg3
        assert queue.try_dequeue().message_id == "msg2"
        assert queue.try_dequeue().message_id == "msg3"
