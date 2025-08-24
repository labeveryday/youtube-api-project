"""Tests for URL parsing utilities."""

import pytest
from src.youtube_api_server.utils.url_utils import (
    extract_video_id, 
    extract_channel_id, 
    extract_playlist_id,
    parse_youtube_url,
    is_valid_youtube_url,
    normalize_youtube_url
)


class TestVideoIdExtraction:
    """Test video ID extraction from various URL formats."""
    
    def test_standard_watch_url(self):
        """Test standard youtube.com/watch?v= URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_short_url(self):
        """Test youtu.be short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_embed_url(self):
        """Test embed URL format."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_watch_url_with_parameters(self):
        """Test watch URL with additional parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s&list=abc123"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_mobile_url(self):
        """Test mobile YouTube URL."""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_direct_video_id(self):
        """Test direct video ID."""
        video_id = extract_video_id("dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
    
    def test_invalid_video_url(self):
        """Test invalid video URL."""
        video_id = extract_video_id("https://example.com/video")
        assert video_id is None
    
    def test_invalid_video_id_length(self):
        """Test invalid video ID length."""
        video_id = extract_video_id("shortid")
        assert video_id is None


class TestChannelIdExtraction:
    """Test channel ID extraction from various URL formats."""
    
    def test_channel_id_url(self):
        """Test channel ID URL format."""
        url = "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"
        channel_id = extract_channel_id(url)
        assert channel_id == "UCuAXFkgsw1L7xaCfnd5JJOw"
    
    def test_custom_url(self):
        """Test custom channel URL."""
        url = "https://www.youtube.com/c/TechChannel"
        channel_id = extract_channel_id(url)
        assert channel_id == "TechChannel"
    
    def test_user_url(self):
        """Test user URL format."""
        url = "https://www.youtube.com/user/username"
        channel_id = extract_channel_id(url)
        assert channel_id == "username"
    
    def test_handle_url(self):
        """Test handle URL format."""
        url = "https://www.youtube.com/@channelhandle"
        channel_id = extract_channel_id(url)
        assert channel_id == "channelhandle"
    
    def test_direct_channel_id(self):
        """Test direct channel ID."""
        channel_id = extract_channel_id("UCuAXFkgsw1L7xaCfnd5JJOw")
        assert channel_id == "UCuAXFkgsw1L7xaCfnd5JJOw"
    
    def test_invalid_channel_url(self):
        """Test invalid channel URL."""
        channel_id = extract_channel_id("https://example.com/channel")
        assert channel_id is None


class TestPlaylistIdExtraction:
    """Test playlist ID extraction."""
    
    def test_playlist_url(self):
        """Test playlist URL format."""
        url = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        playlist_id = extract_playlist_id(url)
        assert playlist_id == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
    
    def test_watch_url_with_playlist(self):
        """Test watch URL with playlist parameter."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        playlist_id = extract_playlist_id(url)
        assert playlist_id == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
    
    def test_direct_playlist_id(self):
        """Test direct playlist ID."""
        playlist_id = extract_playlist_id("PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME")
        assert playlist_id == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
    
    def test_invalid_playlist_url(self):
        """Test invalid playlist URL."""
        playlist_id = extract_playlist_id("https://example.com/playlist")
        assert playlist_id is None


class TestYouTubeUrlParsing:
    """Test comprehensive YouTube URL parsing."""
    
    def test_parse_video_url(self):
        """Test parsing video URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = parse_youtube_url(url)
        
        assert result["video_id"] == "dQw4w9WgXcQ"
        assert result["url_type"] == "video"
        assert result["channel_id"] is None
        assert result["playlist_id"] is None
    
    def test_parse_channel_url(self):
        """Test parsing channel URL."""
        url = "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"
        result = parse_youtube_url(url)
        
        assert result["channel_id"] == "UCuAXFkgsw1L7xaCfnd5JJOw"
        assert result["url_type"] == "channel"
        assert result["video_id"] is None
        assert result["playlist_id"] is None
    
    def test_parse_playlist_url(self):
        """Test parsing playlist URL."""
        url = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        result = parse_youtube_url(url)
        
        assert result["playlist_id"] == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        assert result["url_type"] == "playlist"
        assert result["video_id"] is None
        assert result["channel_id"] is None
    
    def test_parse_complex_url(self):
        """Test parsing URL with multiple IDs."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        result = parse_youtube_url(url)
        
        assert result["video_id"] == "dQw4w9WgXcQ"
        assert result["playlist_id"] == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        assert result["url_type"] == "video"  # Video takes precedence


class TestYouTubeUrlValidation:
    """Test YouTube URL validation."""
    
    def test_valid_youtube_urls(self):
        """Test valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert is_valid_youtube_url(url), f"URL should be valid: {url}"
    
    def test_invalid_youtube_urls(self):
        """Test invalid YouTube URLs."""
        invalid_urls = [
            "https://example.com/video",
            "https://vimeo.com/123456",
            "not_a_url",
            "https://youtube.com.fake.com/watch?v=123"
        ]
        
        for url in invalid_urls:
            assert not is_valid_youtube_url(url), f"URL should be invalid: {url}"


class TestYouTubeUrlNormalization:
    """Test YouTube URL normalization."""
    
    def test_normalize_video_url(self):
        """Test normalizing video URLs."""
        urls = [
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
        ]
        
        expected = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        for url in urls:
            normalized = normalize_youtube_url(url)
            assert normalized == expected, f"Failed to normalize: {url}"
    
    def test_normalize_channel_url_with_id(self):
        """Test normalizing channel URL with ID."""
        url = "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"
        expected = "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"
        
        normalized = normalize_youtube_url(url)
        assert normalized == expected
    
    def test_normalize_channel_url_with_handle(self):
        """Test normalizing channel URL with handle."""
        url = "https://www.youtube.com/@channelhandle"
        expected = "https://www.youtube.com/@channelhandle"
        
        normalized = normalize_youtube_url(url)
        assert normalized == expected
    
    def test_normalize_playlist_url(self):
        """Test normalizing playlist URL."""
        url = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        expected = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME"
        
        normalized = normalize_youtube_url(url)
        assert normalized == expected
    
    def test_normalize_invalid_url(self):
        """Test normalizing invalid URL."""
        url = "https://example.com/video"
        
        normalized = normalize_youtube_url(url)
        assert normalized is None