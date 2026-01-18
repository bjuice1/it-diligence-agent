"""
Rate Limiter for API Calls

Provides semaphore-based rate limiting to prevent hitting API rate limits
when multiple agents run in parallel.
"""

import threading
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class APIRateLimiter:
    """
    Thread-safe rate limiter for API calls using semaphore.
    
    Limits concurrent API calls across all agents to prevent rate limit errors.
    Uses a semaphore to control concurrency and tracks timing for rate limiting.
    """
    
    _instance: Optional['APIRateLimiter'] = None
    _lock = threading.Lock()
    
    def __init__(self, max_concurrent: int = 3, requests_per_minute: int = 40):
        """
        Initialize rate limiter.
        
        Args:
            max_concurrent: Maximum concurrent API calls allowed
            requests_per_minute: Target requests per minute (for tracking)
        """
        self.semaphore = threading.Semaphore(max_concurrent)
        self.requests_per_minute = requests_per_minute
        self.request_times: list = []
        self.request_times_lock = threading.Lock()
        self.max_concurrent = max_concurrent
        
    @classmethod
    def get_instance(cls, max_concurrent: int = 3, requests_per_minute: int = 40) -> 'APIRateLimiter':
        """Get singleton instance of rate limiter."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_concurrent, requests_per_minute)
        return cls._instance
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make an API call.
        
        Blocks if too many concurrent calls are in progress.
        
        Args:
            timeout: Maximum time to wait (None = wait indefinitely)
        
        Returns:
            True if acquired, False if timeout
        """
        acquired = self.semaphore.acquire(timeout=timeout)
        if acquired:
            # Track request time for rate limiting
            with self.request_times_lock:
                now = time.time()
                self.request_times.append(now)
                # Clean up old entries (older than 1 minute)
                self.request_times = [t for t in self.request_times if now - t < 60]
                
                # If we're approaching rate limit, add small delay
                recent_requests = len([t for t in self.request_times if now - t < 60])
                if recent_requests >= self.requests_per_minute * 0.9:  # 90% of limit
                    delay = 60.0 / self.requests_per_minute
                    logger.debug(f"Rate limit approaching ({recent_requests}/{self.requests_per_minute}), delaying {delay:.2f}s")
                    time.sleep(delay)
        
        return acquired
    
    def release(self):
        """Release permission after API call completes."""
        self.semaphore.release()
    
    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False
    
    def get_stats(self) -> dict:
        """Get current rate limiting statistics."""
        with self.request_times_lock:
            now = time.time()
            recent_requests = len([t for t in self.request_times if now - t < 60])
            available = self.semaphore._value  # Current semaphore value
        
        return {
            "max_concurrent": self.max_concurrent,
            "available_slots": available,
            "requests_last_minute": recent_requests,
            "requests_per_minute_limit": self.requests_per_minute
        }
