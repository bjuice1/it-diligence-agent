"""
Analysis Tools for IT Diligence Agents

These tools are used by Claude to record structured findings during analysis.
Each tool creates a specific type of output that feeds into the final report.

Updated for Four-Lens DD Framework:
- create_current_state_entry (Lens 1)
- identify_risk with integration_dependent flag (Lens 2)
- create_strategic_consideration (Lens 3)
- create_work_item with phase tagging (Lens 4)

Anti-Hallucination Features (v2.0):
- source_evidence required on key findings
- exact_quote validation
- confidence_level on all findings
- evidence_type classification
- Evidence density metrics
"""
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from difflib import SequenceMatcher


# =============================================================================
# STANDARDIZED ENUMS
# =============================================================================

# All domains supported by the system
ALL_DOMAINS = [
    "infrastructure",
    "network",
    "cybersecurity",
    "applications",
    "organization",
    "identity_access",
    "cross-domain"
]

# Evidence types for anti-hallucination
EVIDENCE_TYPES = ["direct_statement", "logical_inference", "pattern_based"]

# Confidence levels
CONFIDENCE_LEVELS = ["high", "medium", "low"]

# Gap types for categorization
GAP_TYPES = ["missing_document", "incomplete_detail", "unclear_statement", "unstated_critical"]


# =============================================================================
# SOURCE EVIDENCE SCHEMA (reusable)
# =============================================================================

SOURCE_EVIDENCE_SCHEMA = {
    "type": "object",
    "description": "Evidence from the source document supporting this finding. REQUIRED for all findings.",
    "properties": {
        "exact_quote": {
            "type": "string",
            "description": "Verbatim text from the document (copy-paste, 10-500 chars). REQUIRED."
        },
        "source_section": {
            "type": "string",
            "description": "Section of document where evidence was found (e.g., 'Application Inventory', 'IT Organization')"
        },
        "evidence_type": {
            "type": "string",
            "enum": EVIDENCE_TYPES,
            "description": "direct_statement=explicitly stated, logical_inference=deduced from facts, pattern_based=recognized pattern (use sparingly)"
        },
        "confidence_level": {
            "type": "string",
            "enum": CONFIDENCE_LEVELS,
            "description": "high=certain/direct quote, medium=logical inference, low=pattern-based (consider flagging as gap)"
        }
    },
    "required": ["exact_quote", "evidence_type", "confidence_level"]
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_quote_exists(quote: str, document_text: str, threshold: float = 0.85) -> Tuple[bool, float]:
    """
    Validate that a quote exists in the source document.
    Uses fuzzy matching to handle minor OCR errors or formatting differences.

    Args:
        quote: The exact_quote from a finding
        document_text: The full source document text
        threshold: Minimum similarity ratio to consider a match (0.0-1.0)

    Returns:
        Tuple of (is_valid, best_match_score)
    """
    if not quote or not document_text:
        return False, 0.0

    quote_clean = quote.lower().strip()
    doc_clean = document_text.lower()

    # Quick check for exact substring match
    if quote_clean in doc_clean:
        return True, 1.0

    # Sliding window fuzzy match for longer quotes
    quote_len = len(quote_clean)
    if quote_len < 10:
        return False, 0.0

    best_score = 0.0
    window_size = min(quote_len + 50, len(doc_clean))  # Allow some flexibility

    # Sample positions to avoid O(n*m) complexity
    step = max(1, len(doc_clean) // 1000)
    for i in range(0, len(doc_clean) - quote_len, step):
        window = doc_clean[i:i + window_size]
        score = SequenceMatcher(None, quote_clean, window[:quote_len]).ratio()
        best_score = max(best_score, score)

        if best_score >= threshold:
            return True, best_score

    return best_score >= threshold, best_score


def calculate_evidence_density(findings_count: int, document_length: int) -> float:
    """
    Calculate findings per 1000 characters of source document.
    High density may indicate over-inference.

    Typical ranges:
    - < 0.5: Under-analyzed
    - 0.5 - 2.0: Normal range
    - > 2.0: May be over-inferring / hallucinating
    """
    if document_length == 0:
        return 0.0
    return (findings_count / document_length) * 1000


def assess_confidence_distribution(findings: List[Dict]) -> Dict[str, Any]:
    """
    Assess the distribution of confidence levels across findings.
    Flags suspicious patterns that may indicate hallucination.
    """
    if not findings:
        return {"status": "no_findings", "distribution": {}}

    distribution = {"high": 0, "medium": 0, "low": 0, "missing": 0}

    for finding in findings:
        # Check source_evidence.confidence_level or top-level confidence
        source_evidence = finding.get("source_evidence", {})
        confidence = source_evidence.get("confidence_level") or finding.get("confidence", "missing")

        if confidence in distribution:
            distribution[confidence] += 1
        else:
            distribution["missing"] += 1

    total = len(findings)
    percentages = {k: (v / total * 100) for k, v in distribution.items()}

    # Flag suspicious patterns
    warnings = []
    if percentages.get("high", 0) > 80:
        warnings.append("Over 80% high confidence - likely over-confident")
    if percentages.get("low", 0) > 30:
        warnings.append("Over 30% low confidence - consider converting to gaps")
    if percentages.get("missing", 0) > 10:
        warnings.append("Missing confidence levels on some findings")

    return {
        "status": "analyzed",
        "distribution": distribution,
        "percentages": percentages,
        "total_findings": total,
        "warnings": warnings
    }


# =============================================================================
# TOOL DEFINITIONS (for Anthropic API)
# =============================================================================

ANALYSIS_TOOLS = [
    # =========================================================================
    # LENS 1: CURRENT STATE ASSESSMENT
    # =========================================================================
    {
        "name": "create_current_state_entry",
        "description": """Record a current state observation about the IT environment.
        Use this in LENS 1 to document what exists TODAY, independent of any integration plans.
        Focus on MATURITY assessment, not just existence of tools/systems.

        IMPORTANT: You MUST provide source_evidence with an exact_quote from the document.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this observation relates to"
                },
                "category": {
                    "type": "string",
                    "description": "Specific area within domain (e.g., 'cloud_presence', 'wan_connectivity', 'iam_posture', 'compliance_certifications')"
                },
                "summary": {
                    "type": "string",
                    "description": "Plain-English description of what exists. Be specific - include numbers, versions, coverage percentages."
                },
                "maturity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Maturity level: low=basic/gaps, medium=functional/some gaps, high=robust/optimized"
                },
                "key_characteristics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable attributes (e.g., ['Single cloud provider', 'No IaC adoption', '60% MFA coverage'])"
                },
                "standalone_viability": {
                    "type": "string",
                    "enum": ["viable", "constrained", "high_risk"],
                    "description": "Could this operate independently? viable=yes, constrained=challenges, high_risk=significant issues"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document (for tracking provenance)"
                },
                "source_page": {
                    "type": "integer",
                    "description": "Page number in source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": ["domain", "category", "summary", "maturity", "standalone_viability", "source_evidence"]
        }
    },

    # =========================================================================
    # SUPPORTING TOOLS (used across lenses)
    # =========================================================================
    {
        "name": "log_assumption",
        "description": """Record an assumption made during analysis. Use this when you're making
        a judgment call based on available information. Every assumption should have clear reasoning
        about WHY you're making this assumption and what evidence supports it.

        IMPORTANT: Assumptions require supporting evidence. If you have no evidence, flag as gap instead.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "assumption": {
                    "type": "string",
                    "description": "The assumption being made (e.g., 'SAP ECC migration to S/4HANA will be required')"
                },
                "basis": {
                    "type": "string",
                    "description": "Evidence or reasoning supporting this assumption"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this assumption relates to"
                },
                "confidence": {
                    "type": "string",
                    "enum": CONFIDENCE_LEVELS,
                    "description": "Confidence level in this assumption"
                },
                "impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Impact if this assumption is wrong"
                },
                "validation_needed": {
                    "type": "string",
                    "description": "What would need to be verified to confirm this assumption"
                },
                "supporting_quote": {
                    "type": "string",
                    "description": "Direct quote from document that supports this assumption (if available)"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_section": {
                    "type": "string",
                    "description": "Section of document where assumption is based"
                }
            },
            "required": ["assumption", "basis", "domain", "confidence", "impact", "validation_needed"]
        }
    },
    {
        "name": "flag_gap",
        "description": """Flag a knowledge gap - information that is missing or unclear and needs
        to be obtained. Gaps should be specific and actionable - what exactly do we need to know?

        IMPORTANT: Prefer flagging gaps over making low-confidence findings. Gaps are valuable.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "gap": {
                    "type": "string",
                    "description": "What information is missing (e.g., 'Number of customizations in SAP ECC')"
                },
                "why_needed": {
                    "type": "string",
                    "description": "Why this information matters for the deal"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this gap relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "How urgently this gap needs to be filled"
                },
                "gap_type": {
                    "type": "string",
                    "enum": GAP_TYPES,
                    "description": "missing_document=doc should exist, incomplete_detail=topic mentioned but sparse, unclear_statement=ambiguous info, unstated_critical=critical info completely absent"
                },
                "suggested_source": {
                    "type": "string",
                    "description": "Suggested way to obtain this information (document request, interview, technical assessment)"
                },
                "cost_impact": {
                    "type": "string",
                    "enum": ["high", "medium", "low", "unknown"],
                    "description": "How much this gap affects cost estimation accuracy"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document where this gap was identified"
                },
                "source_section": {
                    "type": "string",
                    "description": "Section of document where gap was identified"
                }
            },
            "required": ["gap", "why_needed", "domain", "priority", "gap_type", "suggested_source"]
        }
    },
    {
        "name": "flag_question",
        "description": """Flag a question that needs to be asked to management/seller during follow-up.
        Use when you identify specific questions that need answers to complete the assessment.

        IMPORTANT: Questions should be specific and actionable. Include context about why the question matters.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific question to ask (e.g., 'What is the current cyber insurance coverage limit?')"
                },
                "context": {
                    "type": "string",
                    "description": "Why this question is important / what decision it impacts"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this question relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "How urgently this needs to be answered"
                },
                "related_gap_id": {
                    "type": "string",
                    "description": "If this question relates to a specific gap, provide the gap ID (e.g., 'G-001')"
                },
                "suggested_source": {
                    "type": "string",
                    "description": "Suggested person/role to ask (e.g., 'CTO', 'IT Director', 'CFO')"
                }
            },
            "required": ["question", "context", "domain", "priority"]
        }
    },

    # =========================================================================
    # LENS 2: RISK IDENTIFICATION (Enhanced with Anti-Hallucination)
    # =========================================================================
    {
        "name": "identify_risk",
        "description": """Identify a risk that could impact the deal, integration, or operations.

        CRITICAL REQUIREMENTS:
        1. You MUST provide source_evidence with an exact_quote from the document
        2. Flag whether this risk exists independent of integration (integration_dependent: false)
           or only because of integration plans (integration_dependent: true)
        3. If you cannot provide evidence, flag as gap instead of creating a risk

        DO NOT create risks based on pattern recognition alone. Every risk must be grounded in the document.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "risk": {
                    "type": "string",
                    "description": "Description of the risk"
                },
                "trigger": {
                    "type": "string",
                    "description": "What would cause this risk to materialize"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this risk relates to"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Severity if the risk materializes"
                },
                "likelihood": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Probability of this risk occurring"
                },
                "risk_type": {
                    "type": "string",
                    "enum": ["technical_debt", "security", "vendor", "organization", "scalability", "compliance", "integration"],
                    "description": "Category of risk"
                },
                "integration_dependent": {
                    "type": "boolean",
                    "description": "Does this risk ONLY exist because of integration? false=standalone risk, true=integration-specific"
                },
                "standalone_exposure": {
                    "type": "string",
                    "description": "If integration_dependent is false, describe the exposure if target operates independently"
                },
                "deal_impact": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["value_leakage", "execution_risk", "dependency", "timeline_risk", "cost_exposure", "tsa_dependency"]
                    },
                    "description": "How this risk affects the deal"
                },
                "impact_description": {
                    "type": "string",
                    "description": "What happens if this risk materializes (cost, timeline, operations)"
                },
                "mitigation": {
                    "type": "string",
                    "description": "Recommended actions to reduce or eliminate this risk"
                },
                "cost_impact_estimate": {
                    "type": "string",
                    "description": "Estimated cost impact if risk occurs (e.g., '$500K-$1M')"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_page": {
                    "type": "integer",
                    "description": "Page number in source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": ["risk", "trigger", "domain", "severity", "likelihood", "risk_type", "integration_dependent", "mitigation", "source_evidence"]
        }
    },

    # =========================================================================
    # LENS 3: STRATEGIC CONSIDERATIONS
    # =========================================================================
    {
        "name": "create_strategic_consideration",
        "description": """Record a strategic consideration - a deal-relevant insight that informs
        negotiation, structure, or planning. This is deal LOGIC, not deal MATH.

        IMPORTANT: The observation must be grounded in document evidence. Provide source_evidence.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "description": "Short theme name (e.g., 'Cloud Platform Mismatch', 'Key Person Dependency')"
                },
                "observation": {
                    "type": "string",
                    "description": "Neutral statement of fact (what IS, not what should be)"
                },
                "implication": {
                    "type": "string",
                    "description": "What this means for the deal - the 'so what'"
                },
                "deal_relevance": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["integration_risk", "value_leakage", "tsa_dependency", "execution_risk", "synergy_barrier"]
                    },
                    "description": "How this affects the deal"
                },
                "buyer_alignment": {
                    "type": "string",
                    "enum": ["aligned", "partial", "misaligned", "unknown"],
                    "description": "How well target approach aligns with buyer standards"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this relates to"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document"
                },
                "source_evidence": SOURCE_EVIDENCE_SCHEMA
            },
            "required": ["theme", "observation", "implication", "deal_relevance", "buyer_alignment", "domain", "source_evidence"]
        }
    },

    # =========================================================================
    # LENS 4: INTEGRATION ACTIONS (Enhanced with phases)
    # =========================================================================
    {
        "name": "create_work_item",
        "description": """Create a work item - a specific task or work package needed for integration.
        Work items should be concrete, estimable, and MUST be tagged with a phase.

        IMPORTANT: Work items should be linked to identified risks or gaps that drive them.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the work item"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the work required"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain this work item belongs to"
                },
                "category": {
                    "type": "string",
                    "enum": ["migration", "integration", "remediation", "assessment", "decommission", "security", "compliance"],
                    "description": "Type of work"
                },
                "phase": {
                    "type": "string",
                    "enum": ["Day_1", "Day_100", "Post_100", "Optional"],
                    "description": "When this work should occur: Day_1=business continuity must-haves, Day_100=stabilization/quick wins, Post_100=full integration, Optional=nice-to-have"
                },
                "phase_rationale": {
                    "type": "string",
                    "description": "Why this timing - what drives the phase assignment"
                },
                "effort_estimate": {
                    "type": "string",
                    "description": "Estimated effort (e.g., '2-4 weeks', '200-400 hours')"
                },
                "cost_estimate_range": {
                    "type": "string",
                    "description": "Estimated cost range (e.g., '$50K-$100K')"
                },
                "depends_on": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Work item IDs this depends on (e.g., ['WI-001', 'WI-003'])"
                },
                "skills_required": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills/roles needed (e.g., ['cloud_engineer', 'dba'])"
                },
                "triggered_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risk or gap IDs that drive this work item (e.g., ['R-001', 'G-003'])"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document that informed this work item"
                }
            },
            "required": ["title", "description", "domain", "category", "phase", "phase_rationale", "effort_estimate"]
        }
    },
    {
        "name": "create_recommendation",
        "description": """Create a strategic recommendation for the deal team. Recommendations
        should be actionable and clearly tied to findings.

        IMPORTANT: Link recommendations to specific risks, gaps, or findings that drive them.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation": {
                    "type": "string",
                    "description": "The recommendation"
                },
                "rationale": {
                    "type": "string",
                    "description": "Why this is recommended based on findings"
                },
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS + ["deal"],
                    "description": "Which domain this recommendation relates to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Priority level"
                },
                "timing": {
                    "type": "string",
                    "enum": ["pre_close", "day_1", "first_90_days", "ongoing"],
                    "description": "When to act on this recommendation"
                },
                "investment_required": {
                    "type": "string",
                    "description": "Resources or investment needed"
                },
                "driven_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Finding IDs that drive this recommendation (e.g., ['R-001', 'R-005', 'G-003'])"
                },
                "source_document_id": {
                    "type": "string",
                    "description": "ID of the source document that informed this recommendation"
                }
            },
            "required": ["recommendation", "rationale", "domain", "priority", "timing"]
        }
    },
    {
        "name": "complete_analysis",
        "description": """Signal that domain analysis is complete and provide a summary.
        Use this as the final tool call for a domain.

        IMPORTANT: Include evidence quality metrics in your summary.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "enum": ALL_DOMAINS,
                    "description": "Which domain analysis is complete"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of key findings (2-3 sentences)"
                },
                "complexity_assessment": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "very_high"],
                    "description": "Overall complexity for this domain"
                },
                "estimated_cost_range": {
                    "type": "string",
                    "description": "Total estimated cost range for this domain (e.g., '$500K-$1.5M')"
                },
                "estimated_timeline": {
                    "type": "string",
                    "description": "Estimated timeline for this domain's work (e.g., '12-18 months')"
                },
                "top_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3 risks for this domain (by risk ID)"
                },
                "critical_gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Most critical information gaps (by gap ID)"
                },
                "evidence_quality": {
                    "type": "object",
                    "description": "Self-assessment of evidence quality",
                    "properties": {
                        "high_confidence_findings": {"type": "integer"},
                        "medium_confidence_findings": {"type": "integer"},
                        "low_confidence_findings": {"type": "integer"},
                        "gaps_flagged": {"type": "integer"}
                    }
                }
            },
            "required": ["domain", "summary", "complexity_assessment", "top_risks", "critical_gaps"]
        }
    }
]


# =============================================================================
# ANALYSIS STORE (collects tool outputs)
# =============================================================================

@dataclass
class AnalysisStore:
    """
    Stores all findings from analysis agents.

    Updated for Four-Lens DD Framework with:
    - current_state entries (Lens 1)
    - strategic_considerations (Lens 3)
    - Enhanced risk schema with integration_dependent flag
    - Enhanced work items with phase tagging
    - DD completeness validation

    Phase 3 Updates (Points 47-52 of 115PP):
    - Database connection support
    - save_to_database() for persisting findings
    - load_from_database() for resuming analysis
    - get_analysis_history() for viewing past runs
    - run_id and document_id tracking
    """

    # Lens 1: Current State
    current_state: List[Dict] = field(default_factory=list)

    # Lens 2: Risks (enhanced)
    risks: List[Dict] = field(default_factory=list)

    # Lens 3: Strategic Considerations
    strategic_considerations: List[Dict] = field(default_factory=list)

    # Lens 4: Integration Actions
    work_items: List[Dict] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)

    # Supporting
    assumptions: List[Dict] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    questions: List[Dict] = field(default_factory=list)  # Questions for follow-up
    domain_summaries: Dict[str, Dict] = field(default_factory=dict)

    # Reasoning chain - stores the logic flow from observation to finding
    reasoning_chains: Dict[str, List[Dict]] = field(default_factory=dict)

    # Executive summary (generated by coordinator)
    executive_summary: Optional[Dict] = None

    # Point 51-52: Analysis run and document tracking
    run_id: Optional[str] = None
    document_ids: List[str] = field(default_factory=list)

    # Point 47: Database connection (injected) - use field() for proper dataclass handling
    _db: Any = field(default=None, init=False, repr=False)
    _repository: Any = field(default=None, init=False, repr=False)

    _id_counters: Dict[str, int] = field(default_factory=lambda: {
        "assumption": 0, "gap": 0, "question": 0, "risk": 0, "work_item": 0,
        "recommendation": 0, "current_state": 0, "strategic_consideration": 0
    })

    def _next_id(self, type_: str) -> str:
        """Generate sequential ID for a finding type"""
        prefix = {
            "assumption": "A",
            "gap": "G",
            "question": "Q",
            "risk": "R",
            "work_item": "WI",
            "recommendation": "REC",
            "current_state": "CS",
            "strategic_consideration": "SC"
        }
        self._id_counters[type_] += 1
        return f"{prefix[type_]}-{self._id_counters[type_]:03d}"

    def _check_duplicate(self, tool_name: str, tool_input: Dict, threshold: float = 0.85) -> Optional[Dict]:
        """Check if finding is duplicate of existing one"""
        finding_map = {
            "log_assumption": ("assumptions", "assumption"),
            "identify_risk": ("risks", "risk"),
            "flag_gap": ("gaps", "gap"),
            "flag_question": ("questions", "question"),
            "create_current_state_entry": ("current_state", "summary"),
            "create_strategic_consideration": ("strategic_considerations", "theme")
        }

        if tool_name not in finding_map:
            return None

        collection_name, key_field = finding_map[tool_name]
        existing = getattr(self, collection_name)

        # Check same domain first
        domain = tool_input.get("domain")
        domain_findings = [f for f in existing if f.get("domain") == domain]

        new_text = tool_input.get(key_field, "").lower().strip()
        if not new_text:
            return None

        # Check similarity
        for existing_item in domain_findings:
            existing_text = existing_item.get(key_field, "").lower().strip()
            if not existing_text:
                continue

            similarity = SequenceMatcher(None, new_text, existing_text).ratio()
            if similarity > threshold:
                return existing_item

        return None

    def execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Execute a tool and store the result.
        Includes duplicate detection and default value handling.
        """
        # Validate tool_input is a dict (Claude may sometimes send malformed input)
        if not isinstance(tool_input, dict):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid tool_input type for {tool_name}: expected dict, got {type(tool_input).__name__}. Value: {str(tool_input)[:200]}")
            return {
                "status": "error",
                "message": f"Invalid tool input: expected dict, got {type(tool_input).__name__}",
                "tool_name": tool_name
            }

        timestamp = datetime.now().isoformat()

        # Check for duplicates before adding
        duplicate = self._check_duplicate(tool_name, tool_input)
        if duplicate:
            return {
                "status": "duplicate",
                "id": duplicate["id"],
                "message": f"Similar finding already exists: {duplicate['id']}",
                "type": tool_name.replace("create_", "").replace("log_", "").replace("identify_", "").replace("flag_", "")
            }

        # Lens 1: Current State
        if tool_name == "create_current_state_entry":
            finding = {
                "id": self._next_id("current_state"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults
            if "key_characteristics" not in finding:
                finding["key_characteristics"] = []
            self.current_state.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "current_state"}

        # Supporting: Assumptions
        elif tool_name == "log_assumption":
            finding = {
                "id": self._next_id("assumption"),
                "timestamp": timestamp,
                **tool_input
            }
            self.assumptions.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "assumption"}

        # Supporting: Gaps
        elif tool_name == "flag_gap":
            finding = {
                "id": self._next_id("gap"),
                "timestamp": timestamp,
                **tool_input
            }
            self.gaps.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "gap"}

        # Supporting: Questions for follow-up
        elif tool_name == "flag_question":
            finding = {
                "id": self._next_id("question"),
                "timestamp": timestamp,
                **tool_input
            }
            self.questions.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "question"}

        # Lens 2: Risks (enhanced)
        elif tool_name == "identify_risk":
            finding = {
                "id": self._next_id("risk"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults for new fields (backward compatibility)
            if "risk_type" not in finding:
                finding["risk_type"] = "integration"
            if "integration_dependent" not in finding:
                finding["integration_dependent"] = True  # Default to integration risk
            if "deal_impact" not in finding:
                finding["deal_impact"] = []
            if "standalone_exposure" not in finding and not finding.get("integration_dependent", True):
                finding["standalone_exposure"] = "See risk description"
            self.risks.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "risk"}

        # Lens 3: Strategic Considerations
        elif tool_name == "create_strategic_consideration":
            finding = {
                "id": self._next_id("strategic_consideration"),
                "timestamp": timestamp,
                **tool_input
            }
            self.strategic_considerations.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "strategic_consideration"}

        # Lens 4: Work Items (enhanced)
        elif tool_name == "create_work_item":
            finding = {
                "id": self._next_id("work_item"),
                "timestamp": timestamp,
                **tool_input
            }
            # Add defaults for new fields
            if "phase" not in finding:
                finding["phase"] = "Day_100"  # Default phase
            if "phase_rationale" not in finding:
                finding["phase_rationale"] = "Default assignment"
            if "depends_on" not in finding:
                finding["depends_on"] = []
            self.work_items.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "work_item"}

        # Lens 4: Recommendations
        elif tool_name == "create_recommendation":
            finding = {
                "id": self._next_id("recommendation"),
                "timestamp": timestamp,
                **tool_input
            }
            self.recommendations.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "recommendation"}

        # Domain completion
        elif tool_name == "complete_analysis":
            domain = tool_input.get("domain")
            self.domain_summaries[domain] = {
                "timestamp": timestamp,
                **tool_input
            }
            return {"status": "domain_complete", "domain": domain}

        # Coordinator tools
        elif tool_name == "create_executive_summary":
            self.executive_summary = {
                "timestamp": timestamp,
                **tool_input
            }
            return {"status": "recorded", "type": "executive_summary"}

        elif tool_name == "identify_cross_domain_dependency":
            # Store as a cross-domain risk
            finding = {
                "id": self._next_id("risk"),
                "timestamp": timestamp,
                "risk": f"Cross-domain dependency: {tool_input.get('dependency', '')}",
                "trigger": tool_input.get("impact", ""),
                "domain": "cross-domain",
                "severity": "high",
                "likelihood": "high",
                "risk_type": "integration",
                "integration_dependent": True,
                "mitigation": tool_input.get("sequencing_requirement", ""),
                **tool_input
            }
            self.risks.append(finding)
            return {"status": "recorded", "id": finding["id"], "type": "cross_domain_dependency"}

        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def get_by_domain(self, domain: str) -> Dict:
        """Get all findings for a specific domain"""
        return {
            "current_state": [c for c in self.current_state if c.get("domain") == domain],
            "assumptions": [a for a in self.assumptions if a.get("domain") == domain],
            "gaps": [g for g in self.gaps if g.get("domain") == domain],
            "risks": [r for r in self.risks if r.get("domain") == domain],
            "strategic_considerations": [s for s in self.strategic_considerations if s.get("domain") == domain],
            "work_items": [w for w in self.work_items if w.get("domain") == domain],
            "recommendations": [r for r in self.recommendations if r.get("domain") == domain],
            "summary": self.domain_summaries.get(domain),
            "reasoning_chain": self.reasoning_chains.get(domain, [])
        }

    def add_reasoning_chain(self, domain: str, reasoning_entries: List[Dict]):
        """Add reasoning chain entries from an agent's analysis."""
        if domain not in self.reasoning_chains:
            self.reasoning_chains[domain] = []
        self.reasoning_chains[domain].extend(reasoning_entries)

    def get_reasoning_for_finding(self, finding_id: str) -> Optional[Dict]:
        """Get the reasoning chain entry for a specific finding"""
        for domain, entries in self.reasoning_chains.items():
            for entry in entries:
                if entry.get("finding_id") == finding_id:
                    return entry
        return None

    def get_all_reasoning(self) -> Dict[str, List[Dict]]:
        """Get all reasoning chains organized by domain"""
        return self.reasoning_chains

    def get_risks_by_type(self) -> Dict[str, List[Dict]]:
        """Get risks grouped by risk_type"""
        by_type = {}
        for risk in self.risks:
            risk_type = risk.get("risk_type", "other")
            if risk_type not in by_type:
                by_type[risk_type] = []
            by_type[risk_type].append(risk)
        return by_type

    def get_standalone_risks(self) -> List[Dict]:
        """Get risks that exist independent of integration"""
        return [r for r in self.risks if not r.get("integration_dependent", True)]

    def get_integration_risks(self) -> List[Dict]:
        """Get risks that only exist because of integration"""
        return [r for r in self.risks if r.get("integration_dependent", True)]

    def get_work_items_by_phase(self) -> Dict[str, List[Dict]]:
        """Get work items grouped by phase"""
        by_phase = {"Day_1": [], "Day_100": [], "Post_100": [], "Optional": []}
        for item in self.work_items:
            phase = item.get("phase", "Day_100")
            if phase in by_phase:
                by_phase[phase].append(item)
            else:
                by_phase["Day_100"].append(item)  # Default
        return by_phase

    def validate_work_item_dependencies(self) -> List[str]:
        """Check for dependency issues in work items"""
        issues = []
        work_item_ids = {w["id"] for w in self.work_items}
        work_item_phases = {w["id"]: w.get("phase", "Day_100") for w in self.work_items}
        phase_order = {"Day_1": 1, "Day_100": 2, "Post_100": 3, "Optional": 4}

        for item in self.work_items:
            item_phase = item.get("phase", "Day_100")
            for dep_id in item.get("depends_on", []):
                # Check if dependency exists
                if dep_id not in work_item_ids:
                    issues.append(f"{item['id']} depends on non-existent {dep_id}")
                else:
                    # Check phase ordering
                    dep_phase = work_item_phases.get(dep_id, "Day_100")
                    if phase_order.get(dep_phase, 2) > phase_order.get(item_phase, 2):
                        issues.append(f"{item['id']} ({item_phase}) depends on {dep_id} ({dep_phase}) - invalid sequence")

        return issues

    def validate_dd_completeness(self) -> Dict[str, Any]:
        """Validate that all four lenses produced output for each domain"""
        domains = ["infrastructure", "network", "cybersecurity"]
        missing_lenses = []
        missing_domains = []

        for domain in domains:
            domain_findings = self.get_by_domain(domain)

            # Check Lens 1: Current State
            if not domain_findings.get("current_state"):
                missing_lenses.append(f"{domain}: current_state")

            # Check Lens 2: Risks
            if not domain_findings.get("risks"):
                missing_lenses.append(f"{domain}: risks")

            # Check Lens 3: Strategic Considerations
            if not domain_findings.get("strategic_considerations"):
                missing_lenses.append(f"{domain}: strategic_considerations")

            # Check Lens 4: Work Items
            if not domain_findings.get("work_items"):
                missing_lenses.append(f"{domain}: work_items")

            # Check domain summary
            if domain not in self.domain_summaries:
                missing_domains.append(domain)

        # Check for non-integration risks
        standalone_risks = self.get_standalone_risks()
        non_integration_risks_evaluated = len(standalone_risks) > 0

        return {
            "dd_completeness_check": "pass" if not missing_lenses and not missing_domains else "fail",
            "missing_lenses": missing_lenses,
            "missing_domains": missing_domains,
            "non_integration_risks_evaluated": non_integration_risks_evaluated,
            "standalone_risk_count": len(standalone_risks)
        }

    def validate_outputs(self) -> Dict[str, Any]:
        """Validate analysis outputs for completeness and quality"""
        issues = []
        warnings = []

        # Check each domain has a summary
        for domain in ["infrastructure", "network", "cybersecurity"]:
            if domain not in self.domain_summaries:
                issues.append(f"Missing summary for {domain}")

        # Check critical risks have mitigations
        for risk in self.risks:
            if risk.get("severity") in ["critical", "high"]:
                mitigation = risk.get("mitigation", "")
                if not mitigation or len(mitigation) < 20:
                    warnings.append(f"Risk {risk['id']} lacks detailed mitigation")

        # Check work items have estimates
        for item in self.work_items:
            if not item.get("effort_estimate"):
                warnings.append(f"Work item {item['id']} missing effort estimate")
            if not item.get("phase"):
                warnings.append(f"Work item {item['id']} missing phase tag")

        # Check assumptions have validation plans
        for assumption in self.assumptions:
            if assumption.get("confidence") == "low":
                if not assumption.get("validation_needed"):
                    warnings.append(f"Low-confidence assumption {assumption['id']} needs validation plan")

        # Check work item dependencies
        dep_issues = self.validate_work_item_dependencies()
        warnings.extend(dep_issues)

        # DD completeness check
        dd_check = self.validate_dd_completeness()

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "quality_score": self._calculate_quality_score(),
            "dd_completeness": dd_check
        }

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0

        # Deduct for missing summaries
        expected_domains = 3
        score -= (expected_domains - len(self.domain_summaries)) * 10

        # Deduct for missing current state entries
        domains_with_current_state = len(set(c.get("domain") for c in self.current_state))
        score -= (expected_domains - domains_with_current_state) * 5

        # Deduct for incomplete findings
        incomplete_risks = sum(1 for r in self.risks
                              if r.get("severity") in ["critical", "high"]
                              and (not r.get("mitigation") or len(r.get("mitigation", "")) < 20))
        score -= incomplete_risks * 2

        incomplete_work_items = sum(1 for w in self.work_items
                                   if not w.get("effort_estimate") or not w.get("phase"))
        score -= incomplete_work_items * 1

        incomplete_assumptions = sum(1 for a in self.assumptions
                                    if a.get("confidence") == "low"
                                    and not a.get("validation_needed"))
        score -= incomplete_assumptions * 1

        # Bonus for non-integration risk coverage
        if self.get_standalone_risks():
            score += 5

        return max(0, min(100, score))

    def enrich_outputs(self):
        """Enrich outputs with additional context and calculations"""
        # Add risk scores
        for risk in self.risks:
            risk["risk_score"] = self._calculate_risk_score(risk)

        # Add priority rankings
        self._rank_findings()

    def _calculate_risk_score(self, risk: Dict) -> float:
        """Calculate numeric risk score"""
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        likelihood_map = {"high": 3, "medium": 2, "low": 1}

        severity = severity_map.get(risk.get("severity", "low"), 1)
        likelihood = likelihood_map.get(risk.get("likelihood", "low"), 1)

        return severity * likelihood

    def _rank_findings(self):
        """Add priority rankings to findings"""
        # Rank risks by score
        for risk in self.risks:
            risk["risk_score"] = self._calculate_risk_score(risk)

        risks_with_scores = [(r, r.get("risk_score", 0)) for r in self.risks]
        risks_with_scores.sort(key=lambda x: x[1], reverse=True)

        for rank, (risk, _) in enumerate(risks_with_scores, 1):
            risk["priority_rank"] = rank

        # Rank work items by priority
        for item in self.work_items:
            priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            item["priority_score"] = priority_map.get(item.get("priority", "low"), 1)

    # =========================================================================
    # DATABASE INTEGRATION (Points 47-52 of 115PP)
    # =========================================================================

    def set_database(self, db=None, repository=None):
        """
        Point 47: Accept database connection for persistence.

        Args:
            db: Database instance (optional if repository provided)
            repository: Repository instance (optional, will be created from db)
        """
        self._db = db
        self._repository = repository

    @property
    def has_database(self) -> bool:
        """Check if database is configured for persistence"""
        return self._repository is not None

    def ensure_database(self):
        """
        Ensure database is configured, auto-configuring if not.

        This is useful for CLI tools that need database access.
        """
        if self._repository is not None:
            return

        # Auto-configure with default database
        try:
            from storage import Database, Repository
            db = Database()
            db.initialize_schema()
            self._db = db
            self._repository = Repository(db)
            print("💾 Auto-configured database connection")
        except ImportError as e:
            raise ValueError(
                "Database repository not set and auto-configuration failed. "
                "Call set_database() first or ensure storage module is available."
            ) from e

    def _require_database(self, operation: str):
        """Helper to check database is available before operations"""
        if self._repository is None:
            raise ValueError(
                f"Database required for {operation}. "
                "Call set_database(db, repository) first, or use ensure_database() for auto-configuration."
            )

    def set_run_id(self, run_id: str):
        """
        Point 51: Set the analysis run ID for tracking which run produced findings.
        """
        self.run_id = run_id

    def add_document_id(self, document_id: str):
        """
        Point 52: Link a source document to this analysis.
        """
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)

    def save_to_database(self) -> Dict[str, int]:
        """
        Point 48: Save all findings to database.

        Returns:
            Dict with counts of saved items per type
        """
        self._require_database("save_to_database")

        if self.run_id is None:
            raise ValueError("Run ID not set. Call set_run_id() first.")

        return self._repository.import_from_analysis_store(self, self.run_id)

    def load_from_database(self, run_id: str) -> bool:
        """
        Point 49: Load findings from a previous run for resuming analysis.

        Args:
            run_id: The run ID to load findings from

        Returns:
            True if loaded successfully
        """
        self._require_database("load_from_database")

        self.run_id = run_id

        # Load all findings from the run
        findings = self._repository.get_all_findings_for_run(run_id)

        # Helper to safely convert list of model objects to dicts
        def convert_list(items: list) -> list:
            if not items:
                return []
            # Check first item to determine conversion method
            if hasattr(items[0], 'to_dict'):
                return [self._model_to_dict(item) for item in items]
            return items

        # Convert model objects back to dicts and populate lists
        self.current_state = convert_list(findings.get('inventory_items', []))
        self.risks = convert_list(findings.get('risks', []))
        self.gaps = convert_list(findings.get('gaps', []))
        self.assumptions = convert_list(findings.get('assumptions', []))
        self.work_items = convert_list(findings.get('work_items', []))
        self.recommendations = convert_list(findings.get('recommendations', []))
        self.strategic_considerations = convert_list(findings.get('strategic_considerations', []))

        # Update ID counters to continue from loaded data
        self._update_id_counters()

        return True

    def _model_to_dict(self, obj) -> Dict:
        """Convert a model object to dict with standardized 'id' field"""
        if hasattr(obj, 'to_dict'):
            d = obj.to_dict()
        elif hasattr(obj, '__dict__'):
            d = obj.__dict__.copy()
        else:
            return obj

        # Standardize ID field names to 'id' for AnalysisStore compatibility
        id_fields = ['risk_id', 'gap_id', 'assumption_id', 'item_id', 'work_item_id',
                     'recommendation_id', 'consideration_id', 'question_id']
        for id_field in id_fields:
            if id_field in d and 'id' not in d:
                d['id'] = d[id_field]
                break

        return d

    def _update_id_counters(self):
        """Update ID counters based on loaded findings to avoid ID collisions"""
        def extract_number(id_str: str) -> int:
            """Extract number from ID like 'R-005' -> 5"""
            if not id_str:
                return 0
            parts = id_str.split('-')
            if len(parts) >= 2:
                try:
                    return int(parts[-1])
                except ValueError:
                    return 0
            return 0

        def get_max_id(items: list, counter_key: str):
            """Safely get max ID from a list of items"""
            if not items:
                return
            max_val = max((extract_number(item.get('id', '')) for item in items), default=0)
            self._id_counters[counter_key] = max(self._id_counters[counter_key], max_val)

        # Update each counter based on max ID found
        get_max_id(self.current_state, 'current_state')
        get_max_id(self.risks, 'risk')
        get_max_id(self.gaps, 'gap')
        get_max_id(self.assumptions, 'assumption')
        get_max_id(self.work_items, 'work_item')
        get_max_id(self.recommendations, 'recommendation')
        get_max_id(self.strategic_considerations, 'strategic_consideration')

    @staticmethod
    def get_analysis_history(repository) -> List[Dict]:
        """
        Point 50: Get history of past analysis runs.

        Args:
            repository: Repository instance to query

        Returns:
            List of analysis run summaries
        """
        runs = repository.get_all_runs()
        history = []
        for run in runs:
            run_dict = run.to_dict() if hasattr(run, 'to_dict') else run
            # Add summary statistics
            try:
                summary = repository.get_run_summary(run_dict.get('run_id'))
                run_dict['statistics'] = summary.get('counts', {})
            except Exception:
                run_dict['statistics'] = {}
            history.append(run_dict)
        return history

    # =========================================================================
    # PHASE 4: ITERATIVE CAPABILITY (Points 70-74 of 115PP)
    # =========================================================================

    def load_previous_state(self, run_id: str = None) -> Dict[str, Any]:
        """
        Point 70: Load previous analysis state for iterative analysis.

        If run_id is None, loads the most recent completed run.

        Args:
            run_id: Specific run to load, or None for latest

        Returns:
            Dict with load status and statistics
        """
        self._require_database("load_previous_state")

        # Get the run to load
        if run_id is None:
            latest_run = self._repository.get_latest_run()
            if latest_run is None:
                return {"status": "no_previous_runs", "loaded": False}
            run_id = latest_run.run_id

        # Load the findings
        success = self.load_from_database(run_id)

        if success:
            return {
                "status": "loaded",
                "loaded": True,
                "run_id": run_id,
                "statistics": {
                    "current_state": len(self.current_state),
                    "risks": len(self.risks),
                    "gaps": len(self.gaps),
                    "assumptions": len(self.assumptions),
                    "work_items": len(self.work_items),
                    "recommendations": len(self.recommendations),
                    "strategic_considerations": len(self.strategic_considerations)
                }
            }
        return {"status": "load_failed", "loaded": False, "run_id": run_id}

    def identify_new_vs_existing(self, new_findings: List[Dict], finding_type: str,
                                   similarity_threshold: float = 0.85) -> Dict[str, List[Dict]]:
        """
        Point 71: Identify what's new vs. existing in a set of findings.

        Args:
            new_findings: List of new findings to compare
            finding_type: Type of finding ('risk', 'gap', 'assumption', 'current_state', etc.)
            similarity_threshold: Threshold for considering findings similar (0.0-1.0)

        Returns:
            Dict with 'new', 'existing', and 'updated' lists
        """
        # Map finding type to collection and key field
        type_map = {
            'risk': (self.risks, 'risk'),
            'gap': (self.gaps, 'gap'),
            'assumption': (self.assumptions, 'assumption'),
            'current_state': (self.current_state, 'summary'),
            'strategic_consideration': (self.strategic_considerations, 'theme'),
            'work_item': (self.work_items, 'title'),
            'recommendation': (self.recommendations, 'recommendation')
        }

        if finding_type not in type_map:
            raise ValueError(f"Unknown finding type: {finding_type}")

        existing_collection, key_field = type_map[finding_type]

        result = {
            'new': [],
            'existing': [],
            'updated': []  # Similar but with changes
        }

        for new_item in new_findings:
            new_text = new_item.get(key_field, '').lower().strip()
            new_domain = new_item.get('domain', '')

            best_match = None
            best_score = 0.0

            # Compare against existing items in same domain
            for existing_item in existing_collection:
                if existing_item.get('domain') != new_domain:
                    continue

                existing_text = existing_item.get(key_field, '').lower().strip()
                score = SequenceMatcher(None, new_text, existing_text).ratio()

                if score > best_score:
                    best_score = score
                    best_match = existing_item

            if best_score >= similarity_threshold:
                # Check if there are meaningful differences
                if self._has_meaningful_changes(new_item, best_match):
                    result['updated'].append({
                        'new': new_item,
                        'existing': best_match,
                        'similarity': best_score
                    })
                else:
                    result['existing'].append({
                        'finding': new_item,
                        'matched_to': best_match['id'],
                        'similarity': best_score
                    })
            else:
                result['new'].append(new_item)

        return result

    def _has_meaningful_changes(self, new_item: Dict, existing_item: Dict) -> bool:
        """Check if two similar findings have meaningful differences"""
        # Fields that indicate meaningful changes
        change_fields = ['severity', 'likelihood', 'priority', 'maturity',
                        'cost_estimate_range', 'effort_estimate', 'phase']

        for field in change_fields:
            if field in new_item and field in existing_item:
                if new_item[field] != existing_item[field]:
                    return True
        return False

    def merge_findings(self, new_findings: List[Dict], finding_type: str,
                       strategy: str = 'update') -> Dict[str, Any]:
        """
        Point 72: Merge new findings with existing ones.

        Args:
            new_findings: List of new findings to merge
            finding_type: Type of finding
            strategy: 'update' (replace existing), 'append' (keep both), 'newest' (keep newer)

        Returns:
            Dict with merge results and any conflicts
        """
        comparison = self.identify_new_vs_existing(new_findings, finding_type)

        merge_result = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'conflicts': []
        }

        # Map finding type to collection
        type_to_collection = {
            'risk': 'risks',
            'gap': 'gaps',
            'assumption': 'assumptions',
            'current_state': 'current_state',
            'strategic_consideration': 'strategic_considerations',
            'work_item': 'work_items',
            'recommendation': 'recommendations'
        }

        collection_name = type_to_collection.get(finding_type)
        if not collection_name:
            raise ValueError(f"Unknown finding type: {finding_type}")

        collection = getattr(self, collection_name)

        # Add genuinely new findings
        for new_item in comparison['new']:
            # Generate ID if needed
            if 'id' not in new_item:
                new_item['id'] = self._next_id(finding_type)
            new_item['_merged_at'] = datetime.now().isoformat()
            new_item['_merge_status'] = 'new'
            collection.append(new_item)
            merge_result['added'] += 1

        # Handle updates based on strategy
        for update_info in comparison['updated']:
            new_item = update_info['new']
            existing_item = update_info['existing']

            if strategy == 'update':
                # Update existing item with new data
                existing_idx = next(i for i, x in enumerate(collection) if x.get('id') == existing_item['id'])
                new_item['id'] = existing_item['id']  # Keep same ID
                new_item['_previous_version'] = existing_item.copy()
                new_item['_updated_at'] = datetime.now().isoformat()
                new_item['_merge_status'] = 'updated'
                collection[existing_idx] = new_item
                merge_result['updated'] += 1

            elif strategy == 'append':
                # Keep both versions
                if 'id' not in new_item:
                    new_item['id'] = self._next_id(finding_type)
                new_item['_related_to'] = existing_item['id']
                new_item['_merge_status'] = 'appended'
                collection.append(new_item)
                merge_result['added'] += 1

            elif strategy == 'newest':
                # Keep only if newer (based on timestamp or higher severity)
                if self._is_newer_or_more_severe(new_item, existing_item):
                    existing_idx = next(i for i, x in enumerate(collection) if x.get('id') == existing_item['id'])
                    new_item['id'] = existing_item['id']
                    new_item['_previous_version'] = existing_item.copy()
                    new_item['_merge_status'] = 'superseded'
                    collection[existing_idx] = new_item
                    merge_result['updated'] += 1
                else:
                    merge_result['skipped'] += 1

        # Skip exact duplicates
        merge_result['skipped'] += len(comparison['existing'])

        return merge_result

    def _is_newer_or_more_severe(self, new_item: Dict, existing_item: Dict) -> bool:
        """Determine if new item should supersede existing"""
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

        new_severity = severity_order.get(new_item.get('severity', 'low'), 1)
        existing_severity = severity_order.get(existing_item.get('severity', 'low'), 1)

        if new_severity > existing_severity:
            return True

        # Check timestamps if available
        new_time = new_item.get('timestamp', '')
        existing_time = existing_item.get('timestamp', '')
        if new_time and existing_time:
            return new_time > existing_time

        return False

    def flag_conflicts(self) -> List[Dict]:
        """
        Point 73: Flag conflicts/contradictions between findings.

        Detects:
        - Risks with conflicting severity assessments
        - Assumptions that contradict each other
        - Gaps that have been filled but not removed
        - Work items with conflicting phase assignments

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check for severity conflicts in similar risks
        for i, risk1 in enumerate(self.risks):
            for risk2 in self.risks[i+1:]:
                if risk1.get('domain') != risk2.get('domain'):
                    continue

                # Check if risks are about the same thing
                text1 = risk1.get('risk', '').lower()
                text2 = risk2.get('risk', '').lower()
                similarity = SequenceMatcher(None, text1, text2).ratio()

                if similarity > 0.7 and risk1.get('severity') != risk2.get('severity'):
                    conflicts.append({
                        'type': 'severity_conflict',
                        'finding_type': 'risk',
                        'items': [risk1['id'], risk2['id']],
                        'description': f"Similar risks with different severities: {risk1['id']} ({risk1.get('severity')}) vs {risk2['id']} ({risk2.get('severity')})",
                        'recommendation': 'Review and reconcile severity assessments'
                    })

        # Check for contradicting assumptions
        for i, a1 in enumerate(self.assumptions):
            for a2 in self.assumptions[i+1:]:
                if a1.get('domain') != a2.get('domain'):
                    continue

                # Look for opposing language
                text1 = a1.get('assumption', '').lower()
                text2 = a2.get('assumption', '').lower()

                # Simple contradiction detection
                opposing_pairs = [
                    ('will', 'will not'), ('can', 'cannot'), ('has', 'lacks'),
                    ('adequate', 'inadequate'), ('sufficient', 'insufficient')
                ]

                for pos, neg in opposing_pairs:
                    if (pos in text1 and neg in text2) or (neg in text1 and pos in text2):
                        similarity = SequenceMatcher(None, text1.replace(pos, '').replace(neg, ''),
                                                    text2.replace(pos, '').replace(neg, '')).ratio()
                        if similarity > 0.5:
                            conflicts.append({
                                'type': 'contradicting_assumptions',
                                'finding_type': 'assumption',
                                'items': [a1['id'], a2['id']],
                                'description': f"Potentially contradicting assumptions: {a1['id']} vs {a2['id']}",
                                'recommendation': 'Validate which assumption is correct'
                            })

        # Check for work items with conflicting dependencies
        work_item_phases = {w['id']: w.get('phase', 'Day_100') for w in self.work_items}
        phase_order = {'Day_1': 1, 'Day_100': 2, 'Post_100': 3, 'Optional': 4}

        for item in self.work_items:
            item_phase = item.get('phase', 'Day_100')
            for dep_id in item.get('depends_on', []):
                if dep_id in work_item_phases:
                    dep_phase = work_item_phases[dep_id]
                    if phase_order.get(dep_phase, 2) > phase_order.get(item_phase, 2):
                        conflicts.append({
                            'type': 'dependency_conflict',
                            'finding_type': 'work_item',
                            'items': [item['id'], dep_id],
                            'description': f"{item['id']} ({item_phase}) depends on {dep_id} ({dep_phase}) - invalid sequence",
                            'recommendation': f"Move {item['id']} to {dep_phase} or later, or move {dep_id} earlier"
                        })

        return conflicts

    def track_status_changes(self, previous_run_id: str = None) -> Dict[str, Any]:
        """
        Point 74: Track finding status changes over time.

        Compares current state against a previous run to identify:
        - New findings
        - Removed findings
        - Changed findings (severity, priority, etc.)
        - Resolved gaps

        Args:
            previous_run_id: Run to compare against (default: latest completed)

        Returns:
            Dict with change summary
        """
        self._require_database("track_status_changes")

        # Get previous run's findings
        if previous_run_id is None:
            latest_run = self._repository.get_latest_run()
            if latest_run is None:
                return {"status": "no_previous_runs", "changes": {}}
            previous_run_id = latest_run.run_id

        previous_findings = self._repository.get_all_findings_for_run(previous_run_id)

        changes = {
            'compared_to_run': previous_run_id,
            'risks': {'added': [], 'removed': [], 'severity_changed': []},
            'gaps': {'added': [], 'removed': [], 'resolved': []},
            'assumptions': {'added': [], 'removed': [], 'validated': [], 'invalidated': []},
            'work_items': {'added': [], 'removed': [], 'phase_changed': []},
            'summary': {}
        }

        # Helper to compare lists
        def compare_findings(current: List, previous: List, key_field: str, finding_type: str):
            current_ids = {f.get('id') for f in current}
            previous_ids = {self._get_id(f) for f in previous}

            added = [f for f in current if f.get('id') not in previous_ids]
            removed_ids = previous_ids - current_ids

            return added, list(removed_ids)

        # Compare each finding type
        for ftype, (current_list, prev_key, key_field) in {
            'risks': (self.risks, 'risks', 'risk'),
            'gaps': (self.gaps, 'gaps', 'gap'),
            'assumptions': (self.assumptions, 'assumptions', 'assumption'),
            'work_items': (self.work_items, 'work_items', 'title')
        }.items():
            prev_list = previous_findings.get(prev_key, [])
            added, removed = compare_findings(current_list, prev_list, key_field, ftype)
            changes[ftype]['added'] = [f.get('id') for f in added]
            changes[ftype]['removed'] = removed

        # Track specific changes for risks (severity)
        prev_risks = {self._get_id(r): r for r in previous_findings.get('risks', [])}
        for risk in self.risks:
            rid = risk.get('id')
            if rid in prev_risks:
                prev_severity = self._get_field(prev_risks[rid], 'severity')
                if risk.get('severity') != prev_severity:
                    changes['risks']['severity_changed'].append({
                        'id': rid,
                        'from': prev_severity,
                        'to': risk.get('severity')
                    })

        # Track resolved gaps (gaps that were removed or answered)
        prev_gaps = {self._get_id(g): g for g in previous_findings.get('gaps', [])}
        current_gap_ids = {g.get('id') for g in self.gaps}
        for gap_id in prev_gaps:
            if gap_id not in current_gap_ids:
                changes['gaps']['resolved'].append(gap_id)

        # Summary
        changes['summary'] = {
            'total_risks_added': len(changes['risks']['added']),
            'total_risks_removed': len(changes['risks']['removed']),
            'total_gaps_added': len(changes['gaps']['added']),
            'total_gaps_resolved': len(changes['gaps']['resolved']),
            'severity_escalations': sum(1 for c in changes['risks']['severity_changed']
                                       if self._severity_increased(c['from'], c['to']))
        }

        return changes

    def _get_id(self, finding) -> str:
        """Get ID from finding (handles both dict and model objects)"""
        if hasattr(finding, 'risk_id'):
            return finding.risk_id
        if hasattr(finding, 'gap_id'):
            return finding.gap_id
        if hasattr(finding, 'assumption_id'):
            return finding.assumption_id
        if hasattr(finding, 'work_item_id'):
            return finding.work_item_id
        if hasattr(finding, 'item_id'):
            return finding.item_id
        if isinstance(finding, dict):
            return finding.get('id', '')
        return ''

    def _get_field(self, finding, field: str):
        """Get field from finding (handles both dict and model objects)"""
        if hasattr(finding, field):
            return getattr(finding, field)
        if isinstance(finding, dict):
            return finding.get(field)
        return None

    def _severity_increased(self, old: str, new: str) -> bool:
        """Check if severity increased"""
        order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return order.get(new, 0) > order.get(old, 0)

    def merge_from(self, other: 'AnalysisStore') -> Dict[str, int]:
        """
        Merge findings from another AnalysisStore into this one.
        Used for parallel agent execution - each agent has its own store,
        then results are merged into a master store.

        Args:
            other: Another AnalysisStore instance to merge from

        Returns:
            Dict with counts of merged items per category
        """
        import logging
        logger = logging.getLogger(__name__)

        counts = {
            'current_state': 0,
            'risks': 0,
            'gaps': 0,
            'questions': 0,
            'assumptions': 0,
            'work_items': 0,
            'recommendations': 0,
            'strategic_considerations': 0,
            'domain_summaries': 0,
            'reasoning_chains': 0,
            'skipped_invalid': 0
        }

        def validate_and_append(source_list, target_list, list_name):
            """Helper to validate items before appending"""
            valid_count = 0
            for item in source_list:
                if isinstance(item, dict):
                    target_list.append(item)
                    valid_count += 1
                else:
                    logger.warning(f"Skipping invalid {list_name} item (type={type(item).__name__}): {str(item)[:100]}")
                    counts['skipped_invalid'] += 1
            return valid_count

        # Merge current state entries
        counts['current_state'] = validate_and_append(other.current_state, self.current_state, 'current_state')

        # Merge risks
        counts['risks'] = validate_and_append(other.risks, self.risks, 'risk')

        # Merge gaps
        counts['gaps'] = validate_and_append(other.gaps, self.gaps, 'gap')

        # Merge questions
        counts['questions'] = validate_and_append(other.questions, self.questions, 'question')

        # Merge assumptions
        counts['assumptions'] = validate_and_append(other.assumptions, self.assumptions, 'assumption')

        # Merge work items
        counts['work_items'] = validate_and_append(other.work_items, self.work_items, 'work_item')

        # Merge recommendations
        counts['recommendations'] = validate_and_append(other.recommendations, self.recommendations, 'recommendation')

        # Merge strategic considerations
        counts['strategic_considerations'] = validate_and_append(other.strategic_considerations, self.strategic_considerations, 'strategic_consideration')

        # Merge domain summaries
        for domain, summary in other.domain_summaries.items():
            self.domain_summaries[domain] = summary
            counts['domain_summaries'] += 1

        # Merge reasoning chains
        for domain, entries in other.reasoning_chains.items():
            if domain not in self.reasoning_chains:
                self.reasoning_chains[domain] = []
            self.reasoning_chains[domain].extend(entries)
            counts['reasoning_chains'] += len(entries)

        return counts

    def get_all(self) -> Dict:
        """Get all findings with validation"""
        # Enrich before returning
        self.enrich_outputs()

        # Validate
        validation = self.validate_outputs()

        # Group risks by type
        risks_by_type = self.get_risks_by_type()
        standalone_risks = self.get_standalone_risks()

        # Group work items by phase
        work_items_by_phase = self.get_work_items_by_phase()

        return {
            # Lens 1
            "current_state": self.current_state,
            # Lens 2
            "risks": self.risks,
            "risks_by_type": risks_by_type,
            "standalone_risks": standalone_risks,
            # Lens 3
            "strategic_considerations": self.strategic_considerations,
            # Lens 4
            "work_items": self.work_items,
            "work_items_by_phase": work_items_by_phase,
            "recommendations": self.recommendations,
            # Supporting
            "assumptions": self.assumptions,
            "gaps": self.gaps,
            "questions": self.questions,
            "domain_summaries": self.domain_summaries,
            "executive_summary": self.executive_summary,
            # Meta
            "statistics": {
                "total_current_state": len(self.current_state),
                "total_assumptions": len(self.assumptions),
                "total_gaps": len(self.gaps),
                "total_questions": len(self.questions),
                "total_risks": len(self.risks),
                "standalone_risks": len(standalone_risks),
                "integration_risks": len(self.risks) - len(standalone_risks),
                "total_strategic_considerations": len(self.strategic_considerations),
                "total_work_items": len(self.work_items),
                "total_recommendations": len(self.recommendations),
                "domains_analyzed": list(self.domain_summaries.keys())
            },
            "validation": validation
        }

    def save(self, output_dir: str):
        """Save all findings to JSON files with validation report"""
        from pathlib import Path
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Validate before saving
        validation = self.validate_outputs()

        # Individual files (organized by lens)
        files = {
            # Lens 1
            "current_state.json": self.current_state,
            # Lens 2
            "risks.json": self.risks,
            # Lens 3
            "strategic_considerations.json": self.strategic_considerations,
            # Lens 4
            "work_items.json": self.work_items,
            "recommendations.json": self.recommendations,
            # Supporting
            "assumptions.json": self.assumptions,
            "gaps.json": self.gaps,
            "questions.json": self.questions,
            "domain_summaries.json": self.domain_summaries,
            "validation_report.json": validation
        }

        for filename, data in files.items():
            with open(output_dir / filename, 'w') as f:
                json.dump(data, f, indent=2)

        # Save executive summary if present
        if self.executive_summary:
            with open(output_dir / "executive_summary.json", 'w') as f:
                json.dump(self.executive_summary, f, indent=2)
            self._save_executive_summary_markdown(output_dir)

        # Save reasoning chains
        if self.reasoning_chains:
            with open(output_dir / "reasoning_chains.json", 'w') as f:
                json.dump(self.reasoning_chains, f, indent=2)
            self._save_reasoning_narrative(output_dir)

        # Combined output
        with open(output_dir / "analysis_output.json", 'w') as f:
            json.dump(self.get_all(), f, indent=2)

        # Count totals
        total_reasoning = sum(len(entries) for entries in self.reasoning_chains.values())
        standalone_count = len(self.get_standalone_risks())

        print(f"\n✓ Analysis saved to {output_dir}/")
        print(f"  - {len(self.current_state)} current state entries")
        print(f"  - {len(self.assumptions)} assumptions")
        print(f"  - {len(self.gaps)} gaps")
        print(f"  - {len(self.risks)} risks ({standalone_count} standalone)")
        print(f"  - {len(self.strategic_considerations)} strategic considerations")
        print(f"  - {len(self.work_items)} work items")
        print(f"  - {len(self.recommendations)} recommendations")
        print(f"  - {total_reasoning} reasoning chain entries")
        print(f"  - Quality Score: {validation['quality_score']:.1f}/100")
        if validation['issues']:
            print(f"  - ⚠️  {len(validation['issues'])} validation issues")
        if validation['warnings']:
            print(f"  - ⚠️  {len(validation['warnings'])} warnings")

    def _save_executive_summary_markdown(self, output_dir):
        """Save IC-ready executive summary as markdown"""
        from pathlib import Path
        output_dir = Path(output_dir)

        if not self.executive_summary:
            return

        es = self.executive_summary
        lines = []
        lines.append("# Executive Summary")
        lines.append("")
        lines.append("*Investment Committee Ready*")
        lines.append("")

        # Overall assessment
        complexity = es.get("overall_complexity", "unknown")
        cost = es.get("total_estimated_cost_range", "TBD")
        timeline = es.get("estimated_timeline", "TBD")
        recommendation = es.get("deal_recommendation", "TBD")

        lines.append(f"**Overall Complexity:** {complexity.upper()}")
        lines.append(f"**Estimated Investment:** {cost}")
        lines.append(f"**Timeline:** {timeline}")
        lines.append(f"**Recommendation:** {recommendation.replace('_', ' ').title()}")
        lines.append("")

        # Key findings
        if es.get("key_findings"):
            lines.append("## Key Findings")
            for finding in es["key_findings"]:
                lines.append(f"- {finding}")
            lines.append("")

        # Critical risks
        if es.get("critical_risks"):
            lines.append("## Critical Risks")
            for risk in es["critical_risks"]:
                lines.append(f"- {risk}")
            lines.append("")

        # Immediate actions
        if es.get("immediate_actions"):
            lines.append("## Immediate Actions (Pre-Close)")
            for action in es["immediate_actions"]:
                lines.append(f"- {action}")
            lines.append("")

        # Day 1 requirements
        if es.get("day_1_requirements"):
            lines.append("## Day 1 Requirements")
            for req in es["day_1_requirements"]:
                lines.append(f"- {req}")
            lines.append("")

        # Key unknowns
        if es.get("key_unknowns"):
            lines.append("## Key Unknowns")
            for unknown in es["key_unknowns"]:
                lines.append(f"- {unknown}")
            lines.append("")

        with open(output_dir / "EXECUTIVE_SUMMARY.md", 'w') as f:
            f.write("\n".join(lines))

    def _save_reasoning_narrative(self, output_dir):
        """Save a human-readable narrative of the reasoning chains"""
        from pathlib import Path
        output_dir = Path(output_dir)

        lines = []
        lines.append("# Analysis Reasoning Chain")
        lines.append("")
        lines.append("This document shows the logic flow from document observations to findings.")
        lines.append("Each entry shows: what Claude observed → what it concluded → the finding created.")
        lines.append("")

        for domain in ["infrastructure", "network", "cybersecurity"]:
            entries = self.reasoning_chains.get(domain, [])
            if not entries:
                continue

            lines.append(f"## {domain.title()} Domain")
            lines.append("")

            for entry in entries:
                finding_id = entry.get("finding_id", "Unknown")
                finding_type = entry.get("finding_type", "unknown")
                finding_summary = entry.get("finding_summary", "")
                reasoning = entry.get("reasoning_text", "")
                evidence = entry.get("evidence_from_finding", "")
                iteration = entry.get("iteration", 0)

                lines.append(f"### {finding_id} ({finding_type})")
                lines.append("")
                lines.append(f"**Finding:** {finding_summary}")
                lines.append("")
                lines.append(f"**Reasoning (Iteration {iteration}):**")
                lines.append("```")
                lines.append(reasoning[:2000] + "..." if len(reasoning) > 2000 else reasoning)
                lines.append("```")
                lines.append("")
                if evidence:
                    lines.append(f"**Evidence/Basis:** {evidence}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        with open(output_dir / "REASONING_NARRATIVE.md", 'w') as f:
            f.write("\n".join(lines))


# =============================================================================
# COORDINATOR TOOLS (additional tools for roll-up agent)
# =============================================================================

COORDINATOR_TOOLS = ANALYSIS_TOOLS + [
    {
        "name": "create_executive_summary",
        "description": """Create the final executive summary that synthesizes all domain findings.
        This is the primary output for deal team leadership and Investment Committee.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "overall_complexity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "very_high"],
                    "description": "Overall integration complexity"
                },
                "total_estimated_cost_range": {
                    "type": "string",
                    "description": "Total one-time cost estimate (e.g., '$2M-$4M')"
                },
                "estimated_timeline": {
                    "type": "string",
                    "description": "Overall timeline estimate (e.g., '18-24 months')"
                },
                "deal_recommendation": {
                    "type": "string",
                    "enum": ["proceed", "proceed_with_caution", "significant_concerns", "reconsider"],
                    "description": "Overall deal recommendation from IT perspective"
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 5-7 key findings for leadership (no jargon)"
                },
                "critical_risks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risks that could materially impact the deal"
                },
                "immediate_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Actions to take before close"
                },
                "day_1_requirements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What must be ready for Day 1"
                },
                "synergy_opportunities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Cost savings or value creation opportunities"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence in estimates given available information"
                },
                "key_unknowns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Critical unknowns that could change the assessment"
                }
            },
            "required": ["overall_complexity", "total_estimated_cost_range", "deal_recommendation",
                        "key_findings", "critical_risks", "confidence_level"]
        }
    },
    {
        "name": "identify_cross_domain_dependency",
        "description": """Identify a dependency or interaction between domains that affects sequencing or risk.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "dependency": {
                    "type": "string",
                    "description": "Description of the cross-domain dependency"
                },
                "source_domain": {
                    "type": "string",
                    "description": "Domain that must happen first or provides input"
                },
                "target_domain": {
                    "type": "string",
                    "description": "Domain that depends on the source"
                },
                "impact": {
                    "type": "string",
                    "description": "What happens if this dependency isn't managed"
                },
                "sequencing_requirement": {
                    "type": "string",
                    "description": "How this affects project sequencing"
                }
            },
            "required": ["dependency", "source_domain", "target_domain", "impact"]
        }
    }
]
