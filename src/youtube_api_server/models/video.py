"""Video models for YouTube API data."""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator

from .base import BaseYouTubeModel, YouTubeThumbnails, YouTubeLocalized


class VideoStatistics(BaseYouTubeModel):
    """YouTube video statistics."""
    view_count: Optional[int] = Field(None, alias="viewCount", description="Number of views")
    like_count: Optional[int] = Field(None, alias="likeCount", description="Number of likes")
    dislike_count: Optional[int] = Field(None, alias="dislikeCount", description="Number of dislikes (deprecated)")
    comment_count: Optional[int] = Field(None, alias="commentCount", description="Number of comments")
    favorite_count: Optional[int] = Field(None, alias="favoriteCount", description="Number of favorites")
    
    @validator('view_count', 'like_count', 'dislike_count', 'comment_count', 'favorite_count', pre=True)
    def parse_string_numbers(cls, v):
        """Convert string numbers to integers."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class VideoSnippet(BaseYouTubeModel):
    """YouTube video snippet data."""
    published_at: datetime = Field(alias="publishedAt", description="Video publish date")
    channel_id: str = Field(alias="channelId", description="Channel ID")
    title: str = Field(description="Video title")
    description: str = Field(description="Video description")
    thumbnails: YouTubeThumbnails = Field(description="Video thumbnails")
    channel_title: str = Field(alias="channelTitle", description="Channel name")
    tags: Optional[List[str]] = Field(None, description="Video tags")
    category_id: Optional[str] = Field(None, alias="categoryId", description="Video category ID")
    live_broadcast_content: Optional[str] = Field(None, alias="liveBroadcastContent", description="Live broadcast status")
    default_language: Optional[str] = Field(None, alias="defaultLanguage", description="Default language")
    default_audio_language: Optional[str] = Field(None, alias="defaultAudioLanguage", description="Default audio language")
    localized: Optional[YouTubeLocalized] = Field(None, description="Localized title and description")


class VideoContentDetails(BaseYouTubeModel):
    """YouTube video content details."""
    duration: str = Field(description="Video duration in ISO 8601 format")
    dimension: Optional[str] = Field(None, description="Video dimension (2d or 3d)")
    definition: Optional[str] = Field(None, description="Video definition (hd or sd)")
    caption: Optional[str] = Field(None, description="Caption availability")
    licensed_content: Optional[bool] = Field(None, alias="licensedContent", description="Licensed content flag")
    region_restriction: Optional[Dict[str, List[str]]] = Field(None, alias="regionRestriction", description="Region restrictions")
    content_rating: Optional[Dict[str, Any]] = Field(None, alias="contentRating", description="Content rating")
    projection: Optional[str] = Field(None, description="Video projection (rectangular or 360)")
    
    def get_duration_seconds(self) -> Optional[int]:
        """Convert ISO 8601 duration to seconds."""
        if not self.duration:
            return None
        
        # Parse ISO 8601 duration format (PT1H2M3S)
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(self.duration)
        
        if not match:
            return None
        
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        return hours * 3600 + minutes * 60 + seconds
    
    def get_duration_formatted(self) -> Optional[str]:
        """Get duration in HH:MM:SS format."""
        total_seconds = self.get_duration_seconds()
        if total_seconds is None:
            return None
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


class VideoStatus(BaseYouTubeModel):
    """YouTube video status."""
    upload_status: Optional[str] = Field(None, alias="uploadStatus", description="Upload status")
    failure_reason: Optional[str] = Field(None, alias="failureReason", description="Failure reason")
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason", description="Rejection reason")
    privacy_status: Optional[str] = Field(None, alias="privacyStatus", description="Privacy status")
    publish_at: Optional[datetime] = Field(None, alias="publishAt", description="Scheduled publish time")
    license: Optional[str] = Field(None, description="Video license")
    embeddable: Optional[bool] = Field(None, description="Embeddable flag")
    public_stats_viewable: Optional[bool] = Field(None, alias="publicStatsViewable", description="Public stats viewable")
    made_for_kids: Optional[bool] = Field(None, alias="madeForKids", description="Made for kids")
    self_declared_made_for_kids: Optional[bool] = Field(None, alias="selfDeclaredMadeForKids", description="Self-declared made for kids")


class VideoInfo(BaseYouTubeModel):
    """Complete YouTube video information."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    id: str = Field(description="Video ID")
    snippet: Optional[VideoSnippet] = Field(None, description="Video snippet")
    statistics: Optional[VideoStatistics] = Field(None, description="Video statistics")
    content_details: Optional[VideoContentDetails] = Field(None, alias="contentDetails", description="Content details")
    status: Optional[VideoStatus] = Field(None, description="Video status")
    
    def get_engagement_rate(self) -> Optional[float]:
        """Calculate engagement rate (likes + comments) / views."""
        if not self.statistics or not self.statistics.view_count:
            return None
        
        likes = self.statistics.like_count or 0
        comments = self.statistics.comment_count or 0
        views = self.statistics.view_count
        
        if views == 0:
            return None
        
        return round((likes + comments) / views * 100, 2)
    
    def get_like_ratio(self) -> Optional[float]:
        """Calculate like ratio (likes / (likes + dislikes))."""
        if not self.statistics:
            return None
        
        likes = self.statistics.like_count or 0
        dislikes = self.statistics.dislike_count or 0
        
        total_ratings = likes + dislikes
        if total_ratings == 0:
            return None
        
        return round(likes / total_ratings * 100, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        result = {
            "id": self.id,
            "url": f"https://www.youtube.com/watch?v={self.id}"
        }
        
        if self.snippet:
            result.update({
                "title": self.snippet.title,
                "description": self.snippet.description,
                "channel": self.snippet.channel_title,
                "channel_id": self.snippet.channel_id,
                "published_at": self.snippet.published_at.isoformat(),
                "thumbnails": self.snippet.thumbnails.dict() if self.snippet.thumbnails else {},
                "tags": self.snippet.tags or [],
                "category_id": self.snippet.category_id
            })
        
        if self.statistics:
            result["statistics"] = {
                "view_count": self.statistics.view_count,
                "like_count": self.statistics.like_count,
                "comment_count": self.statistics.comment_count,
                "favorite_count": self.statistics.favorite_count
            }
            
            # Add calculated metrics
            result["engagement_rate"] = self.get_engagement_rate()
            result["like_ratio"] = self.get_like_ratio()
        
        if self.content_details:
            result["duration"] = {
                "iso_8601": self.content_details.duration,
                "seconds": self.content_details.get_duration_seconds(),
                "formatted": self.content_details.get_duration_formatted()
            }
            result["definition"] = self.content_details.definition
            result["dimension"] = self.content_details.dimension
            result["caption"] = self.content_details.caption
        
        if self.status:
            result["privacy_status"] = self.status.privacy_status
            result["embeddable"] = self.status.embeddable
            result["made_for_kids"] = self.status.made_for_kids
        
        return result