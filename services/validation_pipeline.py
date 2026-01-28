"""
Validation Pipeline Orchestrator - Coordinates All Validation Layers

Orchestrates the complete validation flow:
1. Evidence verification (check quotes exist)
2. Category validation (Layer 1 - fast checks)
3. Domain validation (Layer 2 - thorough analysis)
4. Adversarial review (optional red team)
5. Cross-domain consistency (Layer 3 - after all domains)

This is the main entry point for running validation on extracted data.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from tools_v2.evidence_verifier import (
    verify_all_facts,
    EvidenceVerificationReport,
    create_evidence_flags
)
from tools_v2.category_validator import (
    CategoryValidator,
    CategoryValidationResult,
    DomainCategoryValidationReport
)
from tools_v2.domain_validator import (
    DomainValidator,
    DomainValidationResult
)
from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory,
    FactValidationState, DomainValidationState,
    generate_flag_id
)
from stores.validation_store import ValidationStore

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Validation thresholds
EVIDENCE_VERIFICATION_ENABLED = True
CATEGORY_VALIDATION_ENABLED = True
DOMAIN_VALIDATION_ENABLED = True
ADVERSARIAL_REVIEW_ENABLED = False  # Optional, can enable later

# Score thresholds
PASS_THRESHOLD = 0.80  # Above this = validation passes
RERUN_THRESHOLD = 0.60  # Below this = requires re-extraction
HUMAN_REVIEW_THRESHOLD = 0.70  # Below this = needs human review


# =============================================================================
# RESULT MODELS
# =============================================================================

@dataclass
class ValidationPipelineResult:
    """Complete result of running the validation pipeline."""
    domain: str
    overall_valid: bool
    overall_confidence: float

    # Layer results
    evidence_report: Optional[EvidenceVerificationReport] = None
    category_report: Optional[DomainCategoryValidationReport] = None
    domain_result: Optional[DomainValidationResult] = None
    adversarial_findings: List[Dict[str, Any]] = field(default_factory=list)
    cross_domain_result: Optional[Dict[str, Any]] = None

    # Aggregated issues
    all_flags: List[ValidationFlag] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)

    # Recommendations
    requires_rerun: bool = False
    rerun_guidance: Optional[str] = None
    human_review_needed: bool = False
    human_review_reason: Optional[str] = None

    # Timing
    total_time_ms: float = 0.0
    layer_times: Dict[str, float] = field(default_factory=dict)

    # Metadata
    validated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "overall_valid": self.overall_valid,
            "overall_confidence": self.overall_confidence,
            "evidence_verification": self.evidence_report.to_dict() if self.evidence_report else None,
            "category_validation": self.category_report.to_dict() if self.category_report else None,
            "domain_validation": self.domain_result.to_dict() if self.domain_result else None,
            "requires_rerun": self.requires_rerun,
            "rerun_guidance": self.rerun_guidance,
            "human_review_needed": self.human_review_needed,
            "human_review_reason": self.human_review_reason,
            "flags_count": len(self.all_flags),
            "critical_issues_count": len(self.critical_issues),
            "total_time_ms": self.total_time_ms,
            "validated_at": self.validated_at.isoformat()
        }


# =============================================================================
# VALIDATION PIPELINE CLASS
# =============================================================================

class ValidationPipeline:
    """
    Orchestrates all validation layers for extracted data.

    Runs validation in sequence:
    1. Evidence verification
    2. Category validation (Layer 1)
    3. Domain validation (Layer 2)
    4. Adversarial review (optional)
    5. Cross-domain (when all domains complete)
    """

    def __init__(
        self,
        api_key: str,
        validation_store: Optional[ValidationStore] = None,
        enable_evidence: bool = EVIDENCE_VERIFICATION_ENABLED,
        enable_category: bool = CATEGORY_VALIDATION_ENABLED,
        enable_domain: bool = DOMAIN_VALIDATION_ENABLED,
        enable_adversarial: bool = ADVERSARIAL_REVIEW_ENABLED
    ):
        """
        Initialize the validation pipeline.

        Args:
            api_key: Anthropic API key
            validation_store: Optional store for persisting validation state
            enable_evidence: Enable evidence verification
            enable_category: Enable category validation
            enable_domain: Enable domain validation
            enable_adversarial: Enable adversarial review
        """
        self.api_key = api_key
        self.validation_store = validation_store

        # Configuration
        self.enable_evidence = enable_evidence
        self.enable_category = enable_category
        self.enable_domain = enable_domain
        self.enable_adversarial = enable_adversarial

        # Initialize validators
        self.category_validator = CategoryValidator(api_key=api_key)
        self.domain_validator = DomainValidator(api_key=api_key)

        # Cross-domain validator will be initialized when needed
        self._cross_domain_validator = None

    # =========================================================================
    # MAIN VALIDATION METHOD
    # =========================================================================

    def validate_domain(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]] = None,
        run_cross_domain: bool = False
    ) -> ValidationPipelineResult:
        """
        Run complete validation pipeline for a domain.

        Args:
            domain: Domain name (organization, infrastructure, etc.)
            document_text: Source document text
            facts: Extracted facts for this domain
            gaps: Identified gaps (optional)
            run_cross_domain: Whether to run cross-domain validation

        Returns:
            ValidationPipelineResult with complete assessment
        """
        import time
        start_time = time.time()

        result = ValidationPipelineResult(
            domain=domain,
            overall_valid=True,
            overall_confidence=1.0
        )

        # Organize facts by category
        facts_by_category = self._categorize_facts(facts)

        # Step 1: Evidence Verification
        if self.enable_evidence:
            step_start = time.time()
            result.evidence_report = self._run_evidence_verification(
                facts, document_text, domain
            )
            result.layer_times["evidence"] = (time.time() - step_start) * 1000

            # Collect evidence flags
            self._collect_evidence_flags(result)

        # Step 2: Category Validation (Layer 1)
        if self.enable_category:
            step_start = time.time()
            result.category_report = self._run_category_validation(
                domain, document_text, facts_by_category
            )
            result.layer_times["category"] = (time.time() - step_start) * 1000

            # Collect category flags
            if result.category_report:
                result.all_flags.extend(result.category_report.all_flags)

        # Step 3: Domain Validation (Layer 2)
        if self.enable_domain:
            step_start = time.time()
            result.domain_result = self._run_domain_validation(
                domain, document_text, facts, gaps
            )
            result.layer_times["domain"] = (time.time() - step_start) * 1000

            # Collect domain flags
            if result.domain_result:
                result.all_flags.extend(result.domain_result.flags)

        # Step 4: Adversarial Review (optional)
        if self.enable_adversarial and not self._should_skip_adversarial(result):
            step_start = time.time()
            result.adversarial_findings = self._run_adversarial_review(
                domain, document_text, facts
            )
            result.layer_times["adversarial"] = (time.time() - step_start) * 1000

        # Step 5: Cross-Domain (if requested)
        if run_cross_domain:
            step_start = time.time()
            result.cross_domain_result = self._run_cross_domain_validation()
            result.layer_times["cross_domain"] = (time.time() - step_start) * 1000

        # Calculate final status
        self._calculate_final_status(result)

        # Persist validation state if store is available
        if self.validation_store:
            self._persist_validation_state(domain, facts, result)

        result.total_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Validation pipeline for {domain}: "
            f"valid={result.overall_valid}, conf={result.overall_confidence:.2f}, "
            f"rerun={result.requires_rerun}, time={result.total_time_ms:.0f}ms"
        )

        return result

    # =========================================================================
    # LAYER 1: EVIDENCE VERIFICATION
    # =========================================================================

    def _run_evidence_verification(
        self,
        facts: List[Dict[str, Any]],
        document_text: str,
        domain: str
    ) -> EvidenceVerificationReport:
        """Run evidence verification on all facts."""
        logger.debug(f"Running evidence verification for {domain}")

        report = verify_all_facts(
            facts=facts,
            document_text=document_text,
            domain=domain
        )

        logger.info(
            f"Evidence verification: {report.verified_count}/{report.total_facts} verified, "
            f"{report.not_found_count} not found"
        )

        return report

    def _collect_evidence_flags(self, result: ValidationPipelineResult):
        """Collect flags from evidence verification."""
        if not result.evidence_report:
            return

        report = result.evidence_report

        # Add flags for problematic facts
        for fact_id in report.problematic_facts:
            verification_result = report.results.get(fact_id)
            if verification_result:
                flags = create_evidence_flags(verification_result, fact_id)
                result.all_flags.extend(flags)

                # Track critical issues
                if verification_result.status == "not_found":
                    result.critical_issues.append(
                        f"Evidence not found for fact {fact_id}"
                    )

    # =========================================================================
    # LAYER 2: CATEGORY VALIDATION
    # =========================================================================

    def _run_category_validation(
        self,
        domain: str,
        document_text: str,
        facts_by_category: Dict[str, List[Dict[str, Any]]]
    ) -> DomainCategoryValidationReport:
        """Run category validation (Layer 1)."""
        logger.debug(f"Running category validation for {domain}")

        report = self.category_validator.validate_all_categories(
            domain=domain,
            document_text=document_text,
            facts_by_category=facts_by_category
        )

        logger.info(
            f"Category validation: {report.categories_complete}/{report.total_categories} complete, "
            f"rerun needed: {report.requires_rerun}"
        )

        return report

    # =========================================================================
    # LAYER 3: DOMAIN VALIDATION
    # =========================================================================

    def _run_domain_validation(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict[str, Any]],
        gaps: Optional[List[Dict[str, Any]]]
    ) -> DomainValidationResult:
        """Run domain validation (Layer 2)."""
        logger.debug(f"Running domain validation for {domain}")

        result = self.domain_validator.validate(
            domain=domain,
            document_text=document_text,
            facts=facts,
            gaps=gaps
        )

        logger.info(
            f"Domain validation: completeness={result.completeness_score:.2f}, "
            f"quality={result.quality_score:.2f}, rerun={result.requires_rerun}"
        )

        return result

    # =========================================================================
    # ADVERSARIAL REVIEW
    # =========================================================================

    def _should_skip_adversarial(self, result: ValidationPipelineResult) -> bool:
        """Determine if we should skip adversarial review."""
        # Skip if domain validation already found major issues
        if result.domain_result and result.domain_result.requires_rerun:
            return True

        # Skip if too many critical issues already
        if len(result.critical_issues) > 5:
            return True

        return False

    def _run_adversarial_review(
        self,
        domain: str,
        document_text: str,
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run adversarial review (red team)."""
        # Adversarial reviewer will be implemented in Phase 6
        # For now, return empty list
        logger.debug(f"Adversarial review skipped (not yet implemented)")
        return []

    # =========================================================================
    # CROSS-DOMAIN VALIDATION
    # =========================================================================

    def _run_cross_domain_validation(self) -> Optional[Dict[str, Any]]:
        """Run cross-domain consistency checks."""
        # Cross-domain validator will be implemented in Phase 5
        # For now, return None
        logger.debug(f"Cross-domain validation skipped (not yet implemented)")
        return None

    # =========================================================================
    # FINAL STATUS CALCULATION
    # =========================================================================

    def _calculate_final_status(self, result: ValidationPipelineResult):
        """Calculate final validation status from all layers."""
        scores = []
        rerun_reasons = []

        # Evidence score
        if result.evidence_report:
            evidence_score = result.evidence_report.verification_rate
            scores.append(evidence_score)
            if evidence_score < RERUN_THRESHOLD:
                rerun_reasons.append(
                    f"Low evidence verification: {evidence_score:.0%}"
                )

        # Category score
        if result.category_report:
            category_score = result.category_report.overall_completeness
            scores.append(category_score)
            if result.category_report.requires_rerun:
                rerun_reasons.append(
                    f"Categories incomplete: {result.category_report.rerun_categories}"
                )

        # Domain score
        if result.domain_result:
            domain_score = (
                result.domain_result.completeness_score * 0.6 +
                result.domain_result.quality_score * 0.4
            )
            scores.append(domain_score)
            if result.domain_result.requires_rerun:
                rerun_reasons.append(
                    result.domain_result.rerun_guidance or "Domain validation failed"
                )

        # Calculate overall confidence
        if scores:
            result.overall_confidence = sum(scores) / len(scores)
        else:
            result.overall_confidence = 0.5

        # Determine if rerun is needed
        result.requires_rerun = len(rerun_reasons) > 0
        if result.requires_rerun:
            result.rerun_guidance = " | ".join(rerun_reasons)

        # Determine if human review is needed
        critical_flag_count = sum(
            1 for f in result.all_flags
            if f.severity in [FlagSeverity.CRITICAL, FlagSeverity.ERROR]
        )

        if critical_flag_count > 0:
            result.human_review_needed = True
            result.human_review_reason = f"{critical_flag_count} critical/error flags"
        elif result.overall_confidence < HUMAN_REVIEW_THRESHOLD:
            result.human_review_needed = True
            result.human_review_reason = f"Low confidence: {result.overall_confidence:.0%}"

        # Overall validity
        result.overall_valid = (
            result.overall_confidence >= PASS_THRESHOLD and
            not result.requires_rerun and
            len(result.critical_issues) == 0
        )

    # =========================================================================
    # STATE PERSISTENCE
    # =========================================================================

    def _persist_validation_state(
        self,
        domain: str,
        facts: List[Dict[str, Any]],
        result: ValidationPipelineResult
    ):
        """Persist validation state to store."""
        if not self.validation_store:
            return

        # Update each fact's validation state
        for fact in facts:
            fact_id = fact.get("fact_id", "")
            if not fact_id:
                continue

            # Get or create state
            state = self.validation_store.get_or_create_state(fact_id)

            # Update with evidence verification result
            if result.evidence_report and fact_id in result.evidence_report.results:
                ev_result = result.evidence_report.results[fact_id]
                self.validation_store.update_evidence_status(
                    fact_id=fact_id,
                    verified=(ev_result.status == "verified"),
                    match_score=ev_result.match_score,
                    matched_text=ev_result.matched_text
                )

            # Add flags for this fact
            for flag in result.all_flags:
                if hasattr(flag, 'affected_fact_ids'):
                    if fact_id in flag.affected_fact_ids:
                        self.validation_store.add_flag(fact_id, flag)

            # Mark as AI validated
            self.validation_store.mark_ai_validated(
                fact_id=fact_id,
                confidence=result.overall_confidence
            )

        # Update domain state
        domain_state = self.validation_store.get_domain_state(domain)
        domain_state.total_facts = len(facts)
        domain_state.overall_confidence = result.overall_confidence

        if result.category_report:
            domain_state.category_completeness = {
                cat: res.confidence
                for cat, res in result.category_report.results.items()
            }

        self.validation_store.update_domain_state(domain, domain_state)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _categorize_facts(
        self,
        facts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group facts by category."""
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for fact in facts:
            category = fact.get("category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(fact)
        return by_category


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_domain(
    api_key: str,
    domain: str,
    document_text: str,
    facts: List[Dict[str, Any]],
    validation_store: Optional[ValidationStore] = None
) -> ValidationPipelineResult:
    """Convenience function to validate a domain."""
    pipeline = ValidationPipeline(
        api_key=api_key,
        validation_store=validation_store
    )
    return pipeline.validate_domain(
        domain=domain,
        document_text=document_text,
        facts=facts
    )


def create_pipeline(
    api_key: str,
    validation_store: Optional[ValidationStore] = None
) -> ValidationPipeline:
    """Create a validation pipeline instance."""
    return ValidationPipeline(
        api_key=api_key,
        validation_store=validation_store
    )
