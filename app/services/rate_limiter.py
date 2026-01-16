"""Rate limiting service for abuse prevention."""

import time
from collections import defaultdict
from functools import wraps
from typing import Optional

from flask import request, session


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 3600):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds (default: 1 hour)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self) -> str:
        """Get a unique identifier for the client."""
        # Try session ID first
        if "rate_limit_id" not in session:
            session["rate_limit_id"] = str(time.time())

        # Combine with IP for better tracking
        client_ip = request.remote_addr or "unknown"
        return f"{session['rate_limit_id']}:{client_ip}"

    def _cleanup_old_requests(self, client_id: str) -> None:
        """Remove requests outside the current window."""
        current_time = time.time()
        cutoff = current_time - self.window_seconds

        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > cutoff
        ]

    def is_allowed(self, client_id: Optional[str] = None) -> bool:
        """
        Check if a request is allowed.

        Args:
            client_id: Optional client identifier (auto-detected if not provided)

        Returns:
            True if request is allowed, False if rate limited
        """
        if client_id is None:
            client_id = self._get_client_id()

        self._cleanup_old_requests(client_id)

        return len(self.requests[client_id]) < self.max_requests

    def record_request(self, client_id: Optional[str] = None) -> None:
        """
        Record a request for rate limiting.

        Args:
            client_id: Optional client identifier (auto-detected if not provided)
        """
        if client_id is None:
            client_id = self._get_client_id()

        self.requests[client_id].append(time.time())

    def get_remaining(self, client_id: Optional[str] = None) -> int:
        """
        Get remaining requests in current window.

        Args:
            client_id: Optional client identifier

        Returns:
            Number of remaining allowed requests
        """
        if client_id is None:
            client_id = self._get_client_id()

        self._cleanup_old_requests(client_id)

        return max(0, self.max_requests - len(self.requests[client_id]))

    def get_reset_time(self, client_id: Optional[str] = None) -> Optional[float]:
        """
        Get time until rate limit resets.

        Args:
            client_id: Optional client identifier

        Returns:
            Seconds until oldest request expires, or None if no requests
        """
        if client_id is None:
            client_id = self._get_client_id()

        self._cleanup_old_requests(client_id)

        if not self.requests[client_id]:
            return None

        oldest = min(self.requests[client_id])
        return (oldest + self.window_seconds) - time.time()


# Global rate limiter instance
analysis_rate_limiter = RateLimiter(max_requests=10, window_seconds=3600)


def rate_limit(limiter: RateLimiter = analysis_rate_limiter):
    """
    Decorator to apply rate limiting to a route.

    Args:
        limiter: RateLimiter instance to use

    Returns:
        Decorated function
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not limiter.is_allowed():
                from flask import render_template

                reset_time = limiter.get_reset_time()
                reset_minutes = int(reset_time / 60) if reset_time else 60

                return render_template(
                    "error.html",
                    error=f"Rate limit exceeded. You can perform {limiter.max_requests} analyses per hour. "
                    f"Please try again in {reset_minutes} minutes.",
                ), 429

            limiter.record_request()
            return f(*args, **kwargs)

        return decorated_function

    return decorator
