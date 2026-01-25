"""
Coverage Analysis View

Documentation coverage scoring and gap analysis.

Steps 169-175 of the alignment plan.
"""

import streamlit as st
from typing import Any, List, Optional, Dict

from ..components.layout import page_header, section_header, empty_state
from ..components.charts import coverage_radar, domain_breakdown_bar
from ..components.cards import coverage_score_card


# Coverage checklists by domain
COVERAGE_CHECKLISTS = {
    "infrastructure": {
        "critical": [
            "Server inventory (physical/virtual)",
            "Storage capacity and utilization",
            "Backup solution and schedules",
            "Disaster recovery plan",
            "Network topology",
        ],
        "important": [
            "Hardware refresh schedule",
            "Virtualization platform",
            "Monitoring tools",
            "Capacity planning",
            "Asset management",
        ],
    },
    "network": {
        "critical": [
            "Network topology diagram",
            "WAN connectivity",
            "Firewall configuration",
            "VPN/Remote access",
            "DNS/DHCP infrastructure",
        ],
        "important": [
            "Network segmentation",
            "Load balancing",
            "SD-WAN adoption",
            "Network monitoring",
            "Bandwidth utilization",
        ],
    },
    "cybersecurity": {
        "critical": [
            "Endpoint protection",
            "Security incident history",
            "Vulnerability management",
            "Access controls",
            "Security policies",
        ],
        "important": [
            "SIEM/logging",
            "Penetration testing",
            "Security awareness training",
            "Third-party risk management",
            "Compliance certifications",
        ],
    },
    "applications": {
        "critical": [
            "Application inventory",
            "ERP/Core business systems",
            "Integration architecture",
            "License compliance",
            "Support contracts",
        ],
        "important": [
            "Custom application documentation",
            "SaaS inventory",
            "Development tools",
            "Database platforms",
            "API inventory",
        ],
    },
    "identity_access": {
        "critical": [
            "Directory services",
            "Authentication methods",
            "Privileged access management",
            "User provisioning process",
            "MFA adoption",
        ],
        "important": [
            "SSO implementation",
            "Access review process",
            "Service accounts",
            "Password policies",
            "Identity governance",
        ],
    },
    "organization": {
        "critical": [
            "IT org structure",
            "Key personnel",
            "MSP relationships",
            "IT budget",
            "Vendor contracts",
        ],
        "important": [
            "Skills inventory",
            "Succession planning",
            "Training programs",
            "Outsourcing arrangements",
            "IT roadmap",
        ],
    },
}


def render_coverage_view(
    fact_store: Any,
    domains: Optional[List[str]] = None,
) -> None:
    """
    Render the coverage analysis view page.

    Args:
        fact_store: FactStore with extracted facts
        domains: Optional list of domains to analyze
    """
    page_header(
        title="Coverage Analysis",
        subtitle="Documentation completeness assessment",
        icon="📊",
    )

    if not fact_store or not fact_store.facts:
        empty_state(
            title="No Analysis Data",
            message="Run an analysis to see coverage metrics",
            icon="📊",
        )
        return

    # Calculate coverage
    coverage_results = _calculate_coverage(fact_store, domains)

    # Overall summary
    _render_coverage_summary(coverage_results)

    st.divider()

    # Radar chart
    col1, col2 = st.columns([2, 1])

    with col1:
        coverage_radar(
            coverage_scores={d: r["score"] for d, r in coverage_results["by_domain"].items()},
            title="Coverage by Domain",
        )

    with col2:
        _render_grade_legend()

    st.divider()

    # Domain details
    _render_domain_coverage(coverage_results)

    # Improvement recommendations
    st.divider()
    _render_coverage_recommendations(coverage_results)


def _calculate_coverage(fact_store: Any, domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """Calculate coverage scores for all domains."""
    results = {
        "overall_score": 0,
        "overall_grade": "N/A",
        "by_domain": {},
        "total_items": 0,
        "covered_items": 0,
        "critical_coverage": 0,
    }

    # Get domains from facts if not specified
    if domains is None:
        domains = list(set(f.domain for f in fact_store.facts))

    # Calculate for each domain
    for domain in domains:
        if domain not in COVERAGE_CHECKLISTS:
            continue

        domain_facts = [f for f in fact_store.facts if f.domain == domain]
        checklist = COVERAGE_CHECKLISTS[domain]

        # Check coverage
        critical_items = checklist.get("critical", [])
        important_items = checklist.get("important", [])

        # Simple keyword matching for coverage
        fact_text = " ".join([f.item.lower() + " " + str(f.details).lower() for f in domain_facts])

        critical_covered = []
        critical_missing = []

        for item in critical_items:
            keywords = item.lower().split()
            if any(kw in fact_text for kw in keywords[:2]):  # Match first 2 keywords
                critical_covered.append(item)
            else:
                critical_missing.append(item)

        important_covered = []
        important_missing = []

        for item in important_items:
            keywords = item.lower().split()
            if any(kw in fact_text for kw in keywords[:2]):
                important_covered.append(item)
            else:
                important_missing.append(item)

        # Calculate score
        total_items = len(critical_items) + len(important_items)
        covered = len(critical_covered) + len(important_covered)

        # Weight critical items more heavily (2x)
        weighted_total = len(critical_items) * 2 + len(important_items)
        weighted_covered = len(critical_covered) * 2 + len(important_covered)

        score = (weighted_covered / weighted_total * 100) if weighted_total > 0 else 0
        critical_pct = (len(critical_covered) / len(critical_items) * 100) if critical_items else 100

        results["by_domain"][domain] = {
            "score": score,
            "grade": _score_to_grade(score),
            "critical_score": critical_pct,
            "critical_covered": critical_covered,
            "critical_missing": critical_missing,
            "important_covered": important_covered,
            "important_missing": important_missing,
            "fact_count": len(domain_facts),
        }

        results["total_items"] += total_items
        results["covered_items"] += covered

    # Calculate overall
    if results["by_domain"]:
        avg_score = sum(d["score"] for d in results["by_domain"].values()) / len(results["by_domain"])
        results["overall_score"] = avg_score
        results["overall_grade"] = _score_to_grade(avg_score)

        avg_critical = sum(d["critical_score"] for d in results["by_domain"].values()) / len(results["by_domain"])
        results["critical_coverage"] = avg_critical

    return results


def _score_to_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _render_coverage_summary(results: Dict) -> None:
    """Render coverage summary metrics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        grade = results["overall_grade"]
        grade_color = {"A": "green", "B": "blue", "C": "orange", "D": "red", "F": "red"}.get(grade, "gray")
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f5f5f4; border-radius: 8px;">
            <div style="font-size: 2.5rem; font-weight: bold; color: {grade_color};">{grade}</div>
            <div style="font-size: 0.8rem; color: #666;">Overall Grade</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("📊 Overall Score", f"{results['overall_score']:.0f}%")

    with col3:
        st.metric("🔴 Critical Coverage", f"{results['critical_coverage']:.0f}%")

    with col4:
        st.metric("📁 Domains Analyzed", len(results["by_domain"]))


def _render_grade_legend() -> None:
    """Render grade legend."""
    st.markdown("### Grade Scale")
    grades = [
        ("A", "90-100%", "#22c55e"),
        ("B", "80-89%", "#84cc16"),
        ("C", "70-79%", "#eab308"),
        ("D", "60-69%", "#f97316"),
        ("F", "< 60%", "#dc2626"),
    ]

    for grade, range_str, color in grades:
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="
                display: inline-block;
                width: 24px;
                height: 24px;
                background: {color};
                color: white;
                text-align: center;
                line-height: 24px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 0.5rem;
            ">{grade}</span>
            <span style="font-size: 0.9rem;">{range_str}</span>
        </div>
        """, unsafe_allow_html=True)


def _render_domain_coverage(results: Dict) -> None:
    """Render domain-level coverage details."""
    section_header("Coverage by Domain", icon="📁", level=4)

    for domain, data in sorted(results["by_domain"].items()):
        coverage_score_card(
            domain=domain,
            score=data["score"],
            grade=data["grade"],
            missing_items=data["critical_missing"],
        )

        with st.expander(f"📋 {domain.replace('_', ' ').title()} Details"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ Covered:**")
                for item in data["critical_covered"]:
                    st.markdown(f"- 🔴 {item}")
                for item in data["important_covered"]:
                    st.markdown(f"- 🟡 {item}")

            with col2:
                st.markdown("**❌ Missing:**")
                for item in data["critical_missing"]:
                    st.markdown(f"- 🔴 {item}")
                for item in data["important_missing"]:
                    st.markdown(f"- 🟡 {item}")

            st.caption(f"Based on {data['fact_count']} extracted facts")


def _render_coverage_recommendations(results: Dict) -> None:
    """Render coverage improvement recommendations."""
    section_header("Recommendations", icon="💡", level=4)

    # Find domains with low coverage
    low_coverage = [(d, r) for d, r in results["by_domain"].items() if r["score"] < 70]

    if not low_coverage:
        st.success("All domains have good coverage (70%+)")
        return

    st.warning(f"**{len(low_coverage)} domain(s)** need additional documentation:")

    for domain, data in sorted(low_coverage, key=lambda x: x[1]["score"]):
        st.markdown(f"### {domain.replace('_', ' ').title()} ({data['grade']})")

        if data["critical_missing"]:
            st.markdown("**Priority requests:**")
            for item in data["critical_missing"][:3]:
                st.markdown(f"1. Request documentation for: {item}")
