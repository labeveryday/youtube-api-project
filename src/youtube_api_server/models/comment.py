"""Comment models for YouTube API data."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .base import BaseYouTubeModel


class CommentSnippet(BaseYouTubeModel):
    """YouTube comment snippet data."""
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    text_display: str = Field(alias="textDisplay", description="Comment text (formatted)")
    text_original: str = Field(alias="textOriginal", description="Comment text (original)")
    author_display_name: str = Field(alias="authorDisplayName", description="Author display name")
    author_profile_image_url: str = Field(alias="authorProfileImageUrl", description="Author profile image")
    author_channel_url: Optional[str] = Field(None, alias="authorChannelUrl", description="Author channel URL")
    author_channel_id: Optional[Dict[str, str]] = Field(None, alias="authorChannelId", description="Author channel ID")
    can_rate: bool = Field(alias="canRate", description="Whether comment can be rated")
    total_reply_count: int = Field(default=0, alias="totalReplyCount", description="Number of replies")
    like_count: int = Field(alias="likeCount", description="Number of likes")
    moderation_status: Optional[str] = Field(None, alias="moderationStatus", description="Moderation status")
    published_at: datetime = Field(alias="publishedAt", description="Comment publish date")
    updated_at: datetime = Field(alias="updatedAt", description="Comment update date")
    parent_id: Optional[str] = Field(None, alias="parentId", description="Parent comment ID for replies")
    
    @validator('like_count', 'total_reply_count', pre=True)
    def parse_string_numbers(cls, v):
        """Convert string numbers to integers."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 0
        return v if v is not None else 0


class Comment(BaseYouTubeModel):
    """YouTube comment."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    id: str = Field(description="Comment ID")
    snippet: CommentSnippet = Field(description="Comment snippet")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        return {
            "id": self.id,
            "author": self.snippet.author_display_name,
            "text": self.snippet.text_display,
            "text_original": self.snippet.text_original,
            "likes": self.snippet.like_count,
            "published_at": self.snippet.published_at.isoformat(),
            "updated_at": self.snippet.updated_at.isoformat(),
            "author_channel_url": self.snippet.author_channel_url,
            "author_profile_image": self.snippet.author_profile_image_url,
            "can_rate": self.snippet.can_rate,
            "is_reply": self.snippet.parent_id is not None,
            "parent_id": self.snippet.parent_id
        }


class CommentThreadSnippet(BaseYouTubeModel):
    """YouTube comment thread snippet."""
    channel_id: Optional[str] = Field(None, alias="channelId", description="Channel ID")
    video_id: str = Field(alias="videoId", description="Video ID")
    top_level_comment: Comment = Field(alias="topLevelComment", description="Top level comment")
    can_reply: bool = Field(alias="canReply", description="Whether thread can be replied to")
    total_reply_count: int = Field(alias="totalReplyCount", description="Total number of replies")
    is_public: bool = Field(alias="isPublic", description="Whether thread is public")
    
    @validator('total_reply_count', pre=True)
    def parse_string_numbers(cls, v):
        """Convert string numbers to integers."""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 0
        return v if v is not None else 0


class CommentThreadReplies(BaseYouTubeModel):
    """YouTube comment thread replies."""
    comments: List[Comment] = Field(description="Reply comments")


class CommentThread(BaseYouTubeModel):
    """YouTube comment thread."""
    kind: str = Field(description="API resource type")
    etag: str = Field(description="ETag")
    id: str = Field(description="Thread ID")
    snippet: CommentThreadSnippet = Field(description="Thread snippet")
    replies: Optional[CommentThreadReplies] = Field(None, description="Thread replies")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        top_comment = self.snippet.top_level_comment.to_dict()
        
        result = {
            "id": self.id,
            "video_id": self.snippet.video_id,
            "top_comment": top_comment,
            "can_reply": self.snippet.can_reply,
            "is_public": self.snippet.is_public,
            "total_reply_count": self.snippet.total_reply_count,
            "replies": []
        }
        
        if self.replies and self.replies.comments:
            result["replies"] = [reply.to_dict() for reply in self.replies.comments]
        
        # Add convenience fields from top comment
        result.update({
            "author": top_comment["author"],
            "text": top_comment["text"],
            "likes": top_comment["likes"],
            "published_at": top_comment["published_at"]
        })
        
        return result


class CommentThreadListResponse(BaseYouTubeModel):
    """YouTube comment thread list response."""
    kind: str = Field(description="API resource type")
    etag: Optional[str] = Field(None, description="ETag")
    next_page_token: Optional[str] = Field(None, alias="nextPageToken", description="Next page token")
    page_info: Optional[Dict[str, int]] = Field(None, alias="pageInfo", description="Page information")
    items: List[CommentThread] = Field(description="Comment threads")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MCP responses."""
        return {
            "comments": [thread.to_dict() for thread in self.items],
            "total_results": len(self.items),
            "next_page_token": self.next_page_token,
            "metadata": {
                "api_source": "YouTube Data API v3",
                "reliable": True,
                "has_more": self.next_page_token is not None
            }
        }