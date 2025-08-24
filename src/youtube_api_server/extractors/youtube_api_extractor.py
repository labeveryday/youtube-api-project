"""Main YouTube API extractor class."""

import logging
from typing import Dict, List, Optional, Any, Union

from ..config.settings import get_settings
from ..utils.api_client import YouTubeAPIClient, YouTubeAPIError
from ..utils.url_utils import extract_video_id, extract_channel_id, extract_playlist_id, parse_youtube_url
from ..models.video import VideoInfo
from ..models.channel import ChannelInfo, ChannelListResponse
from ..models.comment import CommentThreadListResponse
from ..models.search import SearchListResponse
from ..models.transcript import TranscriptInfo


logger = logging.getLogger(__name__)


class YouTubeAPIExtractor:
    """Main extractor class using YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_client = YouTubeAPIClient(api_key)
        self._transcript_extractor = None  # Lazy load yt-dlp
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive video information using YouTube Data API v3."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube video URL: {url}")
        
        try:
            # Get video details from API
            response = await self.api_client.get_video_details([video_id])
            
            if not response.get("items"):
                raise ValueError(f"Video not found: {video_id}")
            
            # Parse response into our model
            video_data = response["items"][0]
            video_info = VideoInfo(**video_data)
            
            logger.info(f"Successfully extracted video info for {video_id}")
            return video_info.to_dict()
            
        except YouTubeAPIError as e:
            logger.error(f"YouTube API error extracting video {video_id}: {e}")
            raise RuntimeError(f"Failed to extract video info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting video {video_id}: {e}")
            raise RuntimeError(f"Failed to extract video info: {e}")
    
    async def get_video_comments(self, url: str, max_comments: int = 100) -> Dict[str, Any]:
        """Extract video comments using YouTube Data API - highly reliable!"""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube video URL: {url}")
        
        try:
            # Get comments from API
            response = await self.api_client.get_video_comments(
                video_id, 
                max_results=max_comments,
                order="relevance"
            )
            
            # Parse response into our model
            comment_response = CommentThreadListResponse(**response)
            
            logger.info(f"Successfully extracted {len(comment_response.items)} comments for {video_id}")
            return comment_response.to_dict()
            
        except YouTubeAPIError as e:
            logger.error(f"YouTube API error extracting comments for {video_id}: {e}")
            raise RuntimeError(f"Failed to extract comments: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting comments for {video_id}: {e}")
            raise RuntimeError(f"Failed to extract comments: {e}")
    
    async def get_channel_info(self, url: str) -> Dict[str, Any]:
        """Extract channel information using YouTube Data API v3."""
        channel_id = extract_channel_id(url)
        if not channel_id:
            raise ValueError(f"Invalid YouTube channel URL: {url}")
        
        # If it's not a direct channel ID, we need to resolve it
        if not channel_id.startswith('UC'):
            # For custom URLs/handles, we need to search first
            search_response = await self.api_client.search_videos(
                query=channel_id,
                max_results=1,
                search_type="channel"
            )
            
            if search_response.get("items"):
                channel_id = search_response["items"][0]["snippet"]["channelId"]
            else:
                raise ValueError(f"Channel not found: {url}")
        
        try:
            # Get channel details from API
            response = await self.api_client.get_channel_details(channel_id)
            
            if not response.get("items"):
                raise ValueError(f"Channel not found: {channel_id}")
            
            # Parse response into our model
            channel_data = response["items"][0]
            channel_info = ChannelInfo(**channel_data)
            
            logger.info(f"Successfully extracted channel info for {channel_id}")
            return channel_info.to_dict()
            
        except YouTubeAPIError as e:
            logger.error(f"YouTube API error extracting channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to extract channel info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting channel {channel_id}: {e}")
            raise RuntimeError(f"Failed to extract channel info: {e}")
    
    async def search_youtube(self, query: str, search_type: str = "video", max_results: int = 20) -> Dict[str, Any]:
        """Search YouTube for videos, channels, or playlists."""
        try:
            # Perform search using API
            response = await self.api_client.search_videos(
                query=query,
                max_results=max_results,
                search_type=search_type
            )
            
            # Parse response into our model
            search_response = SearchListResponse(**response)
            
            logger.info(f"Successfully performed search: '{query}' ({search_type}) - {len(search_response.items)} results")
            return search_response.to_dict()
            
        except YouTubeAPIError as e:
            logger.error(f"YouTube API error searching '{query}': {e}")
            raise RuntimeError(f"Failed to search YouTube: {e}")
        except Exception as e:
            logger.error(f"Unexpected error searching '{query}': {e}")
            raise RuntimeError(f"Failed to search YouTube: {e}")
    
    async def get_playlist_info(self, url: str) -> Dict[str, Any]:
        """Extract playlist information using YouTube Data API v3."""
        playlist_id = extract_playlist_id(url)
        if not playlist_id:
            raise ValueError(f"Invalid YouTube playlist URL: {url}")
        
        try:
            # Get playlist details
            playlist_response = await self.api_client.get_playlist_details(playlist_id)
            if not playlist_response.get("items"):
                raise ValueError(f"Playlist not found: {playlist_id}")
            
            playlist_data = playlist_response["items"][0]
            
            # Get playlist videos
            videos_response = await self.api_client.get_playlist_videos(playlist_id, max_results=100)
            
            # Combine data
            result = {
                "id": playlist_id,
                "url": f"https://www.youtube.com/playlist?list={playlist_id}",
                "title": playlist_data["snippet"]["title"],
                "description": playlist_data["snippet"]["description"],
                "channel_id": playlist_data["snippet"]["channelId"],
                "channel_title": playlist_data["snippet"]["channelTitle"],
                "published_at": playlist_data["snippet"]["publishedAt"],
                "thumbnails": playlist_data["snippet"]["thumbnails"],
                "video_count": playlist_data["contentDetails"]["itemCount"],
                "privacy_status": playlist_data.get("status", {}).get("privacyStatus"),
                "videos": [
                    {
                        "video_id": item["contentDetails"]["videoId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "channel_title": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnails": item["snippet"]["thumbnails"],
                        "position": item["snippet"]["position"]
                    }
                    for item in videos_response.get("items", [])
                ],
                "metadata": {
                    "api_source": "YouTube Data API v3",
                    "reliable": True
                }
            }
            
            logger.info(f"Successfully extracted playlist info for {playlist_id}")
            return result
            
        except YouTubeAPIError as e:
            logger.error(f"YouTube API error extracting playlist {playlist_id}: {e}")
            raise RuntimeError(f"Failed to extract playlist info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting playlist {playlist_id}: {e}")
            raise RuntimeError(f"Failed to extract playlist info: {e}")
    
    async def get_video_transcript(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video transcript using yt-dlp fallback (API doesn't support transcripts)."""
        if not self.settings.enable_ytdlp_fallback:
            logger.warning("yt-dlp fallback is disabled, cannot extract transcripts")
            return None
        
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube video URL: {url}")
        
        # Lazy load the transcript extractor
        if self._transcript_extractor is None:
            try:
                from .transcript_extractor import TranscriptExtractor
                self._transcript_extractor = TranscriptExtractor()
            except ImportError as e:
                logger.error(f"Failed to import yt-dlp transcript extractor: {e}")
                return None
        
        try:
            transcript_data = await self._transcript_extractor.extract_transcript(url)
            if transcript_data:
                logger.info(f"Successfully extracted transcript for {video_id} using yt-dlp")
            return transcript_data
            
        except Exception as e:
            logger.warning(f"Failed to extract transcript for {video_id}: {e}")
            return None
    
    async def search_transcript(self, url: str, query: str, case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for specific text within a video's transcript."""
        transcript_data = await self.get_video_transcript(url)
        
        if not transcript_data:
            return {
                "video_id": extract_video_id(url),
                "query": query,
                "matches": [],
                "total_matches": 0,
                "error": "No transcript available"
            }
        
        # Parse transcript and search
        transcript = TranscriptInfo(**transcript_data)
        matches = transcript.search_text(query, case_sensitive)
        
        return {
            "video_id": transcript.video_id,
            "query": query,
            "case_sensitive": case_sensitive,
            "matches": [match.to_dict() for match in matches],
            "total_matches": len(matches),
            "metadata": {
                "source": "yt-dlp",
                "transcript_language": transcript.language
            }
        }
    
    async def analyze_video_engagement(self, url: str) -> Dict[str, Any]:
        """Analyze video engagement metrics with industry benchmarks."""
        video_info = await self.get_video_info(url)
        
        if not video_info.get("statistics"):
            return {
                "video_id": video_info["id"],
                "error": "No statistics available for engagement analysis"
            }
        
        stats = video_info["statistics"]
        
        # Calculate engagement metrics
        views = stats.get("view_count", 0)
        likes = stats.get("like_count", 0)
        comments = stats.get("comment_count", 0)
        
        engagement_rate = video_info.get("engagement_rate", 0)
        like_ratio = video_info.get("like_ratio", 0)
        
        # Industry benchmarks (rough estimates)
        benchmarks = {
            "excellent_engagement": 10.0,  # 10%+
            "good_engagement": 5.0,        # 5-10%
            "average_engagement": 2.0,     # 2-5%
            "poor_engagement": 2.0         # <2%
        }
        
        # Determine engagement level
        if engagement_rate >= benchmarks["excellent_engagement"]:
            engagement_level = "Excellent"
        elif engagement_rate >= benchmarks["good_engagement"]:
            engagement_level = "Good"
        elif engagement_rate >= benchmarks["average_engagement"]:
            engagement_level = "Average"
        else:
            engagement_level = "Below Average"
        
        return {
            "video_id": video_info["id"],
            "title": video_info["title"],
            "engagement_analysis": {
                "engagement_rate": engagement_rate,
                "like_ratio": like_ratio,
                "engagement_level": engagement_level,
                "total_interactions": likes + comments,
                "views_per_like": round(views / likes, 2) if likes > 0 else None,
                "views_per_comment": round(views / comments, 2) if comments > 0 else None
            },
            "benchmarks": benchmarks,
            "recommendations": self._get_engagement_recommendations(engagement_rate, like_ratio),
            "metadata": {
                "api_source": "YouTube Data API v3",
                "analysis_date": "2024-08-24"  # Current date
            }
        }
    
    def _get_engagement_recommendations(self, engagement_rate: float, like_ratio: float) -> List[str]:
        """Get engagement improvement recommendations."""
        recommendations = []
        
        if engagement_rate < 2.0:
            recommendations.extend([
                "Consider improving thumbnail and title to increase click-through rate",
                "Add clear calls-to-action to encourage likes and comments",
                "Engage with viewers by responding to comments"
            ])
        
        if like_ratio < 90.0:
            recommendations.append("Content might be controversial or not meeting viewer expectations")
        
        if engagement_rate < 5.0:
            recommendations.extend([
                "Try asking questions to encourage comments",
                "Create content that sparks discussion",
                "Optimize posting time for your audience"
            ])
        
        return recommendations
    
    def get_extractor_stats(self) -> Dict[str, Any]:
        """Get extractor statistics and health information."""
        return {
            "api_client": self.api_client.get_client_stats(),
            "settings": {
                "cache_enabled": self.settings.cache_enabled,
                "ytdlp_fallback_enabled": self.settings.enable_ytdlp_fallback,
                "daily_quota_limit": self.settings.daily_quota_limit,
                "requests_per_second": self.settings.requests_per_second
            },
            "status": "healthy"
        }