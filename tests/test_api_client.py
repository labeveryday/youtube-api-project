"""Tests for YouTube API client."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.youtube_api_server.utils.api_client import YouTubeAPIClient, YouTubeAPIError
from src.youtube_api_server.utils.rate_limiter import AsyncRateLimiter
from src.youtube_api_server.utils.cache import APICache


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
    return settings


@pytest.fixture
def api_client(mock_settings):
    """Create API client for testing."""
    with patch('src.youtube_api_server.utils.api_client.get_settings', return_value=mock_settings):
        with patch('src.youtube_api_server.utils.api_client.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            client = YouTubeAPIClient("test_key")
            client.service = mock_service
            return client


class TestYouTubeAPIClient:
    """Test YouTube API client functionality."""
    
    @pytest.mark.asyncio
    async def test_get_video_details_success(self, api_client):
        """Test successful video details extraction."""
        # Mock API response
        mock_response = {
            "items": [{
                "id": "test_video_id",
                "snippet": {"title": "Test Video"},
                "statistics": {"viewCount": "1000"}
            }]
        }
        
        # Mock the request execution
        mock_request = Mock()
        mock_request.execute = Mock(return_value=mock_response)
        api_client.service.videos().list.return_value = mock_request
        
        # Test the method
        result = await api_client.get_video_details(["test_video_id"])
        
        assert result == mock_response
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "test_video_id"
    
    @pytest.mark.asyncio
    async def test_get_video_details_with_cache(self, api_client):
        """Test video details with caching."""
        # Setup cache
        api_client.cache.set("videos:test_id:snippet,statistics", {"cached": True})
        
        result = await api_client.get_video_details(["test_id"])
        
        assert result == {"cached": True}
        # Verify service wasn't called
        api_client.service.videos().list.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_video_comments_success(self, api_client):
        """Test successful comments extraction."""
        mock_response = {
            "items": [{
                "id": "comment_id",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "textDisplay": "Test comment"
                        }
                    }
                }
            }],
            "nextPageToken": None
        }
        
        mock_request = Mock()
        mock_request.execute = Mock(return_value=mock_response)
        api_client.service.commentThreads().list.return_value = mock_request
        
        result = await api_client.get_video_comments("test_video_id", 10)
        
        assert "items" in result
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_video_comments_disabled(self, api_client):
        """Test comments extraction when comments are disabled."""
        # Mock API error for disabled comments
        mock_request = Mock()
        mock_request.execute = Mock(side_effect=Exception("commentsDisabled"))
        api_client.service.commentThreads().list.return_value = mock_request
        
        result = await api_client.get_video_comments("test_video_id", 10)
        
        assert result["items"] == []
        assert result["pageInfo"]["totalResults"] == 0
    
    @pytest.mark.asyncio
    async def test_search_videos_success(self, api_client):
        """Test successful video search."""
        mock_response = {
            "items": [{
                "id": {"videoId": "search_result_id"},
                "snippet": {"title": "Search Result"}
            }]
        }
        
        mock_request = Mock()
        mock_request.execute = Mock(return_value=mock_response)
        api_client.service.search().list.return_value = mock_request
        
        result = await api_client.search_videos("test query", max_results=10)
        
        assert result == mock_response
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_client):
        """Test rate limiting functionality."""
        # Mock rate limiter
        rate_limiter = Mock()
        rate_limiter.acquire = AsyncMock()
        api_client.rate_limiter = rate_limiter
        
        mock_response = {"items": []}
        mock_request = Mock()
        mock_request.execute = Mock(return_value=mock_response)
        api_client.service.videos().list.return_value = mock_request
        
        await api_client.get_video_details(["test_id"])
        
        # Verify rate limiter was called
        rate_limiter.acquire.assert_called_once()
    
    def test_client_stats(self, api_client):
        """Test client statistics."""
        stats = api_client.get_client_stats()
        
        assert "rate_limiter" in stats
        assert "cache" in stats


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_acquire_within_limits(self):
        """Test acquiring within rate limits."""
        limiter = AsyncRateLimiter(requests_per_second=10, daily_limit=1000)
        
        # Should not block
        await limiter.acquire()
        
        stats = limiter.get_stats()
        assert stats["current_window_requests"] == 1
        assert stats["daily_requests_made"] == 1
    
    @pytest.mark.asyncio
    async def test_daily_limit_exceeded(self):
        """Test daily limit exceeded."""
        limiter = AsyncRateLimiter(requests_per_second=10, daily_limit=1)
        
        # First request should succeed
        await limiter.acquire()
        
        # Second request should fail
        with pytest.raises(Exception, match="Daily API quota limit"):
            await limiter.acquire()
    
    def test_get_stats(self):
        """Test rate limiter statistics."""
        limiter = AsyncRateLimiter(requests_per_second=5, daily_limit=100)
        
        stats = limiter.get_stats()
        
        assert stats["requests_per_second_limit"] == 5
        assert stats["daily_limit"] == 100
        assert stats["current_window_requests"] == 0
        assert stats["daily_requests_made"] == 0


class TestAPICache:
    """Test API cache functionality."""
    
    def test_cache_set_get(self):
        """Test basic cache set/get operations."""
        cache = APICache(max_size=10, ttl=60)
        
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        
        assert result == {"data": "value"}
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = APICache(max_size=10, ttl=60)
        
        result = cache.get("nonexistent_key")
        
        assert result is None
    
    def test_cache_disabled(self):
        """Test cache when disabled."""
        cache = APICache(max_size=10, ttl=60)
        cache.disable()
        
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        
        assert result is None
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = APICache(max_size=10, ttl=60)
        
        cache.set("test_key", {"data": "value"})
        cache.clear()
        result = cache.get("test_key")
        
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = APICache(max_size=10, ttl=60)
        
        cache.set("test_key", {"data": "value"})
        cache.get("test_key")  # Hit
        cache.get("missing_key")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit out of 2 requests
    
    def test_create_key(self):
        """Test cache key creation."""
        cache = APICache(max_size=10, ttl=60)
        
        key = cache.create_key("videos", "abc123", "snippet")
        
        assert key == "videos:abc123:snippet"