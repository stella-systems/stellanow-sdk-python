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

import pytest

from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import _StellaNowEnvironmentConfigImpl


class TestApiBaseUrlValidation:
    """Tests for api_base_url validation."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        config = _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="https://api.example.com")

        assert config.api_base_url == "https://api.example.com"
        assert config.authority == "https://api.example.com/auth/"

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        config = _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="http://api.example.com")

        assert config.api_base_url == "http://api.example.com"
        assert config.authority == "http://api.example.com/auth/"

    def test_valid_http_url_with_slash(self):
        """Test that valid HTTP URLs are accepted."""
        config = _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="http://api.example.com/")

        assert config.api_base_url == "http://api.example.com"
        assert config.authority == "http://api.example.com/auth/"

    def test_authority_with_none_api_base_url_raises_runtime_error(self):
        """Test that accessing authority with None api_base_url raises RuntimeError with helpful message."""
        config = _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url=None)

        with pytest.raises(RuntimeError) as exc_info:
            _ = config.authority

        error_message = str(exc_info.value)
        assert "api_base_url is not configured" in error_message
        assert "OIDC authentication requires api_base_url" in error_message
        assert "EnvConfig.stellanow_prod()" in error_message
        assert "EnvConfig.stellanow_dev()" in error_message


class TestApiBaseUrlInvalidFormats:
    """Tests for invalid api_base_url formats."""

    def test_url_without_http_scheme_raises_value_error(self):
        """Test that URLs without http:// or https:// raise ValueError."""
        with pytest.raises(ValueError, match="must start with http:// or https://"):
            _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="api.example.com")

    def test_url_with_ftp_scheme_raises_value_error(self):
        """Test that FTP URLs raise ValueError."""
        with pytest.raises(ValueError, match="must start with http:// or https://"):
            _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="ftp://api.example.com")

    def test_empty_string_raises_value_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="must start with http:// or https://"):
            _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url="")


class TestPredefinedConfigurations:
    """Tests for predefined environment configurations."""

    def test_stellanow_prod_has_api_base_url(self):
        """Test that stellanow_prod configuration includes api_base_url."""
        from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig

        config = EnvConfig.stellanow_prod()

        assert config.api_base_url is not None
        assert config.api_base_url.startswith("https://")
        # Should not raise error
        _ = config.authority

    def test_stellanow_dev_has_api_base_url(self):
        """Test that stellanow_dev configuration includes api_base_url."""
        from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig

        config = EnvConfig.stellanow_dev()

        assert config.api_base_url is not None
        assert config.api_base_url.startswith("https://")
        # Should not raise error
        _ = config.authority

    def test_nanomq_local_has_no_api_base_url(self):
        """Test that nanomq_local configuration has no api_base_url."""
        from stellanow_sdk_python.config.eniviroment_config.stellanow_env_config import EnvConfig

        config = EnvConfig.nanomq_local()

        assert config.api_base_url is None
        # Accessing authority should raise error
        with pytest.raises(RuntimeError):
            _ = config.authority


class TestAuthorityProperty:
    """Tests for authority property."""

    def test_authority_appends_auth_path(self):
        """Test that authority correctly appends /auth/ to api_base_url for various URL formats."""
        test_cases = [
            ("https://api.example.com", "https://api.example.com/auth/"),
            ("https://api.example.com:8443", "https://api.example.com:8443/auth/"),
            ("https://auth.api.example.com", "https://auth.api.example.com/auth/"),
        ]

        for api_base_url, expected_authority in test_cases:
            config = _StellaNowEnvironmentConfigImpl(mqtt_url="mqtt://localhost:1883", api_base_url=api_base_url)
            assert config.authority == expected_authority
