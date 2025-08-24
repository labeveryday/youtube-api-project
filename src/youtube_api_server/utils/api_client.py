"""YouTube Data API v3 client wrapper."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .rate_limiter import AsyncRateLimiter
from .cache import APICache
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, reason: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


class YouTubeAPIClient:
    """Async wrapper for YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.youtube_api_key
        self.service = build('youtube', settings.youtube_api_version, developerKey=self.api_key)
        self.rate_limiter = AsyncRateLimiter(
            requests_per_second=settings.requests_per_second,
            daily_limit=settings.daily_quota_limit
        )
        self.cache = APICache(
            max_size=settings.cache_max_size,
            ttl=settings.cache_ttl
        )
        if not settings.cache_enabled:
            self.cache.disable()
    
    async def _execute_request(self, request) -> Dict[str, Any]:
        """Execute API request with rate limiting and error handling."""
        await self.rate_limiter.acquire()
        
        try:
            # Execute in thread pool since googleapiclient is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, request.execute)
            return response
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            raise YouTubeAPIError(
                message=f"YouTube API error: {error_details.get('message', str(e))}",
                status_code=e.resp.status,
                reason=error_details.get('reason')
            )
        except Exception as e:
            raise YouTubeAPIError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def get_video_details(self, video_ids: Union[str, List[str]], parts: List[str] = None) -> Dict[str, Any]:
        """Get video details for one or more videos."""
        if isinstance(video_ids, str):
            video_ids = [video_ids]
        
        if not video_ids:
            return {"items": []}
        
        if parts is None:
            parts = ["snippet", "statistics", "contentDetails", "status"]
        
        # Check cache first
        cache_key = self.cache.create_key("videos", ",".join(video_ids), ",".join(parts))
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for videos: {video_ids}")
            return cached_result
        
        # Make API request
        request = self.service.videos().list(
            part=",".join(parts),
            id=",".join(video_ids),
            maxResults=50
        )
        
        response = await self._execute_request(request)
        
        # Cache the result
        self.cache.set(cache_key, response)
        logger.debug(f"Fetched video details for {len(response.get('items', []))} videos")
        
        return response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def get_video_comments(self, video_id: str, max_results: int = 100, order: str = "relevance") -> Dict[str, Any]:
        """Get comments for a video with pagination support."""
        cache_key = self.cache.create_key("comments", video_id, str(max_results), order)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for comments: {video_id}")
            return cached_result
        
        all_comments = []
        next_page_token = None
        
        while len(all_comments) < max_results:
            batch_size = min(100, max_results - len(all_comments))
            
            request = self.service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=batch_size,
                order=order,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            
            try:
                response = await self._execute_request(request)
            except YouTubeAPIError as e:
                if "commentsDisabled" in str(e):
                    logger.warning(f"Comments disabled for video {video_id}")
                    response = {"items": [], "pageInfo": {"totalResults": 0}}
                    break
                raise
            
            all_comments.extend(response.get("items", []))
            next_page_token = response.get("nextPageToken")
            
            if not next_page_token:
                break
        
        result = {
            "items": all_comments[:max_results],
            "pageInfo": {"totalResults": len(all_comments)},
            "kind": "youtube#commentThreadListResponse"
        }
        
        # Cache the result
        self.cache.set(cache_key, result)
        logger.debug(f"Fetched {len(all_comments)} comments for video {video_id}")
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def get_channel_details(self, channel_id: str, parts: List[str] = None) -> Dict[str, Any]:
        """Get channel details."""
        if parts is None:
            parts = ["snippet", "statistics", "contentDetails", "status"]
        
        cache_key = self.cache.create_key("channel", channel_id, ",".join(parts))
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for channel: {channel_id}")
            return cached_result
        
        request = self.service.channels().list(
            part=",".join(parts),
            id=channel_id
        )
        
        response = await self._execute_request(request)
        
        # Cache the result
        self.cache.set(cache_key, response)
        logger.debug(f"Fetched channel details for {channel_id}")
        
        return response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def search_videos(self, query: str, max_results: int = 50, search_type: str = "video") -> Dict[str, Any]:
        """Search for videos, channels, or playlists."""
        cache_key = self.cache.create_key("search", query, str(max_results), search_type)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for search: {query}")
            return cached_result
        
        request = self.service.search().list(
            part="snippet",
            q=query,
            type=search_type,
            maxResults=min(max_results, 50),
            order="relevance"
        )
        
        response = await self._execute_request(request)
        
        # Cache the result
        self.cache.set(cache_key, response)
        logger.debug(f"Search returned {len(response.get('items', []))} results for: {query}")
        
        return response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def get_playlist_details(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist details."""
        cache_key = self.cache.create_key("playlist", playlist_id)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for playlist: {playlist_id}")
            return cached_result
        
        request = self.service.playlists().list(
            part="snippet,contentDetails,status",
            id=playlist_id
        )
        
        response = await self._execute_request(request)
        
        # Cache the result
        self.cache.set(cache_key, response)
        logger.debug(f"Fetched playlist details for {playlist_id}")
        
        return response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(YouTubeAPIError)
    )
    async def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> Dict[str, Any]:
        """Get videos from a playlist."""
        cache_key = self.cache.create_key("playlist_items", playlist_id, str(max_results))
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for playlist items: {playlist_id}")
            return cached_result
        
        all_items = []
        next_page_token = None
        
        while len(all_items) < max_results:
            batch_size = min(50, max_results - len(all_items))
            
            request = self.service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=batch_size,
                pageToken=next_page_token
            )
            
            response = await self._execute_request(request)
            all_items.extend(response.get("items", []))
            next_page_token = response.get("nextPageToken")
            
            if not next_page_token:
                break
        
        result = {
            "items": all_items[:max_results],
            "pageInfo": {"totalResults": len(all_items)},
            "kind": "youtube#playlistItemListResponse"
        }
        
        # Cache the result
        self.cache.set(cache_key, result)
        logger.debug(f"Fetched {len(all_items)} items from playlist {playlist_id}")
        
        return result
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "cache": self.cache.get_stats()
        }