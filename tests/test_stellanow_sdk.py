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
from unittest.mock import AsyncMock, patch, MagicMock

from pydantic import BaseModel

from stellanow_sdk_python.messages.message_wrapper import StellaNowMessageWrapper
from stellanow_sdk_python.sdk import StellaNowSDK
from stellanow_sdk_python.sinks.i_stellanow_sink import IStellaNowSink
from stellanow_sdk_python.message_queue.message_queue_strategy.fifo_messsage_queue_strategy import FifoMessageQueueStrategy


class MockMessage(BaseModel):
    entities: list = [{"type": "test"}]


@pytest.fixture
def mock_mqtt_sink():
    with patch('stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink.StellaNowMqttSink', autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_auth_strategy():
    return MagicMock(spec=IStellaNowSink)


@pytest.fixture
def mock_queue_strategy():
    return MagicMock(spec=FifoMessageQueueStrategy)


@pytest.mark.asyncio
@patch('stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink.StellaNowMqttSink.connect', new_callable=AsyncMock)
async def test_stellanow_sdk_start(mock_connect, mock_auth_strategy, mock_queue_strategy):
    """
    Test that the SDK starts correctly and connects to the MQTT sink.
    """
    sdk = StellaNowSDK(sink=mock_auth_strategy, queue_strategy=mock_queue_strategy)
    await sdk.start()
    mock_connect.assert_awaited_once()


@pytest.mark.asyncio
@patch('stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink.StellaNowMqttSink.send_message', new_callable=AsyncMock)
async def test_stellanow_sdk_send_message(mock_send_message, mock_auth_strategy, mock_queue_strategy):
    """
    Test that the SDK sends messages correctly through the MQTT sink.
    """
    sdk = StellaNowSDK(sink=mock_auth_strategy, queue_strategy=mock_queue_strategy)
    message = MockMessage()
    wrapped_message = StellaNowMessageWrapper.create(
        message=message,
        organization_id="9dbc5cc1-8c36-463e-893c-b08713868e97",
        project_id="529360a9-e40c-4d93-b3d3-5ed9f76c0037",
        event_id="b822d187-36cb-4d53-9112-e753f45ad9af"
    )
    await sdk.send_message(message)
    mock_send_message.assert_awaited_once_with(wrapped_message)


@pytest.mark.asyncio
@patch('stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink.StellaNowMqttSink.disconnect', new_callable=AsyncMock)
async def test_stellanow_sdk_stop(mock_disconnect, mock_auth_strategy, mock_queue_strategy):
    """
    Test that the SDK stops correctly and disconnects from the MQTT sink.
    """
    sdk = StellaNowSDK(sink=mock_auth_strategy, queue_strategy=mock_queue_strategy)
    await sdk.stop()
    mock_disconnect.assert_awaited_once()
