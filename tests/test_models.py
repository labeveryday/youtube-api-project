"""Tests for Pydantic models."""

import pytest
from datetime import datetime
from src.youtube_api_server.models.video import VideoInfo, VideoStatistics, VideoSnippet, VideoContentDetails
from src.youtube_api_server.models.comment import CommentThread, CommentSnippet, Comment
from src.youtube_api_server.models.channel import ChannelInfo, ChannelStatistics, ChannelSnippet
from src.youtube_api_server.models.transcript import TranscriptInfo, TranscriptSegment


class TestVideoModels:
    """Test video-related models."""
    
    def test_video_statistics_parsing(self):
        """Test video statistics string to int conversion."""
        data = {
            "viewCount": "1000000",
            "likeCount": "50000",
            "commentCount": "1500"
        }
        
        stats = VideoStatistics(**data)
        
        assert stats.view_count == 1000000
        assert stats.like_count == 50000
        assert stats.comment_count == 1500
    
    def test_video_content_details_duration(self):
        """Test duration parsing and formatting."""
        data = {
            "duration": "PT1H2M3S"
        }
        
        details = VideoContentDetails(**data)
        
        assert details.get_duration_seconds() == 3723  # 1*3600 + 2*60 + 3
        assert details.get_duration_formatted() == "01:02:03"
    
    def test_video_content_details_short_duration(self):
        """Test short duration formatting."""
        data = {
            "duration": "PT5M30S"
        }
        
        details = VideoContentDetails(**data)
        
        assert details.get_duration_seconds() == 330
        assert details.get_duration_formatted() == "05:30"
    
    def test_video_info_engagement_rate(self):
        """Test engagement rate calculation."""
        video_data = {
            "kind": "youtube#video",
            "etag": "test",
            "id": "test_id",
            "statistics": {
                "viewCount": "1000",
                "likeCount": "100",
                "commentCount": "50"
            }
        }
        
        video = VideoInfo(**video_data)
        
        engagement_rate = video.get_engagement_rate()
        assert engagement_rate == 15.0  # (100 + 50) / 1000 * 100
    
    def test_video_info_like_ratio(self):
        """Test like ratio calculation."""
        video_data = {
            "kind": "youtube#video",
            "etag": "test",
            "id": "test_id",
            "statistics": {
                "likeCount": "900",
                "dislikeCount": "100"
            }
        }
        
        video = VideoInfo(**video_data)
        
        like_ratio = video.get_like_ratio()
        assert like_ratio == 90.0  # 900 / (900 + 100) * 100
    
    def test_video_info_to_dict(self):
        """Test video info dictionary conversion."""
        video_data = {
            "kind": "youtube#video",
            "etag": "test",
            "id": "test_video_id",
            "snippet": {
                "publishedAt": "2024-01-01T00:00:00Z",
                "channelId": "test_channel_id",
                "title": "Test Video",
                "description": "Test description",
                "thumbnails": {"default": {"url": "test.jpg"}},
                "channelTitle": "Test Channel"
            },
            "statistics": {
                "viewCount": "1000",
                "likeCount": "100"
            }
        }
        
        video = VideoInfo(**video_data)
        result = video.to_dict()
        
        assert result["id"] == "test_video_id"
        assert result["title"] == "Test Video"
        assert result["channel"] == "Test Channel"
        assert result["statistics"]["view_count"] == 1000
        assert result["engagement_rate"] == 10.0


class TestCommentModels:
    """Test comment-related models."""
    
    def test_comment_snippet_parsing(self):
        """Test comment snippet data parsing."""
        data = {
            "textDisplay": "Great video!",
            "textOriginal": "Great video!",
            "authorDisplayName": "Test User",
            "authorProfileImageUrl": "profile.jpg",
            "canRate": True,
            "totalReplyCount": "5",
            "likeCount": "10",
            "publishedAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }
        
        snippet = CommentSnippet(**data)
        
        assert snippet.text_display == "Great video!"
        assert snippet.author_display_name == "Test User"
        assert snippet.total_reply_count == 5
        assert snippet.like_count == 10
        assert isinstance(snippet.published_at, datetime)
    
    def test_comment_to_dict(self):
        """Test comment dictionary conversion."""
        comment_data = {
            "kind": "youtube#comment",
            "etag": "test",
            "id": "comment_id",
            "snippet": {
                "textDisplay": "Test comment",
                "textOriginal": "Test comment",
                "authorDisplayName": "Test Author",
                "authorProfileImageUrl": "profile.jpg",
                "canRate": True,
                "totalReplyCount": 0,
                "likeCount": 5,
                "publishedAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z"
            }
        }
        
        comment = Comment(**comment_data)
        result = comment.to_dict()
        
        assert result["id"] == "comment_id"
        assert result["author"] == "Test Author"
        assert result["text"] == "Test comment"
        assert result["likes"] == 5
        assert result["is_reply"] == False


class TestChannelModels:
    """Test channel-related models."""
    
    def test_channel_statistics_parsing(self):
        """Test channel statistics parsing."""
        data = {
            "viewCount": "1000000",
            "subscriberCount": "50000",
            "videoCount": "100"
        }
        
        stats = ChannelStatistics(**data)
        
        assert stats.view_count == 1000000
        assert stats.subscriber_count == 50000
        assert stats.video_count == 100
    
    def test_channel_subscriber_tier(self):
        """Test channel subscriber tier calculation."""
        channel_data = {
            "kind": "youtube#channel",
            "etag": "test",
            "id": "channel_id",
            "statistics": {
                "subscriberCount": "1500000"
            }
        }
        
        channel = ChannelInfo(**channel_data)
        tier = channel.get_subscriber_tier()
        
        assert "1M+ (Gold)" in tier
    
    def test_channel_engagement_metrics(self):
        """Test channel engagement metrics calculation."""
        channel_data = {
            "kind": "youtube#channel",
            "etag": "test",
            "id": "channel_id",
            "statistics": {
                "viewCount": "1000000",
                "subscriberCount": "10000",
                "videoCount": "100"
            }
        }
        
        channel = ChannelInfo(**channel_data)
        metrics = channel.get_engagement_metrics()
        
        assert metrics["avg_views_per_video"] == 10000
        assert metrics["subscribers_per_video"] == 100.0
    
    def test_channel_keywords_list(self):
        """Test channel keywords parsing."""
        snippet_data = {
            "title": "Test Channel",
            "description": "Test description",
            "publishedAt": "2024-01-01T00:00:00Z",
            "thumbnails": {},
            "keywords": '"tech" "programming" "tutorials"'
        }
        
        snippet = ChannelSnippet(**snippet_data)
        keywords = snippet.get_keywords_list()
        
        assert keywords == ["tech", "programming", "tutorials"]


class TestTranscriptModels:
    """Test transcript-related models."""
    
    def test_transcript_segment_time_calculation(self):
        """Test transcript segment time calculations."""
        data = {
            "text": "Hello world",
            "start": 10.5,
            "duration": 2.5
        }
        
        segment = TranscriptSegment(**data)
        
        assert segment.end == 13.0
        assert segment.get_formatted_time() == "00:10"
    
    def test_transcript_segment_long_time(self):
        """Test transcript segment with hours."""
        data = {
            "text": "Long video segment",
            "start": 3665,  # 1 hour, 1 minute, 5 seconds
            "duration": 5
        }
        
        segment = TranscriptSegment(**data)
        
        assert segment.get_formatted_time() == "01:01:05"
    
    def test_transcript_info_full_text(self):
        """Test transcript full text generation."""
        segments = [
            TranscriptSegment(text="Hello", start=0, duration=1),
            TranscriptSegment(text="world", start=1, duration=1),
            TranscriptSegment(text="!", start=2, duration=1)
        ]
        
        transcript = TranscriptInfo(
            video_id="test_id",
            segments=segments
        )
        
        full_text = transcript.get_full_text()
        assert full_text == "Hello world !"
        
        full_text_with_timestamps = transcript.get_full_text(include_timestamps=True)
        assert "[00:00] Hello" in full_text_with_timestamps
    
    def test_transcript_search_text(self):
        """Test transcript text search."""
        segments = [
            TranscriptSegment(text="Hello world", start=0, duration=2),
            TranscriptSegment(text="How are you?", start=2, duration=2),
            TranscriptSegment(text="Hello again", start=4, duration=2)
        ]
        
        transcript = TranscriptInfo(
            video_id="test_id",
            segments=segments
        )
        
        matches = transcript.search_text("hello", case_sensitive=False)
        assert len(matches) == 2
        
        matches = transcript.search_text("Hello", case_sensitive=True)
        assert len(matches) == 2
    
    def test_transcript_segments_in_range(self):
        """Test getting transcript segments in time range."""
        segments = [
            TranscriptSegment(text="First", start=0, duration=2),
            TranscriptSegment(text="Second", start=2, duration=2),
            TranscriptSegment(text="Third", start=4, duration=2)
        ]
        
        transcript = TranscriptInfo(
            video_id="test_id",
            segments=segments
        )
        
        range_segments = transcript.get_segments_in_range(1.5, 4.5)
        assert len(range_segments) == 1
        assert range_segments[0].text == "Second"
    
    def test_transcript_to_dict(self):
        """Test transcript dictionary conversion."""
        segments = [
            TranscriptSegment(text="Test", start=0, duration=1)
        ]
        
        transcript = TranscriptInfo(
            video_id="test_video",
            language="en",
            is_generated=False,
            segments=segments
        )
        
        result = transcript.to_dict()
        
        assert result["video_id"] == "test_video"
        assert result["language"] == "en"
        assert result["is_generated"] == False
        assert len(result["segments"]) == 1
        assert result["full_text"] == "Test"
        assert result["total_segments"] == 1