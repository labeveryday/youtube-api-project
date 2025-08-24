"""Transcript extractor using yt-dlp fallback for YouTube Data API."""

import asyncio
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

from ..config.settings import get_settings
from ..utils.url_utils import extract_video_id
from ..models.transcript import TranscriptInfo, TranscriptSegment


logger = logging.getLogger(__name__)


class TranscriptExtractor:
    """Extract transcripts using yt-dlp as fallback."""
    
    def __init__(self):
        if not YTDLP_AVAILABLE:
            raise ImportError("yt-dlp is required for transcript extraction")
        
        self.settings = get_settings()
        self._setup_ytdlp_options()
    
    def _setup_ytdlp_options(self):
        """Configure yt-dlp options."""
        self.ytdlp_options = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'json3',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'ratelimit': self._parse_rate_limit(self.settings.ytdlp_rate_limit)
        }
    
    def _parse_rate_limit(self, rate_limit_str: str) -> Optional[int]:
        """Parse rate limit string to bytes per second."""
        if not rate_limit_str:
            return None
        
        rate_limit_str = rate_limit_str.upper()
        
        # Extract number and unit
        import re
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?)', rate_limit_str)
        if not match:
            return None
        
        value, unit = match.groups()
        value = float(value)
        
        # Convert to bytes per second
        multipliers = {
            '': 1,
            'K': 1024,
            'M': 1024**2,
            'G': 1024**3,
            'T': 1024**4
        }
        
        return int(value * multipliers.get(unit, 1))
    
    async def extract_transcript(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract transcript from YouTube video using yt-dlp."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube video URL: {url}")
        
        try:
            # Run yt-dlp in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcript_data = await loop.run_in_executor(
                None, 
                self._extract_transcript_sync, 
                url, 
                video_id
            )
            
            return transcript_data
            
        except Exception as e:
            logger.error(f"Failed to extract transcript for {video_id}: {e}")
            return None
    
    def _extract_transcript_sync(self, url: str, video_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous transcript extraction using yt-dlp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Update options with temp directory
            options = self.ytdlp_options.copy()
            options['outtmpl'] = os.path.join(temp_dir, '%(id)s.%(ext)s')
            
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    # Extract info including subtitles
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        logger.warning(f"No info extracted for {video_id}")
                        return None
                    
                    # Try to get subtitles
                    subtitles = info.get('subtitles', {})
                    automatic_captions = info.get('automatic_captions', {})
                    
                    # Prefer manual subtitles over automatic
                    transcript_data = None
                    language = None
                    is_generated = False
                    
                    # Try manual subtitles first
                    for lang, subs in subtitles.items():
                        for sub in subs:
                            if sub.get('ext') == 'json3':
                                transcript_data = self._download_subtitle_data(sub['url'])
                                language = lang
                                is_generated = False
                                break
                        if transcript_data:
                            break
                    
                    # Fall back to automatic captions
                    if not transcript_data:
                        for lang, subs in automatic_captions.items():
                            for sub in subs:
                                if sub.get('ext') == 'json3':
                                    transcript_data = self._download_subtitle_data(sub['url'])
                                    language = lang
                                    is_generated = True
                                    break
                            if transcript_data:
                                break
                    
                    if not transcript_data:
                        logger.warning(f"No transcript data found for {video_id}")
                        return None
                    
                    # Parse transcript data
                    segments = self._parse_transcript_json(transcript_data)
                    
                    if not segments:
                        logger.warning(f"No transcript segments found for {video_id}")
                        return None
                    
                    # Create transcript info
                    transcript_info = TranscriptInfo(
                        video_id=video_id,
                        language=language,
                        language_code=language,
                        is_generated=is_generated,
                        segments=segments
                    )
                    
                    logger.info(f"Successfully extracted transcript for {video_id} ({len(segments)} segments)")
                    return transcript_info.to_dict()
                    
            except Exception as e:
                logger.error(f"yt-dlp error extracting transcript for {video_id}: {e}")
                return None
    
    def _download_subtitle_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Download subtitle data from URL."""
        try:
            import urllib.request
            import json
            
            with urllib.request.urlopen(url) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to download subtitle data: {e}")
            return None
    
    def _parse_transcript_json(self, transcript_data: Dict[str, Any]) -> List[TranscriptSegment]:
        """Parse JSON transcript data into segments."""
        segments = []
        
        try:
            events = transcript_data.get('events', [])
            
            for event in events:
                segs = event.get('segs')
                if not segs:
                    continue
                
                start_time = event.get('tStartMs', 0) / 1000.0  # Convert to seconds
                duration = event.get('dDurationMs', 0) / 1000.0
                
                # Combine all segments in this event
                text_parts = []
                for seg in segs:
                    if 'utf8' in seg:
                        text_parts.append(seg['utf8'])
                
                if text_parts:
                    text = ''.join(text_parts).strip()
                    if text:  # Only add non-empty segments
                        segment = TranscriptSegment(
                            text=text,
                            start=start_time,
                            duration=duration
                        )
                        segments.append(segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error parsing transcript JSON: {e}")
            return []
    
    async def get_available_transcripts(self, url: str) -> Dict[str, Any]:
        """Get information about available transcripts for a video."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube video URL: {url}")
        
        try:
            loop = asyncio.get_event_loop()
            transcript_info = await loop.run_in_executor(
                None, 
                self._get_available_transcripts_sync, 
                url, 
                video_id
            )
            
            return transcript_info
            
        except Exception as e:
            logger.error(f"Failed to get available transcripts for {video_id}: {e}")
            return {
                "video_id": video_id,
                "available_languages": [],
                "has_manual": False,
                "has_automatic": False,
                "error": str(e)
            }
    
    def _get_available_transcripts_sync(self, url: str, video_id: str) -> Dict[str, Any]:
        """Get available transcript languages synchronously."""
        options = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True
        }
        
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return {
                        "video_id": video_id,
                        "available_languages": [],
                        "has_manual": False,
                        "has_automatic": False
                    }
                
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})
                
                manual_languages = list(subtitles.keys())
                automatic_languages = list(automatic_captions.keys())
                
                return {
                    "video_id": video_id,
                    "manual_languages": manual_languages,
                    "automatic_languages": automatic_languages,
                    "available_languages": list(set(manual_languages + automatic_languages)),
                    "has_manual": len(manual_languages) > 0,
                    "has_automatic": len(automatic_languages) > 0,
                    "total_languages": len(set(manual_languages + automatic_languages))
                }
                
        except Exception as e:
            logger.error(f"Error getting available transcripts for {video_id}: {e}")
            return {
                "video_id": video_id,
                "available_languages": [],
                "has_manual": False,
                "has_automatic": False,
                "error": str(e)
            }