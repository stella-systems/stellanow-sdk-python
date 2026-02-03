"""Test authentication behavior with multiple SDK instances (simulating Nuclio multi-worker scenario)."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from keycloak.exceptions import KeycloakError


@pytest.mark.asyncio
class TestMultiInstanceAuthentication:
    """Test authentication with multiple SDK instances (simulating Nuclio numWorkers: 2)."""

    async def test_two_instances_authenticate_independently(self, create_auth_service, create_token_response):
        """Test that two SDK instances can authenticate independently without conflicts."""
        # Create two separate auth service instances (like two Nuclio workers)
        auth_service_1 = create_auth_service()
        auth_service_2 = create_auth_service()

        # Mock Keycloak responses for both instances
        token_1 = create_token_response("token_worker_1", "refresh_worker_1")
        token_2 = create_token_response("token_worker_2", "refresh_worker_2")

        auth_service_1.keycloak_openid.a_token = AsyncMock(return_value=token_1)
        auth_service_2.keycloak_openid.a_token = AsyncMock(return_value=token_2)

        # Authenticate both simultaneously (like Nuclio workers starting)
        results = await asyncio.gather(
            auth_service_1.authenticate(),
            auth_service_2.authenticate()
        )

        # Verify: both succeeded with their own tokens
        assert results[0] == "token_worker_1"
        assert results[1] == "token_worker_2"
        assert auth_service_1.token_response["access_token"] == "token_worker_1"
        assert auth_service_2.token_response["access_token"] == "token_worker_2"

    async def test_two_instances_with_same_credentials_no_deadlock(self, create_auth_service, create_token_response):
        """Test that two instances using same credentials don't deadlock during authentication."""
        auth_service_1 = create_auth_service()
        auth_service_2 = create_auth_service()

        # Shared call counter to verify both instances complete
        call_count = 0
        call_lock = asyncio.Lock()

        async def mock_token_with_delay(*args, **kwargs):
            """Mock token call with delay to simulate network latency."""
            nonlocal call_count
            await asyncio.sleep(0.1)  # Simulate network delay
            async with call_lock:
                call_count += 1
            return create_token_response(f"token_{call_count}", f"refresh_{call_count}")

        auth_service_1.keycloak_openid.a_token = AsyncMock(side_effect=mock_token_with_delay)
        auth_service_2.keycloak_openid.a_token = AsyncMock(side_effect=mock_token_with_delay)

        # Start authentication simultaneously with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    auth_service_1.authenticate(),
                    auth_service_2.authenticate()
                ),
                timeout=5.0  # Should complete within 5 seconds
            )

            # Verify: both completed successfully
            assert len(results) == 2
            assert call_count == 2
            assert auth_service_1.token_response is not None
            assert auth_service_2.token_response is not None
        except asyncio.TimeoutError:
            pytest.fail("Authentication deadlocked with two instances - CONFIRMED BUG!")

    async def test_two_instances_refresh_tokens_simultaneously(self, create_auth_service, create_token_response):
        """Test that two instances can refresh tokens simultaneously without conflicts."""
        auth_service_1 = create_auth_service()
        auth_service_2 = create_auth_service()

        # Setup: both have valid tokens
        auth_service_1.token_response = create_token_response("token_1", "refresh_1")
        auth_service_1.token_expires = datetime.now() + timedelta(seconds=300)
        auth_service_2.token_response = create_token_response("token_2", "refresh_2")
        auth_service_2.token_expires = datetime.now() + timedelta(seconds=300)

        # Mock refresh responses
        new_token_1 = create_token_response("new_token_1", "new_refresh_1")
        new_token_2 = create_token_response("new_token_2", "new_refresh_2")

        auth_service_1.keycloak_openid.a_refresh_token = AsyncMock(return_value=new_token_1)
        auth_service_2.keycloak_openid.a_refresh_token = AsyncMock(return_value=new_token_2)

        # Refresh both simultaneously
        results = await asyncio.gather(
            auth_service_1.refresh_access_token(),
            auth_service_2.refresh_access_token()
        )

        # Verify: both refreshed successfully with their own tokens
        assert results[0] == "new_token_1"
        assert results[1] == "new_token_2"
        assert auth_service_1.token_response["access_token"] == "new_token_1"
        assert auth_service_2.token_response["access_token"] == "new_token_2"

    async def test_two_instances_one_fails_other_succeeds(self, create_auth_service, create_token_response):
        """Test that one instance failing doesn't affect the other instance."""
        auth_service_1 = create_auth_service()
        auth_service_2 = create_auth_service()

        # Mock: first instance fails, second succeeds
        auth_error = KeycloakError(error_message="Invalid credentials", response_code=401)
        auth_service_1.keycloak_openid.a_token = AsyncMock(side_effect=auth_error)

        success_token = create_token_response("token_worker_2", "refresh_worker_2")
        auth_service_2.keycloak_openid.a_token = AsyncMock(return_value=success_token)

        # Try to authenticate both
        results = await asyncio.gather(
            auth_service_1.authenticate(),
            auth_service_2.authenticate(),
            return_exceptions=True
        )

        # Verify: first failed, second succeeded
        assert isinstance(results[0], Exception)
        assert results[1] == "token_worker_2"
        assert auth_service_2.token_response["access_token"] == "token_worker_2"

    async def test_shared_lock_doesnt_exist_between_instances(self, create_auth_service):
        """Verify that each instance has its own lock (not shared)."""
        auth_service_1 = create_auth_service()
        auth_service_2 = create_auth_service()

        # Verify: different lock objects
        assert auth_service_1.lock is not auth_service_2.lock
        assert id(auth_service_1.lock) != id(auth_service_2.lock)

    async def test_nuclio_scenario_two_workers_init_context(self, create_auth_service, create_token_response):
        """
        Simulate the actual Nuclio scenario:
        - Two workers (separate Python processes in reality, but we simulate with asyncio)
        - Each calls init_context() which creates SDK and calls await sdk.start()
        - SDK start() calls auth_service.authenticate()

        This tests if there's any deadlock or race condition.
        """
        # Simulate two Nuclio workers
        worker_1_auth = create_auth_service()
        worker_2_auth = create_auth_service()

        # Mock Keycloak with realistic delay
        call_order = []

        def create_mock_auth(worker_id):
            """Create a mock auth function for a specific worker."""
            async def mock_auth(*args, **kwargs):
                call_order.append(f"{worker_id}_start")
                await asyncio.sleep(0.1)  # Simulate network latency
                call_order.append(f"{worker_id}_end")
                return create_token_response(f"token_{worker_id}", f"refresh_{worker_id}")
            return mock_auth

        worker_1_auth.keycloak_openid.a_token = AsyncMock(side_effect=create_mock_auth("worker_1"))
        worker_2_auth.keycloak_openid.a_token = AsyncMock(side_effect=create_mock_auth("worker_2"))

        # Simulate init_context() being called on both workers simultaneously
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    worker_1_auth.authenticate(),
                    worker_2_auth.authenticate()
                ),
                timeout=5.0
            )

            # Verify: both completed without deadlock
            assert len(call_order) == 4
            assert "worker_1_start" in call_order
            assert "worker_1_end" in call_order
            assert "worker_2_start" in call_order
            assert "worker_2_end" in call_order

            # Verify: both have valid tokens
            assert worker_1_auth.token_response is not None
            assert worker_2_auth.token_response is not None
        except asyncio.TimeoutError:
            pytest.fail(
                f"DEADLOCK DETECTED in Nuclio scenario! "
                f"Call order: {call_order}. "
                f"This confirms the bug reported in the analysis."
            )
