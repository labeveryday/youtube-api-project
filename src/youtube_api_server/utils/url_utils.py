"""URL parsing utilities for YouTube links."""

import re
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Try direct video ID if it's 11 characters
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    return None


def extract_channel_id(url: str) -> Optional[str]:
    """Extract channel ID from YouTube channel URLs."""
    patterns = [
        r'youtube\.com\/channel\/([a-zA-Z0-9_-]{24})',
        r'youtube\.com\/c\/([a-zA-Z0-9_-]+)',
        r'youtube\.com\/user\/([a-zA-Z0-9_-]+)',
        r'youtube\.com\/@([a-zA-Z0-9_.-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Try direct channel ID if it's 24 characters starting with UC
    if re.match(r'^UC[a-zA-Z0-9_-]{22}$', url):
        return url
    
    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from YouTube playlist URLs."""
    patterns = [
        r'youtube\.com\/playlist\?list=([a-zA-Z0-9_-]+)',
        r'youtube\.com\/watch\?.*list=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Try direct playlist ID
    if re.match(r'^[a-zA-Z0-9_-]+$', url) and len(url) >= 10:
        return url
    
    return None


def parse_youtube_url(url: str) -> Dict[str, Optional[str]]:
    """Parse YouTube URL and extract all possible IDs."""
    result = {
        'video_id': None,
        'channel_id': None,
        'playlist_id': None,
        'url_type': None
    }
    
    # Extract video ID
    video_id = extract_video_id(url)
    if video_id:
        result['video_id'] = video_id
        result['url_type'] = 'video'
    
    # Extract channel ID
    channel_id = extract_channel_id(url)
    if channel_id:
        result['channel_id'] = channel_id
        if not result['url_type']:
            result['url_type'] = 'channel'
    
    # Extract playlist ID
    playlist_id = extract_playlist_id(url)
    if playlist_id:
        result['playlist_id'] = playlist_id
        if not result['url_type']:
            result['url_type'] = 'playlist'
    
    return result


def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL."""
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() in youtube_domains
    except:
        return False


def normalize_youtube_url(url: str) -> Optional[str]:
    """Normalize YouTube URL to standard format."""
    parsed_data = parse_youtube_url(url)
    
    if parsed_data['video_id']:
        return f"https://www.youtube.com/watch?v={parsed_data['video_id']}"
    elif parsed_data['channel_id']:
        if parsed_data['channel_id'].startswith('UC'):
            return f"https://www.youtube.com/channel/{parsed_data['channel_id']}"
        else:
            return f"https://www.youtube.com/@{parsed_data['channel_id']}"
    elif parsed_data['playlist_id']:
        return f"https://www.youtube.com/playlist?list={parsed_data['playlist_id']}"
    
    return None