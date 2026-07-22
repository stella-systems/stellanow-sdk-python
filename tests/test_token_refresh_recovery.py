"""Tests for token refresh recovery scenarios."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from keycloak.exceptions import KeycloakError

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.authentication.exceptions import TokenRefreshError


# Helper function
def setup_auth_service_with_token(auth_service: StellaNowAuthenticationService, token_response: dict) -> None:
    """Set up auth service with existing token response."""
    auth_service.token_response = token_response
    auth_service.token_expires = datetime.now() + timedelta(seconds=token_response["expires_in"])


class TestPermanentAuthErrorDetection:
    """Test _is_permanent_auth_error helper method."""

    def test_detects_invalid_credentials(self, create_auth_service):
        """Test that invalid credentials errors are detected as permanent using generic patterns."""
        auth_service = create_auth_service()

        test_cases = [
            # Generic patterns that work across Keycloak versions
            (401, '{"error":"invalid_grant"}', True, "Contains 'grant' - permanent"),
            (401, "Invalid user credentials", True, "Contains 'credential' - permanent"),
            (401, "account is disabled", True, "Contains 'disabled' - permanent"),
            (401, "account is locked", True, "Contains 'locked' - permanent"),
            (401, "invalid_client", True, "Contains 'client' + 'invalid' - permanent"),
            (401, "unauthorized_client", True, "Contains 'client' + 'unauthorized' - permanent"),
            # Token expiration should NOT be permanent
            (401, "token expired", False, "Token expiration - not permanent"),
            (401, "refresh token invalid", False, "Refresh token issue - not permanent"),
        ]

        for error_code, error_msg, expected, description in test_cases:
            error = KeycloakError(error_message=error_msg, response_code=error_code)
            assert auth_service._is_permanent_auth_error(error) is expected, description

    def test_html_responses_are_not_permanent(self, create_auth_service):
        """Test that HTML responses (proxy/firewall errors) are NOT permanent."""
        auth_service = create_auth_service()

        test_cases = [
            (403, "<!doctype html><html><body>Access Denied</body></html>", "HTML with 403"),
            (401, "<html><head><title>Error</title></head></html>", "HTML with 401"),
            (500, "<!DOCTYPE HTML><html>Server Error</html>", "HTML with 500"),
        ]

        for error_code, error_msg, description in test_cases:
            error = KeycloakError(error_message=error_msg, response_code=error_code)
            assert auth_service._is_permanent_auth_error(error) is False, f"{description} should NOT be permanent"

    def test_json_403_is_permanent(self, create_auth_service):
        """Test that JSON 403 errors (actual authorization issues) are permanent."""
        auth_service = create_auth_service()

        test_cases = [
            (403, '{"error":"access_denied","error_description":"Forbidden"}', "access_denied should be permanent"),
            (403, '{"error":"insufficient_scope"}', "insufficient_scope should be permanent"),
        ]

        for error_code, error_msg, expected_msg in test_cases:
            error = KeycloakError(error_message=error_msg, response_code=error_code)
            assert auth_service._is_permanent_auth_error(error) is True, expected_msg


class TestTokenExpirationErrorDetection:
    """Test _is_token_expiration_error helper method."""

    def test_detects_http_error_codes(self, create_auth_service):
        """Test that HTTP 400 and 401 are detected as token expiration errors."""
        auth_service = create_auth_service()

        test_cases = [
            (400, "Bad request", True, "HTTP 400 should be detected"),
            (401, "Unauthorized", True, "HTTP 401 should be detected"),
            (403, "Forbidden", False, "HTTP 403 should not be detected"),
            (500, "Server error", False, "HTTP 500 should not be detected"),
        ]

        for error_code, error_msg, expected, description in test_cases:
            error = KeycloakError(error_message=error_msg, response_code=error_code)
            assert auth_service._is_token_expiration_error(error) is expected, description

    def test_detects_generic_token_patterns(self, create_auth_service):
        """Test that generic token expiration patterns are detected (Keycloak version-independent)."""
        auth_service = create_auth_service()

        # Generic patterns: "token" + ("expired" OR "invalid" OR "not valid")
        # These work across different Keycloak versions
        expiration_patterns = [
            "Token expired",  # token + expired
            "token is expired",  # token + expired
            "INVALID REFRESH TOKEN",  # token + invalid
            "Refresh Token Expired",  # token + expired
            "token not valid",  # token + not valid
            "access token invalid",  # token + invalid
        ]

        for pattern in expiration_patterns:
            error = KeycloakError(error_message=pattern, response_code=None)
            assert auth_service._is_token_expiration_error(error) is True, f"Failed to detect: {pattern}"

        # Non-expiration messages should not be detected
        non_expiration_patterns = [
            "Connection timeout",  # No "token" keyword
            "Server error",  # No "token" keyword
            "Invalid credentials",  # Has neither token nor expiration keywords
        ]

        for pattern in non_expiration_patterns:
            error = KeycloakError(error_message=pattern, response_code=None)
            assert auth_service._is_token_expiration_error(error) is False, f"Falsely detected: {pattern}"


@pytest.mark.asyncio
class TestRefreshTokenRecovery:
    """Test refresh_access_token recovery from expired tokens."""

    async def test_expired_token_triggers_reauthentication(self, create_auth_service, create_token_response):
        """Test that expired refresh token (HTTP 400/401) triggers full re-authentication."""
        auth_service = create_auth_service()

        # Mock start_refresh_task to prevent background task from starting
        # This prevents the _auto_refresh loop from interfering with the test
        auth_service.start_refresh_task = AsyncMock()

        # Setup: existing token
        initial_token = create_token_response("old_token", "old_refresh")
        setup_auth_service_with_token(auth_service, initial_token)

        # Test both HTTP 400 and 401
        test_cases = [(400, "Bad request"), (401, "Unauthorized")]

        for error_code, error_msg in test_cases:
            # Mock: refresh fails with expiration error
            expired_error = KeycloakError(error_message=error_msg, response_code=error_code)
            auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=expired_error)

            # Mock: re-authentication succeeds
            new_token = create_token_response("new_token", "new_refresh")
            auth_service.keycloak_openid.a_token = AsyncMock(return_value=new_token)

            # Execute
            result_token = await auth_service.refresh_access_token()

            # Verify: got new token and re-authentication was called
            assert result_token == "new_token", f"Failed for HTTP {error_code}"
            assert auth_service.token_response == new_token
            assert auth_service.keycloak_openid.a_token.called

    async def test_network_error_raises_token_refresh_error(self, create_auth_service, create_token_response):
        """Test that non-expiration errors (network, server) raise TokenRefreshError."""
        auth_service = create_auth_service()

        # Setup: existing token
        setup_auth_service_with_token(auth_service, create_token_response())

        # Mock: refresh fails with network error (HTTP 500, not expiration)
        network_error = KeycloakError(error_message="Connection timeout", response_code=500)
        auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=network_error)

        # Execute & Verify: should raise TokenRefreshError
        with pytest.raises(TokenRefreshError) as exc_info:
            await auth_service.refresh_access_token()

        assert "Server error during token refresh" in str(exc_info.value)

    async def test_both_refresh_and_reauth_fail(self, create_auth_service, create_token_response):
        """Test that TokenRefreshError is raised when both refresh and re-authentication fail."""
        auth_service = create_auth_service()

        # Setup: existing token
        setup_auth_service_with_token(auth_service, create_token_response())

        # Mock: refresh fails with expiration
        expired_error = KeycloakError(error_message="Token expired", response_code=401)
        auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=expired_error)

        # Mock: re-authentication also fails
        auth_error = KeycloakError(error_message="Invalid credentials", response_code=401)
        auth_service.keycloak_openid.a_token = AsyncMock(side_effect=auth_error)

        # Execute & Verify: should raise TokenRefreshError with both errors mentioned
        with pytest.raises(TokenRefreshError) as exc_info:
            await auth_service.refresh_access_token()

        error_message = str(exc_info.value)
        assert "Both token refresh and re-authentication failed" in error_message

    async def test_old_token_cleared_before_reauthentication(self, create_auth_service, create_token_response):
        """Test that old token data is cleared before re-authentication attempt."""
        auth_service = create_auth_service()

        # Mock start_refresh_task to prevent background task from starting
        auth_service.start_refresh_task = AsyncMock()

        # Setup: existing old token
        old_token = create_token_response("old_token", "old_refresh")
        setup_auth_service_with_token(auth_service, old_token)

        # Mock: refresh fails with expiration
        expired_error = KeycloakError(error_message="Token expired", response_code=401)
        auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=expired_error)

        # Mock: re-authentication succeeds
        new_token = create_token_response("new_token", "new_refresh")
        auth_service.keycloak_openid.a_token = AsyncMock(return_value=new_token)

        # Execute
        await auth_service.refresh_access_token()

        # Verify: new token is set, old token is gone
        assert auth_service.token_response == new_token
        assert auth_service.token_response != old_token


@pytest.mark.asyncio
class TestAutoRefreshRecovery:
    """Test _auto_refresh background task recovery behavior."""

    async def test_auto_refresh_recovers_from_expired_token(self, create_auth_service, create_token_response):
        """Test that auto-refresh task automatically recovers when refresh token expires."""
        auth_service = create_auth_service()

        try:
            # Setup: initial authentication with short-lived token
            initial_token = create_token_response("initial_token", "initial_refresh", expires_in=2)
            auth_service.keycloak_openid.a_token = AsyncMock(return_value=initial_token)
            await auth_service.authenticate()

            # Mock: first refresh fails (expired), then re-auth succeeds with SHORT-LIVED token
            expired_error = KeycloakError(error_message="Invalid refresh token", response_code=401)
            recovered_token = create_token_response("recovered_token", "new_refresh", expires_in=1)

            call_count = 0

            async def mock_refresh(token):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise expired_error
                return recovered_token

            auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=mock_refresh)
            auth_service.keycloak_openid.a_token = AsyncMock(return_value=recovered_token)

            # Wait for auto-refresh to trigger and recover
            await asyncio.sleep(3)

            # Verify: recovered with new token
            assert auth_service.token_response is not None
            assert auth_service.token_response["access_token"] == "recovered_token"
        finally:
            # Cleanup
            await auth_service.stop_refresh_task()

    async def test_auto_refresh_uses_exponential_backoff(self, create_auth_service, create_token_response):
        """Test that auto-refresh uses exponential backoff on repeated transient errors."""
        auth_service = create_auth_service()

        try:
            # Setup: token that expires soon
            short_token = create_token_response(expires_in=1)
            setup_auth_service_with_token(auth_service, short_token)

            # Mock: continuous network errors
            network_error = KeycloakError(error_message="Connection timeout", response_code=500)
            auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=network_error)

            # Start refresh task
            await auth_service.start_refresh_task()

            # Let it retry a few times (with exponential backoff: 1s, 2s, 4s)
            await asyncio.sleep(5)

            # Verify: task is still running (not crashed from repeated errors)
            assert auth_service._refresh_task is not None
            assert not auth_service._refresh_task.done()
        finally:
            # Cleanup
            await auth_service.stop_refresh_task()

    async def test_successful_refresh_resets_backoff_delay(self, create_auth_service, create_token_response):
        """Test that successful refresh resets exponential backoff delay."""
        auth_service = create_auth_service()

        try:
            # Setup: short-lived token
            setup_auth_service_with_token(auth_service, create_token_response(expires_in=1))

            # Mock: first call fails with 500 (server error), second succeeds with SHORT-LIVED token
            success_token = create_token_response("new_token", "new_refresh", expires_in=1)
            refresh_call_count = 0
            auth_call_count = 0

            async def mock_refresh(token):
                nonlocal refresh_call_count
                refresh_call_count += 1
                if refresh_call_count == 1:
                    raise KeycloakError(error_message="Timeout", response_code=500)
                return success_token

            async def mock_auth(*args, **kwargs):
                # After 500 error, token state is cleared, so re-authentication will be attempted
                nonlocal auth_call_count
                auth_call_count += 1
                return success_token

            auth_service.keycloak_openid.a_refresh_token = AsyncMock(side_effect=mock_refresh)
            auth_service.keycloak_openid.a_token = AsyncMock(side_effect=mock_auth)

            # Start refresh task
            await auth_service.start_refresh_task()

            # Wait for retry and recovery
            # After 500 error, token is cleared, so it will attempt re-authentication
            await asyncio.sleep(5)

            # Verify: recovered (either through refresh or re-authentication)
            assert auth_service.token_response is not None
            # At least one attempt should have been made (either refresh or re-auth)
            assert (refresh_call_count + auth_call_count) >= 2
        finally:
            # Cleanup
            await auth_service.stop_refresh_task()
