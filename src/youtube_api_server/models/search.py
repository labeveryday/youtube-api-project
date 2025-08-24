"""Search models for YouTube API data."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .base import BaseYouTubeModel, YouTubeThumbnails


class SearchResultId(BaseYouTubeModel):
    """YouTube search result ID."""
    kind: str = Field(description="Resource type (video, channel, playlist)")
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    channel_id: Optional[str] = Field(None, alias="channelId", description="Channel ID")
    playlist_id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")


class SearchResultSnippet(BaseYouTubeModel):
    """YouTube search result snippet."""
    published_at: datetime = Field(alias="publishedAt", description="Publish date")
    channel_id: str = Field(alias="channelId", description="Channel ID")
    title: str = Field(description="Result title")
    description: str = Field(description="Result description")
    thumbnails: YouTubeThumbnails = Field(description="Result thumbnails")
    channel_title: str = Field(alias="channelTitle", description="Channel title")
    live_broadcast_content: Optional[str] = Field(None, alias="liveBroadcastContent", description="Live broadcast status")


class SearchResult(BaseYouTubeModel):
    """YouTube search result."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    id: SearchResultId = Field(description="Result ID")
    snippet: SearchResultSnippet = Field(description="Result snippet")
    
    def get_result_type(self) -> str:
        """Get the type of search result."""
        if self.id.video_id:
            return "video"
        elif self.id.channel_id:
            return "channel"
        elif self.id.playlist_id:
            return "playlist"
        return "unknown"
    
    def get_url(self) -> str:
        """Get the URL for this search result."""
        if self.id.video_id:
            return f"https://www.youtube.com/watch?v={self.id.video_id}"
        elif self.id.channel_id:
            return f"https://www.youtube.com/channel/{self.id.channel_id}"
        elif self.id.playlist_id:
            return f"https://www.youtube.com/playlist?list={self.id.playlist_id}"
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        result_type = self.get_result_type()
        
        result = {
            "type": result_type,
            "id": self.id.video_id or self.id.channel_id or self.id.playlist_id,
            "url": self.get_url(),
            "title": self.snippet.title,
            "description": self.snippet.description,
            "channel_id": self.snippet.channel_id,
            "channel_title": self.snippet.channel_title,
            "published_at": self.snippet.published_at.isoformat(),
            "thumbnails": self.snippet.thumbnails.dict() if self.snippet.thumbnails else {},
            "live_broadcast_content": self.snippet.live_broadcast_content
        }
        
        return result


class SearchListResponse(BaseYouTubeModel):
    """YouTube search list response."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    next_page_token: Optional[str] = Field(None, alias="nextPageToken", description="Next page token")
    prev_page_token: Optional[str] = Field(None, alias="prevPageToken", description="Previous page token")
    region_code: Optional[str] = Field(None, alias="regionCode", description="Region code")
    page_info: Optional[Dict[str, int]] = Field(None, alias="pageInfo", description="Page information")
    items: List[SearchResult] = Field(description="Search results")
    
    def get_results_by_type(self) -> Dict[str, List[SearchResult]]:
        """Group results by type."""
        results_by_type = {
            "videos": [],
            "channels": [],
            "playlists": []
        }
        
        for item in self.items:
            result_type = item.get_result_type()
            if result_type == "video":
                results_by_type["videos"].append(item)
            elif result_type == "channel":
                results_by_type["channels"].append(item)
            elif result_type == "playlist":
                results_by_type["playlists"].append(item)
        
        return results_by_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        results_by_type = self.get_results_by_type()
        
        return {
            "results": [item.to_dict() for item in self.items],
            "results_by_type": {
                "videos": [item.to_dict() for item in results_by_type["videos"]],
                "channels": [item.to_dict() for item in results_by_type["channels"]],
                "playlists": [item.to_dict() for item in results_by_type["playlists"]]
            },
            "total_results": len(self.items),
            "next_page_token": self.next_page_token,
            "prev_page_token": self.prev_page_token,
            "region_code": self.region_code,
            "metadata": {
                "api_source": "YouTube Data API v3",
                "reliable": True,
                "has_more": self.next_page_token is not None
            }
        }