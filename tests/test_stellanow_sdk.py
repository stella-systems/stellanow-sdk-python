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

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from stellanow_sdk_python.config.stellanow_config import project_info_from_env
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_message_queue_strategy import (
    FifoMessageQueueStrategy,
)
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase
from stellanow_sdk_python.sdk import StellaNowSDK
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink

# Set environment variables for tests
os.environ["ORGANIZATION_ID"] = "1f40a798-edad-4b51-a41e-178c69491293"
os.environ["PROJECT_ID"] = "1c2825c5-6870-4543-9939-8dccbc7918c4"


@pytest.fixture
def mock_message():
    """Fixture providing a sample StellaNow message instance with EntityType-based entities.

    Returns:
        MockMessage: A configured instance of the MockMessage class.
    """
    class MockMessage(StellaNowMessageBase):
        user_id: str

    return MockMessage(
        event_name="test_event",
        entities=[Entity(entity_type_definition_id="test", entity_id="test_id")],
        user_id="user_98888"
    )


@pytest.fixture
def mock_sink():
    """Fixture providing a mocked sink instance.

    Returns:
        MagicMock: A mock object simulating IStellaNowSink behavior with async methods.
    """
    mock = MagicMock(spec=IStellaNowSink)
    mock.connect = AsyncMock()
    mock.send_message = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_queue_strategy():
    """Fixture providing a mocked queue strategy instance.

    Returns:
        MagicMock: A mock object simulating FifoMessageQueueStrategy behavior.
    """
    return MagicMock(spec=FifoMessageQueueStrategy)


@pytest.mark.asyncio
async def test_stellanow_sdk_start(mock_sink, mock_queue_strategy):
    """Test that StellaNowSDK initializes and starts correctly, connecting to the sink.

    This test verifies that the SDK starts its internal components, including the message queue
    and sink connection, using the provided project information and mocked dependencies.

    Args:
        mock_sink (MagicMock): Mocked sink instance.
        mock_queue_strategy (MagicMock): Mocked queue strategy instance.
    """
    project_info = project_info_from_env()
    sdk = StellaNowSDK(sink=mock_sink, queue_strategy=mock_queue_strategy, project_info=project_info)

    await sdk.start()

    # Verify sink connection (queue processing is internal to SDK)
    mock_sink.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_stellanow_sdk_stop(mock_sink, mock_queue_strategy):
    """Test that StellaNowSDK stops correctly, disconnecting from the sink and stopping the queue.

    This test verifies that the SDK performs a clean shutdown, stopping the message queue processing
    and disconnecting from the sink.

    Args:
        mock_sink (MagicMock): Mocked sink instance.
        mock_queue_strategy (MagicMock): Mocked queue strategy instance.
    """
    project_info = project_info_from_env()
    sdk = StellaNowSDK(sink=mock_sink, queue_strategy=mock_queue_strategy, project_info=project_info)
    await sdk.start()
    await sdk.stop()

    # Verify disconnection (queue stop is internal to SDK)
    mock_sink.disconnect.assert_awaited_once()
