"""Transcript models for yt-dlp fallback functionality."""

from typing import Dict, List, Optional, Any
from datetime import timedelta
from pydantic import BaseModel, Field, validator

from .base import BaseYouTubeModel


class TranscriptSegment(BaseYouTubeModel):
    """Individual transcript segment."""
    text: str = Field(description="Transcript text")
    start: float = Field(description="Start time in seconds")
    duration: float = Field(description="Duration in seconds")
    end: Optional[float] = Field(None, description="End time in seconds")
    
    @validator('end', always=True)
    def calculate_end_time(cls, v, values):
        """Calculate end time if not provided."""
        if v is None and 'start' in values and 'duration' in values:
            return values['start'] + values['duration']
        return v
    
    def get_formatted_time(self) -> str:
        """Get formatted timestamp (MM:SS or HH:MM:SS)."""
        total_seconds = int(self.start)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        return {
            "text": self.text,
            "start": self.start,
            "duration": self.duration,
            "end": self.end,
            "timestamp": self.get_formatted_time()
        }


class TranscriptInfo(BaseYouTubeModel):
    """Complete transcript information."""
    video_id: str = Field(description="Video ID")
    language: Optional[str] = Field(None, description="Transcript language")
    language_code: Optional[str] = Field(None, description="Language code")
    is_generated: Optional[bool] = Field(None, description="Whether transcript is auto-generated")
    segments: List[TranscriptSegment] = Field(description="Transcript segments")
    
    def get_full_text(self, include_timestamps: bool = False) -> str:
        """Get full transcript as text."""
        if include_timestamps:
            return "\n".join([
                f"[{segment.get_formatted_time()}] {segment.text}"
                for segment in self.segments
            ])
        else:
            return " ".join([segment.text for segment in self.segments])
    
    def search_text(self, query: str, case_sensitive: bool = False) -> List[TranscriptSegment]:
        """Search for text within transcript."""
        if not case_sensitive:
            query = query.lower()
        
        matching_segments = []
        for segment in self.segments:
            text = segment.text if case_sensitive else segment.text.lower()
            if query in text:
                matching_segments.append(segment)
        
        return matching_segments
    
    def get_segments_in_range(self, start_time: float, end_time: float) -> List[TranscriptSegment]:
        """Get segments within a time range."""
        return [
            segment for segment in self.segments
            if segment.start >= start_time and segment.end <= end_time
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        return {
            "video_id": self.video_id,
            "language": self.language,
            "language_code": self.language_code,
            "is_generated": self.is_generated,
            "segments": [segment.to_dict() for segment in self.segments],
            "full_text": self.get_full_text(),
            "full_text_with_timestamps": self.get_full_text(include_timestamps=True),
            "total_segments": len(self.segments),
            "duration": max([segment.end for segment in self.segments], default=0),
            "metadata": {
                "source": "yt-dlp",
                "extraction_method": "fallback"
            }
        }