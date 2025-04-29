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

import os
from typing import Optional
from uuid import UUID

from loguru import logger


def read_env(name: str, missing: Optional[str] = None) -> str:
    """
    Read an environment variable, raising an error if not found and no fallback is provided.

    Args:
        name (str): The name of the environment variable.
        missing (Optional[str]): The fallback value if the variable is not set.

    Returns:
        str: The value of the environment variable or the fallback.

    Raises:
        ValueError: If the variable is not set and no fallback is provided.
    """
    value = os.getenv(name, missing)
    if value is None:
        logger.error(f"Required environment variable '{name}' is not set")
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


def read_env_uuid(name: str) -> UUID:
    """
    Read an environment variable and ensure it is a valid UUID.

    Args:
        name (str): The name of the environment variable.

    Returns:
        UUID: The UUID value of the environment variable.

    Raises:
        ValueError: If the environment variable is not set or is not a valid UUID.
    """
    value = read_env(name)
    try:
        return UUID(value)
    except ValueError:
        logger.error(f"Environment variable '{name}' with value '{value}' is not a valid UUID")
        raise ValueError(f"Environment variable '{name}' with value '{value}' is not a valid UUID")
