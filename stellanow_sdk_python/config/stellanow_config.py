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

from stellanow_sdk_python.config.read_env import read_env


class StellaProjectInfo:
    """Holds organization and project identifiers for the StellaNow SDK."""

    def __init__(self, organization_id: str, project_id: str):
        if not organization_id or not project_id:
            raise ValueError("organization_id and project_id must be non-empty strings")
        self.organization_id = organization_id
        self.project_id = project_id


def project_info_from_env() -> StellaProjectInfo:
    """Create a StellaProjectInfo instance from environment variables."""
    return StellaProjectInfo(organization_id=read_env("ORGANIZATION_ID"), project_id=read_env("PROJECT_ID"))
