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
from tests.conftest import TEST_ORG_ID, TEST_PROJECT_ID


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
        organization_id=TEST_ORG_ID,
        project_id=TEST_PROJECT_ID,
    )


class TestQueueOverflowBehavior:
    """Tests for queue overflow behavior with consistent setup across strategies."""

    def test_fifo_drop_oldest(self):
        """Test FIFO queue drops oldest messages when full."""
        queue = FifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_OLDEST)

        # Produce 6 messages
        for i in range(6):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Consume 2 (msg3, msg4)
        assert queue.try_dequeue().message_id == "msg3"
        assert queue.try_dequeue().message_id == "msg4"

        # Produce 4 more (msg6 through msg9)
        for i in range(6, 10):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Should have msg7, msg8, msg9 (msg5, msg6 were dropped)
        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 5  # msg0, msg1, msg2, msg5, msg6
        assert queue.try_dequeue().message_id == "msg7"
        assert queue.try_dequeue().message_id == "msg8"
        assert queue.try_dequeue().message_id == "msg9"

    def test_fifo_drop_newest(self):
        """Test FIFO queue rejects newest messages when full."""
        queue = FifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_NEWEST)

        # Produce 6 messages (msg3, msg4, msg5 rejected)
        for i in range(6):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Consume 2 (msg0, msg1)
        assert queue.try_dequeue().message_id == "msg0"
        assert queue.try_dequeue().message_id == "msg1"

        # Produce 4 more (msg6, msg7 accepted; msg8, msg9 rejected)
        for i in range(6, 10):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Should have msg2, msg6, msg7 (msg3-5, msg8-9 were rejected)
        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 5  # msg3, msg4, msg5, msg8, msg9
        assert queue.try_dequeue().message_id == "msg2"
        assert queue.try_dequeue().message_id == "msg6"
        assert queue.try_dequeue().message_id == "msg7"

    def test_lifo_drop_oldest(self):
        """Test LIFO queue drops oldest messages when full."""
        queue = LifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_OLDEST)

        # Produce 6 messages
        for i in range(6):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Consume 2 (msg5, msg4 - LIFO order)
        assert queue.try_dequeue().message_id == "msg5"
        assert queue.try_dequeue().message_id == "msg4"

        # Produce 4 more (msg6 through msg9)
        for i in range(6, 10):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Should have msg9, msg8, msg7 in LIFO order (msg3, msg6 were dropped)
        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 5  # msg0, msg1, msg2, msg3, msg6
        assert queue.try_dequeue().message_id == "msg9"
        assert queue.try_dequeue().message_id == "msg8"
        assert queue.try_dequeue().message_id == "msg7"

    def test_lifo_drop_newest(self):
        """Test LIFO queue rejects newest messages when full."""
        queue = LifoMessageQueueStrategy(max_size=3, overflow_strategy=OverflowStrategy.DROP_NEWEST)

        # Produce 6 messages (msg3, msg4, msg5 rejected)
        for i in range(6):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Consume 2 (msg2, msg1 - LIFO order)
        assert queue.try_dequeue().message_id == "msg2"
        assert queue.try_dequeue().message_id == "msg1"

        # Produce 4 more (msg6, msg7 accepted; msg8, msg9 rejected)
        for i in range(6, 10):
            queue.enqueue(create_test_message(f"msg{i}"))

        # Should have msg7, msg6, msg0 in LIFO order (msg3-5, msg8-9 were rejected)
        assert queue.get_message_count() == 3
        assert queue.get_dropped_count() == 5  # msg3, msg4, msg5, msg8, msg9
        assert queue.try_dequeue().message_id == "msg7"
        assert queue.try_dequeue().message_id == "msg6"
        assert queue.try_dequeue().message_id == "msg0"


class TestRaiseExceptionStrategy:
    """Tests for RAISE_EXCEPTION strategy."""

    def test_fifo_raise_exception_when_full(self):
        """Test that FIFO QueueFullError is raised when queue is full and queue state is preserved."""
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

        # Queue should still have original 2 messages
        assert queue.get_message_count() == 2
        assert queue.try_dequeue().message_id == "msg1"
        assert queue.try_dequeue().message_id == "msg2"

    def test_lifo_raise_exception_when_full(self):
        """Test that LIFO QueueFullError is raised when queue is full."""
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
        """Test that default max_size is 0 (unlimited)."""
        queue = FifoMessageQueueStrategy()
        # Just verify it's created successfully with default
        assert queue.get_message_count() == 0

    def test_default_overflow_strategy(self):
        """Test that default overflow strategy is RAISE_EXCEPTION."""
        queue = FifoMessageQueueStrategy(max_size=2)

        msg1 = create_test_message("msg1")
        msg2 = create_test_message("msg2")
        queue.enqueue(msg1)
        queue.enqueue(msg2)

        # 3rd message should raise exception with default strategy
        msg3 = create_test_message("msg3")
        with pytest.raises(QueueFullError):
            queue.enqueue(msg3)

        # Queue should still have original 2 messages
        assert queue.get_message_count() == 2
        assert queue.try_dequeue().message_id == "msg1"
        assert queue.try_dequeue().message_id == "msg2"
