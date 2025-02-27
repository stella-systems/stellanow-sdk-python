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
from unittest.mock import AsyncMock, patch
from stellanow_sdk_python.sdk import StellaNowSDK
from stellanow_sdk_python.mqtt.mqtt_client import StellaNowMQTTClient


@pytest.fixture
def mock_mqtt_client():
    with patch('stellanow_sdk_python.mqtt.mqtt_client.StellaNowMQTTClient', autospec=True) as mock:
        yield mock


@pytest.mark.asyncio
@patch('stellanow_sdk_python.mqtt.mqtt_client.StellaNowMQTTClient.connect', new_callable=AsyncMock)
async def test_stellanow_sdk_start(mock_connect):
    sdk = StellaNowSDK()
    await sdk.start()
    mock_connect.assert_awaited_once()


@pytest.mark.asyncio
@patch('stellanow_sdk_python.mqtt.mqtt_client.StellaNowMQTTClient.publish_message', new_callable=AsyncMock)
async def test_stellanow_sdk_send_message(mock_publish):
    sdk = StellaNowSDK()
    message = {"key": "value"}
    await sdk.send_message(message)
    mock_publish.assert_awaited_once_with(message)


@patch('stellanow_sdk_python.mqtt.mqtt_client.StellaNowMQTTClient')
def test_stellanow_sdk_stop(mock_mqtt_client_class, mock_mqtt_client):
    mock_mqtt_client = mock_mqtt_client_class.return_value
    sdk = StellaNowSDK(mqtt_client=mock_mqtt_client)

    sdk.mqtt_client.message_queue.start_processing(lambda x: None)
    sdk.stop()
    mock_mqtt_client.stop.assert_called_once()
