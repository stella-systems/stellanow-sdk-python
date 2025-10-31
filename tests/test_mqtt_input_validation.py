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
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import paho.mqtt.client as mqtt
import pytest

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.messages.event import StellaNowEventWrapper
from stellanow_sdk_python.messages.message import Entity, StellaNowMessageBase, StellaNowMessageWrapper
from stellanow_sdk_python.sinks.mqtt.exceptions import MqttSinkDisconnectedError
from stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink import StellaNowMqttSink


class SampleMessage(StellaNowMessageBase):
    """Simple test message class."""

    test_data: str


@pytest.fixture
def project_info():
    """Fixture providing valid project info."""
    return StellaProjectInfo(organization_id="test-org-123", project_id="test-project-456")


@pytest.fixture
def empty_org_project_info():
    """Fixture providing project info with empty organization ID."""
    return StellaProjectInfo(organization_id="", project_id="test-project-456")


@pytest.fixture
def env_config():
    """Fixture providing environment configuration."""
    return EnvConfig.stellanow_dev()


@pytest.fixture
def mock_auth_strategy():
    """Fixture providing mocked auth strategy."""
    strategy = MagicMock()
    strategy.authenticate = AsyncMock()
    return strategy


@pytest.fixture
async def mqtt_sink(mock_auth_strategy, env_config, project_info):
    """Fixture providing an MQTT sink instance."""
    sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

    # Stop the real client loop started in __init__
    if sink.client:
        sink.client.loop_stop()

    # Mock the client
    sink.client = MagicMock(spec=mqtt.Client)
    sink.client.publish = MagicMock(return_value=MagicMock(rc=mqtt.MQTT_ERR_SUCCESS, mid=1))
    sink.client.loop_misc = MagicMock(return_value=mqtt.MQTT_ERR_SUCCESS)
    sink._is_connected_event.set()

    yield sink

    # Cleanup
    sink._shutdown = True
    if sink._monitor_task:
        sink._monitor_task.cancel()
        try:
            await sink._monitor_task
        except asyncio.CancelledError:
            pass


def create_test_message(data: str = "test") -> StellaNowEventWrapper:
    """Helper to create test messages wrapped for sink."""
    msg = SampleMessage(
        event_name="test_event", entities=[Entity(entity_type_definition_id="test", entity_id="test_entity")], test_data=data
    )
    wrapper = StellaNowMessageWrapper.create(msg)
    return StellaNowEventWrapper.create(
        message=wrapper,
        organization_id=UUID("12345678-1234-5678-1234-567812345678"),
        project_id=UUID("87654321-4321-8765-4321-876543218765"),
    )


class TestOrganizationIdValidation:
    """Tests for organization ID validation."""

    @pytest.mark.asyncio
    async def test_empty_organization_id_raises_error(self, mock_auth_strategy, env_config, empty_org_project_info):
        """Test that empty organization ID raises ValueError."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=empty_org_project_info)

        try:
            # Stop the real client loop
            if sink.client:
                sink.client.loop_stop()

            # Mock connected state
            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(return_value=mqtt.MQTT_ERR_SUCCESS)
            sink._is_connected_event.set()

            message = create_test_message()
            with pytest.raises(ValueError, match="Organization ID is empty"):
                await sink.send_message(message)
        finally:
            pass  # Mock client, nothing to cleanup


class TestTopicValidation:
    """Tests for MQTT topic validation."""

    @pytest.mark.asyncio
    async def test_excessively_long_topic_raises_error(self, mock_auth_strategy, env_config):
        """Test that excessively long topics raise ValueError."""
        # Create project info with very long org ID
        long_org_id = "x" * 70000  # Will exceed 65535 byte limit
        project_info = StellaProjectInfo(organization_id=long_org_id, project_id="test")

        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the real client loop
            if sink.client:
                sink.client.loop_stop()

            # Mock connected state
            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(return_value=mqtt.MQTT_ERR_SUCCESS)
            sink._is_connected_event.set()

            message = create_test_message()
            with pytest.raises(ValueError, match="MQTT topic too long"):
                await sink.send_message(message)
        finally:
            pass  # Mock client, nothing to cleanup


class TestPayloadValidation:
    """Tests for MQTT payload size validation."""

    @pytest.mark.asyncio
    async def test_oversized_payload_raises_error(self, mqtt_sink):
        """Test that oversized payloads raise ValueError."""
        # Create message with huge data
        huge_data = "x" * 268_435_456  # Just over 256 MB limit
        message = create_test_message(data=huge_data)

        with pytest.raises(ValueError, match="Message payload too large"):
            await mqtt_sink.send_message(message)

    @pytest.mark.asyncio
    async def test_normal_payload_size_accepted(self, mqtt_sink):
        """Test that normal-sized payloads are accepted."""
        message = create_test_message(data="normal data")
        await mqtt_sink.send_message(message)

        # Verify publish was called
        mqtt_sink.client.publish.assert_called_once()


class TestQoSValidation:
    """Tests for QoS validation."""

    @pytest.mark.asyncio
    async def test_invalid_qos_raises_error(self, mqtt_sink):
        """Test that invalid QoS levels raise ValueError."""
        # Set invalid QoS
        mqtt_sink.default_qos = 5  # Invalid - must be 0, 1, or 2

        message = create_test_message()
        with pytest.raises(ValueError, match="Invalid QoS level: 5"):
            await mqtt_sink.send_message(message)

    @pytest.mark.asyncio
    async def test_valid_qos_0_accepted(self, mqtt_sink):
        """Test that QoS 0 is accepted."""
        mqtt_sink.default_qos = 0
        message = create_test_message()
        await mqtt_sink.send_message(message)
        mqtt_sink.client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_valid_qos_1_accepted(self, mqtt_sink):
        """Test that QoS 1 is accepted."""
        mqtt_sink.default_qos = 1
        message = create_test_message()
        await mqtt_sink.send_message(message)
        mqtt_sink.client.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_valid_qos_2_accepted(self, mqtt_sink):
        """Test that QoS 2 is accepted."""
        mqtt_sink.default_qos = 2
        message = create_test_message()
        await mqtt_sink.send_message(message)
        mqtt_sink.client.publish.assert_called_once()


class TestDisconnectedState:
    """Tests for validation when sink is disconnected."""

    @pytest.mark.asyncio
    async def test_send_message_when_disconnected_raises_error(self, mqtt_sink):
        """Test that sending message when disconnected raises MqttSinkDisconnectedError."""
        # Simulate disconnected state
        mqtt_sink._is_connected_event.clear()

        message = create_test_message()
        with pytest.raises(MqttSinkDisconnectedError, match="MQTT sink is disconnected"):
            await mqtt_sink.send_message(message)

    @pytest.mark.asyncio
    async def test_send_message_with_none_client_raises_error(self, mqtt_sink):
        """Test that sending message with None client raises MqttSinkDisconnectedError."""
        # Set client to None (can happen during reconnection)
        mqtt_sink.client = None

        message = create_test_message()
        with pytest.raises(MqttSinkDisconnectedError):
            await mqtt_sink.send_message(message)
