"""
Deal Readout View - 1-Page Executive Summary

Provides a clean, printable summary with:
- Complexity verdict badge
- Cost range
- Key metrics (Day 1 Items, Critical Risks, Info Gaps)
- Top 5 Risks (deterministically selected)
- Confidence meter
- Integration flags

Uses the consistency_engine for deterministic calculations.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools_v2.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore
    from tools_v2.consistency_engine import (
        generate_consistency_report,
        calculate_complexity_score,
        calculate_total_costs,
        get_top_risks,
        calculate_confidence,
        check_complexity_flags
    )
except ImportError as e:
    st.error(f"Import error: {e}")


# =============================================================================
# STYLING
# =============================================================================

COMPLEXITY_COLORS = {
    "low": ("#22c55e", "#dcfce7"),       # Green
    "mid": ("#eab308", "#fef9c3"),       # Yellow
    "high": ("#f97316", "#ffedd5"),      # Orange
    "critical": ("#ef4444", "#fee2e2")   # Red
}

SEVERITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢"
}


def render_complexity_badge(tier: str, score: int) -> str:
    """Render the complexity verdict badge."""
    bg_color, light_bg = COMPLEXITY_COLORS.get(tier, ("#6b7280", "#f3f4f6"))

    return f"""
    <div style="
        display: inline-block;
        background: {bg_color};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 1.5em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        {tier}-COMPLEXITY
    </div>
    <div style="
        display: inline-block;
        background: {light_bg};
        color: {bg_color};
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.9em;
        margin-left: 10px;
    ">
        Score: {score}
    </div>
    """


def render_cost_range(costs: Dict) -> str:
    """Render the cost range display."""
    total = costs.get("total", {"low": 0, "high": 0})
    low_m = total["low"] / 1_000_000
    high_m = total["high"] / 1_000_000

    return f"""
    <div style="
        background: linear-gradient(135deg, #1e3a5f, #2563eb);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
    ">
        <div style="font-size: 0.9em; opacity: 0.8;">Estimated Integration Cost</div>
        <div style="font-size: 2.5em; font-weight: bold;">${low_m:.1f}M - ${high_m:.1f}M</div>
    </div>
    """


def render_metric_card(label: str, value: Any, icon: str = "", color: str = "#3b82f6") -> str:
    """Render a single metric card."""
    return f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="font-size: 2em;">{icon}</div>
        <div style="font-size: 1.8em; font-weight: bold; color: {color};">{value}</div>
        <div style="font-size: 0.85em; color: #6b7280;">{label}</div>
    </div>
    """


def render_confidence_meter(confidence: Dict) -> str:
    """Render the confidence meter."""
    score = confidence.get("score", 0)
    label = confidence.get("label", "Unknown")
    pct = int(score * 100)

    # Color based on level
    if score >= 0.7:
        color = "#22c55e"
    elif score >= 0.4:
        color = "#eab308"
    else:
        color = "#ef4444"

    factors = confidence.get("factors", {})

    return f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: bold;">Data Confidence</span>
            <span style="color: {color}; font-weight: bold;">{label} ({pct}%)</span>
        </div>
        <div style="
            background: #e5e7eb;
            border-radius: 4px;
            height: 12px;
            overflow: hidden;
        ">
            <div style="
                background: {color};
                width: {pct}%;
                height: 100%;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="font-size: 0.8em; color: #6b7280; margin-top: 10px;">
            {factors.get('verified_facts', 'N/A')} facts verified |
            {factors.get('source_count', 0)} sources |
            {factors.get('gap_count', 0)} gaps identified
        </div>
    </div>
    """


def render_top_risks_table(risks: List[Dict]) -> None:
    """Render the top risks as a table."""
    if not risks:
        st.info("No risks identified yet.")
        return

    st.markdown("### Top 5 Risks")
    st.markdown("*Deterministically selected by score*")

    for i, risk in enumerate(risks[:5], 1):
        severity = risk.get("severity", "medium")
        icon = SEVERITY_ICONS.get(severity, "⚪")
        title = risk.get("title", "Untitled Risk")
        domain = risk.get("domain", "general")
        score = risk.get("_score", 0)

        with st.expander(f"{icon} **#{i}: {title}** ({severity.upper()})"):
            st.markdown(risk.get("description", "No description"))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Domain:** {domain}")
            with col2:
                st.markdown(f"**Score:** {score}")
            with col3:
                citations = len(risk.get("based_on_facts", []))
                st.markdown(f"**Citations:** {citations}")

            if risk.get("mitigation"):
                st.markdown(f"**Mitigation:** {risk['mitigation']}")


def render_flags_section(flags: List[Dict]) -> None:
    """Render complexity flags that were triggered."""
    if not flags:
        return

    st.markdown("### Integration Flags Triggered")

    for flag in flags:
        flag_name = flag.get("flag", "unknown").replace("_", " ").title()
        bump_to = flag.get("bump_to", "unknown")
        matched = flag.get("matched_text", "")[:100]

        st.warning(f"**{flag_name}** → Bumps complexity to {bump_to.upper()}")
        if matched:
            st.caption(f"Matched: \"{matched}...\"")


def render_phase_breakdown(costs: Dict) -> None:
    """Render cost breakdown by phase."""
    by_phase = costs.get("by_phase", {})

    if not by_phase:
        return

    st.markdown("### Cost by Phase")

    phase_data = []
    for phase, phase_costs in by_phase.items():
        if phase_costs.get("low", 0) > 0 or phase_costs.get("high", 0) > 0:
            phase_data.append({
                "Phase": phase.replace("_", " "),
                "Low ($K)": phase_costs.get("low", 0) / 1000,
                "High ($K)": phase_costs.get("high", 0) / 1000,
                "Items": phase_costs.get("count", 0)
            })

    if phase_data:
        df = pd.DataFrame(phase_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def load_deal_data(session_dir: Path) -> Dict[str, Any]:
    """Load all data needed for the deal readout."""
    facts = []
    gaps = []
    risks = []
    work_items = []

    # Load facts
    facts_path = session_dir / "facts.json"
    if facts_path.exists():
        try:
            fact_store = FactStore.load(str(facts_path))
            facts = [{"item": f.item, "domain": f.domain, "verified": f.verified}
                     for f in fact_store.facts]
        except Exception:
            pass

    # Load findings (risks, gaps, work items)
    findings_path = session_dir / "findings.json"
    if findings_path.exists():
        try:
            reasoning_store = ReasoningStore.load(str(findings_path))

            risks = [
                {
                    "severity": r.severity,
                    "title": r.title,
                    "description": r.description,
                    "domain": r.domain,
                    "based_on_facts": r.based_on_facts,
                    "integration_dependent": r.integration_dependent,
                    "mitigation": r.mitigation
                }
                for r in reasoning_store.risks
            ]

            gaps = [
                {
                    "description": g.description,
                    "importance": g.importance,
                    "domain": g.domain
                }
                for g in reasoning_store.gaps
            ]

            work_items = [
                {
                    "title": w.title,
                    "description": w.description,
                    "phase": w.phase,
                    "domain": w.domain
                }
                for w in reasoning_store.work_items
            ]
        except Exception:
            pass

    return {
        "facts": facts,
        "gaps": gaps,
        "risks": risks,
        "work_items": work_items
    }


def render_deal_readout_section(session_dir: Path, company_name: str = "Target Company"):
    """
    Main entry point for the Deal Readout view.
    """
    st.header("Deal Readout")
    st.markdown(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    # Load data
    data = load_deal_data(session_dir)

    facts = data["facts"]
    gaps = data["gaps"]
    risks = data["risks"]
    work_items = data["work_items"]

    # Check if we have any data
    if not facts and not risks and not work_items:
        st.info("No analysis data found. Run an analysis first to see the deal readout.")

        # Show sample readout
        st.markdown("---")
        st.markdown("### Sample Deal Readout")
        st.markdown("*Below is what a deal readout looks like with data:*")

        # Sample data
        sample_complexity = {"tier": "high", "score": 35, "flags_triggered": []}
        sample_costs = {
            "total": {"low": 2_500_000, "high": 6_000_000},
            "by_phase": {
                "Day_1": {"low": 500_000, "high": 1_000_000, "count": 8},
                "Day_100": {"low": 1_500_000, "high": 3_500_000, "count": 12},
                "Post_100": {"low": 500_000, "high": 1_500_000, "count": 6}
            }
        }
        sample_confidence = {
            "score": 0.65,
            "label": "Medium",
            "factors": {
                "verified_facts": "42/65",
                "source_count": 4,
                "gap_count": 8
            }
        }

        # Display sample
        st.markdown(render_complexity_badge("high", 35), unsafe_allow_html=True)
        st.markdown(render_cost_range(sample_costs), unsafe_allow_html=True)
        st.markdown(render_confidence_meter(sample_confidence), unsafe_allow_html=True)
        return

    # Generate consistency report
    verified_fact_ids = [f["item"] for f in facts if f.get("verified")]

    report = generate_consistency_report(
        facts=facts,
        gaps=gaps,
        risks=risks,
        work_items=work_items,
        verified_fact_ids=verified_fact_ids,
        all_texts=[r.get("description", "") for r in risks] + [g.get("description", "") for g in gaps]
    )

    # ==========================================================================
    # SECTION 1: Verdict Banner
    # ==========================================================================

    complexity = report.get("complexity", {})
    tier = complexity.get("tier", "mid")
    score = complexity.get("score", 0)

    st.markdown(render_complexity_badge(tier, score), unsafe_allow_html=True)

    # ==========================================================================
    # SECTION 2: Cost Range
    # ==========================================================================

    costs = report.get("costs", {})
    st.markdown(render_cost_range(costs), unsafe_allow_html=True)

    # ==========================================================================
    # SECTION 3: Key Metrics
    # ==========================================================================

    counts = report.get("counts", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        day1_count = len([w for w in work_items if "day_1" in w.get("phase", "").lower() or "day1" in w.get("phase", "").lower()])
        st.markdown(render_metric_card("Day 1 Items", day1_count, "📋", "#3b82f6"), unsafe_allow_html=True)

    with col2:
        critical_count = len([r for r in risks if r.get("severity") == "critical"])
        st.markdown(render_metric_card("Critical Risks", critical_count, "🔴", "#ef4444"), unsafe_allow_html=True)

    with col3:
        st.markdown(render_metric_card("Info Gaps", counts.get("gaps", 0), "❓", "#eab308"), unsafe_allow_html=True)

    with col4:
        st.markdown(render_metric_card("Total Facts", counts.get("facts", 0), "📊", "#22c55e"), unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================================================
    # SECTION 4: Top Risks
    # ==========================================================================

    top_risks = report.get("top_risks", [])
    render_top_risks_table(top_risks)

    # ==========================================================================
    # SECTION 5: Flags Triggered
    # ==========================================================================

    flags = complexity.get("flags_triggered", [])
    render_flags_section(flags)

    # ==========================================================================
    # SECTION 6: Confidence Meter
    # ==========================================================================

    confidence = report.get("confidence", {})
    st.markdown(render_confidence_meter(confidence), unsafe_allow_html=True)

    # ==========================================================================
    # SECTION 7: Phase Breakdown
    # ==========================================================================

    with st.expander("View Cost Breakdown by Phase"):
        render_phase_breakdown(costs)

        # Show breakdown details
        breakdown = costs.get("breakdown", [])
        if breakdown:
            st.markdown("#### Work Item Details")
            df = pd.DataFrame(breakdown)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # SECTION 8: Score Breakdown
    # ==========================================================================

    with st.expander("View Complexity Score Breakdown"):
        breakdown = complexity.get("breakdown", {})
        st.json(breakdown)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Deal Readout", layout="wide")
    st.title("Deal Readout Test")
    render_deal_readout_section(Path("sessions/test"), "Test Company")
