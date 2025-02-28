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
from urllib.parse import urljoin

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from loguru import logger

from stellanow_sdk_python.settings import API_KEY, API_SECRET, AUTH_BASE_URL, OIDC_CLIENT_ID, ORGANIZATION_ID


def get_auth_url(base_url: str, realm_id: str) -> str:
    base_url = base_url.rstrip("/") + "/"  # Ensure trailing slash for urljoin
    return urljoin(base_url, f"realms/{realm_id}/protocol/openid-connect/token")


class StellaNowAuthenticationService:
    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=AUTH_BASE_URL,
            client_id=OIDC_CLIENT_ID,
            realm_name=ORGANIZATION_ID,
            verify=True,
        )
        self.token_response = None
        self.token_expires = None
        self.lock = asyncio.Lock()

    async def authenticate(self):
        """
        Authenticate and get the access token asynchronously
        """
        async with self.lock:
            try:
                self.token_response = await self.keycloak_openid.a_token(username=API_KEY, password=API_SECRET)
                self.token_expires = self._calculate_token_expires_time(self.token_response)
                logger.info("Authentication successful!")
                return self.token_response["access_token"]
            except KeycloakError as e:
                logger.error(f"Keycloak authentication error: {e}")
                raise Exception("Failed to authenticate with Keycloak")

    def _calculate_token_expires_time(self, token_response):
        token_expires_time = datetime.now() + timedelta(seconds=token_response.get("expires_in", 60))
        return token_expires_time - timedelta(seconds=10)  # 10 seconds buffer

    def _is_token_expired(self):
        """
        Check if the access token is expired or about to expire
        """
        return datetime.now() >= self.token_expires

    async def get_access_token(self):
        """
        Get the access token, refreshing it if necessary
        """
        if self.token_response is None or self._is_token_expired():
            logger.info("Token expired or missing. Re-authenticating...")
            return await self.authenticate()

        return self.token_response["access_token"]

    async def refresh_access_token(self):
        """
        Refresh the access token asynchronously using the refresh token
        """
        async with self.lock:
            try:
                refresh_token = self.token_response.get("refresh_token")
                if not refresh_token:
                    logger.error("No refresh token available.")
                    raise Exception("No refresh token available.")

                logger.info("Refreshing access token...")
                self.token_response = await self.keycloak_openid.a_refresh_token(refresh_token)
                self.token_expires = self._calculate_token_expires_time(self.token_response)
                logger.info("Access token refreshed successfully.")
                return self.token_response["access_token"]
            except KeycloakError as e:
                logger.error(f"Failed to refresh access token: {e}")
                raise Exception("Failed to refresh access token")
