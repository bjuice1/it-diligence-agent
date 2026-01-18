"""
Shared Prompt Components for IT Due Diligence Agents

These components are imported by all domain agents to ensure consistent
anti-hallucination measures and evidence requirements.
"""

from .evidence_requirements import get_evidence_requirements, EVIDENCE_REQUIREMENTS
from .hallucination_guardrails import get_hallucination_guardrails, HALLUCINATION_GUARDRAILS
from .gap_over_guess import get_gap_over_guess, GAP_OVER_GUESS
from .confidence_calibration import get_confidence_calibration, CONFIDENCE_CALIBRATION
from .entity_distinction import ENTITY_DISTINCTION_PROMPT, ENTITY_DISTINCTION_SHORT


def get_all_shared_guidance() -> str:
    """
    Return all shared guidance components concatenated.
    Use this in domain prompts to include all anti-hallucination measures.
    """
    return "\n\n".join([
        EVIDENCE_REQUIREMENTS,
        HALLUCINATION_GUARDRAILS,
        GAP_OVER_GUESS,
        CONFIDENCE_CALIBRATION
    ])


__all__ = [
    'get_evidence_requirements',
    'get_hallucination_guardrails',
    'get_gap_over_guess',
    'get_confidence_calibration',
    'get_all_shared_guidance',
    'EVIDENCE_REQUIREMENTS',
    'HALLUCINATION_GUARDRAILS',
    'GAP_OVER_GUESS',
    'CONFIDENCE_CALIBRATION',
    'ENTITY_DISTINCTION_PROMPT',
    'ENTITY_DISTINCTION_SHORT'
]
