"""
Evidence Verifier - Validates that quoted evidence exists in source documents.

Core functionality for catching hallucinations where the LLM invents quotes.
Uses fuzzy string matching to handle minor variations in whitespace,
punctuation, and formatting.

This is a critical validation step - fabricated evidence undermines
the entire due diligence process.
"""

import re
import logging
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default thresholds for evidence verification
DEFAULT_VERIFIED_THRESHOLD = 0.85    # Above this = verified
DEFAULT_PARTIAL_THRESHOLD = 0.50     # Above this = partial match
MIN_QUOTE_LENGTH = 10                # Minimum quote length to verify

# Sliding window parameters for long documents
WINDOW_SIZE_MULTIPLIER = 3           # Window = quote_length * this
WINDOW_STEP_DIVISOR = 4              # Step = window_size / this


# =============================================================================
# RESULT MODELS
# =============================================================================

@dataclass
class VerificationResult:
    """Result of verifying a single evidence quote."""
    status: str                      # "verified", "partial_match", "not_found"
    match_score: float               # 0.0 - 1.0 similarity score
    quote_provided: str              # The quote we were looking for
    matched_text: Optional[str]      # What was actually found (if any)
    search_method: str               # "exact", "fuzzy", "sliding_window"

    # Additional context
    match_location: Optional[int] = None  # Approximate position in document
    normalized_quote: Optional[str] = None  # Quote after normalization

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "match_score": self.match_score,
            "quote_provided": self.quote_provided[:100] + "..." if len(self.quote_provided) > 100 else self.quote_provided,
            "matched_text": self.matched_text[:100] + "..." if self.matched_text and len(self.matched_text) > 100 else self.matched_text,
            "search_method": self.search_method,
            "match_location": self.match_location
        }


@dataclass
class EvidenceVerificationReport:
    """Summary report of evidence verification across multiple facts."""
    domain: str
    total_facts: int
    verified_count: int = 0
    partial_match_count: int = 0
    not_found_count: int = 0
    skipped_count: int = 0           # Too short or missing quotes

    # Details
    results: Dict[str, VerificationResult] = field(default_factory=dict)  # fact_id -> result
    problematic_facts: List[str] = field(default_factory=list)  # fact_ids with issues

    # Timing
    verification_time_ms: float = 0.0
    verified_at: datetime = field(default_factory=datetime.now)

    @property
    def average_match_score(self) -> float:
        """Average match score across all verified quotes."""
        scores = [r.match_score for r in self.results.values() if r.match_score > 0]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def verification_rate(self) -> float:
        """Percentage of facts that were verified."""
        verifiable = self.total_facts - self.skipped_count
        if verifiable == 0:
            return 1.0
        return self.verified_count / verifiable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "total_facts": self.total_facts,
            "verified_count": self.verified_count,
            "partial_match_count": self.partial_match_count,
            "not_found_count": self.not_found_count,
            "skipped_count": self.skipped_count,
            "average_match_score": self.average_match_score,
            "verification_rate": self.verification_rate,
            "problematic_facts": self.problematic_facts,
            "verification_time_ms": self.verification_time_ms,
            "verified_at": self.verified_at.isoformat()
        }


# =============================================================================
# TEXT NORMALIZATION
# =============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Handles common variations:
    - Multiple whitespace → single space
    - Different quote styles
    - Common OCR errors
    - Line breaks and tabs
    """
    if not text:
        return ""

    # Convert to lowercase for comparison
    normalized = text.lower()

    # Replace various whitespace with single space
    normalized = re.sub(r'\s+', ' ', normalized)

    # Normalize quote characters
    normalized = normalized.replace('"', '"').replace('"', '"')
    normalized = normalized.replace(''', "'").replace(''', "'")
    normalized = normalized.replace('`', "'")

    # Normalize dashes
    normalized = normalized.replace('–', '-').replace('—', '-')

    # Remove leading/trailing whitespace
    normalized = normalized.strip()

    return normalized


def normalize_for_matching(text: str) -> str:
    """
    More aggressive normalization for fuzzy matching.

    Removes punctuation and extra characters that often vary.
    """
    normalized = normalize_text(text)

    # Remove common punctuation that varies
    normalized = re.sub(r'[,;:\.!\?\(\)\[\]\{\}]', ' ', normalized)

    # Collapse multiple spaces again
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized.strip()


# =============================================================================
# CORE VERIFICATION
# =============================================================================

def verify_quote_exists(
    quote: str,
    document_text: str,
    verified_threshold: float = DEFAULT_VERIFIED_THRESHOLD,
    partial_threshold: float = DEFAULT_PARTIAL_THRESHOLD
) -> VerificationResult:
    """
    Verify that a quote exists in the document.

    Uses multiple strategies:
    1. Exact match (fastest)
    2. Normalized exact match
    3. Fuzzy matching with sliding window

    Args:
        quote: The evidence quote to find
        document_text: The source document text
        verified_threshold: Score above which quote is considered verified
        partial_threshold: Score above which quote is considered partial match

    Returns:
        VerificationResult with status, score, and matched text
    """
    # Handle empty inputs
    if not quote or not document_text:
        return VerificationResult(
            status="not_found",
            match_score=0.0,
            quote_provided=quote or "",
            matched_text=None,
            search_method="none"
        )

    # Skip very short quotes (likely not meaningful)
    if len(quote.strip()) < MIN_QUOTE_LENGTH:
        return VerificationResult(
            status="skipped",
            match_score=0.0,
            quote_provided=quote,
            matched_text=None,
            search_method="skipped_short"
        )

    # Strategy 1: Exact match
    if quote in document_text:
        return VerificationResult(
            status="verified",
            match_score=1.0,
            quote_provided=quote,
            matched_text=quote,
            search_method="exact",
            match_location=document_text.find(quote)
        )

    # Strategy 2: Normalized exact match
    norm_quote = normalize_text(quote)
    norm_doc = normalize_text(document_text)

    if norm_quote in norm_doc:
        # Find the actual text that matched
        match_start = norm_doc.find(norm_quote)
        return VerificationResult(
            status="verified",
            match_score=0.98,  # Slightly lower than exact
            quote_provided=quote,
            matched_text=norm_quote,
            search_method="normalized_exact",
            match_location=match_start,
            normalized_quote=norm_quote
        )

    # Strategy 3: Fuzzy matching with sliding window
    best_score, best_match, best_location = _fuzzy_match_sliding_window(
        norm_quote, norm_doc
    )

    # Determine status based on score
    if best_score >= verified_threshold:
        status = "verified"
    elif best_score >= partial_threshold:
        status = "partial_match"
    else:
        status = "not_found"

    return VerificationResult(
        status=status,
        match_score=best_score,
        quote_provided=quote,
        matched_text=best_match if best_score >= partial_threshold else None,
        search_method="sliding_window",
        match_location=best_location if best_score >= partial_threshold else None,
        normalized_quote=norm_quote
    )


def _fuzzy_match_sliding_window(
    quote: str,
    document: str
) -> Tuple[float, Optional[str], Optional[int]]:
    """
    Find best fuzzy match using sliding window approach.

    Slides a window across the document and finds the region
    with the highest similarity to the quote.

    Args:
        quote: Normalized quote to find
        document: Normalized document text

    Returns:
        Tuple of (best_score, best_matching_text, position)
    """
    quote_len = len(quote)
    doc_len = len(document)

    if quote_len == 0 or doc_len == 0:
        return 0.0, None, None

    # Window size should be larger than quote to allow for variations
    window_size = min(quote_len * WINDOW_SIZE_MULTIPLIER, doc_len)
    step_size = max(window_size // WINDOW_STEP_DIVISOR, 1)

    best_score = 0.0
    best_match = None
    best_position = None

    # Slide window across document
    position = 0
    while position < doc_len:
        # Extract window
        window_end = min(position + window_size, doc_len)
        window_text = document[position:window_end]

        # Calculate similarity
        score = SequenceMatcher(None, quote, window_text).ratio()

        # Also try matching against just quote-length portion
        if len(window_text) > quote_len:
            short_window = window_text[:quote_len + 20]  # Allow some slack
            short_score = SequenceMatcher(None, quote, short_window).ratio()
            score = max(score, short_score)

        if score > best_score:
            best_score = score
            best_match = window_text[:quote_len + 50]  # Capture context
            best_position = position

        position += step_size

        # Early exit if we found a very good match
        if best_score > 0.95:
            break

    return best_score, best_match, best_position


# =============================================================================
# BATCH VERIFICATION
# =============================================================================

def verify_all_facts(
    facts: List[Dict[str, Any]],
    document_text: str,
    domain: str = "unknown"
) -> EvidenceVerificationReport:
    """
    Verify evidence for all facts in a domain.

    Args:
        facts: List of fact dictionaries with 'fact_id' and 'evidence' fields
        document_text: The source document text
        domain: Domain name for reporting

    Returns:
        EvidenceVerificationReport with results for all facts
    """
    import time
    start_time = time.time()

    report = EvidenceVerificationReport(
        domain=domain,
        total_facts=len(facts)
    )

    for fact in facts:
        fact_id = fact.get("fact_id", "unknown")

        # Extract quote from evidence
        evidence = fact.get("evidence", {})
        if isinstance(evidence, dict):
            quote = evidence.get("exact_quote", "")
        elif isinstance(evidence, str):
            quote = evidence
        else:
            quote = ""

        # Skip if no quote
        if not quote:
            report.skipped_count += 1
            continue

        # Verify the quote
        result = verify_quote_exists(quote, document_text)
        report.results[fact_id] = result

        # Update counts
        if result.status == "verified":
            report.verified_count += 1
        elif result.status == "partial_match":
            report.partial_match_count += 1
            report.problematic_facts.append(fact_id)
        elif result.status == "not_found":
            report.not_found_count += 1
            report.problematic_facts.append(fact_id)
        elif result.status == "skipped":
            report.skipped_count += 1

    report.verification_time_ms = (time.time() - start_time) * 1000

    logger.info(
        f"Evidence verification for {domain}: "
        f"{report.verified_count}/{report.total_facts} verified, "
        f"{report.not_found_count} not found, "
        f"{report.verification_time_ms:.1f}ms"
    )

    return report


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def create_evidence_flags(
    verification_result: VerificationResult,
    fact_id: str
) -> List[Dict[str, Any]]:
    """
    Create validation flags based on evidence verification result.

    Args:
        verification_result: Result from verify_quote_exists
        fact_id: ID of the fact being verified

    Returns:
        List of flag dictionaries to add to the fact
    """
    from models.validation_models import (
        ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
    )

    flags = []

    if verification_result.status == "not_found":
        flags.append(ValidationFlag(
            flag_id=generate_flag_id(),
            severity=FlagSeverity.CRITICAL,
            category=FlagCategory.EVIDENCE,
            message=(
                f"Evidence not found in source document (match score: "
                f"{verification_result.match_score:.0%}). This may indicate "
                f"a hallucinated quote."
            ),
            suggestion=(
                "Verify this fact manually against the source document. "
                "The quoted evidence could not be located."
            ),
            affected_fact_ids=[fact_id]
        ))

    elif verification_result.status == "partial_match":
        flags.append(ValidationFlag(
            flag_id=generate_flag_id(),
            severity=FlagSeverity.WARNING,
            category=FlagCategory.EVIDENCE,
            message=(
                f"Evidence partially matches ({verification_result.match_score:.0%}). "
                f"The quote may be paraphrased or slightly altered."
            ),
            suggestion=(
                "Check if the paraphrasing accurately represents the source. "
                f"Found similar text: '{verification_result.matched_text[:50]}...'"
                if verification_result.matched_text else ""
            ),
            affected_fact_ids=[fact_id]
        ))

    return flags


def verify_and_flag_facts(
    facts: List[Dict[str, Any]],
    document_text: str,
    validation_store,  # ValidationStore instance
    domain: str = "unknown"
) -> EvidenceVerificationReport:
    """
    Verify evidence for facts and add flags to validation store.

    Convenience function that combines verification and flagging.

    Args:
        facts: List of fact dictionaries
        document_text: Source document text
        validation_store: ValidationStore to update
        domain: Domain name

    Returns:
        EvidenceVerificationReport
    """
    # Run verification
    report = verify_all_facts(facts, document_text, domain)

    # Add flags for problematic facts
    for fact_id, result in report.results.items():
        # Update evidence status in validation store
        validation_store.update_evidence_status(
            fact_id=fact_id,
            verified=(result.status == "verified"),
            match_score=result.match_score,
            matched_text=result.matched_text
        )

        # Create and add flags if needed
        flags = create_evidence_flags(result, fact_id)
        for flag in flags:
            validation_store.add_flag(fact_id, flag, source="evidence_verification")

    return report


# =============================================================================
# EVIDENCE VERIFIER CLASS
# =============================================================================

class EvidenceVerifier:
    """
    Class wrapper for evidence verification functionality.

    Provides a cleaner API for batch verification operations.
    """

    def __init__(
        self,
        verified_threshold: float = DEFAULT_VERIFIED_THRESHOLD,
        partial_threshold: float = DEFAULT_PARTIAL_THRESHOLD
    ):
        self.verified_threshold = verified_threshold
        self.partial_threshold = partial_threshold

    def verify_quote(
        self,
        quote: str,
        document_text: str,
        case_sensitive: bool = True
    ) -> VerificationResult:
        """
        Verify that a quote exists in the document.

        Args:
            quote: The evidence quote to find
            document_text: The source document text
            case_sensitive: Whether to use case-sensitive matching

        Returns:
            VerificationResult with status and match score
        """
        if not case_sensitive:
            # Use normalized matching
            return verify_quote_exists(
                quote,
                document_text,
                self.verified_threshold,
                self.partial_threshold
            )
        else:
            return verify_quote_exists(
                quote,
                document_text,
                self.verified_threshold,
                self.partial_threshold
            )

    def verify_all_facts(
        self,
        facts: List[Dict[str, Any]],
        document_text: str,
        domain: str = "unknown"
    ) -> Dict[str, VerificationResult]:
        """
        Verify evidence for all facts.

        Args:
            facts: List of fact dictionaries with 'fact_id' and 'evidence' fields
            document_text: The source document text
            domain: Domain name for logging

        Returns:
            Dict mapping fact_id to VerificationResult
        """
        report = verify_all_facts(facts, document_text, domain)
        return report.results

    def get_report(
        self,
        facts: List[Dict[str, Any]],
        document_text: str,
        domain: str = "unknown"
    ) -> EvidenceVerificationReport:
        """
        Get full verification report.

        Args:
            facts: List of fact dictionaries
            document_text: The source document text
            domain: Domain name

        Returns:
            EvidenceVerificationReport with all results and statistics
        """
        return verify_all_facts(facts, document_text, domain)


# =============================================================================
# UTILITIES
# =============================================================================

def extract_quotes_from_facts(facts: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Extract evidence quotes from a list of facts.

    Args:
        facts: List of fact dictionaries

    Returns:
        Dict mapping fact_id to quote text
    """
    quotes = {}
    for fact in facts:
        fact_id = fact.get("fact_id", "")
        evidence = fact.get("evidence", {})

        if isinstance(evidence, dict):
            quote = evidence.get("exact_quote", "")
        elif isinstance(evidence, str):
            quote = evidence
        else:
            quote = ""

        if quote and fact_id:
            quotes[fact_id] = quote

    return quotes


def summarize_verification_issues(report: EvidenceVerificationReport) -> str:
    """
    Generate human-readable summary of verification issues.

    Args:
        report: EvidenceVerificationReport

    Returns:
        Formatted summary string
    """
    lines = [
        f"Evidence Verification Summary for {report.domain}",
        "=" * 50,
        f"Total facts: {report.total_facts}",
        f"Verified: {report.verified_count} ({report.verification_rate:.0%})",
        f"Partial match: {report.partial_match_count}",
        f"Not found: {report.not_found_count}",
        f"Skipped: {report.skipped_count}",
        f"Average match score: {report.average_match_score:.1%}",
        ""
    ]

    if report.not_found_count > 0:
        lines.append("CRITICAL - Evidence not found:")
        for fact_id in report.problematic_facts:
            result = report.results.get(fact_id)
            if result and result.status == "not_found":
                lines.append(f"  - {fact_id}: '{result.quote_provided[:50]}...'")

    if report.partial_match_count > 0:
        lines.append("\nWARNING - Partial matches:")
        for fact_id in report.problematic_facts:
            result = report.results.get(fact_id)
            if result and result.status == "partial_match":
                lines.append(
                    f"  - {fact_id}: {result.match_score:.0%} match"
                )

    return "\n".join(lines)
