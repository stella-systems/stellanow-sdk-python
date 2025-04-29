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
        """Periodically refresh the token before it expires."""
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
            except Exception as e:
                logger.error(f"Failed to auto-refresh token: {e}")
                if self._is_token_expired():
                    logger.warning("Token is expired, retrying immediately.")
                    continue
                await asyncio.sleep(15)

    async def authenticate(self) -> str:
        """Authenticate and get the access token asynchronously."""
        async with self.lock:
            try:
                token_response = await self.keycloak_openid.a_token(
                    username=self.credentials.username, password=self.credentials.password  # type: ignore[arg-type]
                )
                if not isinstance(token_response, dict):
                    logger.error(
                        f"Unexpected response type from Keycloak: {type(token_response)}, value: {token_response}"
                    )
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
                error_message = (
                    getattr(e, "error_message", str(e)).splitlines()[0] if hasattr(e, "error_message") else str(e)[:100]
                )
                logger.error(f"Keycloak authentication failed: {error_status} - {error_message}")
                logger.debug(f"Full Keycloak error details: {e}")
                raise Exception(f"Failed to authenticate with Keycloak: {error_status} - {error_message}")
            except Exception as e:
                logger.error(f"Unexpected authentication error: {e}")
                raise Exception(f"Authentication failed: {e}")

    @staticmethod
    def _calculate_token_expires_time(token_response: Dict[str, Any]) -> datetime:
        token_expires_time = datetime.now() + timedelta(seconds=token_response.get("expires_in", 60))
        return token_expires_time - timedelta(seconds=10)

    def _is_token_expired(self) -> bool:
        if self.token_expires is None:
            return True
        return datetime.now() >= self.token_expires

    async def get_access_token(self) -> str:
        if self.token_response is None or self._is_token_expired():
            logger.info("Token expired or missing. Re-authenticating...")
            return await self.authenticate()
        assert self.token_response is not None
        return self.token_response["access_token"]

    async def refresh_access_token(self) -> str:
        async with self.lock:
            if not self.token_response or "refresh_token" not in self.token_response:
                logger.warning("No valid refresh token available, falling back to authenticate.")
                return await self.authenticate()
            try:
                refresh_token = self.token_response["refresh_token"]
                logger.info("Refreshing access token...")
                self.token_response = await self.keycloak_openid.a_refresh_token(refresh_token)
                self.token_expires = self._calculate_token_expires_time(self.token_response)
                access_token: str = self.token_response["access_token"]
                logger.info("Access token refreshed successfully.")
                logger.debug(f"Refreshed token: {access_token[:20]}..., expires: {self.token_expires}")
                # Notify callbacks of new token
                for callback in self._token_update_callbacks:
                    try:
                        await callback(access_token)
                    except Exception as e:
                        logger.error(f"Token update callback failed: {e}")
                assert self.token_response is not None
                return access_token
            except KeycloakError as e:
                logger.error(f"Failed to refresh access token: {e}")
                raise Exception("Failed to refresh access token")
