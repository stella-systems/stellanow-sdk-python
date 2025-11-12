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
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from loguru import logger

from stellanow_sdk_python.authentication.exceptions import AuthenticationError, TokenRefreshError
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import StellaNowEnvironmentConfig
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo


class StellaNowAuthenticationService:
    def __init__(
        self, project_info: StellaProjectInfo, credentials: StellaNowCredentials, env_config: StellaNowEnvironmentConfig
    ):
        if credentials.client_id is None:
            raise ValueError("Client ID is not set.")

        self.env_config = env_config
        self.keycloak_openid = KeycloakOpenID(
            server_url=env_config.authority,
            client_id=credentials.client_id,
            realm_name=str(project_info.organization_id),
            verify=True,
        )
        self.project_info = project_info
        self.credentials = credentials
        self.token_response: Optional[Dict[str, str]] = None
        self.token_expires: Optional[datetime] = None
        self.lock = asyncio.Lock()
        self._refresh_task: Optional[asyncio.Task[None]] = None
        self._token_update_callbacks: list[Callable[[str], Any]] = []  # Callbacks for token updates

    def register_token_update_callback(self, callback: Callable[[str], Any]) -> None:
        """Register a callback to be called when the token is refreshed."""
        self._token_update_callbacks.append(callback)
        logger.debug("Registered token update callback")

    async def start_refresh_task(self) -> None:
        """Start a background task to refresh the token periodically."""
        if self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._auto_refresh())
            logger.info("Started token refresh task.")

    async def stop_refresh_task(self) -> None:
        """Stop the token refresh task."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                logger.info("Token refresh task cancelled.")
            self._refresh_task = None

    async def _auto_refresh(self) -> None:
        """
        Background task that automatically refreshes the access token before expiration.

        This method runs continuously in the background and:
        1. Calculates when the token will expire
        2. Sleeps until 30 seconds before expiration
        3. Refreshes the token using the refresh_token
        4. Falls back to full re-authentication if refresh token is expired
        5. Notifies registered callbacks of the new token
        6. Retries with exponential backoff on transient failures (network errors)

        If no valid token exists, it will retry authentication every second.
        This ensures the SDK always has a valid token for MQTT authentication.
        """
        retry_delay = 1  # Initial retry delay for transient errors
        max_retry_delay = 60  # Cap at 60 seconds

        while True:
            if self.token_response and self.token_expires and not self._is_token_expired():
                logger.debug("In _auto_refresh loop")
                logger.debug(f"Token expired: {self._is_token_expired()}")
                logger.debug(f"Token expires at: {self.token_expires}")
                expires_in = (self.token_expires - datetime.now()).total_seconds()
                await asyncio.sleep(max(expires_in - 30, 1))
            else:
                logger.debug("No valid token to refresh, attempting initial authentication.")
                await asyncio.sleep(1)

            try:
                await self.refresh_access_token()
                # Reset retry delay on success
                retry_delay = 1
            except TokenRefreshError as e:
                # TokenRefreshError means BOTH refresh and re-auth failed
                # This is a critical error - likely credential issue or Keycloak down
                logger.error(f"Critical: Token refresh and re-authentication both failed: {e}")
                if self._is_token_expired():
                    logger.warning("Token is expired, retrying immediately with re-authentication.")
                    # Reset delay for immediate retry
                    retry_delay = 1
                    continue
                # Exponential backoff for transient errors
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            except (ConnectionError, asyncio.TimeoutError) as e:
                # Network errors - use exponential backoff
                logger.error(f"Network error during token refresh: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            except (KeycloakError, ValueError) as e:
                logger.error(f"Unexpected error in auto-refresh: {e}")
                if self._is_token_expired():
                    logger.warning("Token is expired, retrying immediately.")
                    retry_delay = 1
                    continue
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

    async def _authenticate_internal(self) -> str:
        """Internal authentication method that doesn't acquire the lock."""
        try:
            token_response = await self.keycloak_openid.a_token(
                username=self.credentials.username,
                password=self.credentials.password.get_secret_value() if self.credentials.password else None,
            )
            if not isinstance(token_response, dict):
                logger.error(f"Unexpected response type from Keycloak: {type(token_response)}, value: {token_response}")
                raise ValueError(f"Keycloak returned non-dict response: {token_response}")
            if "access_token" not in token_response:
                logger.error(f"Token response missing 'access_token': {token_response}")
                raise ValueError(f"Token response missing 'access_token': {token_response}")
            self.token_response = token_response
            self.token_expires = self._calculate_token_expires_time(self.token_response)
            logger.info("Authentication successful!")
            logger.debug(f"Token expires_in: {token_response.get('expires_in')}, expires at: {self.token_expires}")
            await self.start_refresh_task()
            return self.token_response["access_token"]
        except KeycloakError as e:
            error_status = getattr(e, "response_code", "Unknown")
            error_message = self._format_error_message(e)
            logger.error(f"Keycloak authentication failed: {error_status} - {error_message}")
            logger.debug(f"Full Keycloak error details: {e}")

            # Check if this is a permanent error (invalid credentials, etc.)
            if self._is_permanent_auth_error(e):
                logger.critical(
                    f"Permanent authentication error detected: {error_message}. "
                    "This error requires manual intervention (check credentials, account status, etc.). "
                    "SDK will not retry automatically."
                )
                raise AuthenticationError(
                    f"Permanent authentication failure: {error_status} - {error_message}",
                    error_code=error_status,
                    is_permanent=True,
                ) from None

            # Transient errors (network, server) - raise ValueError for retry
            raise ValueError(f"Failed to authenticate with Keycloak: {error_status} - {error_message}")
        except (ValueError, ConnectionError, asyncio.TimeoutError) as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise ValueError(f"Authentication failed: {e}")

    async def authenticate(self) -> str:
        """Authenticate and get the access token asynchronously."""
        async with self.lock:
            return await self._authenticate_internal()

    @staticmethod
    def _calculate_token_expires_time(token_response: Dict[str, Any]) -> datetime:
        token_expires_time = datetime.now() + timedelta(seconds=token_response.get("expires_in", 60))
        return token_expires_time - timedelta(seconds=10)

    def _is_token_expired(self) -> bool:
        if self.token_expires is None:
            return True
        return datetime.now() >= self.token_expires

    def _extract_error_info(self, error: KeycloakError) -> tuple[Optional[int], str]:
        """Extract error code and lowercase message from KeycloakError."""
        error_code = getattr(error, "response_code", None)
        error_message = self._format_error_message(error).lower()
        return error_code, error_message

    @staticmethod
    def _format_error_message(error: KeycloakError) -> str:
        """Format error message from KeycloakError, handling bytes and multiline messages."""
        raw_message = getattr(error, "error_message", str(error))

        # Handle bytes objects (decode to string)
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8", errors="replace")

        # Convert to string and take first line only
        message = str(raw_message).splitlines()[0] if raw_message else str(error)[:100]

        return message

    def _is_html_response(self, error_message: str) -> bool:
        """Check if error message looks like HTML (proxy/firewall error)."""
        return "<!doctype html>" in error_message or "<html" in error_message

    def _is_credential_error(self, error_message: str, error_code: Optional[int]) -> bool:
        """Check if error indicates credential/grant issues (permanent auth problem)."""
        return error_code == 401 and ("grant" in error_message or "credential" in error_message)

    def _is_permanent_auth_error(self, error: KeycloakError) -> bool:
        """
        Check if a KeycloakError indicates a permanent authentication error.

        Permanent errors include invalid credentials, locked accounts, etc.
        These should NOT be retried automatically.

        Detection strategy:
        - Primary: HTTP status codes (version-independent)
        - Secondary: Generic patterns in error messages (optional hints)
        - Avoids exact string matching to remain compatible with Keycloak upgrades

        Args:
            error: The KeycloakError exception to check

        Returns:
            True if the error is permanent (requires manual intervention), False otherwise
        """
        error_code, error_message = self._extract_error_info(error)

        if self._is_html_response(error_message):
            return False

        if error_code == 401:
            if self._is_credential_error(error_message, error_code):
                return True
            if "disabled" in error_message or "locked" in error_message:
                return True
            if "client" in error_message and ("invalid" in error_message or "unauthorized" in error_message):
                return True
            return False

        if error_code == 403:
            if '"error"' in error_message and any(
                word in error_message for word in ["denied", "forbidden", "insufficient"]
            ):
                return True
            return False

        return False

    def _is_token_expiration_error(self, error: KeycloakError) -> bool:
        """
        Check if a KeycloakError indicates an expired or invalid refresh token.

        Detection strategy:
        - Primary: HTTP status codes (400, 401 = token issues)
        - Secondary: Generic patterns as hints (not exact strings)
        - Designed to work across Keycloak versions

        Args:
            error: The KeycloakError exception to check

        Returns:
            True if the error indicates token expiration/invalidity, False otherwise
        """
        error_code, error_message = self._extract_error_info(error)

        if self._is_credential_error(error_message, error_code):
            return False

        if error_code in [400, 401]:
            return True

        if "token" in error_message and any(word in error_message for word in ["expired", "invalid", "not valid"]):
            return True

        return False

    async def get_access_token(self) -> str:
        if self.token_response is None or self._is_token_expired():
            logger.info("Token expired or missing. Re-authenticating...")
            return await self.authenticate()
        if self.token_response is None:
            raise RuntimeError("Token response is None after authentication check")
        return self.token_response["access_token"]

    async def refresh_access_token(self) -> str:
        async with self.lock:
            if not self.token_response or "refresh_token" not in self.token_response:
                logger.warning("No valid refresh token available, falling back to authenticate.")
                # Call internal method to avoid deadlock (we already hold the lock)
                return await self._authenticate_internal()
            try:
                refresh_token = self.token_response["refresh_token"]
                logger.info("Refreshing access token...")
                self.token_response = await self.keycloak_openid.a_refresh_token(refresh_token)
                self.token_expires = self._calculate_token_expires_time(self.token_response)
                access_token: str = self.token_response["access_token"]
                logger.info("Access token refreshed successfully.")
                logger.debug(f"Token refreshed, expires at: {self.token_expires}")
                for callback in self._token_update_callbacks:
                    try:
                        await callback(access_token)
                    except (RuntimeError, ValueError, ConnectionError) as e:
                        logger.error(f"Token update callback failed: {e}")
                if self.token_response is None:
                    raise RuntimeError("Token response became None after refresh")
                return access_token
            except KeycloakError as e:
                logger.error(f"Failed to refresh access token: {e}")
                if self._is_token_expiration_error(e):
                    error_code = getattr(e, "response_code", "Unknown")
                    logger.warning(
                        f"Refresh token appears to be expired or invalid (HTTP {error_code}). "
                        "Falling back to full re-authentication with username/password."
                    )
                    try:
                        self.token_response = None
                        self.token_expires = None
                        return await self._authenticate_internal()
                    except Exception as auth_error:
                        logger.error(f"Re-authentication also failed: {auth_error}")
                        raise TokenRefreshError(
                            f"Both token refresh and re-authentication failed. "
                            f"Refresh error: {e}, Auth error: {auth_error}"
                        ) from None
                raise TokenRefreshError(f"Failed to refresh access token: {e}") from None
