"""
Rate Limiter for API Calls

Provides semaphore-based rate limiting to prevent hitting API rate limits
when multiple agents run in parallel.

Enhanced with:
- Point 95: API error classification (retriable vs fatal)
- Point 96: Configurable rate limits with validation
- Point 97: Per-user rate limiting
- Point 98: Circuit breaker monitoring
- Point 99: Graceful degradation support
- Point 100: Request queuing
"""

import threading
import time
from typing import Optional, Dict, List, Any, Callable
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Point 95: API Error Classification
# =============================================================================

class APIErrorType(Enum):
    """Classification of API errors."""
    RETRIABLE = "retriable"  # Can retry (rate limit, timeout, 5xx)
    FATAL = "fatal"  # Should not retry (auth, invalid request, 4xx)
    UNKNOWN = "unknown"


@dataclass
class APIError:
    """Structured API error with classification."""
    error_type: APIErrorType
    status_code: Optional[int]
    message: str
    is_retriable: bool
    retry_after: Optional[float] = None  # Seconds to wait before retry
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def classify_error(cls, error: Exception, status_code: Optional[int] = None) -> 'APIError':
        """
        Classify an API error as retriable or fatal.

        Retriable errors (should retry with backoff):
        - Rate limit errors (429)
        - Server errors (500, 502, 503, 504)
        - Timeout errors
        - Connection errors

        Fatal errors (should not retry):
        - Authentication errors (401, 403)
        - Bad request errors (400)
        - Not found errors (404)
        - Invalid API key
        """
        error_str = str(error).lower()

        # Check for rate limit
        if status_code == 429 or "rate limit" in error_str or "too many requests" in error_str:
            # Try to extract retry-after from error
            retry_after = 60.0  # Default 60 seconds
            if hasattr(error, 'response') and error.response:
                retry_after = float(error.response.headers.get('Retry-After', 60))
            return cls(
                error_type=APIErrorType.RETRIABLE,
                status_code=status_code or 429,
                message=str(error),
                is_retriable=True,
                retry_after=retry_after
            )

        # Check for server errors
        if status_code and 500 <= status_code < 600:
            return cls(
                error_type=APIErrorType.RETRIABLE,
                status_code=status_code,
                message=str(error),
                is_retriable=True,
                retry_after=5.0
            )

        # Check for timeout
        if "timeout" in error_str or "timed out" in error_str:
            return cls(
                error_type=APIErrorType.RETRIABLE,
                status_code=None,
                message=str(error),
                is_retriable=True,
                retry_after=2.0
            )

        # Check for connection errors
        if "connection" in error_str or "network" in error_str:
            return cls(
                error_type=APIErrorType.RETRIABLE,
                status_code=None,
                message=str(error),
                is_retriable=True,
                retry_after=5.0
            )

        # Check for authentication errors (fatal)
        if status_code in [401, 403] or "unauthorized" in error_str or "forbidden" in error_str:
            return cls(
                error_type=APIErrorType.FATAL,
                status_code=status_code or 401,
                message=str(error),
                is_retriable=False
            )

        # Check for bad request (fatal)
        if status_code == 400 or "invalid" in error_str:
            return cls(
                error_type=APIErrorType.FATAL,
                status_code=status_code or 400,
                message=str(error),
                is_retriable=False
            )

        # Default to unknown but retriable
        return cls(
            error_type=APIErrorType.UNKNOWN,
            status_code=status_code,
            message=str(error),
            is_retriable=True,
            retry_after=10.0
        )


# =============================================================================
# Point 96: Rate Limit Configuration
# =============================================================================

@dataclass
class RateLimitConfig:
    """
    Configurable rate limit settings with validation.

    Anthropic API limits (as of 2024):
    - claude-3-opus: 4,000 requests/min, 400,000 tokens/min
    - claude-3-sonnet: 4,000 requests/min, 400,000 tokens/min
    - claude-3-haiku: 4,000 requests/min, 400,000 tokens/min

    Default conservative settings to stay well under limits.
    """
    requests_per_minute: int = 40  # Conservative default
    max_concurrent: int = 3
    burst_limit: int = 10  # Max requests in burst
    min_delay_seconds: float = 0.5  # Minimum delay between requests

    # Tier-based limits (can be upgraded based on API tier)
    TIER_LIMITS = {
        "free": {"rpm": 20, "concurrent": 2},
        "basic": {"rpm": 40, "concurrent": 3},
        "pro": {"rpm": 100, "concurrent": 5},
        "enterprise": {"rpm": 500, "concurrent": 10}
    }

    def validate(self) -> List[str]:
        """Validate configuration and return warnings."""
        warnings = []

        if self.requests_per_minute > 500:
            warnings.append(f"requests_per_minute ({self.requests_per_minute}) may exceed API tier limits")

        if self.max_concurrent > 10:
            warnings.append(f"max_concurrent ({self.max_concurrent}) is very high, may cause issues")

        if self.min_delay_seconds < 0.1:
            warnings.append("min_delay_seconds < 0.1 may cause rate limit errors")

        return warnings

    @classmethod
    def for_tier(cls, tier: str) -> 'RateLimitConfig':
        """Get configuration for a specific API tier."""
        limits = cls.TIER_LIMITS.get(tier, cls.TIER_LIMITS["basic"])
        return cls(
            requests_per_minute=limits["rpm"],
            max_concurrent=limits["concurrent"]
        )


# =============================================================================
# Point 98: Circuit Breaker
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    last_success_time: Optional[datetime]
    time_in_current_state: float
    total_requests: int
    total_failures: int


class CircuitBreaker:
    """
    Circuit breaker pattern for API resilience.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, all requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._state_changed_at = time.time()
        self._total_requests = 0
        self._total_failures = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current state, checking for automatic recovery."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if time.time() - self._state_changed_at >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        logger.info(f"Circuit breaker: {self._state.value} -> {new_state.value}")
        self._state = new_state
        self._state_changed_at = time.time()
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state  # This checks for recovery

        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        else:  # HALF_OPEN
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

    def record_success(self):
        """Record a successful request."""
        with self._lock:
            self._success_count += 1
            self._total_requests += 1
            self._last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Recovery successful
                self._transition_to(CircuitState.CLOSED)
                self._failure_count = 0

    def record_failure(self, error: Optional[Exception] = None):
        """Record a failed request."""
        with self._lock:
            self._failure_count += 1
            self._total_failures += 1
            self._total_requests += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.HALF_OPEN:
                # Recovery failed, go back to open
                self._transition_to(CircuitState.OPEN)

    def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        with self._lock:
            return CircuitBreakerStats(
                state=self._state,
                failure_count=self._failure_count,
                success_count=self._success_count,
                last_failure_time=datetime.fromtimestamp(self._last_failure_time) if self._last_failure_time else None,
                last_success_time=datetime.fromtimestamp(self._last_success_time) if self._last_success_time else None,
                time_in_current_state=time.time() - self._state_changed_at,
                total_requests=self._total_requests,
                total_failures=self._total_failures
            )

    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._state_changed_at = time.time()


# =============================================================================
# Point 100: Request Queue
# =============================================================================

@dataclass
class QueuedRequest:
    """A request waiting in the queue."""
    id: str
    callback: Callable
    args: tuple
    kwargs: dict
    priority: int = 0  # Higher = more important
    queued_at: float = field(default_factory=time.time)
    timeout: float = 300.0  # 5 minute default timeout


class RequestQueue:
    """
    Queue for requests when rate limited.

    Instead of failing immediately, requests are queued and
    processed when capacity becomes available.
    """

    def __init__(self, max_size: int = 100, process_interval: float = 1.0):
        self.max_size = max_size
        self.process_interval = process_interval
        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._processing = False
        self._processor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def enqueue(self, request: QueuedRequest) -> bool:
        """
        Add a request to the queue.

        Returns:
            True if queued, False if queue is full
        """
        with self._lock:
            if len(self._queue) >= self.max_size:
                return False

            # Insert by priority (higher priority first)
            inserted = False
            for i, existing in enumerate(self._queue):
                if request.priority > existing.priority:
                    self._queue.insert(i, request)
                    inserted = True
                    break

            if not inserted:
                self._queue.append(request)

            logger.debug(f"Queued request {request.id}, queue size: {len(self._queue)}")
            return True

    def dequeue(self) -> Optional[QueuedRequest]:
        """Get the next request from the queue."""
        with self._lock:
            if not self._queue:
                return None

            # Check for expired requests
            now = time.time()
            while self._queue:
                request = self._queue[0]
                if now - request.queued_at > request.timeout:
                    self._queue.popleft()
                    logger.warning(f"Request {request.id} expired in queue")
                else:
                    break

            if self._queue:
                return self._queue.popleft()
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "max_size": self.max_size,
                "is_full": len(self._queue) >= self.max_size,
                "oldest_request_age": time.time() - self._queue[0].queued_at if self._queue else 0
            }

    def clear(self):
        """Clear all queued requests."""
        with self._lock:
            self._queue.clear()


class APIRateLimiter:
    """
    Thread-safe rate limiter for API calls using semaphore.

    Limits concurrent API calls across all agents to prevent rate limit errors.
    Uses a semaphore to control concurrency and tracks timing for rate limiting.

    Enhanced with:
    - Per-user rate limiting (Point 97)
    - Circuit breaker integration (Point 98)
    - Graceful degradation (Point 99)
    - Request queuing (Point 100)
    """

    _instance: Optional['APIRateLimiter'] = None
    _lock = threading.Lock()

    def __init__(
        self,
        max_concurrent: int = 3,
        requests_per_minute: int = 40,
        config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize rate limiter.

        Args:
            max_concurrent: Maximum concurrent API calls allowed
            requests_per_minute: Target requests per minute (for tracking)
            config: Optional RateLimitConfig for advanced settings
        """
        self.config = config or RateLimitConfig(
            requests_per_minute=requests_per_minute,
            max_concurrent=max_concurrent
        )

        # Validate config
        warnings = self.config.validate()
        for warning in warnings:
            logger.warning(f"Rate limit config: {warning}")

        self.semaphore = threading.Semaphore(self.config.max_concurrent)
        self.requests_per_minute = self.config.requests_per_minute
        self.request_times: list = []
        self.request_times_lock = threading.Lock()
        self.max_concurrent = self.config.max_concurrent

        # Point 97: Per-user rate limiting
        self._user_request_times: Dict[str, List[float]] = {}
        self._user_limits: Dict[str, int] = {}  # Custom per-user limits
        self._default_user_limit = requests_per_minute // 2  # Default: half of global

        # Point 98: Circuit breaker
        self.circuit_breaker = CircuitBreaker()

        # Point 100: Request queue
        self.request_queue = RequestQueue()

        # Point 99: Graceful degradation
        self._cached_results: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        self._degraded_mode = False

    @classmethod
    def get_instance(
        cls,
        max_concurrent: int = 3,
        requests_per_minute: int = 40
    ) -> 'APIRateLimiter':
        """Get singleton instance of rate limiter."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_concurrent, requests_per_minute)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    # =========================================================================
    # Point 97: Per-User Rate Limiting
    # =========================================================================

    def set_user_limit(self, user_id: str, requests_per_minute: int):
        """Set custom rate limit for a specific user."""
        self._user_limits[user_id] = requests_per_minute

    def check_user_limit(self, user_id: str) -> bool:
        """
        Check if user is within their rate limit.

        Args:
            user_id: Unique user identifier

        Returns:
            True if user can make request, False if rate limited
        """
        with self.request_times_lock:
            now = time.time()

            # Get user's request history
            if user_id not in self._user_request_times:
                self._user_request_times[user_id] = []

            # Clean old entries
            self._user_request_times[user_id] = [
                t for t in self._user_request_times[user_id]
                if now - t < 60
            ]

            # Check against user's limit
            user_limit = self._user_limits.get(user_id, self._default_user_limit)
            current_count = len(self._user_request_times[user_id])

            if current_count >= user_limit:
                logger.warning(f"User {user_id} rate limited: {current_count}/{user_limit}")
                return False

            return True

    def record_user_request(self, user_id: str):
        """Record a request for a user."""
        with self.request_times_lock:
            if user_id not in self._user_request_times:
                self._user_request_times[user_id] = []
            self._user_request_times[user_id].append(time.time())

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limiting stats for a specific user."""
        with self.request_times_lock:
            now = time.time()
            user_times = self._user_request_times.get(user_id, [])
            recent = [t for t in user_times if now - t < 60]
            user_limit = self._user_limits.get(user_id, self._default_user_limit)

            return {
                "user_id": user_id,
                "requests_last_minute": len(recent),
                "limit": user_limit,
                "remaining": max(0, user_limit - len(recent)),
                "reset_in_seconds": 60 - (now - min(recent)) if recent else 0
            }

    # =========================================================================
    # Point 99: Graceful Degradation
    # =========================================================================

    def cache_result(self, cache_key: str, result: Any, ttl: float = 300.0):
        """
        Cache a result for graceful degradation.

        Args:
            cache_key: Unique key for the cached result
            result: The result to cache
            ttl: Time to live in seconds (default 5 minutes)
        """
        with self._cache_lock:
            self._cached_results[cache_key] = {
                "result": result,
                "cached_at": time.time(),
                "ttl": ttl
            }

    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """
        Get a cached result if available and not expired.

        Args:
            cache_key: The cache key to look up

        Returns:
            Cached result or None if not found/expired
        """
        with self._cache_lock:
            if cache_key not in self._cached_results:
                return None

            cached = self._cached_results[cache_key]
            if time.time() - cached["cached_at"] > cached["ttl"]:
                del self._cached_results[cache_key]
                return None

            return cached["result"]

    def enter_degraded_mode(self):
        """Enter degraded mode - will return cached results when possible."""
        self._degraded_mode = True
        logger.warning("Entering degraded mode - will use cached results")

    def exit_degraded_mode(self):
        """Exit degraded mode - normal operation."""
        self._degraded_mode = False
        logger.info("Exiting degraded mode - normal operation resumed")

    def is_degraded(self) -> bool:
        """Check if in degraded mode."""
        return self._degraded_mode

    # =========================================================================
    # Core Rate Limiting (Enhanced)
    # =========================================================================

    def acquire(
        self,
        timeout: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Acquire permission to make an API call.

        Blocks if too many concurrent calls are in progress.
        Checks circuit breaker and per-user limits.

        Args:
            timeout: Maximum time to wait (None = wait indefinitely)
            user_id: Optional user ID for per-user rate limiting

        Returns:
            True if acquired, False if timeout or blocked
        """
        # Check circuit breaker first
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker OPEN - request blocked")
            return False

        # Check per-user limit if user_id provided
        if user_id and not self.check_user_limit(user_id):
            return False

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

            # Record user request if applicable
            if user_id:
                self.record_user_request(user_id)

        return acquired

    def release(self):
        """Release permission after API call completes."""
        self.semaphore.release()

    def record_success(self):
        """Record successful API call (for circuit breaker)."""
        self.circuit_breaker.record_success()
        if self._degraded_mode and self.circuit_breaker.state == CircuitState.CLOSED:
            self.exit_degraded_mode()

    def record_failure(self, error: Optional[Exception] = None):
        """Record failed API call (for circuit breaker)."""
        self.circuit_breaker.record_failure(error)
        if self.circuit_breaker.state == CircuitState.OPEN:
            self.enter_degraded_mode()

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.record_failure(exc_val)
        else:
            self.record_success()
        self.release()
        return False

    def get_stats(self) -> dict:
        """Get current rate limiting statistics."""
        with self.request_times_lock:
            now = time.time()
            recent_requests = len([t for t in self.request_times if now - t < 60])
            available = self.semaphore._value  # Current semaphore value

        cb_stats = self.circuit_breaker.get_stats()
        queue_stats = self.request_queue.get_stats()

        return {
            "max_concurrent": self.max_concurrent,
            "available_slots": available,
            "requests_last_minute": recent_requests,
            "requests_per_minute_limit": self.requests_per_minute,
            "degraded_mode": self._degraded_mode,
            "circuit_breaker": {
                "state": cb_stats.state.value,
                "failure_count": cb_stats.failure_count,
                "total_requests": cb_stats.total_requests,
                "total_failures": cb_stats.total_failures
            },
            "queue": queue_stats
        }

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        Point 98: Get comprehensive monitoring dashboard data.

        Returns all metrics needed for a monitoring UI.
        """
        stats = self.get_stats()
        cb_stats = self.circuit_breaker.get_stats()

        # Calculate health score
        failure_rate = cb_stats.total_failures / max(cb_stats.total_requests, 1)
        utilization = stats["requests_last_minute"] / stats["requests_per_minute_limit"]

        if cb_stats.state == CircuitState.OPEN:
            health = "critical"
        elif failure_rate > 0.2 or utilization > 0.9:
            health = "warning"
        else:
            health = "healthy"

        return {
            "health": health,
            "health_score": round(1.0 - failure_rate, 2),
            "rate_limiting": {
                "current_rpm": stats["requests_last_minute"],
                "max_rpm": stats["requests_per_minute_limit"],
                "utilization_pct": round(utilization * 100, 1),
                "available_slots": stats["available_slots"]
            },
            "circuit_breaker": {
                "state": cb_stats.state.value,
                "failure_count": cb_stats.failure_count,
                "success_count": cb_stats.success_count,
                "failure_rate_pct": round(failure_rate * 100, 1),
                "time_in_state_seconds": round(cb_stats.time_in_current_state, 1),
                "last_failure": cb_stats.last_failure_time.isoformat() if cb_stats.last_failure_time else None,
                "last_success": cb_stats.last_success_time.isoformat() if cb_stats.last_success_time else None
            },
            "queue": stats["queue"],
            "degraded_mode": stats["degraded_mode"],
            "cached_items": len(self._cached_results)
        }
