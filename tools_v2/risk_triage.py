"""
Risk Triage Module

Post-processes risks from ReasoningStore to categorize them into:
- RISKS: True integration/operational risks (red flags)
- OPEN_QUESTIONS: Information gaps that need answers
- INTEGRATION_ACTIVITIES: Actions required for integration (move to work items)

This keeps the reasoning prompt simple while ensuring clean output categorization.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum


class FindingCategory(Enum):
    """Categories for triaged findings."""
    RISK = "risk"                         # True risks - things that could go wrong
    OPEN_QUESTION = "open_question"       # Info gaps - need more data
    INTEGRATION_ACTIVITY = "integration_activity"  # Actions needed


# =============================================================================
# SIGNAL PATTERNS
# =============================================================================

# Signals that indicate an information gap (should be Open Question)
INFO_GAP_SIGNALS = [
    # Explicit gap language
    "no documentation",
    "not provided",
    "not documented",
    "no evidence",
    "no information",
    "not mentioned",
    "not specified",
    "not disclosed",
    "no details",
    "unclear",
    "unknown",
    "unconfirmed",
    "not available",
    "missing",
    "gap in",
    "lack of",
    "absence of",
    "unable to confirm",
    "unable to verify",
    "cannot determine",
    "insufficient information",
    "limited visibility",
    "no visibility",
    # Question-like language
    "needs clarification",
    "requires confirmation",
    "should be verified",
    "needs to be confirmed",
    "awaiting",
    "pending information",
]

# Signals that indicate an integration activity (should be Work Item)
ACTIVITY_SIGNALS = [
    # Separation/migration language
    "must be separated",
    "needs to be separated",
    "will need to separate",
    "must be migrated",
    "needs to be migrated",
    "will need to migrate",
    "requires migration",
    "must be established",
    "needs to be established",
    "must be implemented",
    "needs to be implemented",
    "will require implementation",
    # Dependency language that implies action
    "depends on parent",
    "dependent on parent",
    "hosted by parent",
    "provided by parent",
    "shared with parent",
    "on parent's",
    "parent-owned",
    "parent-managed",
    # Action-oriented language
    "buyer will need to",
    "buyer must",
    "requires standup",
    "requires setup",
    "needs to be replaced",
    "needs to be transitioned",
    "transition required",
    "cutover required",
]

# Signals that confirm this is a true risk (keep as Risk)
TRUE_RISK_SIGNALS = [
    # Security/vulnerability language
    "vulnerability",
    "vulnerabilities",
    "security risk",
    "security concern",
    "exposure",
    "breach",
    "compromised",
    "insecure",
    "unpatched",
    "end-of-life",
    "end of life",
    "unsupported",
    "deprecated",
    # Operational risk language
    "single point of failure",
    "key person",
    "key man",
    "bus factor",
    "no backup",
    "no redundancy",
    "critical dependency",
    "technical debt",
    "legacy system",
    # Impact language
    "could cause",
    "may result in",
    "risk of",
    "potential for",
    "failure",
    "outage",
    "downtime",
    "data loss",
    "business continuity",
    "compliance violation",
    "regulatory",
]


# =============================================================================
# TRIAGE LOGIC
# =============================================================================

def _check_signals(text: str, signals: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if text contains any of the signal phrases.

    Returns:
        (has_match, list_of_matched_signals)
    """
    text_lower = text.lower()
    matches = [s for s in signals if s in text_lower]
    return len(matches) > 0, matches


def triage_risk(risk) -> Tuple[FindingCategory, str, List[str]]:
    """
    Categorize a single risk into the appropriate bucket.

    Args:
        risk: Risk object with title, description, severity fields

    Returns:
        (category, reason, matched_signals)
    """
    # Combine title and description for analysis
    text = f"{risk.title} {risk.description}".lower()

    # Also check mitigation if available
    if hasattr(risk, 'mitigation') and risk.mitigation:
        text += f" {risk.mitigation}".lower()

    # Check for each signal type
    has_gap_signals, gap_matches = _check_signals(text, INFO_GAP_SIGNALS)
    has_activity_signals, activity_matches = _check_signals(text, ACTIVITY_SIGNALS)
    has_risk_signals, risk_matches = _check_signals(text, TRUE_RISK_SIGNALS)

    # Decision logic with precedence

    # 1. If it has strong risk signals, keep as risk (even if it also has gap signals)
    if has_risk_signals and len(risk_matches) >= 2:
        return (
            FindingCategory.RISK,
            f"Contains risk indicators: {', '.join(risk_matches[:3])}",
            risk_matches
        )

    # 2. If it's clearly an info gap with no risk signals
    if has_gap_signals and not has_risk_signals:
        return (
            FindingCategory.OPEN_QUESTION,
            f"Information gap: {', '.join(gap_matches[:3])}",
            gap_matches
        )

    # 3. If it's clearly an activity with no risk signals
    if has_activity_signals and not has_risk_signals:
        return (
            FindingCategory.INTEGRATION_ACTIVITY,
            f"Integration activity: {', '.join(activity_matches[:3])}",
            activity_matches
        )

    # 4. If it has gap signals AND activity signals, prefer activity
    if has_gap_signals and has_activity_signals:
        return (
            FindingCategory.INTEGRATION_ACTIVITY,
            f"Integration activity (with info needs): {', '.join(activity_matches[:3])}",
            activity_matches
        )

    # 5. If it has only gap signals (weaker case)
    if has_gap_signals:
        return (
            FindingCategory.OPEN_QUESTION,
            f"Likely information gap: {', '.join(gap_matches[:3])}",
            gap_matches
        )

    # 6. If it has only activity signals (weaker case)
    if has_activity_signals:
        return (
            FindingCategory.INTEGRATION_ACTIVITY,
            f"Likely integration activity: {', '.join(activity_matches[:3])}",
            activity_matches
        )

    # 7. Default: keep as risk (conservative approach)
    return (
        FindingCategory.RISK,
        "No reclassification signals detected - keeping as risk",
        []
    )


def triage_all_risks(risks: List) -> Dict[str, List]:
    """
    Triage all risks into categorized buckets.

    Args:
        risks: List of Risk objects

    Returns:
        {
            "risks": [risks that are true risks],
            "open_questions": [risks that are really info gaps],
            "integration_activities": [risks that are really activities],
            "triage_log": [log of decisions made]
        }
    """
    results = {
        "risks": [],
        "open_questions": [],
        "integration_activities": [],
        "triage_log": []
    }

    for risk in risks:
        category, reason, signals = triage_risk(risk)

        # Log the decision
        results["triage_log"].append({
            "finding_id": risk.finding_id if hasattr(risk, 'finding_id') else "unknown",
            "title": risk.title if hasattr(risk, 'title') else str(risk),
            "original_severity": risk.severity if hasattr(risk, 'severity') else "unknown",
            "triaged_to": category.value,
            "reason": reason,
            "signals": signals
        })

        # Add to appropriate bucket
        if category == FindingCategory.RISK:
            results["risks"].append(risk)
        elif category == FindingCategory.OPEN_QUESTION:
            results["open_questions"].append(risk)
        elif category == FindingCategory.INTEGRATION_ACTIVITY:
            results["integration_activities"].append(risk)

    return results


# =============================================================================
# CONVERSION HELPERS
# =============================================================================

def risk_to_open_question(risk) -> Dict:
    """
    Convert a Risk object to an Open Question format.
    """
    return {
        "id": f"OQ-{risk.finding_id}" if hasattr(risk, 'finding_id') else "OQ-XXX",
        "domain": risk.domain if hasattr(risk, 'domain') else "general",
        "question": risk.title if hasattr(risk, 'title') else str(risk),
        "context": risk.description if hasattr(risk, 'description') else "",
        "importance": _severity_to_importance(risk.severity if hasattr(risk, 'severity') else "medium"),
        "source_facts": risk.based_on_facts if hasattr(risk, 'based_on_facts') else [],
        "suggested_action": "Request documentation or clarification from target"
    }


def risk_to_activity(risk) -> Dict:
    """
    Convert a Risk object to an Integration Activity format.
    """
    return {
        "id": f"IA-{risk.finding_id}" if hasattr(risk, 'finding_id') else "IA-XXX",
        "domain": risk.domain if hasattr(risk, 'domain') else "general",
        "activity": risk.title if hasattr(risk, 'title') else str(risk),
        "description": risk.description if hasattr(risk, 'description') else "",
        "phase": _infer_phase(risk),
        "source_facts": risk.based_on_facts if hasattr(risk, 'based_on_facts') else [],
        "notes": risk.mitigation if hasattr(risk, 'mitigation') else ""
    }


def _severity_to_importance(severity: str) -> str:
    """Map risk severity to question importance."""
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low"
    }
    return mapping.get(severity.lower(), "medium")


def _infer_phase(risk) -> str:
    """Infer integration phase from risk content."""
    text = f"{risk.title} {risk.description}".lower() if hasattr(risk, 'description') else str(risk).lower()

    # Day 1 indicators
    day1_signals = ["day 1", "day-1", "immediate", "authentication", "access", "sso", "login"]
    if any(s in text for s in day1_signals):
        return "Day_1"

    # Post-100 indicators
    post100_signals = ["long-term", "optimization", "future", "roadmap"]
    if any(s in text for s in post100_signals):
        return "Post_100"

    # Default to Day 100
    return "Day_100"


# =============================================================================
# SUMMARY STATS
# =============================================================================

def get_triage_summary(triage_results: Dict) -> Dict:
    """
    Get summary statistics from triage results.
    """
    return {
        "total_input": len(triage_results["triage_log"]),
        "risks_kept": len(triage_results["risks"]),
        "moved_to_questions": len(triage_results["open_questions"]),
        "moved_to_activities": len(triage_results["integration_activities"]),
        "breakdown": {
            "risks": [r.title if hasattr(r, 'title') else str(r) for r in triage_results["risks"]],
            "open_questions": [r.title if hasattr(r, 'title') else str(r) for r in triage_results["open_questions"]],
            "integration_activities": [r.title if hasattr(r, 'title') else str(r) for r in triage_results["integration_activities"]]
        }
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'FindingCategory',
    'triage_risk',
    'triage_all_risks',
    'risk_to_open_question',
    'risk_to_activity',
    'get_triage_summary',
    'INFO_GAP_SIGNALS',
    'ACTIVITY_SIGNALS',
    'TRUE_RISK_SIGNALS',
]
