"""
Circuit Breaker Pattern for API Calls

Prevents cascading failures by stopping retries when API is consistently failing.
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable, TypeVar
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes (half-open)
    timeout: float = 60.0  # Seconds before trying half-open
    expected_exception: type = Exception  # Exception type that indicates failure


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    failures: int = 0
    successes: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    rejected_requests: int = 0


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading API failures.
    
    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60.0
        )
        
        try:
            result = breaker.call(api_function, arg1, arg2)
        except CircuitBreakerOpenError:
            # Circuit is open, service is down
            pass
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self.stats.total_requests += 1
        
        # Check circuit state
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed, move to half-open
            if self.stats.last_failure_time:
                elapsed = time.time() - self.stats.last_failure_time
                if elapsed >= self.config.timeout:
                    logger.info("Circuit breaker: Moving to HALF_OPEN state")
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.successes = 0
                else:
                    self.stats.rejected_requests += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. "
                        f"Last failure: {elapsed:.1f}s ago. "
                        f"Will retry in {self.config.timeout - elapsed:.1f}s"
                    )
        
        # Try to execute
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        self.stats.last_success_time = time.time()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.successes += 1
            if self.stats.successes >= self.config.success_threshold:
                logger.info("Circuit breaker: Moving to CLOSED state (service recovered)")
                self.stats.state = CircuitState.CLOSED
                self.stats.failures = 0
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success (sliding window)
            if self.stats.failures > 0:
                self.stats.failures = max(0, self.stats.failures - 1)
    
    def _on_failure(self):
        """Handle failed call."""
        self.stats.last_failure_time = time.time()
        self.stats.failures += 1
        
        if self.stats.state == CircuitState.HALF_OPEN:
            # Failed during half-open, go back to open
            logger.warning("Circuit breaker: Service still failing, moving back to OPEN")
            self.stats.state = CircuitState.OPEN
            self.stats.successes = 0
        elif self.stats.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.stats.failures >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker: Opening circuit after {self.stats.failures} failures"
                )
                self.stats.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        logger.info("Circuit breaker: Manually reset to CLOSED")
        self.stats.state = CircuitState.CLOSED
        self.stats.failures = 0
        self.stats.successes = 0
        self.stats.last_failure_time = None
    
    def get_stats(self) -> dict:
        """Get current circuit breaker statistics."""
        return {
            "state": self.stats.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_requests": self.stats.total_requests,
            "rejected_requests": self.stats.rejected_requests,
            "last_failure": self.stats.last_failure_time,
            "last_success": self.stats.last_success_time
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected."""
    pass
