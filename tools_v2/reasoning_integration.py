"""
Reasoning Integration Module

Bridges the gap between:
1. FactStore (discovery output) → facts in reasoning engine format
2. ReasoningEngine → actionable output for UI/reports

This module handles the conversion and orchestration so the
reasoning engine can be easily integrated into the main pipeline.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import csv
import io
import logging

from stores.fact_store import FactStore, Fact as FactStoreFact
from tools_v2.reasoning_engine import ReasoningEngine, ReasoningOutput

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATION
# =============================================================================

VALID_DEAL_TYPES = ["carveout", "acquisition", "divestiture", "merger", "platform_addon"]

class ReasoningError(Exception):
    """Custom exception for reasoning errors."""
    pass


def validate_deal_type(deal_type: str) -> str:
    """Validate and normalize deal type."""
    normalized = deal_type.lower().strip()

    # Handle common aliases
    aliases = {
        "carve-out": "carveout",
        "carve out": "carveout",
        "add-on": "platform_addon",
        "addon": "platform_addon",
        "bolt-on": "platform_addon",
        "bolt on": "platform_addon",
        "tuck-in": "platform_addon",
    }
    normalized = aliases.get(normalized, normalized)

    if normalized not in VALID_DEAL_TYPES:
        raise ReasoningError(
            f"Invalid deal type '{deal_type}'. "
            f"Valid types: {', '.join(VALID_DEAL_TYPES)}"
        )
    return normalized


# =============================================================================
# FACT CONVERSION
# =============================================================================

def factstore_to_reasoning_format(fact_store: FactStore, entity: str = "target") -> List[Dict]:
    """
    Convert FactStore facts to the format expected by ReasoningEngine.

    FactStore Facts have:
        - fact_id, domain, category, item, details, status, evidence, entity

    ReasoningEngine expects:
        - fact_id, content, source, confidence, category

    We create a "content" string by combining item + details + evidence.
    """
    reasoning_facts = []

    # Get facts for specified entity (target or buyer)
    facts = fact_store.get_entity_facts(entity)

    for fact in facts:
        # Build content string from fact components
        content_parts = [fact.item]

        # Add key details
        if fact.details:
            detail_strs = []
            for k, v in fact.details.items():
                if v:  # Only include non-empty values
                    detail_strs.append(f"{k}: {v}")
            if detail_strs:
                content_parts.append(", ".join(detail_strs))

        # Add evidence quote if available (very useful for pattern matching)
        evidence_quote = fact.evidence.get("exact_quote", "")
        if evidence_quote:
            content_parts.append(f"Evidence: \"{evidence_quote}\"")

        content = ". ".join(content_parts)

        # Determine confidence based on status
        confidence_map = {
            "documented": 1.0,
            "partial": 0.7,
            "gap": 0.3,
        }

        reasoning_facts.append({
            "fact_id": fact.fact_id,
            "content": content,
            "source": "document",
            "confidence": confidence_map.get(fact.status, 0.5),
            "category": f"{fact.domain}/{fact.category}",
            "original_domain": fact.domain,
            "original_category": fact.category,
        })

    # Also convert gaps to fact-like format (gaps are important signals)
    for gap in fact_store.gaps:
        reasoning_facts.append({
            "fact_id": gap.gap_id,
            "content": f"GAP: {gap.description} (Importance: {gap.importance})",
            "source": "gap",
            "confidence": 0.9,  # Gaps are usually well-identified
            "category": f"{gap.domain}/{gap.category}",
            "original_domain": gap.domain,
            "original_category": gap.category,
        })

    logger.info(f"Converted {len(reasoning_facts)} facts/gaps from FactStore to reasoning format")
    return reasoning_facts


def extract_buyer_context(fact_store: FactStore) -> Dict[str, Any]:
    """
    Extract buyer technology context from buyer entity facts.

    Returns a dict suitable for the buyer_context parameter
    in ReasoningEngine.reason().
    """
    buyer_context = {}
    buyer_facts = fact_store.get_entity_facts("buyer")

    if not buyer_facts:
        logger.info("No buyer facts found - will skip technology mismatch analysis")
        return buyer_context

    # Technology keyword mappings
    email_keywords = {
        "microsoft 365": "Microsoft 365",
        "m365": "Microsoft 365",
        "outlook": "Microsoft 365",
        "exchange": "Microsoft 365",
        "gmail": "Google Workspace",
        "google workspace": "Google Workspace",
        "g suite": "Google Workspace",
    }

    cloud_keywords = {
        "aws": "AWS",
        "amazon": "AWS",
        "azure": "Azure",
        "microsoft azure": "Azure",
        "gcp": "GCP",
        "google cloud": "GCP",
    }

    identity_keywords = {
        "azure ad": "Azure AD",
        "entra": "Azure AD",
        "active directory": "Azure AD",
        "okta": "Okta",
    }

    erp_keywords = {
        "sap": "SAP",
        "s/4": "SAP",
        "netsuite": "NetSuite",
        "oracle": "Oracle",
    }

    def find_tech(facts: List[FactStoreFact], keywords: Dict[str, str]) -> str:
        """Find technology from facts using keyword matching."""
        for fact in facts:
            content_lower = fact.item.lower()
            details_str = json.dumps(fact.details).lower() if fact.details else ""
            evidence_str = fact.evidence.get("exact_quote", "").lower()

            full_content = f"{content_lower} {details_str} {evidence_str}"

            for keyword, tech in keywords.items():
                if keyword in full_content:
                    return tech
        return ""

    buyer_context["email"] = find_tech(buyer_facts, email_keywords)
    buyer_context["cloud"] = find_tech(buyer_facts, cloud_keywords)
    buyer_context["identity"] = find_tech(buyer_facts, identity_keywords)
    buyer_context["erp"] = find_tech(buyer_facts, erp_keywords)

    # Remove empty values
    buyer_context = {k: v for k, v in buyer_context.items() if v}

    logger.info(f"Extracted buyer context: {buyer_context}")
    return buyer_context


# =============================================================================
# OUTPUT CONVERSION (for UI/Reports)
# =============================================================================

@dataclass
class WorkstreamSummary:
    """Summary of a workstream for UI display."""
    name: str
    status: str  # "major_change", "minor_change", "no_change"
    activities: List[Dict]
    cost_range: tuple
    timeline_months: tuple
    requires_tsa: bool
    tsa_duration_months: Optional[tuple]


@dataclass
class ReasoningResultForUI:
    """Result formatted for Streamlit UI."""
    deal_type: str
    user_count: int

    # Executive summary
    executive_summary: str

    # Key numbers
    total_cost_low: float
    total_cost_high: float
    tsa_count: int
    critical_path_months: tuple

    # Workstream breakdown
    workstreams: List[WorkstreamSummary]

    # TSA details
    tsa_services: List[Dict]

    # Considerations (for drill-down)
    considerations: List[Dict]

    # Full activity list (for export)
    activities: List[Dict]

    # Synergies (for acquisition)
    synergies: List[Dict]

    # Traceability
    input_hash: str
    facts_analyzed: int


def convert_output_for_ui(output: ReasoningOutput, synergies: List[Dict] = None) -> ReasoningResultForUI:
    """
    Convert ReasoningOutput to a format optimized for Streamlit UI.
    """
    workstream_names = {
        "identity": "Identity & Access Management",
        "email": "Email & Collaboration",
        "infrastructure": "Infrastructure & Hosting",
        "network": "Network & Connectivity",
        "security": "Security & Compliance",
        "service_desk": "IT Support",
        "applications": "Business Applications/ERP",
    }

    # Build workstream summaries
    workstreams = []
    activities_by_ws = {}

    for activity in output.derived_activities:
        ws = activity.workstream
        if ws not in activities_by_ws:
            activities_by_ws[ws] = []
        activities_by_ws[ws].append({
            "id": activity.activity_id,
            "name": activity.name,
            "description": activity.description,
            "why_needed": activity.why_needed,
            "cost_low": activity.cost_range[0],
            "cost_high": activity.cost_range[1],
            "timeline_months": activity.timeline_months,
            "requires_tsa": activity.requires_tsa,
            "tsa_duration": activity.tsa_duration_months,
        })

    for ws, costs in output.workstream_costs.items():
        ws_activities = activities_by_ws.get(ws, [])

        # Determine status
        if costs[1] > 500000:
            status = "major_change"
        elif costs[1] > 100000:
            status = "minor_change"
        else:
            status = "no_change"

        # Calculate timeline
        if ws_activities:
            timeline_months = (
                min(a["timeline_months"][0] for a in ws_activities),
                max(a["timeline_months"][1] for a in ws_activities),
            )
        else:
            timeline_months = (0, 0)

        # Check TSA
        requires_tsa = any(a.get("requires_tsa") for a in ws_activities)
        tsa_durations = [a["tsa_duration"] for a in ws_activities if a.get("tsa_duration")]
        tsa_duration_months = max(tsa_durations, key=lambda x: x[1]) if tsa_durations else None

        workstreams.append(WorkstreamSummary(
            name=workstream_names.get(ws, ws),
            status=status,
            activities=ws_activities,
            cost_range=costs,
            timeline_months=timeline_months,
            requires_tsa=requires_tsa,
            tsa_duration_months=tsa_duration_months,
        ))

    # Sort workstreams by cost (highest first)
    workstreams.sort(key=lambda w: w.cost_range[1], reverse=True)

    # TSA services
    tsa_services = [
        {
            "service": tsa.service,
            "workstream": tsa.workstream,
            "duration_months": tsa.duration_months,
            "criticality": tsa.criticality,
            "why_needed": tsa.why_needed,
        }
        for tsa in output.tsa_requirements
    ]

    # Considerations for drill-down
    considerations = [
        {
            "id": c.consideration_id,
            "workstream": c.workstream,
            "finding": c.finding,
            "implication": c.implication,
            "reasoning": c.reasoning,
            "criticality": c.criticality,
            "supporting_facts": c.supporting_facts,
        }
        for c in output.considerations
    ]

    # All activities
    all_activities = [
        {
            "id": a.activity_id,
            "workstream": a.workstream,
            "name": a.name,
            "description": a.description,
            "why_needed": a.why_needed,
            "cost_low": a.cost_range[0],
            "cost_high": a.cost_range[1],
            "timeline_months": a.timeline_months,
            "requires_tsa": a.requires_tsa,
            "tsa_duration": a.tsa_duration_months,
            "triggered_by": a.triggered_by,
        }
        for a in output.derived_activities
    ]

    return ReasoningResultForUI(
        deal_type=output.deal_type,
        user_count=output.user_count,
        executive_summary=output.executive_summary,
        total_cost_low=output.grand_total[0],
        total_cost_high=output.grand_total[1],
        tsa_count=len(output.tsa_requirements),
        critical_path_months=output.critical_path_months,
        workstreams=[asdict(w) for w in workstreams],
        tsa_services=tsa_services,
        considerations=considerations,
        activities=all_activities,
        synergies=synergies or [],
        input_hash=output.input_hash,
        facts_analyzed=output.facts_analyzed,
    )


# =============================================================================
# MAIN INTEGRATION FUNCTION
# =============================================================================

def run_reasoning_analysis(
    fact_store: FactStore,
    deal_type: str,
    meeting_notes: Optional[str] = None,
    include_buyer_context: bool = True,
) -> Dict[str, Any]:
    """
    Main integration function: Run reasoning analysis on fact store data.

    This is the primary entry point for integrating reasoning into the pipeline.

    Args:
        fact_store: FactStore with extracted facts (from discovery phase)
        deal_type: "carveout", "acquisition", "divestiture", etc.
        meeting_notes: Optional additional context from meetings
        include_buyer_context: Whether to extract buyer context from buyer facts

    Returns:
        Dict with:
        - raw_output: ReasoningOutput dataclass
        - ui_result: ReasoningResultForUI for Streamlit
        - formatted_text: Human-readable text output
        - synergies: List of synergy opportunities (for acquisitions)

    Raises:
        ReasoningError: If deal_type is invalid
    """
    # Validate and normalize deal type
    deal_type = validate_deal_type(deal_type)
    logger.info(f"Running reasoning analysis: deal_type={deal_type}")

    # Initialize engine
    engine = ReasoningEngine()

    # Convert facts
    reasoning_facts = factstore_to_reasoning_format(fact_store, entity="target")
    logger.info(f"Converted {len(reasoning_facts)} facts for reasoning")

    # Extract buyer context if needed
    buyer_context = None
    if include_buyer_context and deal_type.lower() in ["acquisition", "platform_addon"]:
        buyer_context = extract_buyer_context(fact_store)

    # Run reasoning
    output = engine.reason(
        facts=reasoning_facts,
        deal_type=deal_type,
        buyer_context=buyer_context,
        meeting_notes=meeting_notes,
    )

    # Extract synergies for acquisitions
    synergies = []
    if deal_type.lower() in ["acquisition", "platform_addon"] and buyer_context:
        tech_stack = engine.identify_technology_stack(reasoning_facts)
        tech_mismatches = engine.identify_technology_mismatches(tech_stack, buyer_context)
        quant_context = engine.extract_quantitative_context(reasoning_facts)
        synergies = engine.derive_synergy_opportunities(tech_mismatches, quant_context)

    # Convert for UI
    ui_result = convert_output_for_ui(output, synergies)

    # Format as text
    formatted_text = engine.format_output(output)

    logger.info(f"Reasoning complete: ${output.grand_total[0]:,.0f} - ${output.grand_total[1]:,.0f}")

    return {
        "raw_output": output,
        "ui_result": ui_result,
        "formatted_text": formatted_text,
        "synergies": synergies,
        "metadata": {
            "deal_type": deal_type,
            "facts_analyzed": output.facts_analyzed,
            "considerations_count": len(output.considerations),
            "activities_count": len(output.derived_activities),
            "tsa_count": len(output.tsa_requirements),
            "input_hash": output.input_hash,
        }
    }


# =============================================================================
# EXPORT FUNCTIONS (for reports)
# =============================================================================

def export_to_json(result: Dict[str, Any]) -> str:
    """Export reasoning result to JSON for reports."""

    # Convert dataclasses to dicts
    output = result["raw_output"]

    export_data = {
        "summary": {
            "deal_type": output.deal_type,
            "user_count": output.user_count,
            "facts_analyzed": output.facts_analyzed,
            "total_cost_range": {
                "low": output.grand_total[0],
                "high": output.grand_total[1],
            },
            "critical_path_months": {
                "low": output.critical_path_months[0],
                "high": output.critical_path_months[1],
            },
            "tsa_services_required": len(output.tsa_requirements),
        },
        "workstream_costs": {
            ws: {"low": cost[0], "high": cost[1]}
            for ws, cost in output.workstream_costs.items()
        },
        "considerations": [
            {
                "id": c.consideration_id,
                "workstream": c.workstream,
                "finding": c.finding,
                "implication": c.implication,
                "reasoning": c.reasoning,
                "criticality": c.criticality,
                "supporting_facts": c.supporting_facts,
            }
            for c in output.considerations
        ],
        "activities": [
            {
                "id": a.activity_id,
                "workstream": a.workstream,
                "name": a.name,
                "description": a.description,
                "why_needed": a.why_needed,
                "cost_range": {"low": a.cost_range[0], "high": a.cost_range[1]},
                "timeline_months": {"low": a.timeline_months[0], "high": a.timeline_months[1]},
                "requires_tsa": a.requires_tsa,
                "tsa_duration_months": {
                    "low": a.tsa_duration_months[0],
                    "high": a.tsa_duration_months[1]
                } if a.tsa_duration_months else None,
            }
            for a in output.derived_activities
        ],
        "tsa_requirements": [
            {
                "service": t.service,
                "workstream": t.workstream,
                "why_needed": t.why_needed,
                "duration_months": {"low": t.duration_months[0], "high": t.duration_months[1]},
                "criticality": t.criticality,
            }
            for t in output.tsa_requirements
        ],
        "synergies": result.get("synergies", []),
        "narrative": {
            "executive_summary": output.executive_summary,
            "detailed_narrative": output.detailed_narrative,
        },
        "metadata": result.get("metadata", {}),
    }

    return json.dumps(export_data, indent=2)


def export_cost_table(result: Dict[str, Any]) -> List[Dict]:
    """Export cost table for spreadsheet/CSV export."""
    output = result["raw_output"]

    rows = []
    for activity in output.derived_activities:
        rows.append({
            "Activity ID": activity.activity_id,
            "Workstream": activity.workstream,
            "Activity": activity.name,
            "Description": activity.description,
            "Why Needed": activity.why_needed,
            "Cost Low": activity.cost_range[0],
            "Cost High": activity.cost_range[1],
            "Timeline Low (months)": activity.timeline_months[0],
            "Timeline High (months)": activity.timeline_months[1],
            "Requires TSA": "Yes" if activity.requires_tsa else "No",
            "TSA Duration Low (months)": activity.tsa_duration_months[0] if activity.tsa_duration_months else "",
            "TSA Duration High (months)": activity.tsa_duration_months[1] if activity.tsa_duration_months else "",
        })

    return rows


def export_to_csv(result: Dict[str, Any]) -> str:
    """Export cost table as CSV string."""
    rows = export_cost_table(result)
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def get_quick_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a quick summary of reasoning results for display.

    Useful for showing key metrics without full detail.
    """
    output = result["raw_output"]

    return {
        "deal_type": output.deal_type,
        "user_count": output.user_count,
        "total_cost": f"${output.grand_total[0]:,.0f} - ${output.grand_total[1]:,.0f}",
        "tsa_count": len(output.tsa_requirements),
        "activity_count": len(output.derived_activities),
        "critical_path": f"{output.critical_path_months[0]}-{output.critical_path_months[1]} months",
        "workstream_count": len(output.workstream_costs),
        "top_cost_workstream": max(
            output.workstream_costs.items(),
            key=lambda x: x[1][1]
        )[0] if output.workstream_costs else "N/A",
        "considerations_count": len(output.considerations),
    }


def compare_scenarios(
    fact_store: FactStore,
    deal_types: List[str],
    meeting_notes: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Compare reasoning results across multiple deal type scenarios.

    Useful for showing clients what-if analysis (e.g., carveout vs acquisition).

    Args:
        fact_store: FactStore with facts
        deal_types: List of deal types to compare (e.g., ["carveout", "acquisition"])
        meeting_notes: Optional meeting notes

    Returns:
        Dict mapping deal_type to summary results
    """
    results = {}

    for deal_type in deal_types:
        try:
            result = run_reasoning_analysis(
                fact_store=fact_store,
                deal_type=deal_type,
                meeting_notes=meeting_notes,
                include_buyer_context=True,
            )
            results[deal_type] = {
                "summary": get_quick_summary(result),
                "full_result": result,
            }
        except ReasoningError as e:
            results[deal_type] = {"error": str(e)}

    return results


# =============================================================================
# SESSION INTEGRATION
# =============================================================================

def run_reasoning_on_session(
    session: Any,  # DDSession - using Any to avoid circular import
    meeting_notes: Optional[str] = None,
    deal_type_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run reasoning analysis on a DDSession.

    This is the main integration point between the session-based workflow
    and the new reasoning engine.

    Args:
        session: DDSession with completed discovery phase
        meeting_notes: Optional additional context from meetings
        deal_type_override: Override deal type from session context

    Returns:
        Dict with reasoning results (same as run_reasoning_analysis)
    """
    # Get deal type from session or override
    deal_context = session.state.deal_context
    deal_type = deal_type_override or deal_context.deal_type

    # Map session deal types to reasoning engine deal types
    deal_type_map = {
        "carve_out": "carveout",
        "bolt_on": "acquisition",
        "platform": "acquisition",
    }
    deal_type = deal_type_map.get(deal_type, deal_type)

    logger.info(f"Running reasoning on session {session.session_id} (deal_type={deal_type})")

    # Build meeting notes with deal context
    full_notes = []

    # Add deal context as notes
    full_notes.append(f"Target: {deal_context.target_name}")
    if deal_context.buyer_name:
        full_notes.append(f"Buyer: {deal_context.buyer_name}")
    if deal_context.industry:
        full_notes.append(f"Industry: {deal_context.industry}")
    if deal_context.notes:
        full_notes.append(deal_context.notes)

    # Add user-provided meeting notes
    if meeting_notes:
        full_notes.append(meeting_notes)

    combined_notes = "\n".join(full_notes) if full_notes else None

    # Run reasoning analysis
    result = run_reasoning_analysis(
        fact_store=session.fact_store,
        deal_type=deal_type,
        meeting_notes=combined_notes,
        include_buyer_context=True,
    )

    # Store result in session outputs directory
    output_dir = session.session_dir / "outputs"
    output_dir.mkdir(exist_ok=True)

    # Save reasoning output
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"reasoning_{timestamp}.json"

    json_output = export_to_json(result)
    with open(output_file, 'w') as f:
        f.write(json_output)

    logger.info(f"Saved reasoning output to {output_file}")

    return result


def analyze_from_session_file(
    facts_file: str,
    deal_type: str,
    meeting_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run reasoning analysis directly from a saved facts file.

    Useful for running reasoning without a full session.

    Args:
        facts_file: Path to saved facts JSON file
        deal_type: Deal type for analysis
        meeting_notes: Optional meeting notes

    Returns:
        Dict with reasoning results
    """
    fact_store = FactStore.load(facts_file)
    logger.info(f"Loaded {len(fact_store.facts)} facts from {facts_file}")

    return run_reasoning_analysis(
        fact_store=fact_store,
        deal_type=deal_type,
        meeting_notes=meeting_notes,
        include_buyer_context=True,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'factstore_to_reasoning_format',
    'extract_buyer_context',
    'convert_output_for_ui',
    'run_reasoning_analysis',
    'export_to_json',
    'export_cost_table',
    'export_to_csv',
    'get_quick_summary',
    'compare_scenarios',
    'validate_deal_type',
    'run_reasoning_on_session',
    'analyze_from_session_file',
    'ReasoningError',
    'WorkstreamSummary',
    'ReasoningResultForUI',
    'VALID_DEAL_TYPES',
]


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """
    Command-line entry point for reasoning analysis.

    Usage:
        python -m tools_v2.reasoning_integration --facts facts.json --deal-type carveout
        python -m tools_v2.reasoning_integration --session my_session --meeting-notes "Notes here"
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Run IT Due Diligence Reasoning Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Analyze from facts file
    python -m tools_v2.reasoning_integration --facts facts.json --deal-type carveout

    # Analyze from session
    python -m tools_v2.reasoning_integration --session acme_corp_2024

    # Compare deal types
    python -m tools_v2.reasoning_integration --facts facts.json --compare carveout acquisition
        """
    )

    parser.add_argument('--facts', help='Path to facts JSON file')
    parser.add_argument('--session', help='Session ID to analyze')
    parser.add_argument('--deal-type', dest='deal_type', default='carveout',
                        help='Deal type (carveout, acquisition, etc.)')
    parser.add_argument('--meeting-notes', dest='meeting_notes',
                        help='Additional meeting notes context')
    parser.add_argument('--compare', nargs='+',
                        help='Compare multiple deal types')
    parser.add_argument('--output', help='Output file path (JSON)')
    parser.add_argument('--csv', action='store_true',
                        help='Also export CSV cost table')

    args = parser.parse_args()

    if not args.facts and not args.session:
        parser.error('Must specify either --facts or --session')

    try:
        if args.session:
            # Load session
            from tools_v2.session import DDSession
            session = DDSession.load(args.session)
            print(f"Loaded session: {session.session_id}")
            print(f"  Facts: {len(session.fact_store.facts)}")
            print(f"  Gaps: {len(session.fact_store.gaps)}")

            result = run_reasoning_on_session(
                session=session,
                meeting_notes=args.meeting_notes,
                deal_type_override=args.deal_type if args.deal_type != 'carveout' else None,
            )
        else:
            # Load from facts file
            if args.compare:
                # Compare multiple deal types
                fact_store = FactStore.load(args.facts)
                print(f"Loaded {len(fact_store.facts)} facts")

                results = compare_scenarios(fact_store, args.compare, args.meeting_notes)

                print("\n" + "="*60)
                print("SCENARIO COMPARISON")
                print("="*60)

                for deal_type, data in results.items():
                    if 'error' in data:
                        print(f"\n{deal_type}: ERROR - {data['error']}")
                    else:
                        summary = data['summary']
                        print(f"\n{deal_type.upper()}:")
                        print(f"  Total Cost: {summary['total_cost']}")
                        print(f"  Activities: {summary['activity_count']}")
                        print(f"  TSA Services: {summary['tsa_count']}")
                        print(f"  Critical Path: {summary['critical_path']}")

                return

            # Single deal type analysis
            result = analyze_from_session_file(
                facts_file=args.facts,
                deal_type=args.deal_type,
                meeting_notes=args.meeting_notes,
            )

        # Print summary
        summary = get_quick_summary(result)
        print("\n" + "="*60)
        print("REASONING ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nDeal Type: {summary['deal_type']}")
        print(f"User Count: {summary['user_count']:,}")
        print(f"Total Cost: {summary['total_cost']}")
        print(f"TSA Services: {summary['tsa_count']}")
        print(f"Activities: {summary['activity_count']}")
        print(f"Critical Path: {summary['critical_path']}")

        # Save output if specified
        if args.output:
            json_output = export_to_json(result)
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"\nOutput saved to: {args.output}")

        if args.csv:
            csv_path = (args.output or 'reasoning_output').replace('.json', '') + '_costs.csv'
            csv_output = export_to_csv(result)
            with open(csv_path, 'w') as f:
                f.write(csv_output)
            print(f"CSV saved to: {csv_path}")

        # Print formatted text output
        print("\n" + result['formatted_text'])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
