"""MCP Server for YouTube API integration."""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, ImageContent, EmbeddedResource

from .config.settings import get_settings
from .extractors.youtube_api_extractor import YouTubeAPIExtractor


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global extractor instance
extractor: Optional[YouTubeAPIExtractor] = None

# Initialize FastMCP
app = FastMCP("YouTube API MCP Server")


async def initialize_extractor():
    """Initialize the YouTube API extractor."""
    global extractor
    if extractor is None:
        settings = get_settings()
        extractor = YouTubeAPIExtractor()
        logger.info("YouTube API extractor initialized successfully")


@app.tool()
async def get_video_info(url: str) -> Dict[str, Any]:
    """Extract comprehensive information about a YouTube video using YouTube Data API v3.
    
    Args:
        url: YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)
    
    Returns:
        Dictionary containing video information including title, channel, views, likes, comments, duration, and engagement rates
    
    Examples:
        - get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.get_video_info(url)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to extract video info: {str(e)}")


@app.tool()
async def get_video_comments(url: str, max_comments: int = 20) -> Dict[str, Any]:
    """Extract comments from a YouTube video with smart rate limiting.
    
    Args:
        url: YouTube video URL
        max_comments: Maximum number of comments to extract (default: 20, recommended: ≤50)
    
    Returns:
        List of comment threads with author, text, likes, and replies
    
    Note:
        • Recommended limit: ≤20 for reliable extraction
        • Higher limits (>50) may fail due to YouTube rate limiting
        • If rate limited, automatically retries with smaller limits
        • For videos with many comments, use multiple smaller requests
    
    Examples:
        - get_video_comments("https://www.youtube.com/watch?v=dQw4w9WgXcQ", max_comments=10)
        - get_video_comments("https://www.youtube.com/watch?v=dQw4w9WgXcQ", max_comments=50)
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.get_video_comments(url, max_comments)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to extract comments: {str(e)}")


@app.tool()
async def get_video_comments_batch(url: str, total_desired: int = 100, batch_size: int = 20) -> Dict[str, Any]:
    """Extract a large number of comments by making multiple smaller requests.
    
    Args:
        url: YouTube video URL
        total_desired: Total number of comments to try to extract (default: 100)
        batch_size: Size of each batch request (default: 20, max: 50)
    
    Returns:
        Dictionary with comments list, metadata, and extraction info
    
    Note:
        • Use this for extracting >50 comments reliably
        • Makes multiple smaller requests to avoid rate limiting
        • May not get exactly total_desired due to YouTube limitations
        • Returns actual count and success rate
    
    Examples:
        - get_video_comments_batch("https://www.youtube.com/watch?v=dQw4w9WgXcQ", total_desired=200)
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        all_comments = []
        batches_completed = 0
        total_batches = (total_desired + batch_size - 1) // batch_size  # Ceiling division
        
        for batch in range(total_batches):
            batch_max = min(batch_size, total_desired - len(all_comments))
            if batch_max <= 0:
                break
            
            try:
                batch_result = await extractor.get_video_comments(url, batch_max)
                batch_comments = batch_result.get("comments", [])
                all_comments.extend(batch_comments)
                batches_completed += 1
                
                # Stop if we got fewer comments than requested (likely end of available comments)
                if len(batch_comments) < batch_max:
                    break
                    
            except Exception as e:
                logger.warning(f"Batch {batch + 1} failed: {e}")
                continue
        
        success_rate = batches_completed / total_batches if total_batches > 0 else 0
        
        return {
            "comments": all_comments[:total_desired],
            "metadata": {
                "total_extracted": len(all_comments),
                "total_desired": total_desired,
                "batches_completed": batches_completed,
                "total_batches": total_batches,
                "success_rate": round(success_rate * 100, 1),
                "batch_size": batch_size,
                "api_source": "YouTube Data API v3",
                "reliable": True
            }
        }
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract comments in batches: {str(e)}")


@app.tool()
async def get_video_transcript(url: str) -> Optional[Dict[str, Any]]:
    """Extract transcript/subtitles from a YouTube video.
    
    Args:
        url: YouTube video URL
    
    Returns:
        Dictionary containing transcript information with timestamped entries, or None if no transcript available
    
    Examples:
        - get_video_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.get_video_transcript(url)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to extract transcript: {str(e)}")


@app.tool()
async def search_transcript(url: str, query: str, case_sensitive: bool = False) -> Dict[str, Any]:
    """Search for specific text within a video's transcript.
    
    Args:
        url: YouTube video URL
        query: Text to search for in the transcript
        case_sensitive: Whether search should be case sensitive (default: false)
    
    Returns:
        List of transcript entries containing the search query
    
    Examples:
        - search_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "never gonna")
        - search_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "NEVER", case_sensitive=True)
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.search_transcript(url, query, case_sensitive)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to search transcript: {str(e)}")


@app.tool()
async def analyze_video_engagement(url: str) -> Dict[str, Any]:
    """Analyze engagement metrics for a YouTube video with industry benchmarks.
    
    Args:
        url: YouTube video URL
    
    Returns:
        Dictionary containing engagement analysis with benchmarks and recommendations
    
    Examples:
        - analyze_video_engagement("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.analyze_video_engagement(url)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to analyze video engagement: {str(e)}")


@app.tool()
async def get_channel_info(url: str) -> Dict[str, Any]:
    """Extract information about a YouTube channel.
    
    Args:
        url: YouTube channel URL (supports both old and new formats)
            - Modern format: https://www.youtube.com/@channelname
            - Legacy format: https://www.youtube.com/channelname
            - /c/ format: https://www.youtube.com/c/channelname
            - /user/ format: https://www.youtube.com/user/channelname
    
    Returns:
        Dictionary containing channel information and statistics
    
    Examples:
        - get_channel_info("https://www.youtube.com/@RickAstleyYT")
        - get_channel_info("https://www.youtube.com/LabEveryday") 
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.get_channel_info(url)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to extract channel info: {str(e)}")


@app.tool()
async def get_playlist_info(url: str) -> Dict[str, Any]:
    """Extract information about a YouTube playlist including all videos.
    
    Args:
        url: YouTube playlist URL
    
    Returns:
        Dictionary containing playlist information and video list
    
    Examples:
        - get_playlist_info("https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8HmPME")
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.get_playlist_info(url)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to extract playlist info: {str(e)}")


@app.tool()
async def search_youtube(query: str, search_type: str = "video", max_results: int = 20) -> Dict[str, Any]:
    """Search YouTube for videos, channels, or playlists.
    
    Args:
        query: Search query string
        search_type: Type of search ("video", "channel", "playlist")
        max_results: Maximum number of results to return (max 50)
    
    Returns:
        Dictionary containing search results and metadata
    
    Examples:
        - search_youtube("Python programming tutorials", "video", 10)
        - search_youtube("Tech channels", "channel", 5)
        - search_youtube("Music playlists", "playlist", 15)
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = await extractor.search_youtube(query, search_type, max_results)
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to search YouTube: {str(e)}")


@app.tool()
async def get_trending_videos(region: str = "US", max_results: int = 20) -> Dict[str, Any]:
    """Get trending videos for a specific region.
    
    Args:
        region: Country code (e.g., "US", "GB", "DE", "JP", "IN")
        max_results: Maximum number of results to return (max 50)
    
    Returns:
        Dictionary containing trending videos and metadata
    
    Examples:
        - get_trending_videos("US", 10)
        - get_trending_videos("GB", 20)
        - get_trending_videos("JP", 15)
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        # Use search with a trending-like query for now
        # TODO: Implement proper trending API call
        result = await extractor.search_youtube(
            query="trending popular viral",
            search_type="video", 
            max_results=max_results
        )
        
        # Add region metadata
        result["metadata"]["region"] = region
        result["metadata"]["note"] = "Using search approximation - consider YouTube Trends API for true trending data"
        
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to get trending videos: {str(e)}")


@app.tool()
async def batch_extract_urls(urls: List[str], extract_type: str = "video") -> Dict[str, Any]:
    """Extract information from multiple YouTube URLs concurrently.
    
    Args:
        urls: List of YouTube URLs to process
        extract_type: Type of extraction ("video", "channel", "playlist")
    
    Returns:
        Dictionary containing batch extraction results and metadata
    
    Examples:
        - batch_extract_urls(["https://youtube.com/watch?v=...", "https://youtube.com/watch?v=..."], "video")
        - batch_extract_urls(["https://youtube.com/@channel1", "https://youtube.com/@channel2"], "channel")
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    if len(urls) > 10:
        raise ValueError("Maximum 10 URLs allowed per batch request")
    
    try:
        results = []
        errors = []
        
        # Process URLs concurrently
        if extract_type == "video":
            extract_func = extractor.get_video_info
        elif extract_type == "channel":
            extract_func = extractor.get_channel_info
        elif extract_type == "playlist":
            extract_func = extractor.get_playlist_info
        else:
            raise ValueError(f"Invalid extract_type: {extract_type}")
        
        # Create tasks for concurrent execution
        tasks = [extract_func(url) for url in urls]
        
        # Wait for all tasks to complete
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, (url, result) in enumerate(zip(urls, task_results)):
            if isinstance(result, Exception):
                errors.append({
                    "url": url,
                    "error": str(result),
                    "index": i
                })
            else:
                results.append({
                    "url": url,
                    "data": result,
                    "index": i
                })
        
        success_rate = len(results) / len(urls) if urls else 0
        
        return {
            "results": results,
            "errors": errors,
            "metadata": {
                "total_urls": len(urls),
                "successful": len(results),
                "failed": len(errors),
                "success_rate": round(success_rate * 100, 1),
                "extract_type": extract_type,
                "api_source": "YouTube Data API v3"
            }
        }
        
    except Exception as e:
        raise RuntimeError(f"Failed to batch extract URLs: {str(e)}")


@app.tool()
async def get_extractor_health() -> Dict[str, Any]:
    """Get the health status and configuration of the YouTube extractor.
    
    Returns:
        Dictionary containing extractor health information, configuration, and cache statistics
    
    Examples:
        - get_extractor_health()
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        result = extractor.get_extractor_stats()
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to get extractor health: {str(e)}")


@app.tool()
async def clear_extractor_cache() -> Dict[str, Any]:
    """Clear all cached data from the extractor.
    
    Returns:
        Dictionary confirming cache clearance
    
    Examples:
        - clear_extractor_cache()
    """
    global extractor
    if not extractor:
        await initialize_extractor()
    
    try:
        extractor.api_client.cache.clear()
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "cache_stats": extractor.api_client.cache.get_stats()
        }
    except Exception as e:
        raise RuntimeError(f"Failed to clear cache: {str(e)}")


@app.tool()
async def get_extractor_config() -> Dict[str, Any]:
    """Get the current configuration of the YouTube extractor.
    
    Returns:
        Dictionary containing extractor configuration parameters
    
    Examples:
        - get_extractor_config()
    """
    settings = get_settings()
    
    return {
        "youtube_api_version": settings.youtube_api_version,
        "daily_quota_limit": settings.daily_quota_limit,
        "requests_per_second": settings.requests_per_second,
        "cache_enabled": settings.cache_enabled,
        "cache_ttl": settings.cache_ttl,
        "cache_max_size": settings.cache_max_size,
        "enable_ytdlp_fallback": settings.enable_ytdlp_fallback,
        "ytdlp_rate_limit": settings.ytdlp_rate_limit,
        "log_level": settings.log_level
    }


def main():
    """Run the MCP server via stdio transport."""
    logger.info("Starting YouTube API MCP Server via stdio transport")
    
    # Run the FastMCP app with stdio transport for MCP
    app.run()


if __name__ == "__main__":
    main()