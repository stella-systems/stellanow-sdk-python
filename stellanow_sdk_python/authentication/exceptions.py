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


class TokenRefreshError(Exception):
    """
    Raised when token refresh operation fails.

    This exception indicates that both:
    1. Refresh token refresh failed (e.g., expired refresh token)
    2. Fallback to full re-authentication also failed

    This is a critical error that typically requires manual intervention,
    such as updating credentials or checking Keycloak availability.
    """


class AuthenticationError(Exception):
    """
    Raised when authentication fails due to permanent errors.

    This exception indicates a non-recoverable authentication error, such as:
    - Invalid username/password (HTTP 401 with invalid_grant)
    - Invalid client credentials
    - User account locked/disabled

    These errors should NOT be retried automatically as they require
    manual intervention (updating credentials, unlocking account, etc.).
    """

    def __init__(self, message: str, error_code: int | None = None, is_permanent: bool = True):
        super().__init__(message)
        self.error_code = error_code
        self.is_permanent = is_permanent
