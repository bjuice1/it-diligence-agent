"""
File Hasher Utility

Provides SHA-256 hashing for document integrity verification.
Used by DocumentStore to create unique document identifiers and detect duplicates.

Key principle: Hash the raw bytes, not extracted text.
Text extraction can vary; bytes are immutable.
"""

import hashlib
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)

# Buffer size for reading large files (64KB chunks)
HASH_BUFFER_SIZE = 65536


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash (64 characters)

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IOError: If file cannot be read for other reasons
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(HASH_BUFFER_SIZE), b""):
                sha256_hash.update(chunk)
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

    hex_digest = sha256_hash.hexdigest()
    logger.debug(f"Computed hash for {file_path.name}: {hex_digest[:16]}...")

    return hex_digest


def compute_sha256_from_bytes(data: bytes) -> str:
    """
    Compute SHA-256 hash from bytes directly.

    Useful for hashing uploaded files before saving to disk.

    Args:
        data: Bytes to hash

    Returns:
        Hexadecimal string of the SHA-256 hash (64 characters)
    """
    if not isinstance(data, bytes):
        raise TypeError(f"Expected bytes, got {type(data).__name__}")

    sha256_hash = hashlib.sha256(data)
    return sha256_hash.hexdigest()


def verify_file_hash(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify that a file matches an expected hash.

    Args:
        file_path: Path to the file to verify
        expected_hash: Expected SHA-256 hash (hexadecimal string)

    Returns:
        True if hash matches, False otherwise
    """
    try:
        actual_hash = compute_sha256(file_path)
        matches = actual_hash.lower() == expected_hash.lower()

        if not matches:
            logger.warning(
                f"Hash mismatch for {file_path}: "
                f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
            )

        return matches
    except Exception as e:
        logger.error(f"Error verifying hash for {file_path}: {e}")
        return False


def get_short_hash(full_hash: str, length: int = 8) -> str:
    """
    Get a shortened version of a hash for display purposes.

    Args:
        full_hash: Full SHA-256 hash (64 characters)
        length: Number of characters to return (default 8)

    Returns:
        First N characters of the hash
    """
    return full_hash[:length]
