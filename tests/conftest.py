"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.youtube_api_key = "test_api_key"
    settings.youtube_api_version = "v3"
    settings.requests_per_second = 10.0
    settings.daily_quota_limit = 10000
    settings.cache_enabled = True
    settings.cache_max_size = 100
    settings.cache_ttl = 3600
    settings.enable_ytdlp_fallback = True
    settings.ytdlp_rate_limit = "500K"
    settings.log_level = "INFO"
    return settings