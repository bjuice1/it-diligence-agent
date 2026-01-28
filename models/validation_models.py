"""
Validation Models for IT Due Diligence System

Core data models for the three-layer validation architecture:
- Layer 1: Category checkpoints
- Layer 2: Domain validation
- Layer 3: Cross-domain consistency

Also includes models for human review workflow and correction pipeline.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class ValidationStatus(Enum):
    """Status of a fact's validation lifecycle."""
    EXTRACTED = "extracted"           # Just pulled from doc, no validation yet
    AI_VALIDATED = "ai_validated"     # AI has reviewed
    HUMAN_PENDING = "human_pending"   # Flagged for human review
    HUMAN_CONFIRMED = "confirmed"     # Human verified as correct
    HUMAN_CORRECTED = "corrected"     # Human fixed an error
    HUMAN_REJECTED = "rejected"       # Human says this is wrong/fabricated


class FlagSeverity(Enum):
    """How serious is the validation flag."""
    INFO = "info"           # FYI, looks fine
    WARNING = "warning"     # Might be an issue, please check
    ERROR = "error"         # Likely wrong, needs review
    CRITICAL = "critical"   # Almost certainly wrong or missing

    @property
    def priority(self) -> int:
        """Numeric priority for sorting (higher = more urgent)."""
        priorities = {
            FlagSeverity.INFO: 1,
            FlagSeverity.WARNING: 2,
            FlagSeverity.ERROR: 3,
            FlagSeverity.CRITICAL: 4
        }
        return priorities.get(self, 0)


class FlagCategory(Enum):
    """Category of validation flag."""
    EVIDENCE = "evidence"             # Evidence quote issues
    COMPLETENESS = "completeness"     # Missing items
    CONSISTENCY = "consistency"       # Numbers don't add up
    CROSS_DOMAIN = "cross_domain"     # Cross-domain inconsistency
    DERIVED = "derived"               # Issue from correction ripple
    MANUAL = "manual"                 # Human-added flag
    ADVERSARIAL = "adversarial"       # From adversarial review


# =============================================================================
# VALIDATION FLAGS
# =============================================================================

def generate_flag_id() -> str:
    """Generate a unique flag ID."""
    return f"FLAG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


@dataclass
class ValidationFlag:
    """A specific issue found during validation."""
    flag_id: str
    severity: FlagSeverity
    category: FlagCategory
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False

    # What fact(s) this flag relates to
    affected_fact_ids: List[str] = field(default_factory=list)

    # Resolution tracking
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source: str = "ai_validation"  # "ai_validation", "manual", "correction_ripple"

    def resolve(self, resolved_by: str, note: Optional[str] = None):
        """Mark this flag as resolved."""
        self.resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = datetime.now()
        self.resolution_note = note

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "flag_id": self.flag_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "affected_fact_ids": self.affected_fact_ids,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_note": self.resolution_note,
            "created_at": self.created_at.isoformat(),
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationFlag":
        """Create from dictionary."""
        return cls(
            flag_id=data["flag_id"],
            severity=FlagSeverity(data["severity"]),
            category=FlagCategory(data["category"]),
            message=data["message"],
            suggestion=data.get("suggestion"),
            auto_fixable=data.get("auto_fixable", False),
            affected_fact_ids=data.get("affected_fact_ids", []),
            resolved=data.get("resolved", False),
            resolved_by=data.get("resolved_by"),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            resolution_note=data.get("resolution_note"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            source=data.get("source", "ai_validation")
        )


# =============================================================================
# FACT VALIDATION STATE
# =============================================================================

@dataclass
class FactValidationState:
    """Validation state for a single fact."""
    fact_id: str

    # Current status
    status: ValidationStatus = ValidationStatus.EXTRACTED

    # AI validation results
    ai_confidence: float = 0.0                    # 0.0 - 1.0
    ai_flags: List[ValidationFlag] = field(default_factory=list)
    ai_validated_at: Optional[datetime] = None

    # Evidence validation
    evidence_verified: Optional[bool] = None     # Did quote exist in source?
    evidence_match_score: Optional[float] = None # How closely did it match?
    evidence_matched_text: Optional[str] = None  # What was actually found

    # Human review
    human_reviewed: bool = False
    human_reviewer: Optional[str] = None
    human_reviewed_at: Optional[datetime] = None
    human_verdict: Optional[str] = None          # "confirmed", "corrected", "rejected"
    human_notes: Optional[str] = None

    # If corrected, track the correction
    correction_id: Optional[str] = None
    original_value: Optional[Dict[str, Any]] = None
    corrected_value: Optional[Dict[str, Any]] = None

    @property
    def effective_confidence(self) -> float:
        """
        Combined confidence score based on AI validation and human review.

        Human review trumps AI:
        - HUMAN_CONFIRMED: 0.95 (high but not perfect - human could be wrong)
        - HUMAN_CORRECTED: 1.0 (human correction is ground truth)
        - HUMAN_REJECTED: 0.0 (fact is invalid)
        - Otherwise: AI confidence
        """
        if self.status == ValidationStatus.HUMAN_CONFIRMED:
            return 0.95
        elif self.status == ValidationStatus.HUMAN_CORRECTED:
            return 1.0
        elif self.status == ValidationStatus.HUMAN_REJECTED:
            return 0.0
        else:
            return self.ai_confidence

    @property
    def needs_human_review(self) -> bool:
        """Does this fact need human attention?"""
        # Already reviewed - no need
        if self.human_reviewed:
            return False

        # Low AI confidence - needs review
        if self.ai_confidence < 0.7:
            return True

        # Has ERROR or CRITICAL flags - needs review
        if any(f.severity in (FlagSeverity.ERROR, FlagSeverity.CRITICAL)
               for f in self.ai_flags if not f.resolved):
            return True

        # Evidence not found - needs review
        if self.evidence_verified is False:
            return True

        return False

    @property
    def unresolved_flags(self) -> List[ValidationFlag]:
        """Get flags that haven't been resolved."""
        return [f for f in self.ai_flags if not f.resolved]

    @property
    def highest_severity(self) -> Optional[FlagSeverity]:
        """Get the highest severity among unresolved flags."""
        unresolved = self.unresolved_flags
        if not unresolved:
            return None
        return max(unresolved, key=lambda f: f.severity.priority).severity

    def add_flag(self, flag: ValidationFlag):
        """Add a validation flag."""
        self.ai_flags.append(flag)

        # Update status if this is a serious flag
        if flag.severity in (FlagSeverity.ERROR, FlagSeverity.CRITICAL):
            if self.status == ValidationStatus.AI_VALIDATED:
                self.status = ValidationStatus.HUMAN_PENDING

    def mark_ai_validated(self, confidence: float):
        """Mark as AI validated with given confidence."""
        self.ai_confidence = confidence
        self.ai_validated_at = datetime.now()
        self.status = ValidationStatus.AI_VALIDATED

        # If low confidence or has serious flags, mark for human review
        if self.needs_human_review:
            self.status = ValidationStatus.HUMAN_PENDING

    def mark_human_confirmed(self, reviewer: str, notes: Optional[str] = None):
        """Mark as confirmed by human."""
        self.human_reviewed = True
        self.human_reviewer = reviewer
        self.human_reviewed_at = datetime.now()
        self.human_verdict = "confirmed"
        self.human_notes = notes
        self.status = ValidationStatus.HUMAN_CONFIRMED

    def mark_human_corrected(self, reviewer: str, correction_id: str,
                             original: Dict, corrected: Dict, notes: Optional[str] = None):
        """Mark as corrected by human."""
        self.human_reviewed = True
        self.human_reviewer = reviewer
        self.human_reviewed_at = datetime.now()
        self.human_verdict = "corrected"
        self.human_notes = notes
        self.correction_id = correction_id
        self.original_value = original
        self.corrected_value = corrected
        self.status = ValidationStatus.HUMAN_CORRECTED

    def mark_human_rejected(self, reviewer: str, reason: str):
        """Mark as rejected by human."""
        self.human_reviewed = True
        self.human_reviewer = reviewer
        self.human_reviewed_at = datetime.now()
        self.human_verdict = "rejected"
        self.human_notes = reason
        self.status = ValidationStatus.HUMAN_REJECTED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "fact_id": self.fact_id,
            "status": self.status.value,
            "ai_confidence": self.ai_confidence,
            "ai_flags": [f.to_dict() for f in self.ai_flags],
            "ai_validated_at": self.ai_validated_at.isoformat() if self.ai_validated_at else None,
            "evidence_verified": self.evidence_verified,
            "evidence_match_score": self.evidence_match_score,
            "evidence_matched_text": self.evidence_matched_text,
            "human_reviewed": self.human_reviewed,
            "human_reviewer": self.human_reviewer,
            "human_reviewed_at": self.human_reviewed_at.isoformat() if self.human_reviewed_at else None,
            "human_verdict": self.human_verdict,
            "human_notes": self.human_notes,
            "correction_id": self.correction_id,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "effective_confidence": self.effective_confidence,
            "needs_human_review": self.needs_human_review
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactValidationState":
        """Create from dictionary."""
        state = cls(fact_id=data["fact_id"])
        state.status = ValidationStatus(data.get("status", "extracted"))
        state.ai_confidence = data.get("ai_confidence", 0.0)
        state.ai_flags = [ValidationFlag.from_dict(f) for f in data.get("ai_flags", [])]
        state.ai_validated_at = datetime.fromisoformat(data["ai_validated_at"]) if data.get("ai_validated_at") else None
        state.evidence_verified = data.get("evidence_verified")
        state.evidence_match_score = data.get("evidence_match_score")
        state.evidence_matched_text = data.get("evidence_matched_text")
        state.human_reviewed = data.get("human_reviewed", False)
        state.human_reviewer = data.get("human_reviewer")
        state.human_reviewed_at = datetime.fromisoformat(data["human_reviewed_at"]) if data.get("human_reviewed_at") else None
        state.human_verdict = data.get("human_verdict")
        state.human_notes = data.get("human_notes")
        state.correction_id = data.get("correction_id")
        state.original_value = data.get("original_value")
        state.corrected_value = data.get("corrected_value")
        return state


# =============================================================================
# DOMAIN VALIDATION STATE
# =============================================================================

@dataclass
class DomainValidationState:
    """Validation state for an entire domain."""
    domain: str

    # Aggregate stats
    total_facts: int = 0
    facts_validated: int = 0
    facts_flagged: int = 0
    facts_human_reviewed: int = 0
    facts_confirmed: int = 0
    facts_corrected: int = 0
    facts_rejected: int = 0

    # Category-level validation
    category_completeness: Dict[str, float] = field(default_factory=dict)
    categories_validated: Dict[str, bool] = field(default_factory=dict)

    # Domain-level flags
    domain_flags: List[ValidationFlag] = field(default_factory=list)

    # Validation metadata
    validated_at: Optional[datetime] = None
    requires_rerun: bool = False
    rerun_guidance: Optional[str] = None

    # Missing items identified during validation
    missing_items: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def overall_confidence(self) -> float:
        """
        Calculate overall confidence for the domain.

        Weights human-reviewed facts higher than AI-only validation.
        """
        if self.total_facts == 0:
            return 0.0

        # Human reviewed facts get high confidence
        human_reviewed_weight = (self.facts_confirmed + self.facts_corrected) / self.total_facts

        # AI-only validated facts get moderate confidence
        ai_only = self.facts_validated - self.facts_human_reviewed
        ai_only_weight = ai_only / self.total_facts if ai_only > 0 else 0

        # Calculate weighted confidence
        # Human reviewed: 0.95, AI only: 0.70, Not validated: 0.30
        not_validated = self.total_facts - self.facts_validated
        not_validated_weight = not_validated / self.total_facts if not_validated > 0 else 0

        confidence = (human_reviewed_weight * 0.95) + (ai_only_weight * 0.70) + (not_validated_weight * 0.30)

        # Penalize for unresolved domain-level flags
        unresolved_critical = sum(1 for f in self.domain_flags
                                   if f.severity == FlagSeverity.CRITICAL and not f.resolved)
        unresolved_error = sum(1 for f in self.domain_flags
                               if f.severity == FlagSeverity.ERROR and not f.resolved)

        confidence -= (unresolved_critical * 0.15)
        confidence -= (unresolved_error * 0.05)

        return max(0.0, min(1.0, confidence))

    @property
    def review_progress(self) -> float:
        """What percentage of flagged items have been reviewed?"""
        if self.facts_flagged == 0:
            return 1.0
        return self.facts_human_reviewed / self.facts_flagged

    @property
    def is_complete(self) -> bool:
        """Is domain validation complete (no reruns needed, no critical flags)?"""
        if self.requires_rerun:
            return False
        critical_flags = [f for f in self.domain_flags
                        if f.severity == FlagSeverity.CRITICAL and not f.resolved]
        return len(critical_flags) == 0

    def update_stats(self, fact_states: List[FactValidationState]):
        """Update aggregate stats from fact validation states."""
        self.total_facts = len(fact_states)
        self.facts_validated = sum(1 for s in fact_states if s.status != ValidationStatus.EXTRACTED)
        self.facts_flagged = sum(1 for s in fact_states if s.needs_human_review)
        self.facts_human_reviewed = sum(1 for s in fact_states if s.human_reviewed)
        self.facts_confirmed = sum(1 for s in fact_states if s.status == ValidationStatus.HUMAN_CONFIRMED)
        self.facts_corrected = sum(1 for s in fact_states if s.status == ValidationStatus.HUMAN_CORRECTED)
        self.facts_rejected = sum(1 for s in fact_states if s.status == ValidationStatus.HUMAN_REJECTED)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "domain": self.domain,
            "total_facts": self.total_facts,
            "facts_validated": self.facts_validated,
            "facts_flagged": self.facts_flagged,
            "facts_human_reviewed": self.facts_human_reviewed,
            "facts_confirmed": self.facts_confirmed,
            "facts_corrected": self.facts_corrected,
            "facts_rejected": self.facts_rejected,
            "category_completeness": self.category_completeness,
            "categories_validated": self.categories_validated,
            "domain_flags": [f.to_dict() for f in self.domain_flags],
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "requires_rerun": self.requires_rerun,
            "rerun_guidance": self.rerun_guidance,
            "missing_items": self.missing_items,
            "overall_confidence": self.overall_confidence,
            "review_progress": self.review_progress,
            "is_complete": self.is_complete
        }


# =============================================================================
# CROSS-DOMAIN VALIDATION STATE
# =============================================================================

@dataclass
class ConsistencyCheck:
    """Result of a single cross-domain consistency check."""
    check_name: str
    domains_involved: List[str]
    is_consistent: bool
    expected_value: Any
    actual_value: Any
    discrepancy: Optional[str] = None
    severity: FlagSeverity = FlagSeverity.WARNING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "domains_involved": self.domains_involved,
            "is_consistent": self.is_consistent,
            "expected_value": str(self.expected_value),
            "actual_value": str(self.actual_value),
            "discrepancy": self.discrepancy,
            "severity": self.severity.value
        }


@dataclass
class CrossDomainValidationState:
    """Validation state across all domains."""

    # Consistency checks
    consistency_checks: List[ConsistencyCheck] = field(default_factory=list)
    consistency_flags: List[ValidationFlag] = field(default_factory=list)

    # LLM holistic review findings
    holistic_findings: List[str] = field(default_factory=list)

    # Metadata
    validated_at: Optional[datetime] = None
    domains_included: List[str] = field(default_factory=list)

    @property
    def checks_passed(self) -> int:
        return sum(1 for c in self.consistency_checks if c.is_consistent)

    @property
    def checks_failed(self) -> int:
        return sum(1 for c in self.consistency_checks if not c.is_consistent)

    @property
    def consistency_score(self) -> float:
        """Calculate consistency score based on checks."""
        if not self.consistency_checks:
            return 1.0

        # Start at 1.0, subtract for failures weighted by severity
        score = 1.0
        for check in self.consistency_checks:
            if not check.is_consistent:
                if check.severity == FlagSeverity.CRITICAL:
                    score -= 0.2
                elif check.severity == FlagSeverity.ERROR:
                    score -= 0.1
                else:
                    score -= 0.05

        return max(0.0, score)

    @property
    def is_consistent(self) -> bool:
        """Are all domains consistent with each other?"""
        # Check for unresolved critical flags
        critical_unresolved = [f for f in self.consistency_flags
                              if f.severity == FlagSeverity.CRITICAL and not f.resolved]
        if critical_unresolved:
            return False

        # Check consistency score threshold
        return self.consistency_score >= 0.7

    @property
    def requires_investigation(self) -> List[str]:
        """Get list of issues requiring human investigation."""
        issues = []

        # Failed checks
        for check in self.consistency_checks:
            if not check.is_consistent and check.discrepancy:
                issues.append(check.discrepancy)

        # Unresolved flags
        for flag in self.consistency_flags:
            if not flag.resolved:
                issues.append(flag.message)

        # Holistic findings
        issues.extend(self.holistic_findings)

        return issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consistency_checks": [c.to_dict() for c in self.consistency_checks],
            "consistency_flags": [f.to_dict() for f in self.consistency_flags],
            "holistic_findings": self.holistic_findings,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "domains_included": self.domains_included,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "consistency_score": self.consistency_score,
            "is_consistent": self.is_consistent,
            "requires_investigation": self.requires_investigation
        }


# =============================================================================
# CORRECTION MODELS
# =============================================================================

@dataclass
class CorrectionRecord:
    """Record of a human correction to a fact."""
    correction_id: str
    fact_id: str
    timestamp: datetime
    corrected_by: str

    # What changed
    original_value: Dict[str, Any]
    corrected_value: Dict[str, Any]

    # Context
    reason: str
    new_evidence: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correction_id": self.correction_id,
            "fact_id": self.fact_id,
            "timestamp": self.timestamp.isoformat(),
            "corrected_by": self.corrected_by,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "reason": self.reason,
            "new_evidence": self.new_evidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrectionRecord":
        return cls(
            correction_id=data["correction_id"],
            fact_id=data["fact_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            corrected_by=data["corrected_by"],
            original_value=data["original_value"],
            corrected_value=data["corrected_value"],
            reason=data["reason"],
            new_evidence=data.get("new_evidence")
        )


@dataclass
class RippleEffect:
    """A derived value that was updated due to a correction."""
    field: str
    old_value: Any
    new_value: Any
    reason: str
    affected_fact_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "affected_fact_ids": self.affected_fact_ids
        }


@dataclass
class CorrectionResult:
    """Result of applying a human correction."""
    success: bool
    correction_id: str

    # What changed
    original_value: Dict[str, Any]
    corrected_value: Dict[str, Any]

    # Ripple effects
    derived_values_updated: List[RippleEffect] = field(default_factory=list)
    new_flags_created: List[ValidationFlag] = field(default_factory=list)

    # For user feedback
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "correction_id": self.correction_id,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "derived_values_updated": [r.to_dict() for r in self.derived_values_updated],
            "new_flags_created": [f.to_dict() for f in self.new_flags_created],
            "message": self.message
        }


# =============================================================================
# VALIDATION PIPELINE RESULT
# =============================================================================

@dataclass
class CategoryValidationResult:
    """Result of validating a single category."""
    category: str
    is_complete: bool
    confidence: float
    missing_items: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendation: str = "pass"  # "pass", "retry", "manual_review"
    raw_validation: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "is_complete": self.is_complete,
            "confidence": self.confidence,
            "missing_items": self.missing_items,
            "errors": self.errors,
            "recommendation": self.recommendation
        }


@dataclass
class DomainValidationResult:
    """Result of domain-level validation."""
    domain: str
    is_valid: bool
    completeness_score: float

    categories_validated: Dict[str, bool] = field(default_factory=dict)
    missing_items: List[Dict[str, Any]] = field(default_factory=list)
    inconsistencies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    requires_rerun: bool = False
    rerun_guidance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "is_valid": self.is_valid,
            "completeness_score": self.completeness_score,
            "categories_validated": self.categories_validated,
            "missing_items": self.missing_items,
            "inconsistencies": self.inconsistencies,
            "recommendations": self.recommendations,
            "requires_rerun": self.requires_rerun,
            "rerun_guidance": self.rerun_guidance
        }


@dataclass
class ValidationPipelineResult:
    """Complete result from the validation pipeline."""
    domain: str

    # Layer results
    layer1_results: Dict[str, CategoryValidationResult] = field(default_factory=dict)
    layer2_result: Optional[DomainValidationResult] = None
    layer3_result: Optional[CrossDomainValidationState] = None

    # Evidence verification summary
    evidence_verified_count: int = 0
    evidence_failed_count: int = 0

    # Overall status
    overall_valid: bool = True
    requires_rerun: bool = False
    rerun_guidance: Optional[str] = None
    human_review_needed: bool = False
    human_review_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "layer1_results": {k: v.to_dict() for k, v in self.layer1_results.items()},
            "layer2_result": self.layer2_result.to_dict() if self.layer2_result else None,
            "layer3_result": self.layer3_result.to_dict() if self.layer3_result else None,
            "evidence_verified_count": self.evidence_verified_count,
            "evidence_failed_count": self.evidence_failed_count,
            "overall_valid": self.overall_valid,
            "requires_rerun": self.requires_rerun,
            "rerun_guidance": self.rerun_guidance,
            "human_review_needed": self.human_review_needed,
            "human_review_reasons": self.human_review_reasons
        }
