"""Configuration settings for YouTube API MCP Server."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # YouTube API Configuration
    youtube_api_key: str = Field(description="YouTube Data API v3 key")
    youtube_api_version: str = Field(default="v3", description="YouTube API version")
    
    # Optional OAuth Configuration (for private channel data)
    my_channel_id: Optional[str] = Field(default=None, description="Your channel ID (optional)")
    my_uploaded_video_playlist_id: Optional[str] = Field(default=None, description="Your uploads playlist ID (optional)")
    
    # Rate Limiting Configuration
    daily_quota_limit: int = Field(default=10000, description="Daily API quota limit")
    requests_per_second: float = Field(default=10.0, description="Max requests per second")
    
    # Caching Configuration
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Maximum cache entries")
    
    # Fallback Configuration
    enable_ytdlp_fallback: bool = Field(default=True, description="Enable yt-dlp for transcripts")
    ytdlp_rate_limit: str = Field(default="500K", description="yt-dlp rate limit")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "YOUTUBE_",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings