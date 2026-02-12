"""Observation value object - evidence about an application from a document."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass(frozen=True)
class Observation:
    """Single observation about an application from a source document.

    Replaces the current "Fact" concept, but stored as PART OF Application
    (not as a separate parallel store).

    Key difference from Facts:
    - Observations belong to Applications (composition)
    - Facts existed independently (separate store)

    This solves the "which is truth?" problem - Application IS the truth,
    observations are just supporting evidence.
    """
    # Source tracking
    source_document: str  # Filename or document ID
    source_type: str  # "table", "llm_prose", "manual", "import"

    # Extracted data (flexible schema)
    extracted_data: Dict[str, Any]  # {"vendor": "Salesforce.com", "users": 100}

    # Quality metadata
    confidence: float  # 0.0-1.0 (deterministic=1.0, LLM=0.7-0.9)
    timestamp: str  # ISO format

    # Optional: Evidence quote
    source_quote: str = ""

    def __post_init__(self):
        """Validate invariants."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

        valid_types = ["table", "llm_prose", "manual", "import", "enrichment"]
        if self.source_type not in valid_types:
            raise ValueError(f"Invalid source_type: {self.source_type}")

    def is_deterministic(self) -> bool:
        """Check if observation came from deterministic source (table parser)."""
        return self.source_type == "table" and self.confidence == 1.0

    def is_llm_extracted(self) -> bool:
        """Check if observation came from LLM discovery."""
        return self.source_type == "llm_prose"

    @classmethod
    def from_table(
        cls,
        source_document: str,
        extracted_data: Dict[str, Any],
        source_quote: str = ""
    ) -> "Observation":
        """Create observation from deterministic table parser."""
        return cls(
            source_document=source_document,
            source_type="table",
            extracted_data=extracted_data,
            confidence=1.0,  # Deterministic = 100% confidence
            timestamp=datetime.now().isoformat(),
            source_quote=source_quote
        )

    @classmethod
    def from_llm(
        cls,
        source_document: str,
        extracted_data: Dict[str, Any],
        confidence: float = 0.7,
        source_quote: str = ""
    ) -> "Observation":
        """Create observation from LLM extraction."""
        return cls(
            source_document=source_document,
            source_type="llm_prose",
            extracted_data=extracted_data,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            source_quote=source_quote
        )
