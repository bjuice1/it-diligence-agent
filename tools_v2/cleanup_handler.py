"""
Cleanup Handler for Interrupt Signals

Handles cleanup of temporary files and resources when process is interrupted (Ctrl+C).
"""

import signal
import atexit
import tempfile
import os
import logging
from typing import Set, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Global registry of temporary files to clean up
_temp_files: Set[str] = set()
_cleanup_registered = False


def register_temp_file(filepath: str):
    """
    Register a temporary file for cleanup on interrupt.
    
    Args:
        filepath: Path to temporary file
    """
    global _temp_files
    _temp_files.add(filepath)
    
    # Register cleanup handlers if not already done
    if not _cleanup_registered:
        _register_handlers()


def unregister_temp_file(filepath: str):
    """
    Unregister a temporary file (e.g., after successful completion).
    
    Args:
        filepath: Path to temporary file
    """
    global _temp_files
    _temp_files.discard(filepath)


def cleanup_temp_files():
    """
    Clean up all registered temporary files.
    
    Called on normal exit or interrupt.
    """
    global _temp_files
    if not _temp_files:
        return
    
    logger.info(f"Cleaning up {len(_temp_files)} temporary files...")
    cleaned = 0
    failed = 0
    
    for filepath in list(_temp_files):
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
                cleaned += 1
                logger.debug(f"Cleaned up: {filepath}")
        except OSError as e:
            failed += 1
            logger.warning(f"Failed to clean up {filepath}: {e}")
    
    _temp_files.clear()
    
    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} temporary files")
    if failed > 0:
        logger.warning(f"Failed to clean up {failed} temporary files")


def _signal_handler(signum, frame):
    """Handle interrupt signals (SIGINT, SIGTERM)."""
    logger.warning(f"Received signal {signum}, cleaning up...")
    cleanup_temp_files()
    # Re-raise to allow normal exit
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


def _register_handlers():
    """Register signal handlers and atexit handler."""
    global _cleanup_registered
    
    if _cleanup_registered:
        return
    
    # Register atexit handler for normal exit
    atexit.register(cleanup_temp_files)
    
    # Register signal handlers for interrupts
    try:
        signal.signal(signal.SIGINT, _signal_handler)  # Ctrl+C
    except (ValueError, OSError):
        # Signal not available on this platform
        pass
    
    try:
        signal.signal(signal.SIGTERM, _signal_handler)  # Termination
    except (ValueError, OSError):
        # Signal not available on this platform
        pass
    
    _cleanup_registered = True
    logger.debug("Cleanup handlers registered")


# Auto-register on import
_register_handlers()
