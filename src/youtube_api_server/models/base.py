"""Base models for YouTube API data structures."""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class BaseYouTubeModel(BaseModel):
    """Base model for all YouTube API responses."""
    
    model_config = {
        "validate_by_name": True,
        "use_enum_values": True,
        "validate_assignment": True
    }


class YouTubeThumbnail(BaseModel):
    """YouTube thumbnail data."""
    url: str = Field(description="Thumbnail image URL")
    width: Optional[int] = Field(None, description="Thumbnail width in pixels")
    height: Optional[int] = Field(None, description="Thumbnail height in pixels")


class YouTubeThumbnails(BaseModel):
    """YouTube thumbnails collection."""
    default: Optional[YouTubeThumbnail] = Field(None, description="Default thumbnail (120x90)")
    medium: Optional[YouTubeThumbnail] = Field(None, description="Medium thumbnail (320x180)")
    high: Optional[YouTubeThumbnail] = Field(None, description="High quality thumbnail (480x360)")
    standard: Optional[YouTubeThumbnail] = Field(None, description="Standard thumbnail (640x480)")
    maxres: Optional[YouTubeThumbnail] = Field(None, description="Maximum resolution thumbnail (1280x720)")
    
    def get_best_thumbnail(self) -> Optional[YouTubeThumbnail]:
        """Get the highest quality available thumbnail."""
        for thumb in [self.maxres, self.standard, self.high, self.medium, self.default]:
            if thumb:
                return thumb
        return None


class YouTubeLocalized(BaseModel):
    """Localized text content."""
    title: Optional[str] = Field(None, description="Localized title")
    description: Optional[str] = Field(None, description="Localized description")


class PageInfo(BaseModel):
    """YouTube API page information."""
    total_results: int = Field(alias="totalResults", description="Total number of results")
    results_per_page: int = Field(alias="resultsPerPage", description="Number of results per page")


class YouTubeResponse(BaseYouTubeModel):
    """Base YouTube API response structure."""
    kind: str = Field(description="YouTube API resource type")
    etag: str = Field(description="ETag for caching")
    next_page_token: Optional[str] = Field(None, alias="nextPageToken", description="Token for next page")
    prev_page_token: Optional[str] = Field(None, alias="prevPageToken", description="Token for previous page")
    page_info: Optional[PageInfo] = Field(None, alias="pageInfo", description="Page information")
    items: list = Field(default_factory=list, description="Response items")