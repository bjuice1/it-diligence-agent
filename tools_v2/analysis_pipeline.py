"""
Analysis Pipeline - Unified Entry Point

This is the main entry point for running IT Due Diligence analysis.

It provides:
1. Simple interface for running analysis
2. Support for different modes (fast, validated, enhanced)
3. Integration with refinement sessions
4. Full traceability from facts to costs

Usage:
    from tools_v2.analysis_pipeline import analyze_deal, AnalysisMode

    # Quick analysis
    result = analyze_deal(fact_store, "carveout")

    # With refinement session
    session = create_analysis_session(fact_store, "carveout")
    result = session.run_initial_analysis()
    session.add_tsa_requirement(...)
    result = session.apply_refinements_fast()
    final = session.run_full_validation()
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class AnalysisMode(Enum):
    """Analysis quality/cost modes."""

    FAST = "fast"
    """Stage 1 + 2 only (~$0.15-0.20). Use for quick iterations."""

    VALIDATED = "validated"
    """Full three-stage (~$0.30-0.50). Use for important analysis."""

    ENHANCED = "enhanced"
    """Three-stage + enhanced narratives (~$0.50-0.70). Use for client delivery."""


@dataclass
class AnalysisResult:
    """Result from the analysis pipeline."""

    # Metadata
    mode: str
    deal_type: str
    timestamp: str
    session_id: Optional[str]

    # Core results
    considerations: List[Dict]
    activities: List[Dict]
    tsa_services: List[Dict]

    # Totals
    total_cost_range: tuple
    total_timeline_months: tuple

    # Validation (if validated mode)
    validation: Optional[Dict]
    confidence_score: float

    # Cost tracking
    llm_cost: float

    # Formatted output
    formatted_text: str

    # Summary for quick viewing
    summary: Dict


# =============================================================================
# MAIN ENTRY POINTS
# =============================================================================

def analyze_deal(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
    mode: AnalysisMode = AnalysisMode.VALIDATED,
    model: str = "claude-sonnet-4-20250514",
) -> AnalysisResult:
    """
    Run IT due diligence analysis on a deal.

    This is the main entry point for analysis.

    Args:
        fact_store: FactStore with extracted facts
        deal_type: "carveout", "acquisition", "standalone"
        meeting_notes: Additional context from discussions
        mode: Analysis mode (FAST, VALIDATED, ENHANCED)
        model: Which Claude model to use

    Returns:
        AnalysisResult with complete analysis

    Examples:
        # Quick analysis during exploration
        result = analyze_deal(facts, "carveout", mode=AnalysisMode.FAST)

        # Full validated analysis
        result = analyze_deal(facts, "acquisition", mode=AnalysisMode.VALIDATED)
    """
    logger.info(f"Starting {mode.value} analysis for {deal_type}")

    if mode == AnalysisMode.FAST:
        return _run_fast_analysis(fact_store, deal_type, meeting_notes, model)
    elif mode == AnalysisMode.VALIDATED:
        return _run_validated_analysis(fact_store, deal_type, meeting_notes, model)
    else:  # ENHANCED
        return _run_enhanced_analysis(fact_store, deal_type, meeting_notes, model)


def create_analysis_session(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
    model: str = "claude-sonnet-4-20250514",
):
    """
    Create a refinement session for iterative analysis.

    Use this when you need to:
    - Add refinements based on team input
    - Run multiple iterations
    - Track changes over time

    Returns:
        ThreeStageRefinementSession for iterative refinement
    """
    from tools_v2.three_stage_refinement import ThreeStageRefinementSession

    return ThreeStageRefinementSession.create(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
        model=model,
    )


# =============================================================================
# INTERNAL IMPLEMENTATION
# =============================================================================

def _run_fast_analysis(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str,
    model: str,
) -> AnalysisResult:
    """Fast analysis - Stage 1 + 2 only."""

    from tools_v2.three_stage_reasoning import (
        stage1_identify_considerations,
        stage2_match_activities,
    )
    from tools_v2.reasoning_integration import factstore_to_reasoning_format

    facts = factstore_to_reasoning_format(fact_store)

    # Stage 1: LLM identifies considerations
    considerations, quant_context, cost = stage1_identify_considerations(
        facts=facts,
        deal_type=deal_type,
        additional_context=meeting_notes,
        model=model,
    )

    # Stage 2: Rules match activities
    activities, tsa_services = stage2_match_activities(
        considerations=considerations,
        quant_context=quant_context,
        deal_type=deal_type,
    )

    # Calculate totals
    total_low = sum(a.cost_range[0] for a in activities)
    total_high = sum(a.cost_range[1] for a in activities)

    timeline_low = min((a.timeline_months[0] for a in activities), default=0)
    timeline_high = max((a.timeline_months[1] for a in activities), default=0)

    # Format output
    formatted = _format_fast_output(deal_type, considerations, activities, tsa_services)

    from dataclasses import asdict
    return AnalysisResult(
        mode="fast",
        deal_type=deal_type,
        timestamp=datetime.now().isoformat(),
        session_id=None,
        considerations=[asdict(c) for c in considerations],
        activities=[asdict(a) for a in activities],
        tsa_services=tsa_services,
        total_cost_range=(total_low, total_high),
        total_timeline_months=(timeline_low, timeline_high),
        validation=None,
        confidence_score=0.0,  # No validation in fast mode
        llm_cost=cost,
        formatted_text=formatted,
        summary={
            "total_cost": f"${total_low:,.0f} - ${total_high:,.0f}",
            "considerations": len(considerations),
            "activities": len(activities),
            "tsa_services": len(tsa_services),
            "timeline": f"{timeline_low}-{timeline_high} months",
        },
    )


def _run_validated_analysis(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str,
    model: str,
) -> AnalysisResult:
    """Full three-stage validated analysis."""

    from tools_v2.three_stage_reasoning import (
        run_three_stage_analysis,
        format_three_stage_output,
    )

    output = run_three_stage_analysis(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
        model=model,
    )

    formatted = format_three_stage_output(output)

    from dataclasses import asdict
    return AnalysisResult(
        mode="validated",
        deal_type=deal_type,
        timestamp=output.timestamp,
        session_id=None,
        considerations=[asdict(c) for c in output.considerations],
        activities=[asdict(a) for a in output.activities],
        tsa_services=output.tsa_services,
        total_cost_range=output.total_cost_range,
        total_timeline_months=output.total_timeline_months,
        validation={
            "is_valid": output.validation.is_valid,
            "confidence_score": output.validation.confidence_score,
            "missing_considerations": output.validation.missing_considerations,
            "suggested_additions": output.validation.suggested_additions,
            "recommendations": output.validation.recommendations,
            "assessment": output.validation.assessment,
        },
        confidence_score=output.validation.confidence_score,
        llm_cost=output.total_llm_cost,
        formatted_text=formatted,
        summary={
            "total_cost": f"${output.total_cost_range[0]:,.0f} - ${output.total_cost_range[1]:,.0f}",
            "considerations": len(output.considerations),
            "activities": len(output.activities),
            "tsa_services": len(output.tsa_services),
            "timeline": f"{output.total_timeline_months[0]}-{output.total_timeline_months[1]} months",
            "confidence": f"{output.validation.confidence_score:.0%}",
        },
    )


def _run_enhanced_analysis(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str,
    model: str,
) -> AnalysisResult:
    """Enhanced analysis with improved narratives."""

    from tools_v2.three_stage_reasoning import run_three_stage_analysis

    # First run validated analysis
    output = run_three_stage_analysis(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
        model=model,
    )

    # Then enhance the output
    enhanced_text = _enhance_output(output, deal_type, model)

    total_cost = output.total_llm_cost

    from dataclasses import asdict
    return AnalysisResult(
        mode="enhanced",
        deal_type=deal_type,
        timestamp=output.timestamp,
        session_id=None,
        considerations=[asdict(c) for c in output.considerations],
        activities=[asdict(a) for a in output.activities],
        tsa_services=output.tsa_services,
        total_cost_range=output.total_cost_range,
        total_timeline_months=output.total_timeline_months,
        validation={
            "is_valid": output.validation.is_valid,
            "confidence_score": output.validation.confidence_score,
            "missing_considerations": output.validation.missing_considerations,
            "suggested_additions": output.validation.suggested_additions,
            "recommendations": output.validation.recommendations,
            "assessment": output.validation.assessment,
        },
        confidence_score=output.validation.confidence_score,
        llm_cost=total_cost,
        formatted_text=enhanced_text,
        summary={
            "total_cost": f"${output.total_cost_range[0]:,.0f} - ${output.total_cost_range[1]:,.0f}",
            "considerations": len(output.considerations),
            "activities": len(output.activities),
            "tsa_services": len(output.tsa_services),
            "timeline": f"{output.total_timeline_months[0]}-{output.total_timeline_months[1]} months",
            "confidence": f"{output.validation.confidence_score:.0%}",
            "mode": "enhanced",
        },
    )


def _format_fast_output(
    deal_type: str,
    considerations: List,
    activities: List,
    tsa_services: List,
) -> str:
    """Format fast mode output."""

    lines = []
    lines.append("=" * 70)
    lines.append(f"IT DUE DILIGENCE ANALYSIS (Fast Mode)")
    lines.append("=" * 70)
    lines.append(f"Deal Type: {deal_type}")
    lines.append(f"Note: Validation skipped in fast mode")

    lines.append(f"\n{'='*70}")
    lines.append("KEY CONSIDERATIONS")
    lines.append("=" * 70)

    for c in considerations:
        lines.append(f"\n[{c.consideration_id}] {c.workstream.upper()}")
        lines.append(f"  Finding: {c.finding}")
        lines.append(f"  Impact: {c.deal_impact}")

    lines.append(f"\n{'='*70}")
    lines.append("DERIVED ACTIVITIES")
    lines.append("=" * 70)

    total_low = 0
    total_high = 0

    for a in activities:
        lines.append(f"\n[{a.activity_id}] {a.name}")
        lines.append(f"  Cost: ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}")
        lines.append(f"  Formula: {a.cost_formula}")
        total_low += a.cost_range[0]
        total_high += a.cost_range[1]

    lines.append(f"\n{'='*70}")
    lines.append("SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Total Cost: ${total_low:,.0f} - ${total_high:,.0f}")
    lines.append(f"TSA Services: {len(tsa_services)}")

    return "\n".join(lines)


def _enhance_output(output: Any, deal_type: str, model: str) -> str:
    """Enhance output with improved executive summary."""
    import anthropic
    import os

    # Build enhancement prompt
    prompt = f"""You are an expert IT M&A advisor preparing a client-ready executive summary.

## Analysis Results
Deal Type: {deal_type}
Total Cost: ${output.total_cost_range[0]:,.0f} - ${output.total_cost_range[1]:,.0f}
TSA Services: {len(output.tsa_services)}
Confidence: {output.validation.confidence_score:.0%}

## Key Considerations
{chr(10).join([f'- [{c.workstream}] {c.finding}' for c in output.considerations[:5]])}

## Validation Assessment
{output.validation.assessment}

## Task
Write a 3-4 paragraph executive summary suitable for a PE partner audience.

Be direct and professional. Focus on:
1. The key message (what does this deal need?)
2. The cost drivers (where is the money going?)
3. The risks (what could go wrong?)
4. The timeline (how long and what's critical?)
"""

    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        enhanced_summary = response.content[0].text

        # Build full enhanced output
        from tools_v2.three_stage_reasoning import format_three_stage_output
        base_output = format_three_stage_output(output)

        # Prepend enhanced summary
        enhanced = f"""{'='*70}
EXECUTIVE SUMMARY (Enhanced)
{'='*70}

{enhanced_summary}

{'='*70}
DETAILED ANALYSIS
{'='*70}

{base_output}
"""
        return enhanced

    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        from tools_v2.three_stage_reasoning import format_three_stage_output
        return format_three_stage_output(output)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'analyze_deal',
    'create_analysis_session',
    'AnalysisMode',
    'AnalysisResult',
]
