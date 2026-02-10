"""
Evidence Quote Validation

Validates that evidence quotes actually exist in the source document
using fuzzy matching to handle minor variations.
"""

from typing import Optional, Dict
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

try:
    from config_v2 import QUOTE_VALIDATION_THRESHOLD, ENABLE_FACT_VALIDATION
except ImportError:
    QUOTE_VALIDATION_THRESHOLD = 0.85
    ENABLE_FACT_VALIDATION = True


def validate_evidence_quote(
    quote: str,
    source_document_text: Optional[str] = None,
    threshold: float = QUOTE_VALIDATION_THRESHOLD
) -> Dict[str, any]:
    """
    Validate that an evidence quote exists in the source document.
    
    Uses fuzzy matching to handle minor variations (whitespace, punctuation, etc.).
    
    Args:
        quote: The exact quote to validate
        source_document_text: Full text of the source document (optional)
        threshold: Similarity threshold (0.0-1.0)
    
    Returns:
        Dict with:
        - valid: bool
        - similarity: float (if source provided)
        - message: str
    """
    if not ENABLE_FACT_VALIDATION:
        return {"valid": True, "message": "Validation disabled"}
    
    if not quote or len(quote.strip()) < 10:
        return {
            "valid": False,
            "similarity": 0.0,
            "message": "Quote too short or empty"
        }
    
    if not source_document_text:
        # Can't validate without source - warn but don't fail
        logger.warning(f"Cannot validate quote (no source document): {quote[:50]}...")
        return {
            "valid": True,  # Don't fail if source not available
            "similarity": None,
            "message": "Source document not available for validation"
        }
    
    # Normalize both quote and source for comparison
    quote_normalized = _normalize_text(quote)
    source_normalized = _normalize_text(source_document_text)
    
    # Check if quote appears in source (exact match after normalization)
    if quote_normalized in source_normalized:
        return {
            "valid": True,
            "similarity": 1.0,
            "message": "Quote found in source document"
        }
    
    # Try fuzzy matching - look for best match in source
    # Split source into chunks and find best match
    chunk_size = max(len(quote_normalized) * 2, 500)
    best_similarity = 0.0
    best_match_pos = -1
    
    for i in range(0, len(source_normalized), chunk_size // 2):
        chunk = source_normalized[i:i + chunk_size]
        similarity = SequenceMatcher(None, quote_normalized, chunk).ratio()
        if similarity > best_similarity:
            best_similarity = similarity
            best_match_pos = i
    
    # Also try sliding window for better accuracy
    if len(quote_normalized) < len(source_normalized):
        for i in range(len(source_normalized) - len(quote_normalized) + 1):
            chunk = source_normalized[i:i + len(quote_normalized)]
            similarity = SequenceMatcher(None, quote_normalized, chunk).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_pos = i
    
    is_valid = best_similarity >= threshold
    
    if not is_valid:
        logger.warning(
            f"Evidence quote validation failed: similarity {best_similarity:.2f} < {threshold} "
            f"for quote: {quote[:100]}..."
        )
    
    return {
        "valid": is_valid,
        "similarity": best_similarity,
        "match_position": best_match_pos if is_valid else None,
        "message": f"Quote {'validated' if is_valid else 'not found'} in source (similarity: {best_similarity:.2f})"
    }


def _normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    
    Removes extra whitespace, converts to lowercase, removes punctuation.
    """
    import re
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation (optional - can be too aggressive)
    # text = re.sub(r'[^\w\s]', '', text)
    return text.strip()
