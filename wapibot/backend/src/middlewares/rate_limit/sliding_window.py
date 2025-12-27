"""Sliding window rate limiter.

In-memory sliding window algorithm with automatic expiration.
"""

import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Deque


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter (suitable for single server)."""

    def __init__(self):
        """Initialize rate limiter."""
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 1
    ) -> bool:
        """Check if request is within rate limit.

        Uses sliding window algorithm with automatic expiration.

        Args:
            key: Unique key (e.g., "192.168.1.10:/api/v1/chat")
            limit: Maximum requests allowed per window
            window_seconds: Window size in seconds

        Returns:
            True if allowed, False if exceeded
        """
        async with self._lock:
            now = time.time()
            window = self._windows[key]

            # Remove expired timestamps
            while window and window[0] < (now - window_seconds):
                window.popleft()

            # Check limit
            if len(window) >= limit:
                return False  # Rate limit exceeded

            # Add current timestamp
            window.append(now)
            return True

    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int = 1
    ) -> int:
        """Get remaining requests in current window.

        Args:
            key: Unique key
            limit: Maximum requests allowed
            window_seconds: Window size in seconds

        Returns:
            Number of requests remaining
        """
        async with self._lock:
            now = time.time()
            window = self._windows[key]

            # Remove expired
            while window and window[0] < (now - window_seconds):
                window.popleft()

            return max(0, limit - len(window))

    async def reset_key(self, key: str):
        """Reset rate limit for a specific key.

        Args:
            key: Key to reset
        """
        async with self._lock:
            if key in self._windows:
                del self._windows[key]

    async def cleanup_expired(self, window_seconds: int = 60):
        """Cleanup expired entries (call periodically).

        Args:
            window_seconds: Window size for cleanup
        """
        async with self._lock:
            now = time.time()
            keys_to_delete = []

            for key, window in self._windows.items():
                # Remove expired timestamps
                while window and window[0] < (now - window_seconds):
                    window.popleft()

                # Mark empty windows for deletion
                if not window:
                    keys_to_delete.append(key)

            # Delete empty windows
            for key in keys_to_delete:
                del self._windows[key]


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()
