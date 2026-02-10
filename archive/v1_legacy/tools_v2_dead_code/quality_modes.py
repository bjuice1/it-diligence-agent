"""
Quality Modes for Reasoning Analysis

Supports different quality/cost trade-offs:

1. FAST MODE (default for refinements)
   - Pure rule-based reasoning
   - No LLM calls
   - Instant results
   - Use for: Quick iterations, exploring scenarios

2. VALIDATED MODE (for important decisions)
   - Rule-based + LLM validation
   - LLM checks if reasoning makes sense
   - Flags potential issues
   - Use for: Before presenting to client

3. ENHANCED MODE (for final output)
   - Rule-based + LLM enhancement
   - LLM improves narratives, adds context
   - Highest quality prose
   - Use for: Final deliverable

Cost comparison (per analysis):
- FAST: $0.00
- VALIDATED: ~$0.10-0.20
- ENHANCED: ~$0.30-0.50
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class QualityMode(Enum):
    """Analysis quality modes."""
    FAST = "fast"              # Rule-based only, instant
    VALIDATED = "validated"    # Rule-based + LLM validation
    ENHANCED = "enhanced"      # Rule-based + LLM enhancement


@dataclass
class ValidationIssue:
    """An issue flagged during LLM validation."""
    severity: str  # "warning", "error", "suggestion"
    category: str  # "cost", "timeline", "tsa", "activity", "consideration"
    message: str
    affected_item: Optional[str] = None  # activity_id, workstream, etc.
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """Report from quality validation/enhancement."""
    mode: str
    issues_found: List[ValidationIssue]
    enhancements_made: List[Dict]
    confidence_score: float  # 0-1, how confident we are in the analysis
    llm_cost: float  # Actual $ spent
    recommendations: List[str]


# =============================================================================
# VALIDATION PROMPTS
# =============================================================================

VALIDATION_PROMPT = """You are an expert IT M&A advisor reviewing an automated due diligence analysis.

The analysis was generated using rule-based reasoning from extracted facts.

## Your Task
Review the analysis for:
1. **Reasonableness** - Do the costs and timelines make sense?
2. **Completeness** - Are there obvious gaps or missing considerations?
3. **Consistency** - Do the workstream assessments align with each other?
4. **Red Flags** - Anything that would concern a client?

## Analysis Summary
Deal Type: {deal_type}
User Count: {user_count:,}
Total Cost Range: ${total_low:,.0f} - ${total_high:,.0f}
TSA Services: {tsa_count}
Activities: {activity_count}

## Workstream Costs
{workstream_summary}

## Key Considerations
{considerations_summary}

## Activities (sample)
{activities_sample}

---

Respond with a JSON object:
{{
    "confidence_score": 0.0-1.0,
    "issues": [
        {{
            "severity": "warning|error|suggestion",
            "category": "cost|timeline|tsa|activity|consideration",
            "message": "description of issue",
            "affected_item": "optional - which item",
            "suggestion": "optional - how to fix"
        }}
    ],
    "recommendations": ["list of recommendations for the team"]
}}

Be concise. Only flag genuine issues, not minor quibbles.
"""


ENHANCEMENT_PROMPT = """You are an expert IT M&A advisor enhancing a due diligence analysis for client presentation.

The analysis was generated using rule-based reasoning. Your job is to:
1. Improve the executive summary prose
2. Add strategic context to key findings
3. Ensure the narrative flows professionally

## Current Executive Summary
{executive_summary}

## Deal Context
{deal_context}

## Key Numbers
- Total Cost: ${total_low:,.0f} - ${total_high:,.0f}
- TSA Services: {tsa_count}
- Critical Path: {critical_path}

## Top Workstreams by Cost
{top_workstreams}

---

Provide an enhanced executive summary (3-4 paragraphs) that:
- Leads with the key message
- Provides context for the numbers
- Highlights critical risks/considerations
- Is suitable for a PE partner audience

Write in professional consulting prose. Be direct, not flowery.
"""


# =============================================================================
# QUALITY FUNCTIONS
# =============================================================================

def validate_analysis(
    result: Dict[str, Any],
    deal_context: Optional[Dict] = None,
) -> QualityReport:
    """
    Validate analysis using LLM.

    Checks for reasonableness, completeness, and red flags.

    Args:
        result: Output from run_reasoning_analysis()
        deal_context: Optional additional context

    Returns:
        QualityReport with issues and recommendations
    """
    output = result["raw_output"]

    # Build prompt context
    workstream_summary = "\n".join([
        f"- {ws}: ${cost[0]:,.0f} - ${cost[1]:,.0f}"
        for ws, cost in sorted(output.workstream_costs.items(), key=lambda x: -x[1][1])
    ])

    considerations_summary = "\n".join([
        f"- [{c.workstream}] {c.finding}: {c.implication}"
        for c in output.considerations[:10]
    ])

    activities_sample = "\n".join([
        f"- {a.name}: ${a.cost_range[0]:,.0f}-${a.cost_range[1]:,.0f} ({a.timeline_months[0]}-{a.timeline_months[1]} mo)"
        for a in output.derived_activities[:10]
    ])

    prompt = VALIDATION_PROMPT.format(
        deal_type=output.deal_type,
        user_count=output.user_count,
        total_low=output.grand_total[0],
        total_high=output.grand_total[1],
        tsa_count=len(output.tsa_requirements),
        activity_count=len(output.derived_activities),
        workstream_summary=workstream_summary,
        considerations_summary=considerations_summary,
        activities_sample=activities_sample,
    )

    # Call LLM
    try:
        import anthropic
        import json
        import os

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast, cheap model for validation
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            validation_result = json.loads(json_match.group())
        else:
            validation_result = {"confidence_score": 0.7, "issues": [], "recommendations": []}

        # Calculate cost (approximate)
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        llm_cost = (input_tokens * 0.001 + output_tokens * 0.005) / 1000  # Haiku pricing

        issues = [
            ValidationIssue(
                severity=i.get("severity", "warning"),
                category=i.get("category", "general"),
                message=i.get("message", ""),
                affected_item=i.get("affected_item"),
                suggestion=i.get("suggestion"),
            )
            for i in validation_result.get("issues", [])
        ]

        return QualityReport(
            mode="validated",
            issues_found=issues,
            enhancements_made=[],
            confidence_score=validation_result.get("confidence_score", 0.7),
            llm_cost=llm_cost,
            recommendations=validation_result.get("recommendations", []),
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return QualityReport(
            mode="validated",
            issues_found=[ValidationIssue(
                severity="error",
                category="system",
                message=f"Validation failed: {str(e)}",
            )],
            enhancements_made=[],
            confidence_score=0.5,
            llm_cost=0.0,
            recommendations=["Manual review recommended due to validation failure"],
        )


def enhance_analysis(
    result: Dict[str, Any],
    deal_context: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Enhance analysis with LLM-improved narratives.

    Args:
        result: Output from run_reasoning_analysis()
        deal_context: Optional additional context

    Returns:
        Enhanced result with improved narratives
    """
    output = result["raw_output"]

    # Build prompt
    top_workstreams = "\n".join([
        f"- {ws}: ${cost[0]:,.0f} - ${cost[1]:,.0f}"
        for ws, cost in sorted(output.workstream_costs.items(), key=lambda x: -x[1][1])[:5]
    ])

    deal_context_str = ""
    if deal_context:
        deal_context_str = f"""
Target: {deal_context.get('target_name', 'N/A')}
Buyer: {deal_context.get('buyer_name', 'N/A')}
Industry: {deal_context.get('industry', 'N/A')}
"""

    prompt = ENHANCEMENT_PROMPT.format(
        executive_summary=output.executive_summary,
        deal_context=deal_context_str or "Not provided",
        total_low=output.grand_total[0],
        total_high=output.grand_total[1],
        tsa_count=len(output.tsa_requirements),
        critical_path=f"{output.critical_path_months[0]}-{output.critical_path_months[1]} months",
        top_workstreams=top_workstreams,
    )

    try:
        import anthropic
        import os

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Better model for prose
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        enhanced_summary = response.content[0].text

        # Create enhanced result
        enhanced_result = dict(result)
        enhanced_result["enhanced_executive_summary"] = enhanced_summary
        enhanced_result["enhancement_applied"] = True

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        enhanced_result["enhancement_cost"] = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

        return enhanced_result

    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        result["enhancement_error"] = str(e)
        return result


def run_with_quality_mode(
    fact_store: Any,
    deal_type: str,
    mode: QualityMode = QualityMode.FAST,
    meeting_notes: Optional[str] = None,
    deal_context: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run analysis with specified quality mode.

    Args:
        fact_store: FactStore with facts
        deal_type: Deal type
        mode: Quality mode (FAST, VALIDATED, ENHANCED)
        meeting_notes: Optional notes
        deal_context: Optional context

    Returns:
        Analysis result (with validation/enhancement if requested)
    """
    from tools_v2.reasoning_integration import run_reasoning_analysis

    # Always run base analysis (free)
    result = run_reasoning_analysis(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
    )

    result["quality_mode"] = mode.value
    result["total_llm_cost"] = 0.0

    if mode == QualityMode.FAST:
        # Just return rule-based result
        return result

    elif mode == QualityMode.VALIDATED:
        # Add validation
        validation = validate_analysis(result, deal_context)
        result["validation"] = {
            "confidence_score": validation.confidence_score,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in validation.issues_found
            ],
            "recommendations": validation.recommendations,
        }
        result["total_llm_cost"] = validation.llm_cost
        return result

    elif mode == QualityMode.ENHANCED:
        # Validate first
        validation = validate_analysis(result, deal_context)
        result["validation"] = {
            "confidence_score": validation.confidence_score,
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in validation.issues_found
            ],
            "recommendations": validation.recommendations,
        }

        # Then enhance
        result = enhance_analysis(result, deal_context)
        result["total_llm_cost"] = validation.llm_cost + result.get("enhancement_cost", 0)

        return result


# =============================================================================
# QUICK QUALITY CHECK (rule-based, no LLM)
# =============================================================================

def quick_quality_check(result: Dict[str, Any]) -> List[Dict]:
    """
    Quick rule-based quality check (no LLM cost).

    Checks for obvious issues without calling an LLM.
    """
    issues = []
    output = result["raw_output"]

    # Check: Cost seems too low for user count
    cost_per_user_low = output.grand_total[0] / max(output.user_count, 1)
    if cost_per_user_low < 50:  # Less than $50/user is suspiciously low
        issues.append({
            "severity": "warning",
            "category": "cost",
            "message": f"Cost per user (${cost_per_user_low:.0f}) seems low. Verify all activities captured.",
        })

    # Check: Carveout with no TSA
    if output.deal_type == "carveout" and len(output.tsa_requirements) == 0:
        issues.append({
            "severity": "warning",
            "category": "tsa",
            "message": "Carveout with no TSA services - verify parent dependencies.",
        })

    # Check: Very short timeline
    if output.critical_path_months[0] < 3:
        issues.append({
            "severity": "warning",
            "category": "timeline",
            "message": f"Timeline of {output.critical_path_months[0]} months is aggressive. Verify feasibility.",
        })

    # Check: No identity activities
    identity_activities = [a for a in output.derived_activities if a.workstream == "identity"]
    if not identity_activities and output.user_count > 100:
        issues.append({
            "severity": "warning",
            "category": "completeness",
            "message": "No identity activities derived. Check if identity facts were captured.",
        })

    # Check: Wide cost range (high > 3x low)
    if output.grand_total[1] > output.grand_total[0] * 3:
        issues.append({
            "severity": "suggestion",
            "category": "cost",
            "message": "Wide cost range suggests high uncertainty. Consider refining inputs.",
        })

    return issues


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'QualityMode',
    'ValidationIssue',
    'QualityReport',
    'validate_analysis',
    'enhance_analysis',
    'run_with_quality_mode',
    'quick_quality_check',
]
