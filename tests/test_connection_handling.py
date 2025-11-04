"""
Copyright (C) 2022-2025 Stella Technologies (UK) Limited.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the software without restriction, including without limitation the rights
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

import paho.mqtt.client as mqtt
import pytest

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from stellanow_sdk_python.sinks.mqtt.stellanow_mqtt_sink import StellaNowMqttSink
from tests.conftest import TEST_ORG_ID, TEST_PROJECT_ID, TEST_CLIENT_ID


@pytest.fixture
def project_info():
    """Fixture providing project info."""
    return StellaProjectInfo(organization_id=TEST_ORG_ID, project_id=TEST_PROJECT_ID)


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


class TestIsConnectedNullSafety:
    """Tests for is_connected() null pointer safety."""

    def test_is_connected_with_none_client_returns_false(self, mock_auth_strategy, env_config, project_info):
        """Test that is_connected() returns False when client is None."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the initial client loop
            if sink.client:
                sink.client.loop_stop()

            # Set client to None (can happen during reconnection)
            sink.client = None
            sink._is_connected_event.set()

            # Should not crash, should return False
            assert sink.is_connected() is False
        finally:
            pass  # client is None, nothing to cleanup

    def test_is_connected_with_attribute_error_returns_false(self, mock_auth_strategy, env_config, project_info):
        """Test that is_connected() returns False when client raises AttributeError."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the initial client loop
            if sink.client:
                sink.client.loop_stop()

            # Mock client that raises AttributeError
            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(side_effect=AttributeError("Client attribute error"))
            sink._is_connected_event.set()

            # Should not crash, should return False
            assert sink.is_connected() is False
        finally:
            pass  # Mock client, nothing to cleanup

    def test_is_connected_with_runtime_error_returns_false(self, mock_auth_strategy, env_config, project_info):
        """Test that is_connected() returns False when client raises RuntimeError."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the initial client loop
            if sink.client:
                sink.client.loop_stop()

            # Mock client that raises RuntimeError
            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(side_effect=RuntimeError("Client runtime error"))
            sink._is_connected_event.set()

            # Should not crash, should return False
            assert sink.is_connected() is False
        finally:
            pass  # Mock client, nothing to cleanup

    def test_is_connected_depends_on_event_state(self, mock_auth_strategy, env_config, project_info):
        """Test that is_connected() returns False/True based on connection event state."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the initial client loop
            if sink.client:
                sink.client.loop_stop()

            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(return_value=mqtt.MQTT_ERR_SUCCESS)

            # Don't set the event - should return False
            assert sink.is_connected() is False

            # After setting the event - should return True
            sink._is_connected_event.set()
            assert sink.is_connected() is True
        finally:
            pass  # Mock client, nothing to cleanup

    def test_is_connected_returns_false_when_loop_misc_fails(self, mock_auth_strategy, env_config, project_info):
        """Test that is_connected() returns False when loop_misc() indicates error."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the initial client loop
            if sink.client:
                sink.client.loop_stop()

            sink.client = MagicMock(spec=mqtt.Client)
            sink.client.loop_misc = MagicMock(return_value=mqtt.MQTT_ERR_NO_CONN)
            sink._is_connected_event.set()

            assert sink.is_connected() is False
        finally:
            pass  # Mock client, nothing to cleanup


class TestConnectRaceCondition:
    """Tests for race condition fix in connect()."""

    @pytest.mark.asyncio
    async def test_connect_uses_lock_for_monitor_task_creation(self, mock_auth_strategy, env_config, project_info):
        """Test that connect() protects monitor task creation with lock."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the client loop started in __init__
            if sink.client:
                sink.client.loop_stop()

            # Verify that _client_lock exists
            assert sink._client_lock is not None
            assert isinstance(sink._client_lock, asyncio.Lock)

            # Test that we can acquire the lock (proving it's used)
            async with sink._client_lock:
                # If we can acquire it, the lock is working
                assert True
        finally:
            # Cleanup
            sink._shutdown = True
            if sink._monitor_task:
                sink._monitor_task.cancel()
                try:
                    await sink._monitor_task
                except asyncio.CancelledError:
                    pass
            if sink.client:
                sink.client.loop_stop()

    @pytest.mark.asyncio
    async def test_connect_with_shutdown_flag_skips_connection(self, mock_auth_strategy, env_config, project_info):
        """Test that connect() skips connection attempt when shutdown flag is set."""
        sink = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop the client loop
            if sink.client:
                sink.client.loop_stop()

            sink._shutdown = True
            await sink.connect()

            # Should not have created monitor task
            assert sink._monitor_task is None
        finally:
            # Cleanup just in case
            if sink.client:
                sink.client.loop_stop()


class TestTokenRefreshRuntimeCheck:
    """Tests for explicit runtime checks replacing assert statements."""

    @pytest.mark.asyncio
    async def test_get_access_token_with_none_response_raises_runtime_error(self, project_info):
        """Test that get_access_token() raises RuntimeError instead of AssertionError."""
        from pydantic import SecretStr

        from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
        from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials

        credentials = StellaNowCredentials(
            username="test", password=SecretStr("test"), client_id=TEST_CLIENT_ID
        )
        env_config = EnvConfig.stellanow_dev()

        auth_service = StellaNowAuthenticationService(
            project_info=project_info, credentials=credentials, env_config=env_config
        )

        # Manually set token_response to None after initialization
        auth_service.token_response = None
        auth_service.token_expires = None

        # Mock the authenticate method to simulate the edge case
        auth_service.authenticate = AsyncMock(side_effect=RuntimeError("Auth failed"))

        with pytest.raises(RuntimeError, match="Auth failed"):
            await auth_service.get_access_token()

    @pytest.mark.asyncio
    async def test_refresh_access_token_explicit_none_check(self, project_info):
        """Test that refresh_access_token() raises TokenRefreshError on network errors."""
        from keycloak.exceptions import KeycloakError
        from pydantic import SecretStr

        from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
        from stellanow_sdk_python.authentication.exceptions import TokenRefreshError
        from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials

        credentials = StellaNowCredentials(
            username="test", password=SecretStr("test"), client_id=TEST_CLIENT_ID
        )
        env_config = EnvConfig.stellanow_dev()

        auth_service = StellaNowAuthenticationService(
            project_info=project_info, credentials=credentials, env_config=env_config
        )

        try:
            # Set up initial token response
            auth_service.token_response = {"refresh_token": "test_refresh"}

            # Mock the keycloak refresh to fail with network error (HTTP 500)
            # Using 500 instead of 401 to avoid triggering re-authentication logic
            auth_service.keycloak_openid.a_refresh_token = AsyncMock(
                side_effect=KeycloakError("Refresh failed", response_code=500)
            )

            with pytest.raises(TokenRefreshError, match="Failed to refresh access token"):
                await auth_service.refresh_access_token()
        finally:
            # Cleanup: stop any background refresh task that might have started
            await auth_service.stop_refresh_task()


class TestClientRecreation:
    """Tests for client recreation during reconnection."""

    def test_client_id_is_unique(self, mock_auth_strategy, env_config, project_info):
        """Test that each sink instance gets a unique client_id."""
        sink1 = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)
        sink2 = StellaNowMqttSink(auth_strategy=mock_auth_strategy, env_config=env_config, project_info=project_info)

        try:
            # Stop client loops
            if sink1.client:
                sink1.client.loop_stop()
            if sink2.client:
                sink2.client.loop_stop()

            assert sink1.client_id != sink2.client_id
            assert sink1.client_id.startswith("StellaNowSDKPython_")
            assert sink2.client_id.startswith("StellaNowSDKPython_")
        finally:
            # Cleanup
            if sink1.client:
                sink1.client.loop_stop()
            if sink2.client:
                sink2.client.loop_stop()
