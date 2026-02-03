"""Test retry logic for concurrent authentication scenarios (numWorkers > 1)."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from keycloak.exceptions import KeycloakError

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.authentication.exceptions import AuthenticationError
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo
from tests.conftest import TEST_CLIENT_ID, TEST_ORG_ID, TEST_PASSWORD, TEST_PROJECT_ID, TEST_USERNAME


def create_auth_service() -> StellaNowAuthenticationService:
    """Create a test authentication service instance."""
    project_info = StellaProjectInfo(organization_id=TEST_ORG_ID, project_id=TEST_PROJECT_ID)
    credentials = StellaNowCredentials(client_id=TEST_CLIENT_ID, username=TEST_USERNAME, password=TEST_PASSWORD)
    env_config = EnvConfig.stellanow_dev()
    return StellaNowAuthenticationService(project_info=project_info, credentials=credentials, env_config=env_config)


def create_token_response(access_token: str = "test_token", refresh_token: str = "test_refresh", expires_in: int = 300):
    """Create a standard token response dictionary."""
    return {"access_token": access_token, "refresh_token": refresh_token, "expires_in": expires_in}


@pytest.mark.asyncio
class TestConcurrentAuthenticationRetry:
    """Test authentication retry logic for race conditions during concurrent authentication."""

    async def test_invalid_grant_retries_once_and_succeeds(self):
        """
        Test that invalid_grant error during initial auth triggers a retry that succeeds.

        This simulates the numWorkers:2 scenario where one worker gets invalid_grant
        due to concurrent authentication, but retry succeeds.
        """
        auth_service = create_auth_service()

        # Mock: First call fails with invalid_grant, second succeeds
        invalid_grant_error = KeycloakError(
            error_message='{"error":"invalid_grant","error_description":"Invalid user credentials"}',
            response_code=401
        )
        success_token = create_token_response("successful_token", "refresh_token")

        call_count = 0

        async def mock_token_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise invalid_grant_error
            return success_token

        auth_service.keycloak_openid.a_token = AsyncMock(side_effect=mock_token_with_retry)

        # Execute: should retry and succeed
        result = await auth_service.authenticate()

        # Verify: got token after retry
        assert result == "successful_token"
        assert call_count == 2  # Called twice (initial + retry)
        assert auth_service.token_response == success_token

    async def test_invalid_grant_retries_then_fails(self):
        """
        Test that invalid_grant error that persists after retries raises AuthenticationError.

        This ensures we don't endlessly retry real credential problems.
        """
        auth_service = create_auth_service()

        # Mock: All attempts fail with invalid_grant (real credential problem)
        invalid_grant_error = KeycloakError(
            error_message='{"error":"invalid_grant","error_description":"Invalid user credentials"}',
            response_code=401
        )

        auth_service.keycloak_openid.a_token = AsyncMock(side_effect=invalid_grant_error)

        # Execute & Verify: should raise AuthenticationError after all retries
        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.authenticate()

        assert "invalid_grant" in str(exc_info.value).lower()
        assert auth_service.keycloak_openid.a_token.call_count == 3  # Initial + 2 retries

    async def test_other_401_errors_not_retried(self):
        """
        Test that 401 errors that are NOT invalid_grant are not retried.

        Only invalid_grant should trigger retry (it can be transient in concurrent scenarios).
        """
        auth_service = create_auth_service()

        # Mock: Account locked error (permanent, should not retry)
        locked_error = KeycloakError(
            error_message='{"error":"account_locked","error_description":"Account is locked"}',
            response_code=401
        )

        auth_service.keycloak_openid.a_token = AsyncMock(side_effect=locked_error)

        # Execute & Verify: should raise immediately without retry
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate()

        assert auth_service.keycloak_openid.a_token.call_count == 1  # No retry

    async def test_two_workers_concurrent_auth_with_retry(self):
        """
        Test realistic numWorkers:2 scenario where one worker gets invalid_grant.

        Simulates:
        - Worker 1 and Worker 2 authenticate simultaneously
        - Worker 1 gets invalid_grant (race condition), retries, succeeds
        - Worker 2 succeeds immediately
        - Both end up authenticated successfully
        """
        worker_1_auth = create_auth_service()
        worker_2_auth = create_auth_service()

        # Worker 1: fails first, succeeds on retry
        invalid_grant_error = KeycloakError(
            error_message='{"error":"invalid_grant"}',
            response_code=401
        )
        worker_1_success_token = create_token_response("worker_1_token", "worker_1_refresh")

        worker_1_call_count = 0

        async def worker_1_mock(*args, **kwargs):
            nonlocal worker_1_call_count
            worker_1_call_count += 1
            if worker_1_call_count == 1:
                raise invalid_grant_error
            return worker_1_success_token

        worker_1_auth.keycloak_openid.a_token = AsyncMock(side_effect=worker_1_mock)

        # Worker 2: succeeds immediately
        worker_2_token = create_token_response("worker_2_token", "worker_2_refresh")
        worker_2_auth.keycloak_openid.a_token = AsyncMock(return_value=worker_2_token)

        # Execute: both authenticate concurrently
        results = await asyncio.gather(
            worker_1_auth.authenticate(),
            worker_2_auth.authenticate()
        )

        # Verify: both succeeded
        assert results[0] == "worker_1_token"
        assert results[1] == "worker_2_token"
        assert worker_1_call_count == 2  # Worker 1 retried
        assert worker_2_auth.keycloak_openid.a_token.call_count == 1  # Worker 2 succeeded first try

    async def test_retry_delay_desynchronizes_workers(self):
        """
        Test that the 100ms retry delay helps desynchronize workers.

        The retry delay ensures that if both workers initially conflict,
        the retry won't happen at exactly the same time.
        """
        auth_service = create_auth_service()

        invalid_grant_error = KeycloakError(
            error_message='{"error":"invalid_grant"}',
            response_code=401
        )
        success_token = create_token_response()

        call_times = []

        async def mock_token_with_timing(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) == 1:
                raise invalid_grant_error
            return success_token

        auth_service.keycloak_openid.a_token = AsyncMock(side_effect=mock_token_with_timing)

        # Execute
        await auth_service.authenticate()

        # Verify: retry happened at least 100ms after initial attempt
        assert len(call_times) == 2
        time_between_calls = (call_times[1] - call_times[0]) * 1000  # Convert to ms
        assert time_between_calls >= 100  # At least 100ms delay
        assert time_between_calls < 200  # But not too long (should be ~100ms)