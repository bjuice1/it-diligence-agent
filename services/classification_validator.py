"""
Classification Validator for Risks vs Gaps (B3 Fix)

Validates that risks are properly classified and have supporting evidence.
Risks without evidence should be downgraded to observations.
Items with "unknown" or "not provided" language should be gaps, not risks.

Usage:
    from services.classification_validator import validate_and_classify, validate_risk

    result = validate_and_classify(finding, 'risk')
    if result.suggested_type != 'risk':
        # Downgrade this item

    # Or for simple risk validation:
    if not validate_risk(risk):
        # Risk lacks evidence, should be observation
"""

from dataclasses import dataclass
from typing import Optional, List, Any
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# INDICATOR PATTERNS
# =============================================================================

# Language that indicates a gap (missing information)
GAP_INDICATORS = [
    'unknown', 'not provided', 'not documented',
    'not specified', 'unclear', 'need to confirm',
    'should verify', 'requires clarification',
    'missing', 'not included', 'unavailable',
    'no information', 'not stated', 'pending',
    'unable to determine', 'could not find',
    'not mentioned', 'no evidence of',
]

# Language that indicates uncertainty (observation, not confirmed risk)
OBSERVATION_INDICATORS = [
    'may', 'might', 'appears', 'possibly', 'seems',
    'could be', 'potential', 'likely', 'suggests',
    'probable', 'suspected', 'indication', 'concern',
    'appears to', 'seems to', 'may have', 'might be',
    'unclear if', 'uncertain whether',
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClassificationResult:
    """Result of classification validation."""
    original_type: str
    suggested_type: str
    reason: str
    confidence: float  # 0.0 to 1.0
    needs_review: bool = False

    @property
    def was_reclassified(self) -> bool:
        return self.original_type != self.suggested_type


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def validate_and_classify(item: Any, current_type: str) -> ClassificationResult:
    """
    Validate classification and suggest correction if needed.

    Args:
        item: Finding/risk/gap object with description and evidence attributes
        current_type: Current classification ('risk', 'gap', 'observation')

    Returns:
        ClassificationResult with suggested type and reason
    """
    # Get description text
    description = getattr(item, 'description', '') or ''
    title = getattr(item, 'title', '') or ''
    text = f"{title} {description}".lower()

    # Get evidence (various attribute names)
    evidence = (
        getattr(item, 'evidence_facts', None) or
        getattr(item, 'based_on_facts', None) or
        getattr(item, 'supporting_facts', [])
    )
    evidence_count = len(evidence) if evidence else 0

    # Check 1: Risks MUST have evidence
    if current_type == 'risk':
        if evidence_count == 0:
            logger.info(f"B3: Downgrading risk to observation (no evidence): {title[:50]}")
            return ClassificationResult(
                original_type='risk',
                suggested_type='observation',
                reason='Risk has no supporting evidence',
                confidence=0.9,
                needs_review=True
            )

    # Check 2: Gap indicators in risk/observation -> should be gap
    if current_type in ('risk', 'observation'):
        for indicator in GAP_INDICATORS:
            if indicator in text:
                logger.info(f"B3: Reclassifying to gap (contains '{indicator}'): {title[:50]}")
                return ClassificationResult(
                    original_type=current_type,
                    suggested_type='gap',
                    reason=f'Contains gap indicator: "{indicator}"',
                    confidence=0.8,
                    needs_review=False
                )

    # Check 3: Observation indicators in risk -> should be observation
    if current_type == 'risk':
        for indicator in OBSERVATION_INDICATORS:
            if indicator in text:
                logger.info(f"B3: Downgrading risk to observation (uncertainty: '{indicator}'): {title[:50]}")
                return ClassificationResult(
                    original_type='risk',
                    suggested_type='observation',
                    reason=f'Contains uncertainty indicator: "{indicator}"',
                    confidence=0.7,
                    needs_review=True
                )

    # No issues found
    return ClassificationResult(
        original_type=current_type,
        suggested_type=current_type,
        reason='Classification appears correct',
        confidence=1.0,
        needs_review=False
    )


def validate_risk(risk: Any) -> bool:
    """
    Simple validation: does this risk have evidence?

    Args:
        risk: Risk object with evidence_facts or based_on_facts attribute

    Returns:
        True if risk has evidence, False otherwise
    """
    evidence = (
        getattr(risk, 'evidence_facts', None) or
        getattr(risk, 'based_on_facts', None) or
        []
    )
    return len(evidence) > 0


def validate_findings_batch(findings: List[Any]) -> dict:
    """
    Validate a batch of findings and return summary.

    Args:
        findings: List of finding objects (risks, gaps, observations)

    Returns:
        Dict with counts and items needing reclassification
    """
    results = {
        'total': len(findings),
        'valid': 0,
        'reclassify': [],
        'by_type': {
            'risk_to_observation': [],
            'risk_to_gap': [],
            'observation_to_gap': [],
        }
    }

    for finding in findings:
        finding_type = getattr(finding, 'finding_type', 'risk')
        result = validate_and_classify(finding, finding_type)

        if result.was_reclassified:
            key = f"{result.original_type}_to_{result.suggested_type}"
            if key in results['by_type']:
                results['by_type'][key].append({
                    'id': getattr(finding, 'id', 'unknown'),
                    'title': getattr(finding, 'title', '')[:50],
                    'reason': result.reason,
                })
            results['reclassify'].append(result)
        else:
            results['valid'] += 1

    logger.info(
        f"B3 Batch validation: {results['valid']}/{results['total']} valid, "
        f"{len(results['reclassify'])} need reclassification"
    )

    return results


def has_gap_language(text: str) -> bool:
    """Check if text contains gap indicator language."""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in GAP_INDICATORS)


def has_uncertainty_language(text: str) -> bool:
    """Check if text contains uncertainty/observation language."""
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in OBSERVATION_INDICATORS)
