"""Channel models for YouTube API data."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .base import BaseYouTubeModel, YouTubeThumbnails, YouTubeLocalized


class ChannelStatistics(BaseYouTubeModel):
    """YouTube channel statistics."""
    view_count: Optional[int] = Field(None, alias="viewCount", description="Total channel views")
    subscriber_count: Optional[int] = Field(None, alias="subscriberCount", description="Number of subscribers")
    hidden_subscriber_count: Optional[bool] = Field(None, alias="hiddenSubscriberCount", description="Whether subscriber count is hidden")
    video_count: Optional[int] = Field(None, alias="videoCount", description="Number of videos")
    
    @validator('view_count', 'subscriber_count', 'video_count', pre=True)
    def parse_string_numbers(cls, v):
        """Convert string numbers to integers."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class ChannelSnippet(BaseYouTubeModel):
    """YouTube channel snippet data."""
    title: str = Field(description="Channel title")
    description: str = Field(description="Channel description")
    custom_url: Optional[str] = Field(None, alias="customUrl", description="Channel custom URL")
    published_at: datetime = Field(alias="publishedAt", description="Channel creation date")
    thumbnails: YouTubeThumbnails = Field(description="Channel thumbnails")
    default_language: Optional[str] = Field(None, alias="defaultLanguage", description="Default language")
    localized: Optional[YouTubeLocalized] = Field(None, description="Localized title and description")
    country: Optional[str] = Field(None, description="Channel country")
    keywords: Optional[str] = Field(None, description="Channel keywords")
    
    def get_keywords_list(self) -> List[str]:
        """Get keywords as a list."""
        if not self.keywords:
            return []
        return [kw.strip().strip('"') for kw in self.keywords.split()]


class ChannelContentDetails(BaseYouTubeModel):
    """YouTube channel content details."""
    related_playlists: Dict[str, str] = Field(alias="relatedPlaylists", description="Related playlists")
    
    def get_uploads_playlist_id(self) -> Optional[str]:
        """Get the uploads playlist ID."""
        return self.related_playlists.get("uploads")


class ChannelStatus(BaseYouTubeModel):
    """YouTube channel status."""
    privacy_status: Optional[str] = Field(None, alias="privacyStatus", description="Privacy status")
    is_linked: Optional[bool] = Field(None, alias="isLinked", description="Whether channel is linked to Google+")
    long_uploads_status: Optional[str] = Field(None, alias="longUploadsStatus", description="Long uploads status")
    made_for_kids: Optional[bool] = Field(None, alias="madeForKids", description="Made for kids")
    self_declared_made_for_kids: Optional[bool] = Field(None, alias="selfDeclaredMadeForKids", description="Self-declared made for kids")


class ChannelBrandingSettings(BaseYouTubeModel):
    """YouTube channel branding settings."""
    channel: Optional[Dict[str, Any]] = Field(None, description="Channel branding")
    watch: Optional[Dict[str, Any]] = Field(None, description="Watch page branding")
    image: Optional[Dict[str, Any]] = Field(None, description="Image branding")


class ChannelInfo(BaseYouTubeModel):
    """Complete YouTube channel information."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    id: str = Field(description="Channel ID")
    snippet: Optional[ChannelSnippet] = Field(None, description="Channel snippet")
    statistics: Optional[ChannelStatistics] = Field(None, description="Channel statistics")
    content_details: Optional[ChannelContentDetails] = Field(None, alias="contentDetails", description="Content details")
    status: Optional[ChannelStatus] = Field(None, description="Channel status")
    branding_settings: Optional[ChannelBrandingSettings] = Field(None, alias="brandingSettings", description="Branding settings")
    
    def get_subscriber_tier(self) -> str:
        """Get subscriber count tier description."""
        if not self.statistics or not self.statistics.subscriber_count:
            return "Unknown"
        
        count = self.statistics.subscriber_count
        
        if count >= 10000000:
            return f"{count // 1000000}M+ (Diamond)"
        elif count >= 1000000:
            return f"{count // 1000000}M+ (Gold)"
        elif count >= 100000:
            return f"{count // 1000}K+ (Silver)"
        elif count >= 1000:
            return f"{count // 1000}K+ (Bronze)"
        else:
            return f"{count} (Starting)"
    
    def get_engagement_metrics(self) -> Dict[str, Any]:
        """Calculate engagement metrics."""
        if not self.statistics:
            return {}
        
        metrics = {}
        
        # Views per video average
        if self.statistics.view_count and self.statistics.video_count:
            metrics["avg_views_per_video"] = round(
                self.statistics.view_count / self.statistics.video_count
            )
        
        # Subscribers per video ratio
        if self.statistics.subscriber_count and self.statistics.video_count:
            metrics["subscribers_per_video"] = round(
                self.statistics.subscriber_count / self.statistics.video_count, 2
            )
        
        return metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        result = {
            "id": self.id,
            "url": f"https://www.youtube.com/channel/{self.id}"
        }
        
        if self.snippet:
            result.update({
                "title": self.snippet.title,
                "description": self.snippet.description,
                "custom_url": self.snippet.custom_url,
                "published_at": self.snippet.published_at.isoformat(),
                "thumbnails": self.snippet.thumbnails.dict() if self.snippet.thumbnails else {},
                "country": self.snippet.country,
                "keywords": self.snippet.get_keywords_list()
            })
            
            # Add handle-based URL if custom URL exists
            if self.snippet.custom_url:
                result["handle_url"] = f"https://www.youtube.com/@{self.snippet.custom_url.lstrip('@')}"
        
        if self.statistics:
            result["statistics"] = {
                "view_count": self.statistics.view_count,
                "subscriber_count": self.statistics.subscriber_count,
                "video_count": self.statistics.video_count,
                "hidden_subscriber_count": self.statistics.hidden_subscriber_count
            }
            
            # Add calculated metrics
            result["subscriber_tier"] = self.get_subscriber_tier()
            result["engagement_metrics"] = self.get_engagement_metrics()
        
        if self.content_details:
            result["uploads_playlist_id"] = self.content_details.get_uploads_playlist_id()
        
        if self.status:
            result["privacy_status"] = self.status.privacy_status
            result["made_for_kids"] = self.status.made_for_kids
        
        return result


class ChannelListResponse(BaseYouTubeModel):
    """YouTube channel list response."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    page_info: Optional[Dict[str, int]] = Field(None, alias="pageInfo", description="Page information")
    items: List[ChannelInfo] = Field(description="Channels")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        return {
            "channels": [channel.to_dict() for channel in self.items],
            "total_results": len(self.items),
            "metadata": {
                "api_source": "YouTube Data API v3",
                "reliable": True
            }
        }