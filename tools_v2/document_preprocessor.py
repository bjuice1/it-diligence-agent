"""
Document Preprocessor

Centralized text cleaning and normalization for all document types.
Call this BEFORE any parsing or chunking operations.

Handles:
- Private-use Unicode (U+E000 to U+F8FF)
- Citation artifacts (filecite patterns)
- Control characters
- Whitespace normalization
"""

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DocumentPreprocessor:
    """
    Cleans and normalizes document text before parsing.

    Usage:
        preprocessor = DocumentPreprocessor()
        clean_text = preprocessor.clean(raw_text)

    Or use class method for one-off cleaning:
        clean_text = DocumentPreprocessor.clean_text(raw_text)
    """

    # Private Use Area (PUA) - full range
    PRIVATE_USE_PATTERN = re.compile(r'[\ue000-\uf8ff]+')

    # Supplementary PUA (rarely seen but included for completeness)
    SUPPLEMENTARY_PUA_PATTERN = re.compile(r'[\U000f0000-\U000ffffd\U00100000-\U0010fffd]+')

    # Citation artifacts (filecite, oaicite, etc.)
    CITATION_PATTERN = re.compile(r'(?:file|oai)cite[^\s\]]*(?:\][^\]]*\])?', re.IGNORECASE)

    # Control characters (keep newlines, tabs)
    CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

    # Replacement character (indicates encoding error)
    REPLACEMENT_CHAR_PATTERN = re.compile(r'\ufffd+')

    # Multiple spaces/tabs to single space
    MULTI_SPACE_PATTERN = re.compile(r'[ \t]+')

    # Multiple newlines to max 2
    MULTI_NEWLINE_PATTERN = re.compile(r'\n{3,}')

    def __init__(self, aggressive: bool = False):
        """
        Initialize preprocessor.

        Args:
            aggressive: If True, also normalize fancy quotes, dashes, etc.
        """
        self.aggressive = aggressive
        self.stats = {
            'private_use_removed': 0,
            'citations_removed': 0,
            'control_chars_removed': 0,
        }

    def clean(self, text: str) -> str:
        """
        Clean document text.

        Args:
            text: Raw text from document

        Returns:
            Cleaned text ready for parsing
        """
        if not text:
            return text

        original_len = len(text)

        # Step 1: Remove private-use Unicode characters
        text, pua_count = self._remove_private_use(text)
        self.stats['private_use_removed'] += pua_count

        # Step 2: Remove citation artifacts
        text, cite_count = self._remove_citations(text)
        self.stats['citations_removed'] += cite_count

        # Step 3: Remove control characters
        text = self.CONTROL_CHAR_PATTERN.sub('', text)

        # Step 4: Replace replacement characters with space
        text = self.REPLACEMENT_CHAR_PATTERN.sub(' ', text)

        # Step 5: Normalize whitespace
        text = self.MULTI_SPACE_PATTERN.sub(' ', text)
        text = self.MULTI_NEWLINE_PATTERN.sub('\n\n', text)

        # Step 6: Aggressive normalization (optional)
        if self.aggressive:
            text = self._normalize_typography(text)

        # Trim
        text = text.strip()

        # Log if significant cleaning occurred
        cleaned_len = len(text)
        if original_len - cleaned_len > 100:
            logger.info(f"Preprocessor removed {original_len - cleaned_len} chars "
                       f"({self.stats['private_use_removed']} PUA, "
                       f"{self.stats['citations_removed']} citations)")

        return text

    def _remove_private_use(self, text: str) -> Tuple[str, int]:
        """Remove private-use Unicode characters."""
        matches = self.PRIVATE_USE_PATTERN.findall(text)
        count = sum(len(m) for m in matches)
        text = self.PRIVATE_USE_PATTERN.sub('', text)
        text = self.SUPPLEMENTARY_PUA_PATTERN.sub('', text)
        return text, count

    def _remove_citations(self, text: str) -> Tuple[str, int]:
        """Remove citation artifacts like filecite markers."""
        matches = self.CITATION_PATTERN.findall(text)
        count = len(matches)
        text = self.CITATION_PATTERN.sub('', text)
        return text, count

    def _normalize_typography(self, text: str) -> str:
        """Normalize fancy typography to ASCII equivalents."""
        replacements = {
            '"': '"', '"': '"',  # Smart quotes
            ''': "'", ''': "'",  # Smart apostrophes
            '–': '-', '—': '-',  # En/em dashes
            '…': '...',          # Ellipsis
            '\u00a0': ' ',       # Non-breaking space
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @classmethod
    def clean_text(cls, text: str, aggressive: bool = False) -> str:
        """Class method for one-off cleaning."""
        return cls(aggressive=aggressive).clean(text)

    def get_stats(self) -> Dict[str, int]:
        """Get cleaning statistics."""
        return dict(self.stats)

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {k: 0 for k in self.stats}


# Convenience function
def preprocess_document(text: str, aggressive: bool = False) -> str:
    """
    Clean document text (convenience function).

    Args:
        text: Raw document text
        aggressive: If True, also normalize fancy quotes/dashes

    Returns:
        Cleaned text
    """
    return DocumentPreprocessor.clean_text(text, aggressive=aggressive)
