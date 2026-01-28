"""
Extraction Orchestrator - Manages Extract-Validate-Retry Loop

Coordinates the extraction workflow:
1. Initial extraction
2. Validation
3. Targeted re-extraction if validation fails
4. Repeat up to MAX_ATTEMPTS
5. Escalate to human if still incomplete

This ensures we get complete, validated data before presenting to users.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from services.validation_pipeline import (
    ValidationPipeline,
    ValidationPipelineResult
)
from stores.validation_store import ValidationStore
from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_RERUN_ATTEMPTS = 3  # Maximum re-extraction attempts before escalation
RERUN_THRESHOLD = 0.70  # Score below which triggers re-extraction


# =============================================================================
# ENUMS
# =============================================================================

class ExtractionStatus(Enum):
    """Status of an extraction attempt."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    ESCALATED = "escalated"


# =============================================================================
# RESULT MODELS
# =============================================================================

@dataclass
class ExtractionAttempt:
    """Record of a single extraction attempt."""
    attempt_number: int
    timestamp: datetime
    facts_extracted: int
    validation_result: Optional[ValidationPipelineResult]
    was_targeted: bool = False
    targeted_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "timestamp": self.timestamp.isoformat(),
            "facts_extracted": self.facts_extracted,
            "was_targeted": self.was_targeted,
            "targeted_items": self.targeted_items,
            "validation_passed": (
                self.validation_result.overall_valid
                if self.validation_result else False
            )
        }


@dataclass
class EscalationRecord:
    """Record of an escalation to human review."""
    domain: str
    attempts: int
    remaining_issues: List[Dict[str, Any]]
    suggested_actions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "high"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "attempts": self.attempts,
            "remaining_issues": self.remaining_issues,
            "suggested_actions": self.suggested_actions,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }


@dataclass
class ExtractionResult:
    """Final result of the extraction orchestration."""
    domain: str
    status: ExtractionStatus
    final_facts: List[Dict[str, Any]]
    final_validation: Optional[ValidationPipelineResult]

    # Attempt history
    attempts: List[ExtractionAttempt] = field(default_factory=list)
    total_attempts: int = 0

    # Escalation (if applicable)
    escalation: Optional[EscalationRecord] = None

    # Timing
    total_time_ms: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "status": self.status.value,
            "facts_count": len(self.final_facts),
            "total_attempts": self.total_attempts,
            "final_confidence": (
                self.final_validation.overall_confidence
                if self.final_validation else 0.0
            ),
            "escalated": self.escalation is not None,
            "total_time_ms": self.total_time_ms,
            "completed_at": self.completed_at.isoformat()
        }


# =============================================================================
# EXTRACTION ORCHESTRATOR
# =============================================================================

class ExtractionOrchestrator:
    """
    Orchestrates the extraction-validation-retry loop.

    Coordinates:
    1. Initial extraction using discovery tools
    2. Validation using the validation pipeline
    3. Targeted re-extraction for missing items
    4. Escalation to human if max attempts reached
    """

    def __init__(
        self,
        api_key: str,
        validation_store: Optional[ValidationStore] = None,
        extraction_function: Optional[Callable] = None,
        max_attempts: int = MAX_RERUN_ATTEMPTS
    ):
        """
        Initialize the extraction orchestrator.

        Args:
            api_key: Anthropic API key
            validation_store: Optional validation store for persistence
            extraction_function: Function to call for extraction
            max_attempts: Maximum re-extraction attempts
        """
        self.api_key = api_key
        self.validation_store = validation_store
        self.extraction_function = extraction_function
        self.max_attempts = max_attempts

        # Initialize validation pipeline
        self.validation_pipeline = ValidationPipeline(
            api_key=api_key,
            validation_store=validation_store
        )

        # Track attempts per domain
        self._attempt_counts: Dict[str, int] = {}
        self._domain_facts: Dict[str, List[Dict[str, Any]]] = {}

    # =========================================================================
    # MAIN EXTRACTION METHOD
    # =========================================================================

    async def extract_domain(
        self,
        domain: str,
        document_text: str,
        document_name: str,
        existing_facts: Optional[List[Dict[str, Any]]] = None
    ) -> ExtractionResult:
        """
        Extract and validate a domain with automatic retry.

        Args:
            domain: Domain name (organization, infrastructure, etc.)
            document_text: Source document text
            document_name: Name of the source document
            existing_facts: Optional existing facts (for continuation)

        Returns:
            ExtractionResult with final facts and validation
        """
        import time
        start_time = time.time()

        # Initialize tracking
        self._attempt_counts[domain] = 0
        self._domain_facts[domain] = existing_facts or []

        result = ExtractionResult(
            domain=domain,
            status=ExtractionStatus.PARTIAL,
            final_facts=[],
            final_validation=None
        )

        while True:
            attempt_num = self._attempt_counts[domain] + 1
            is_retry = attempt_num > 1

            logger.info(
                f"Extraction attempt {attempt_num}/{self.max_attempts} for {domain}"
                + (" (targeted re-extraction)" if is_retry else "")
            )

            # Step 1: Run extraction (or targeted re-extraction)
            if is_retry and result.final_validation:
                # Targeted re-extraction
                new_facts = await self._run_targeted_extraction(
                    domain=domain,
                    document_text=document_text,
                    document_name=document_name,
                    validation_result=result.final_validation
                )
                targeted_items = self._get_targeted_items(result.final_validation)
            else:
                # Initial extraction
                new_facts = await self._run_initial_extraction(
                    domain=domain,
                    document_text=document_text,
                    document_name=document_name
                )
                targeted_items = []

            # Merge new facts with existing
            self._merge_facts(domain, new_facts)
            current_facts = self._domain_facts[domain]

            # Step 2: Validate extraction
            validation_result = self.validation_pipeline.validate_domain(
                domain=domain,
                document_text=document_text,
                facts=current_facts
            )

            # Record attempt
            attempt = ExtractionAttempt(
                attempt_number=attempt_num,
                timestamp=datetime.now(),
                facts_extracted=len(new_facts),
                validation_result=validation_result,
                was_targeted=is_retry,
                targeted_items=targeted_items
            )
            result.attempts.append(attempt)
            self._attempt_counts[domain] = attempt_num

            # Update result
            result.final_facts = current_facts
            result.final_validation = validation_result

            # Step 3: Decide next action
            if validation_result.overall_valid:
                # Success! Validation passed
                result.status = ExtractionStatus.SUCCESS
                logger.info(f"Extraction for {domain} succeeded on attempt {attempt_num}")
                break

            elif not validation_result.requires_rerun:
                # Validation has issues but doesn't require rerun
                result.status = ExtractionStatus.PARTIAL
                logger.info(
                    f"Extraction for {domain} partial on attempt {attempt_num}, "
                    f"confidence: {validation_result.overall_confidence:.0%}"
                )
                break

            elif attempt_num >= self.max_attempts:
                # Max attempts reached - escalate
                result.status = ExtractionStatus.ESCALATED
                result.escalation = self._create_escalation(
                    domain, attempt_num, validation_result
                )
                logger.warning(
                    f"Extraction for {domain} escalated after {attempt_num} attempts"
                )
                break

            else:
                # Need to retry
                logger.info(
                    f"Extraction for {domain} needs retry: "
                    f"{validation_result.rerun_guidance}"
                )
                continue

        result.total_attempts = self._attempt_counts[domain]
        result.total_time_ms = (time.time() - start_time) * 1000
        result.completed_at = datetime.now()

        return result

    # =========================================================================
    # EXTRACTION METHODS
    # =========================================================================

    async def _run_initial_extraction(
        self,
        domain: str,
        document_text: str,
        document_name: str
    ) -> List[Dict[str, Any]]:
        """Run initial extraction for a domain."""
        if self.extraction_function:
            # Use provided extraction function
            return await self.extraction_function(
                domain=domain,
                document_text=document_text,
                document_name=document_name
            )
        else:
            # Placeholder - in production, this would call the discovery agent
            logger.warning(
                f"No extraction function provided, returning empty list for {domain}"
            )
            return []

    async def _run_targeted_extraction(
        self,
        domain: str,
        document_text: str,
        document_name: str,
        validation_result: ValidationPipelineResult
    ) -> List[Dict[str, Any]]:
        """
        Run targeted re-extraction for missing items.

        Uses validation result to focus on specific gaps.
        """
        # Build targeted extraction prompt
        existing_items = [f.get("item", "") for f in self._domain_facts.get(domain, [])]
        missing_items = self._get_missing_items(validation_result)

        if not missing_items:
            logger.info(f"No specific missing items identified for {domain}")
            # Fall back to full re-extraction with guidance
            if self.extraction_function:
                return await self.extraction_function(
                    domain=domain,
                    document_text=document_text,
                    document_name=document_name,
                    guidance=validation_result.rerun_guidance
                )
            return []

        # Build targeted prompt
        targeted_prompt = self._build_targeted_prompt(
            domain=domain,
            existing_items=existing_items,
            missing_items=missing_items,
            document_text=document_text
        )

        if self.extraction_function:
            return await self.extraction_function(
                domain=domain,
                document_text=document_text,
                document_name=document_name,
                targeted_prompt=targeted_prompt,
                missing_items=missing_items
            )

        return []

    def _build_targeted_prompt(
        self,
        domain: str,
        existing_items: List[str],
        missing_items: List[Dict[str, Any]],
        document_text: str
    ) -> str:
        """Build a targeted extraction prompt for missing items."""
        existing_list = "\n".join(f"- {item}" for item in existing_items[:20])
        missing_list = "\n".join(
            f"- {item.get('item', 'Unknown')}: {item.get('evidence', '')[:100]}"
            for item in missing_items[:10]
        )

        return f"""
You are completing an INCOMPLETE extraction for the {domain} domain.

IMPORTANT: Focus ONLY on finding the MISSING items listed below.
Do NOT re-extract items that are already captured.

ALREADY EXTRACTED (do not re-extract these):
{existing_list}

MISSING ITEMS (you MUST find and extract these):
{missing_list}

Search the document carefully for these specific items.
For each item found:
1. Extract the exact details as structured data
2. Include the exact quote from the document as evidence
3. Verify the quote exists in the document

If an item truly doesn't exist in the document, note it as a gap.
"""

    def _get_missing_items(
        self,
        validation_result: ValidationPipelineResult
    ) -> List[Dict[str, Any]]:
        """Extract missing items from validation result."""
        missing = []

        # From category validation
        if validation_result.category_report:
            missing.extend(validation_result.category_report.all_missing_items)

        # From domain validation
        if validation_result.domain_result:
            missing.extend(validation_result.domain_result.missing_items)

        return missing

    def _get_targeted_items(
        self,
        validation_result: ValidationPipelineResult
    ) -> List[str]:
        """Get list of item names that were targeted for re-extraction."""
        missing = self._get_missing_items(validation_result)
        return [m.get("item", "Unknown") for m in missing[:10]]

    # =========================================================================
    # FACT MANAGEMENT
    # =========================================================================

    def _merge_facts(
        self,
        domain: str,
        new_facts: List[Dict[str, Any]]
    ):
        """Merge new facts into existing facts, avoiding duplicates."""
        existing = self._domain_facts.get(domain, [])
        existing_ids = {f.get("fact_id") for f in existing if f.get("fact_id")}
        existing_items = {
            (f.get("category", ""), f.get("item", "").lower())
            for f in existing
        }

        for fact in new_facts:
            fact_id = fact.get("fact_id")
            item_key = (fact.get("category", ""), fact.get("item", "").lower())

            # Skip if duplicate
            if fact_id and fact_id in existing_ids:
                continue
            if item_key in existing_items:
                continue

            # Add new fact
            existing.append(fact)
            if fact_id:
                existing_ids.add(fact_id)
            existing_items.add(item_key)

        self._domain_facts[domain] = existing

    # =========================================================================
    # ESCALATION
    # =========================================================================

    def _create_escalation(
        self,
        domain: str,
        attempts: int,
        validation_result: ValidationPipelineResult
    ) -> EscalationRecord:
        """Create an escalation record for human review."""
        # Collect remaining issues
        remaining_issues = []

        if validation_result.category_report:
            for item in validation_result.category_report.all_missing_items[:10]:
                remaining_issues.append({
                    "type": "missing_item",
                    "category": item.get("category", "unknown"),
                    "item": item.get("item", "Unknown"),
                    "evidence": item.get("evidence", "")[:200]
                })

        if validation_result.domain_result:
            for issue in validation_result.domain_result.inconsistencies[:5]:
                remaining_issues.append({
                    "type": "inconsistency",
                    "description": issue.get("description", str(issue))
                })

        # Generate suggested actions
        suggested_actions = [
            f"Review document for missing {domain} items",
            "Verify extracted data against source document",
            "Check for items that may be in different sections"
        ]

        if validation_result.rerun_guidance:
            suggested_actions.insert(0, validation_result.rerun_guidance)

        # Determine priority
        if len(validation_result.critical_issues) > 0:
            priority = "critical"
        elif validation_result.overall_confidence < 0.5:
            priority = "high"
        else:
            priority = "medium"

        escalation = EscalationRecord(
            domain=domain,
            attempts=attempts,
            remaining_issues=remaining_issues,
            suggested_actions=suggested_actions,
            priority=priority
        )

        # Add escalation flag to validation store
        if self.validation_store:
            flag = ValidationFlag(
                flag_id=generate_flag_id(),
                severity=FlagSeverity.CRITICAL,
                category=FlagCategory.COMPLETENESS,
                message=(
                    f"Extraction escalated after {attempts} attempts. "
                    f"{len(remaining_issues)} issues remain."
                ),
                suggestion="; ".join(suggested_actions[:2])
            )
            # Add to domain state
            domain_state = self.validation_store.get_domain_state(domain)
            domain_state.domain_flags.append(flag)
            self.validation_store.update_domain_state(domain, domain_state)

        logger.warning(
            f"Created escalation for {domain}: {len(remaining_issues)} issues, "
            f"priority={priority}"
        )

        return escalation

    # =========================================================================
    # STATUS METHODS
    # =========================================================================

    def get_attempt_count(self, domain: str) -> int:
        """Get current attempt count for a domain."""
        return self._attempt_counts.get(domain, 0)

    def get_current_facts(self, domain: str) -> List[Dict[str, Any]]:
        """Get current facts for a domain."""
        return self._domain_facts.get(domain, [])

    def reset_domain(self, domain: str):
        """Reset tracking for a domain."""
        self._attempt_counts[domain] = 0
        self._domain_facts[domain] = []


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_orchestrator(
    api_key: str,
    validation_store: Optional[ValidationStore] = None,
    extraction_function: Optional[Callable] = None
) -> ExtractionOrchestrator:
    """Create an extraction orchestrator instance."""
    return ExtractionOrchestrator(
        api_key=api_key,
        validation_store=validation_store,
        extraction_function=extraction_function
    )


async def extract_with_validation(
    api_key: str,
    domain: str,
    document_text: str,
    document_name: str,
    extraction_function: Callable,
    validation_store: Optional[ValidationStore] = None
) -> ExtractionResult:
    """
    Convenience function to extract and validate a domain.

    Args:
        api_key: Anthropic API key
        domain: Domain to extract
        document_text: Source document
        document_name: Document name
        extraction_function: Function to call for extraction
        validation_store: Optional validation store

    Returns:
        ExtractionResult with validated facts
    """
    orchestrator = ExtractionOrchestrator(
        api_key=api_key,
        validation_store=validation_store,
        extraction_function=extraction_function
    )

    return await orchestrator.extract_domain(
        domain=domain,
        document_text=document_text,
        document_name=document_name
    )
