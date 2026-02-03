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
from uuid import UUID

import pytest

from stellanow_sdk_python.authentication.auth_service import StellaNowAuthenticationService
from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig
from stellanow_sdk_python.config.stellanow_auth_credentials import StellaNowCredentials
from stellanow_sdk_python.config.stellanow_config import StellaProjectInfo

# Test constants
TEST_ORG_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_PROJECT_ID = UUID("87654321-4321-8765-4321-876543218765")
TEST_CLIENT_ID = "test-client"
TEST_USERNAME = "test-user"
TEST_PASSWORD = "test-pass"


@pytest.fixture
def create_auth_service():
    """Factory fixture for creating auth service instances.

    Returns a factory function that creates StellaNowAuthenticationService instances
    with standard test configuration. Use this to avoid duplicating auth service
    creation logic across test files.

    Usage:
        def test_something(create_auth_service):
            auth_service = create_auth_service()
            # ... test code
    """
    def _create() -> StellaNowAuthenticationService:
        project_info = StellaProjectInfo(organization_id=TEST_ORG_ID, project_id=TEST_PROJECT_ID)
        credentials = StellaNowCredentials(client_id=TEST_CLIENT_ID, username=TEST_USERNAME, password=TEST_PASSWORD)
        env_config = EnvConfig.stellanow_dev()
        return StellaNowAuthenticationService(project_info=project_info, credentials=credentials, env_config=env_config)
    return _create


@pytest.fixture
def create_token_response():
    """Factory fixture for creating token response dictionaries.

    Returns a factory function that creates standard Keycloak token response dicts.

    Usage:
        def test_something(create_token_response):
            token = create_token_response("my_token", "my_refresh", expires_in=600)
            # ... test code
    """
    def _create(access_token: str = "test_token", refresh_token: str = "test_refresh", expires_in: int = 300):
        return {"access_token": access_token, "refresh_token": refresh_token, "expires_in": expires_in}
    return _create


@pytest.fixture(autouse=True)
async def cleanup_sdk():
    """Fixture to clean up SDK and message queue tasks after each test."""
    yield

    # Cancel all tasks except the current one
    current_task = asyncio.current_task()
    tasks_to_cancel = [task for task in asyncio.all_tasks() if task is not current_task and not task.done()]

    if tasks_to_cancel:
        for task in tasks_to_cancel:
            task.cancel()

        # Wait for all tasks to be cancelled with a timeout
        await asyncio.gather(*tasks_to_cancel, return_exceptions=True)