"""Rate limiting utilities for YouTube API requests."""

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class RateLimiterState:
    """State tracking for rate limiter."""
    requests_made: int = 0
    window_start: float = field(default_factory=time.time)
    daily_requests: int = 0
    daily_window_start: float = field(default_factory=time.time)


class AsyncRateLimiter:
    """Async rate limiter for YouTube API requests."""
    
    def __init__(self, requests_per_second: float = 10.0, daily_limit: int = 10000):
        self.requests_per_second = requests_per_second
        self.daily_limit = daily_limit
        self.state = RateLimiterState()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if necessary."""
        async with self._lock:
            current_time = time.time()
            
            # Reset daily counter if new day
            if current_time - self.state.daily_window_start >= 86400:  # 24 hours
                self.state.daily_requests = 0
                self.state.daily_window_start = current_time
            
            # Check daily limit
            if self.state.daily_requests >= self.daily_limit:
                raise Exception(f"Daily API quota limit of {self.daily_limit} exceeded")
            
            # Reset per-second counter if new window
            if current_time - self.state.window_start >= 1.0:
                self.state.requests_made = 0
                self.state.window_start = current_time
            
            # Check if we need to wait
            if self.state.requests_made >= self.requests_per_second:
                wait_time = 1.0 - (current_time - self.state.window_start)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Reset counters after waiting
                    self.state.requests_made = 0
                    self.state.window_start = time.time()
            
            # Track the request
            self.state.requests_made += 1
            self.state.daily_requests += 1
    
    def get_stats(self) -> Dict[str, any]:
        """Get current rate limiter statistics."""
        current_time = time.time()
        return {
            "requests_per_second_limit": self.requests_per_second,
            "daily_limit": self.daily_limit,
            "current_window_requests": self.state.requests_made,
            "daily_requests_made": self.state.daily_requests,
            "daily_requests_remaining": self.daily_limit - self.state.daily_requests,
            "window_time_remaining": 1.0 - (current_time - self.state.window_start),
            "daily_time_remaining": 86400 - (current_time - self.state.daily_window_start)
        }