"""
I/O Utilities with Retry Logic

Provides retry mechanisms for file operations to handle transient I/O errors.
"""

import time
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_io(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    exceptions: tuple = (IOError, OSError)
):
    """
    Decorator to retry I/O operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry on
    
    Example:
        @retry_io(max_retries=3)
        def save_file(path, data):
            with open(path, 'w') as f:
                json.dump(data, f)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"I/O error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"I/O error in {func.__name__} after {max_retries + 1} attempts: {e}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def safe_file_write(
    path: str,
    data: Any,
    mode: str = 'w',
    encoding: Optional[str] = 'utf-8',
    max_retries: int = 3
) -> None:
    """
    Safely write data to file with retry logic.
    
    Args:
        path: File path to write to
        data: Data to write (will be JSON serialized if dict/list)
        mode: File mode ('w', 'wb', etc.)
        encoding: Text encoding (None for binary mode)
        max_retries: Maximum retry attempts
    """
    import json
    import os
    
    @retry_io(max_retries=max_retries)
    def _write():
        # Ensure directory exists
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        if encoding:
            with open(path, mode, encoding=encoding) as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))
        else:
            with open(path, mode) as f:
                if isinstance(data, bytes):
                    f.write(data)
                else:
                    f.write(str(data))
    
    _write()


def safe_file_read(
    path: str,
    mode: str = 'r',
    encoding: Optional[str] = 'utf-8',
    max_retries: int = 3
) -> Any:
    """
    Safely read data from file with retry logic.
    
    Args:
        path: File path to read from
        mode: File mode ('r', 'rb', etc.)
        encoding: Text encoding (None for binary mode)
        max_retries: Maximum retry attempts
    
    Returns:
        File contents (parsed JSON if JSON file, otherwise string/bytes)
    """
    import json
    
    @retry_io(max_retries=max_retries)
    def _read():
        if encoding:
            with open(path, mode, encoding=encoding) as f:
                content = f.read()
                # Try to parse as JSON if it looks like JSON
                if content.strip().startswith(('{', '[')):
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        pass
                return content
        else:
            with open(path, mode) as f:
                return f.read()
    
    return _read()
