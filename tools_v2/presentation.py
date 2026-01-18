"""
Investment Thesis Presentation Generator.

Generates slide-deck style HTML presentations for PE buyers.
Follows a candid, partner-level tone - not salesy, but practical.

Design philosophy:
- Think: Big Four Partner sitting across from a PE deal team
- Candid about what works and what doesn't
- Focus on "what you'll actually deal with when you own this"
- Every claim traces back to source documents

Two generation modes:
1. generate_presentation() - Template-based (fast, no LLM calls)
2. generate_presentation_from_narratives() - Agent-generated (higher quality)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from tools_v2.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore, COST_RANGE_VALUES
from tools_v2.narrative_tools import NarrativeStore, DomainNarrative, CostNarrative
from tools_v2.html_report import _synthesize_fact_statement


# Domain display configuration
DOMAIN_CONFIG = {
    'infrastructure': {
        'title': 'Infrastructure',
        'icon': '🏗️',
        'focus_areas': ['hosting', 'compute', 'cloud', 'backup_dr', 'legacy']
    },
    'network': {
        'title': 'Network',
        'icon': '🌐',
        'focus_areas': ['connectivity', 'security', 'architecture', 'remote_access']
    },
    'cybersecurity': {
        'title': 'Cybersecurity',
        'icon': '🔒',
        'focus_areas': ['endpoint', 'perimeter', 'detection', 'response', 'governance']
    },
    'applications': {
        'title': 'Applications',
        'icon': '📱',
        'focus_areas': ['erp', 'crm', 'productivity', 'custom', 'integration']
    },
    'identity_access': {
        'title': 'Identity & Access',
        'icon': '🔑',
        'focus_areas': ['identity', 'authentication', 'authorization', 'pam', 'lifecycle']
    },
    'organization': {
        'title': 'IT Organization',
        'icon': '👥',
        'focus_areas': ['structure', 'outsourcing', 'capabilities', 'governance']
    }
}


@dataclass
class SlideContent:
    """Content for a single slide."""
    id: str
    title: str
    so_what: str  # The key implication - one sentence
    considerations: List[str]  # 3-5 bullet points
    narrative: str  # The story - succinct but complete
    cost_impact: Optional[str] = None
    sources: List[str] = None
    metrics: Dict[str, Any] = None
    open_questions: List[str] = None  # Gaps/VDR items for this domain
    extra_content: Optional[str] = None  # Additional HTML content (org chart, app landscape, etc.)


def _detect_primary_entity(fact_store: FactStore, domain: str) -> str:
    """
    Detect which entity (target or buyer) has the most facts for a domain.

    This handles cases where discovery tagged facts with the wrong entity.
    """
    domain_facts = [f for f in fact_store.facts if f.domain == domain]

    target_count = sum(1 for f in domain_facts if getattr(f, 'entity', 'target') == 'target')
    buyer_count = sum(1 for f in domain_facts if getattr(f, 'entity', 'target') == 'buyer')

    # Return whichever has more facts, defaulting to target
    if buyer_count > target_count:
        return 'buyer'
    return 'target'


def _build_org_chart_html(fact_store: FactStore, entity: str = "target") -> str:
    """
    Build an IT organization chart table from fact store data.

    Args:
        fact_store: The fact store containing organization facts
        entity: "target" or "buyer" to filter by

    Returns:
        HTML table for org chart, or empty string if no data
    """
    # Filter organization facts by entity
    org_facts = [f for f in fact_store.facts
                 if f.domain == "organization" and getattr(f, 'entity', 'target') == entity]

    if not org_facts:
        return ""

    # Organize by category
    leadership = [f for f in org_facts if f.category == "leadership"]
    teams = [f for f in org_facts if f.category in ("staffing", "team", "teams", "central_it", "it_team")]
    vendors = [f for f in org_facts if f.category in ("vendors", "outsourcing", "msp")]
    budget = [f for f in org_facts if f.category in ("budget", "costs", "spending")]

    html_parts = []

    # Leadership section
    if leadership:
        rows = []
        for f in leadership:
            name = f.details.get('name', 'Not specified')
            role = f.item
            reports_to = f.details.get('reports_to', '-')
            tenure = f.details.get('tenure', '-')
            rows.append(f'''
                <tr>
                    <td><strong>{role}</strong></td>
                    <td>{name}</td>
                    <td>{reports_to}</td>
                    <td>{tenure}</td>
                </tr>''')

        html_parts.append(f'''
        <div class="org-chart-section">
            <h4>IT Leadership</h4>
            <table class="org-chart-table">
                <thead>
                    <tr>
                        <th>Role</th>
                        <th>Name</th>
                        <th>Reports To</th>
                        <th>Tenure</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>''')

    # Teams section
    if teams:
        rows = []
        for f in teams:
            team_name = f.item
            headcount = f.details.get('headcount', f.details.get('count', '-'))
            personnel_cost = f.details.get('personnel_cost', f.details.get('cost', None))
            outsourced_pct = f.details.get('outsourced_percentage', f.details.get('outsourced', None))

            # Format personnel cost
            if personnel_cost and isinstance(personnel_cost, (int, float)):
                cost_str = f"${personnel_cost:,.0f}"
            else:
                cost_str = str(personnel_cost) if personnel_cost else '-'

            # Format outsourced percentage
            if outsourced_pct is not None:
                outsourced_str = f"{outsourced_pct}%"
            else:
                outsourced_str = '-'

            rows.append(f'''
                <tr>
                    <td><strong>{team_name}</strong></td>
                    <td class="count">{headcount}</td>
                    <td>{cost_str}</td>
                    <td>{outsourced_str}</td>
                </tr>''')

        html_parts.append(f'''
        <div class="org-chart-section">
            <h4>IT Teams</h4>
            <table class="org-chart-table">
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Headcount</th>
                        <th>Personnel Cost</th>
                        <th>Outsourced</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>''')

    # Vendors/Outsourcing section
    if vendors:
        rows = []
        for f in vendors:
            vendor_name = f.item
            services = f.details.get('services', f.details.get('scope', '-'))
            contract_end = f.details.get('contract_expiry', f.details.get('contract_end', '-'))
            spend = f.details.get('annual_spend', f.details.get('spend', '-'))
            rows.append(f'''
                <tr>
                    <td><strong>{vendor_name}</strong></td>
                    <td>{services}</td>
                    <td>{contract_end}</td>
                    <td>{spend}</td>
                </tr>''')

        html_parts.append(f'''
        <div class="org-chart-section">
            <h4>Key Vendors / Outsourcing</h4>
            <table class="org-chart-table">
                <thead>
                    <tr>
                        <th>Vendor</th>
                        <th>Services</th>
                        <th>Contract End</th>
                        <th>Annual Spend</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
        </div>''')

    # Budget/Summary section
    if budget:
        budget_items = []
        for f in budget:
            details = f.details
            if 'total_it_budget' in details:
                val = details['total_it_budget']
                if isinstance(val, (int, float)):
                    budget_items.append(f"<strong>IT Budget:</strong> ${val:,.0f}")
            if 'percent_of_revenue' in details:
                budget_items.append(f"<strong>IT % of Revenue:</strong> {details['percent_of_revenue']}%")
            if 'total_personnel_cost' in details:
                val = details['total_personnel_cost']
                if isinstance(val, (int, float)):
                    budget_items.append(f"<strong>Total Personnel Cost:</strong> ${val:,.0f}")
            if 'total_it_headcount' in details:
                budget_items.append(f"<strong>Total IT Headcount:</strong> {details['total_it_headcount']}")
            if 'outsourced_percentage' in details:
                budget_items.append(f"<strong>Overall Outsourced:</strong> {details['outsourced_percentage']}%")

        if budget_items:
            html_parts.append(f'''
        <div class="org-chart-section org-budget-summary">
            <h4>IT Budget Summary</h4>
            <div class="budget-metrics">
                {"<br>".join(budget_items)}
            </div>
        </div>''')

    # Also add overall org metrics if we have outsourcing fact
    outsourcing_facts = [f for f in org_facts if f.category == 'outsourcing']
    for f in outsourcing_facts:
        details = f.details
        if 'total_it_headcount' in details or 'outsourced_percentage' in details:
            metrics = []
            if 'total_it_headcount' in details:
                metrics.append(f"<strong>Total IT Headcount:</strong> {details['total_it_headcount']}")
            if 'outsourced_percentage' in details:
                metrics.append(f"<strong>Overall Outsourced:</strong> {details['outsourced_percentage']}%")
            if metrics and not budget:  # Don't duplicate if budget section exists
                html_parts.append(f'''
        <div class="org-chart-section org-summary">
            <h4>Organization Summary</h4>
            <div class="org-metrics">
                {"<br>".join(metrics)}
            </div>
        </div>''')
            break

    if not html_parts:
        return ""

    return f'<div class="org-chart-container">{"".join(html_parts)}</div>'


def _build_app_landscape_html(fact_store: FactStore, entity: str = "target") -> str:
    """
    Build an Enterprise Application Landscape table from fact store data.

    Args:
        fact_store: The fact store containing application facts
        entity: "target" or "buyer" to filter by

    Returns:
        HTML table for app landscape, or empty string if no data
    """
    # Filter application facts by entity
    app_facts = [f for f in fact_store.facts
                 if f.domain == "applications" and getattr(f, 'entity', 'target') == entity]

    if not app_facts:
        return ""

    # Organize by category
    categories = {}
    for f in app_facts:
        cat = f.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    # Category display order and labels
    category_order = [
        ('erp', 'ERP / Core Business'),
        ('crm', 'CRM / Sales'),
        ('hcm', 'HCM / HR'),
        ('finance', 'Finance'),
        ('custom', 'Custom / Proprietary'),
        ('productivity', 'Productivity'),
        ('integration', 'Integration / Middleware'),
        ('database', 'Database'),
        ('saas', 'SaaS Applications'),
    ]

    html_parts = []

    # Build summary table
    summary_rows = []
    for cat_key, cat_label in category_order:
        if cat_key in categories:
            apps = categories[cat_key]
            count = len(apps)
            vendors = list(set(f.details.get('vendor', 'Unknown') for f in apps))[:3]
            vendor_str = ', '.join(vendors)
            if len(vendors) >= 3:
                vendor_str += '...'
            summary_rows.append(f'''
                <tr>
                    <td><strong>{cat_label}</strong></td>
                    <td class="count">{count}</td>
                    <td>{vendor_str}</td>
                </tr>''')

    # Add any remaining categories not in the order list
    for cat_key, apps in categories.items():
        if cat_key not in [c[0] for c in category_order]:
            count = len(apps)
            vendors = list(set(f.details.get('vendor', 'Unknown') for f in apps))[:3]
            vendor_str = ', '.join(vendors)
            summary_rows.append(f'''
                <tr>
                    <td><strong>{cat_key.replace('_', ' ').title()}</strong></td>
                    <td class="count">{count}</td>
                    <td>{vendor_str}</td>
                </tr>''')

    if summary_rows:
        html_parts.append(f'''
        <div class="app-landscape-section">
            <h4>Application Portfolio Summary</h4>
            <table class="app-landscape-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                        <th>Key Vendors</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(summary_rows)}
                </tbody>
            </table>
        </div>''')

    # Build detailed app table for key applications
    key_apps = []
    for f in app_facts:
        criticality = f.details.get('criticality', f.details.get('business_criticality', '')).lower()
        user_count = f.details.get('user_count', 0)
        if criticality in ('high', 'critical') or (isinstance(user_count, int) and user_count > 100):
            key_apps.append(f)

    if key_apps:
        detail_rows = []
        for f in key_apps[:10]:  # Limit to top 10
            app_name = f.item
            vendor = f.details.get('vendor', '-')
            version = f.details.get('version', '-')
            deployment = f.details.get('deployment', '-')
            users = f.details.get('user_count', '-')
            criticality = f.details.get('criticality', f.details.get('business_criticality', '-'))
            detail_rows.append(f'''
                <tr>
                    <td><strong>{app_name}</strong></td>
                    <td>{vendor}</td>
                    <td>{version}</td>
                    <td>{deployment}</td>
                    <td class="count">{users}</td>
                    <td><span class="criticality-{criticality.lower() if isinstance(criticality, str) else 'unknown'}">{criticality}</span></td>
                </tr>''')

        html_parts.append(f'''
        <div class="app-landscape-section">
            <h4>Key Business Applications</h4>
            <table class="app-landscape-table">
                <thead>
                    <tr>
                        <th>Application</th>
                        <th>Vendor</th>
                        <th>Version</th>
                        <th>Deployment</th>
                        <th>Users</th>
                        <th>Criticality</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(detail_rows)}
                </tbody>
            </table>
        </div>''')

    if not html_parts:
        return ""

    return f'<div class="app-landscape-container">{"".join(html_parts)}</div>'


def generate_presentation(
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    output_dir: Path,
    target_name: str = "Target Company",
    timestamp: str = None
) -> Path:
    """
    Generate an investment thesis presentation.

    Args:
        fact_store: Discovered facts
        reasoning_store: Analysis findings (risks, work items)
        output_dir: Where to save the presentation
        target_name: Name of the target company
        timestamp: Optional timestamp for filename

    Returns:
        Path to the generated HTML file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = output_dir / f"investment_thesis_{timestamp}.html"

    # Build presentation data
    exec_summary = _build_executive_summary(fact_store, reasoning_store, target_name)
    domain_slides = _build_domain_slides(fact_store, reasoning_store)
    work_plan = _build_work_plan_slide(reasoning_store)
    open_questions = _build_open_questions_slide(fact_store, reasoning_store)

    # Generate HTML
    html = _render_presentation(
        target_name=target_name,
        exec_summary=exec_summary,
        domain_slides=domain_slides,
        work_plan=work_plan,
        open_questions=open_questions,
        timestamp=timestamp
    )

    output_file.write_text(html)
    return output_file


def _build_executive_summary(
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    target_name: str
) -> Dict[str, Any]:
    """Build executive summary slide content."""

    # Calculate totals
    total_facts = len(fact_store.facts)
    total_gaps = len(fact_store.gaps)
    total_risks = len(reasoning_store.risks)
    total_work_items = len(reasoning_store.work_items)

    # Cost summary by phase
    cost_by_phase = {
        'Day_1': {'low': 0, 'high': 0, 'count': 0},
        'Day_100': {'low': 0, 'high': 0, 'count': 0},
        'Post_100': {'low': 0, 'high': 0, 'count': 0}
    }

    for wi in reasoning_store.work_items:
        if wi.phase in cost_by_phase:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})
            cost_by_phase[wi.phase]['low'] += cost_range['low']
            cost_by_phase[wi.phase]['high'] += cost_range['high']
            cost_by_phase[wi.phase]['count'] += 1

    total_low = sum(p['low'] for p in cost_by_phase.values())
    total_high = sum(p['high'] for p in cost_by_phase.values())

    # Top risks (critical and high severity)
    top_risks = [r for r in reasoning_store.risks if r.severity in ('critical', 'high')]
    top_risks = sorted(top_risks, key=lambda r: 0 if r.severity == 'critical' else 1)[:5]

    # Count by severity
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for risk in reasoning_store.risks:
        if risk.severity in severity_counts:
            severity_counts[risk.severity] += 1

    # Identify key systems from facts
    key_systems = _identify_key_systems(fact_store)

    # Generate bottom line assessment
    bottom_line = _generate_bottom_line(
        total_risks, severity_counts, total_low, total_high, total_gaps
    )

    return {
        'target_name': target_name,
        'metrics': {
            'facts': total_facts,
            'gaps': total_gaps,
            'risks': total_risks,
            'work_items': total_work_items
        },
        'severity_counts': severity_counts,
        'key_systems': key_systems,
        'top_risks': top_risks,
        'cost_by_phase': cost_by_phase,
        'total_cost': {'low': total_low, 'high': total_high},
        'bottom_line': bottom_line
    }


def _identify_key_systems(fact_store: FactStore) -> List[Dict[str, str]]:
    """Identify key systems from facts for executive summary."""
    key_systems = []

    # Look for major system categories
    priority_categories = [
        ('erp', 'ERP'),
        ('crm', 'CRM'),
        ('identity', 'Identity'),
        ('api_identity', 'Identity'),
        ('cloud', 'Cloud'),
        ('hosting', 'Hosting'),
        ('email', 'Email/Collab')
    ]

    for category, label in priority_categories:
        for fact in fact_store.facts:
            if fact.category == category:
                key_systems.append({
                    'label': label,
                    'system': fact.item,
                    'source': fact.evidence.get('source_section', '') if fact.evidence else ''
                })
                break  # Only first match per category

    return key_systems[:6]  # Limit to 6 key systems


def _generate_bottom_line(
    total_risks: int,
    severity_counts: Dict[str, int],
    total_low: float,
    total_high: float,
    total_gaps: int
) -> str:
    """Generate the bottom line assessment statement."""

    # Determine complexity level
    critical_high = severity_counts['critical'] + severity_counts['high']

    if critical_high >= 5 or severity_counts['critical'] >= 2:
        complexity = "High-complexity integration"
        outlook = "Significant remediation work required before or immediately after close."
    elif critical_high >= 2:
        complexity = "Mid-complexity integration"
        outlook = "Core systems are functional but require attention. Manageable with proper planning."
    else:
        complexity = "Lower-complexity integration"
        outlook = "IT environment is relatively mature. Focus will be on optimization rather than remediation."

    # Cost statement
    if total_high > 0:
        cost_stmt = f"Expected integration cost: ${total_low:,.0f} - ${total_high:,.0f}"
    else:
        cost_stmt = "Cost estimates pending detailed analysis."

    # Gap warning
    gap_warning = ""
    if total_gaps >= 10:
        gap_warning = f" Note: {total_gaps} information gaps remain - estimates may shift as visibility improves."
    elif total_gaps >= 5:
        gap_warning = f" {total_gaps} information gaps should be resolved before finalizing estimates."

    return f"{complexity}. {outlook} {cost_stmt}.{gap_warning}"


def _build_domain_slides(
    fact_store: FactStore,
    reasoning_store: ReasoningStore
) -> List[SlideContent]:
    """Build slides for each domain."""

    slides = []

    for domain_key, config in DOMAIN_CONFIG.items():
        # Get domain facts
        domain_facts = [f for f in fact_store.facts if f.domain == domain_key]
        domain_gaps = [g for g in fact_store.gaps if g.domain == domain_key]
        domain_risks = [r for r in reasoning_store.risks if r.domain == domain_key]
        domain_work_items = [w for w in reasoning_store.work_items if w.domain == domain_key]

        if not domain_facts and not domain_risks:
            continue  # Skip domains with no data

        # Calculate domain cost
        domain_cost_low = 0
        domain_cost_high = 0
        for wi in domain_work_items:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})
            domain_cost_low += cost_range['low']
            domain_cost_high += cost_range['high']

        # Generate "So What" - the key implication
        so_what = _generate_so_what(domain_key, domain_facts, domain_risks, domain_gaps)

        # Key considerations (top findings)
        considerations = _extract_considerations(domain_facts, domain_risks, domain_gaps, domain=domain_key)

        # The narrative story
        narrative = _generate_narrative(domain_key, domain_facts, domain_risks, domain_work_items)

        # Source documents
        sources = _extract_sources(domain_facts)

        # Cost impact
        cost_impact = None
        if domain_cost_high > 0:
            cost_impact = f"${domain_cost_low:,.0f} - ${domain_cost_high:,.0f}"

        # Build extra content for specific domains (org chart, app landscape)
        extra_content = None
        if domain_key == 'organization':
            # Auto-detect which entity has data
            entity = _detect_primary_entity(fact_store, domain_key)
            extra_content = _build_org_chart_html(fact_store, entity=entity)
        elif domain_key == 'applications':
            entity = _detect_primary_entity(fact_store, domain_key)
            extra_content = _build_app_landscape_html(fact_store, entity=entity)

        slides.append(SlideContent(
            id=domain_key,
            title=config['title'],
            so_what=so_what,
            considerations=considerations,
            narrative=narrative,
            cost_impact=cost_impact,
            sources=sources,
            metrics={
                'facts': len(domain_facts),
                'gaps': len(domain_gaps),
                'risks': len(domain_risks),
                'work_items': len(domain_work_items)
            },
            extra_content=extra_content
        ))

    return slides


def _generate_so_what(
    domain: str,
    facts: List,
    risks: List,
    gaps: List
) -> str:
    """Generate the 'So What' statement for a domain."""

    # Count high-severity issues
    critical_risks = [r for r in risks if r.severity == 'critical']
    high_risks = [r for r in risks if r.severity == 'high']
    high_gaps = [g for g in gaps if g.importance in ('critical', 'high')]

    # Domain-specific logic
    if domain == 'infrastructure':
        if critical_risks or len(high_risks) >= 2:
            return "Infrastructure requires significant modernization. Plan for remediation costs within first 12 months."
        elif high_gaps:
            return "Infrastructure documentation is incomplete. Key decisions blocked until visibility improves."
        elif facts:
            cloud_facts = [f for f in facts if f.category == 'cloud']
            if cloud_facts:
                return "Hybrid cloud footprint in place. Focus will be on governance and potential consolidation."
            return "On-premises infrastructure. Evaluate cloud migration path as part of integration planning."
        return "Limited infrastructure visibility. Prioritize discovery before integration planning."

    elif domain == 'network':
        if high_gaps or len(gaps) >= 3:
            return "Network architecture undocumented. Significant blind spot for integration planning."
        elif critical_risks or high_risks:
            return "Network security gaps identified. Day 1 remediation required."
        return "Network infrastructure documented. Standard integration considerations apply."

    elif domain == 'cybersecurity':
        pam_gap = any('pam' in g.category.lower() or 'privileged' in g.description.lower()
                      for g in gaps)
        ir_gap = any('incident' in g.description.lower() or 'response' in g.description.lower()
                     for g in gaps)

        if critical_risks:
            return "Critical security gaps require immediate attention. Budget for Day 1 remediation."
        elif pam_gap and ir_gap:
            return "No PAM solution, no documented incident response. Day 1 security work required."
        elif pam_gap:
            return "Privileged access management absent. Security control gap needs addressing."
        elif high_risks:
            return "Security foundation exists but gaps need attention. Plan for security improvements."
        return "Security posture appears adequate. Standard due diligence applies."

    elif domain == 'applications':
        erp_facts = [f for f in facts if f.category == 'erp']
        if len(erp_facts) > 1:
            systems = [f.item for f in erp_facts]
            return f"Dual-ERP environment ({', '.join(systems[:2])}). Rationalization decision required."
        elif critical_risks or high_risks:
            return "Application landscape has significant risks. Modernization planning needed."
        elif erp_facts:
            return f"Single ERP platform ({erp_facts[0].item}). Integration path is clearer."
        return "Application inventory incomplete. Discovery needed before planning."

    elif domain == 'identity_access':
        pam_risks = [r for r in risks if 'pam' in r.category.lower() or 'privileged' in r.title.lower()]
        if pam_risks:
            return "No privileged access controls. Immediate security work needed."
        elif critical_risks or high_risks:
            return "Identity infrastructure has gaps. Plan for Day 1 remediation."
        elif facts:
            return "Identity platform deployed. Integration planning can proceed."
        return "Identity architecture unclear. Discovery required."

    elif domain == 'organization':
        # Extract key org metrics for the So What
        total_headcount = None
        total_budget = None
        outsourced_pct = None

        for f in facts:
            details = f.details or {}
            if 'total_it_headcount' in details:
                total_headcount = details['total_it_headcount']
            if 'total_it_budget' in details:
                total_budget = details['total_it_budget']
            if f.category == 'outsourcing' and 'outsourced_percentage' in details:
                outsourced_pct = details['outsourced_percentage']

        # Build a metrics-rich So What
        parts = []
        if total_headcount:
            parts.append(f"{total_headcount} IT headcount")
        if total_budget and isinstance(total_budget, (int, float)):
            parts.append(f"${total_budget/1000000:.1f}M budget")
        if outsourced_pct:
            parts.append(f"{outsourced_pct}% outsourced")

        if parts:
            metrics_str = ", ".join(parts)
            if outsourced_pct and outsourced_pct > 20:
                return f"IT organization: {metrics_str}. Significant outsourcing requires TSA/transition planning."
            elif high_risks:
                return f"IT organization: {metrics_str}. Organizational gaps may impact integration velocity."
            else:
                return f"IT organization: {metrics_str}. Standard integration considerations."

        # Fallback if no metrics
        if high_risks:
            return "Organizational gaps may impact integration velocity. Plan accordingly."
        return "IT organization structure documented. Standard integration considerations."

    return "Domain analysis complete. See details below."


def _extract_considerations(facts: List, risks: List, gaps: List, domain: str = None) -> List[str]:
    """Extract 3-5 key considerations for a domain."""

    considerations = []

    # For organization domain, lead with key metrics
    if domain == 'organization':
        for fact in facts:
            details = fact.details or {}
            # Budget/headcount summary
            if 'total_it_headcount' in details:
                considerations.append(f"Total IT Headcount: {details['total_it_headcount']}")
            if 'total_it_budget' in details:
                val = details['total_it_budget']
                if isinstance(val, (int, float)):
                    considerations.append(f"IT Budget: ${val:,.0f}")
            if 'outsourced_percentage' in details and fact.category == 'outsourcing':
                considerations.append(f"Overall Outsourced: {details['outsourced_percentage']}%")
            # Team details
            if fact.category in ('central_it', 'staffing', 'team') and 'headcount' in details:
                hc = details['headcount']
                outsourced = details.get('outsourced_percentage')
                if outsourced:
                    considerations.append(f"{fact.item}: {hc} headcount ({outsourced}% outsourced)")
                else:
                    considerations.append(f"{fact.item}: {hc} headcount")

        # If we have good org facts, limit risks/gaps
        if len(considerations) >= 3:
            # Add top risk if critical/high
            for risk in sorted(risks, key=lambda r: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(r.severity, 4)):
                if risk.severity in ('critical', 'high'):
                    considerations.append(f"Risk: {risk.title}")
                    break
            return considerations[:5]

    # Add top risks first (most important)
    for risk in sorted(risks, key=lambda r: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(r.severity, 4)):
        if len(considerations) >= 5:
            break
        considerations.append(f"{risk.title}")

    # Add critical gaps
    for gap in sorted(gaps, key=lambda g: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(g.importance, 4)):
        if len(considerations) >= 5:
            break
        considerations.append(f"Gap: {gap.description}")

    # Add key facts if we have room
    if len(considerations) < 3 and facts:
        for fact in facts[:3]:
            if len(considerations) >= 5:
                break
            detail_str = ""
            if fact.details:
                # Pull out interesting details - expanded list
                for key in ['version', 'users', 'headcount', 'vendor', 'location', 'count', 'vm_count', 'capacity']:
                    if key in fact.details:
                        val = fact.details[key]
                        if isinstance(val, (int, float)) and val > 1000:
                            detail_str = f" ({val:,.0f})"
                        else:
                            detail_str = f" ({val})"
                        break
            considerations.append(f"{fact.item}{detail_str}")

    return considerations[:5]


def _generate_narrative(
    domain: str,
    facts: List,
    risks: List,
    work_items: List
) -> str:
    """Generate the narrative 'story' for a domain."""

    if not facts and not risks:
        return "Insufficient data available for this domain. Additional discovery required."

    # Build narrative parts
    parts = []

    # Current state
    if facts:
        fact_summary = _summarize_facts(facts)
        if fact_summary:
            parts.append(fact_summary)

    # Key concerns
    if risks:
        risk_summary = _summarize_risks(risks)
        if risk_summary:
            parts.append(risk_summary)

    # Work implications
    if work_items:
        work_summary = _summarize_work(work_items)
        if work_summary:
            parts.append(work_summary)

    if not parts:
        return "Analysis complete. No significant concerns identified."

    return " ".join(parts)


def _summarize_facts(facts: List) -> str:
    """Summarize key facts into narrative."""
    if not facts:
        return ""

    # Group by category
    by_category = {}
    for f in facts:
        by_category.setdefault(f.category, []).append(f)

    if len(facts) <= 3:
        items = [f.item for f in facts]
        return f"Key systems include {', '.join(items)}."
    else:
        return f"The environment includes {len(facts)} documented systems across {len(by_category)} categories."


def _summarize_risks(risks: List) -> str:
    """Summarize risks into narrative."""
    if not risks:
        return ""

    critical = [r for r in risks if r.severity == 'critical']
    high = [r for r in risks if r.severity == 'high']

    if critical:
        return f"Critical concern: {critical[0].title}. This requires immediate attention."
    elif high:
        if len(high) == 1:
            return f"Primary concern is {high[0].title.lower()}."
        else:
            return f"Key concerns include {high[0].title.lower()} and {len(high)-1} other high-priority items."
    else:
        return f"{len(risks)} moderate risks identified for tracking."


def _summarize_work(work_items: List) -> str:
    """Summarize work items into narrative."""
    if not work_items:
        return ""

    day1 = [w for w in work_items if w.phase == 'Day_1']
    day100 = [w for w in work_items if w.phase == 'Day_100']

    if day1:
        return f"Plan for {len(day1)} Day 1 work items requiring immediate attention."
    elif day100:
        return f"{len(day100)} items targeted for the Day 100 plan."
    return ""


def _extract_sources(facts: List) -> List[str]:
    """Extract unique source documents from facts."""
    sources = set()
    for f in facts:
        if f.evidence and f.evidence.get('source_section'):
            sources.add(f.evidence['source_section'])
    return sorted(list(sources))[:5]  # Limit to 5 sources


def _build_work_plan_slide(reasoning_store: ReasoningStore) -> Dict[str, Any]:
    """Build the work plan slide."""

    phases = {
        'Day_1': {'items': [], 'low': 0, 'high': 0},
        'Day_100': {'items': [], 'low': 0, 'high': 0},
        'Post_100': {'items': [], 'low': 0, 'high': 0}
    }

    for wi in reasoning_store.work_items:
        if wi.phase in phases:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})
            phases[wi.phase]['items'].append({
                'id': wi.finding_id,
                'title': wi.title,
                'domain': wi.domain,
                'owner': wi.owner_type,
                'priority': wi.priority,
                'cost_low': cost_range['low'],
                'cost_high': cost_range['high']
            })
            phases[wi.phase]['low'] += cost_range['low']
            phases[wi.phase]['high'] += cost_range['high']

    # Sort items by priority within each phase
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    for phase in phases.values():
        phase['items'].sort(key=lambda x: priority_order.get(x['priority'], 4))

    total_low = sum(p['low'] for p in phases.values())
    total_high = sum(p['high'] for p in phases.values())

    return {
        'phases': phases,
        'total': {'low': total_low, 'high': total_high},
        'total_items': len(reasoning_store.work_items)
    }


def _build_open_questions_slide(
    fact_store: FactStore,
    reasoning_store: ReasoningStore
) -> Dict[str, Any]:
    """Build the open questions slide."""

    # High-importance gaps are open questions
    critical_gaps = [g for g in fact_store.gaps if g.importance == 'critical']
    high_gaps = [g for g in fact_store.gaps if g.importance == 'high']

    # Group gaps by domain
    gaps_by_domain = {}
    for gap in fact_store.gaps:
        gaps_by_domain.setdefault(gap.domain, []).append(gap)

    return {
        'critical_gaps': critical_gaps,
        'high_gaps': high_gaps,
        'total_gaps': len(fact_store.gaps),
        'gaps_by_domain': gaps_by_domain,
        'domains_with_gaps': len(gaps_by_domain)
    }


def _render_presentation(
    target_name: str,
    exec_summary: Dict,
    domain_slides: List[SlideContent],
    work_plan: Dict,
    open_questions: Dict,
    timestamp: str
) -> str:
    """Render the complete HTML presentation."""

    # Build navigation
    nav_items = ['executive-summary']
    nav_items.extend([s.id for s in domain_slides])
    nav_items.extend(['work-plan', 'open-questions'])

    nav_html = _build_navigation(nav_items, domain_slides)

    # Build slides
    exec_html = _render_executive_slide(exec_summary)
    domain_html = "\n".join(_render_domain_slide(s) for s in domain_slides)
    work_html = _render_work_plan_slide(work_plan)
    questions_html = _render_open_questions_slide(open_questions)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - IT Investment Thesis</title>
    <style>
{_get_presentation_css()}
    </style>
</head>
<body>
    <div class="presentation">
        {nav_html}

        <main class="slides">
            {exec_html}
            {domain_html}
            {work_html}
            {questions_html}
        </main>
    </div>

    <script>
{_get_presentation_js()}
    </script>
</body>
</html>'''


def _build_navigation(nav_items: List[str], domain_slides: List[SlideContent]) -> str:
    """Build the slide navigation."""

    links = ['<a href="#executive-summary" class="nav-item active">Executive Summary</a>']

    for slide in domain_slides:
        config = DOMAIN_CONFIG.get(slide.id, {})
        icon = config.get('icon', '📋')
        links.append(f'<a href="#{slide.id}" class="nav-item">{icon} {slide.title}</a>')

    links.append('<a href="#work-plan" class="nav-item">📊 Work Plan</a>')
    links.append('<a href="#open-questions" class="nav-item">❓ Open Questions</a>')

    return f'''
    <nav class="nav">
        <div class="nav-brand">IT Investment Thesis</div>
        <div class="nav-items">
            {"".join(links)}
        </div>
        <div class="nav-controls">
            <button onclick="prevSlide()" class="nav-btn">← Prev</button>
            <span class="slide-counter">1 / {len(nav_items)}</span>
            <button onclick="nextSlide()" class="nav-btn">Next →</button>
        </div>
    </nav>'''


def _render_executive_slide(data: Dict) -> str:
    """Render the executive summary slide."""

    # Key metrics
    metrics = data['metrics']
    severity = data['severity_counts']
    cost = data['total_cost']
    cost_by_phase = data['cost_by_phase']

    # Key systems
    systems_html = ""
    if data['key_systems']:
        system_items = []
        for sys in data['key_systems']:
            source_note = f'<span class="source-note">{sys["source"]}</span>' if sys['source'] else ''
            system_items.append(f'<li><strong>{sys["label"]}:</strong> {sys["system"]} {source_note}</li>')
        systems_html = f'<ul class="key-systems">{"".join(system_items)}</ul>'

    # Top risks
    risks_html = ""
    if data['top_risks']:
        risk_items = []
        for risk in data['top_risks']:
            risk_items.append(f'''
            <div class="risk-item risk-{risk.severity}">
                <span class="risk-badge">{risk.severity.upper()}</span>
                <span class="risk-title">{risk.title}</span>
                <span class="risk-domain">{risk.domain.replace("_", " ").title()}</span>
            </div>''')
        risks_html = f'<div class="top-risks">{"".join(risk_items)}</div>'

    return f'''
    <section id="executive-summary" class="slide slide-executive">
        <div class="slide-header">
            <h1>{data['target_name']}</h1>
            <p class="slide-subtitle">IT Due Diligence - Investment Thesis Summary</p>
        </div>

        <div class="slide-content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics['facts']}</div>
                    <div class="metric-label">Facts Discovered</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['gaps']}</div>
                    <div class="metric-label">Information Gaps</div>
                </div>
                <div class="metric-card metric-warning">
                    <div class="metric-value">{severity['critical'] + severity['high']}</div>
                    <div class="metric-label">Critical/High Risks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['work_items']}</div>
                    <div class="metric-label">Work Items</div>
                </div>
            </div>

            <div class="two-column">
                <div class="column">
                    <h3>Key Systems</h3>
                    {systems_html if systems_html else '<p class="no-data">Key systems pending identification</p>'}
                </div>
                <div class="column">
                    <h3>Top Risks</h3>
                    {risks_html if risks_html else '<p class="no-data">No critical or high risks identified</p>'}
                </div>
            </div>

            <div class="cost-summary">
                <h3>Integration Cost Estimate</h3>
                <table class="cost-table">
                    <thead>
                        <tr>
                            <th>Phase</th>
                            <th>Items</th>
                            <th>Cost Range</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Day 1</td>
                            <td>{cost_by_phase['Day_1']['count']}</td>
                            <td class="cost">${cost_by_phase['Day_1']['low']:,.0f} - ${cost_by_phase['Day_1']['high']:,.0f}</td>
                        </tr>
                        <tr>
                            <td>Day 100</td>
                            <td>{cost_by_phase['Day_100']['count']}</td>
                            <td class="cost">${cost_by_phase['Day_100']['low']:,.0f} - ${cost_by_phase['Day_100']['high']:,.0f}</td>
                        </tr>
                        <tr>
                            <td>Post 100</td>
                            <td>{cost_by_phase['Post_100']['count']}</td>
                            <td class="cost">${cost_by_phase['Post_100']['low']:,.0f} - ${cost_by_phase['Post_100']['high']:,.0f}</td>
                        </tr>
                        <tr class="total-row">
                            <td><strong>Total</strong></td>
                            <td><strong>{metrics['work_items']}</strong></td>
                            <td class="cost"><strong>${cost['low']:,.0f} - ${cost['high']:,.0f}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="bottom-line">
                <h3>Bottom Line</h3>
                <p class="assessment">{data['bottom_line']}</p>
            </div>
        </div>
    </section>'''


def _render_domain_slide(slide: SlideContent) -> str:
    """Render a domain slide."""

    config = DOMAIN_CONFIG.get(slide.id, {})
    icon = config.get('icon', '📋')

    # Considerations list
    considerations_html = ""
    if slide.considerations:
        items = [f'<li>{c}</li>' for c in slide.considerations]
        considerations_html = f'<ul class="considerations">{"".join(items)}</ul>'

    # Sources callout
    sources_html = ""
    if slide.sources:
        source_items = [f'<span class="source-tag">{s}</span>' for s in slide.sources]
        sources_html = f'''
        <div class="sources-callout">
            <span class="sources-label">Sources:</span>
            {"".join(source_items)}
        </div>'''

    # Cost impact
    cost_html = ""
    if slide.cost_impact:
        cost_html = f'''
        <div class="cost-impact">
            <span class="cost-label">Cost Impact:</span>
            <span class="cost-value">{slide.cost_impact}</span>
        </div>'''

    # Metrics sidebar
    metrics_html = ""
    if slide.metrics:
        metrics_html = f'''
        <div class="slide-metrics">
            <div class="mini-metric"><span class="mm-value">{slide.metrics['facts']}</span> facts</div>
            <div class="mini-metric"><span class="mm-value">{slide.metrics['gaps']}</span> gaps</div>
            <div class="mini-metric"><span class="mm-value">{slide.metrics['risks']}</span> risks</div>
            <div class="mini-metric"><span class="mm-value">{slide.metrics['work_items']}</span> work items</div>
        </div>'''

    # Open questions section
    open_questions_html = ""
    if slide.open_questions:
        question_items = [f'<li>{q}</li>' for q in slide.open_questions[:5]]
        total_gaps = slide.metrics.get('gaps', 0) if slide.metrics else 0
        more_text = f' <span class="more-gaps">(+{total_gaps - 5} more in VDR)</span>' if total_gaps > 5 else ''
        open_questions_html = f'''
        <div class="open-questions-section">
            <h4>Open Questions{more_text}</h4>
            <ul class="open-questions-list">{"".join(question_items)}</ul>
        </div>'''

    return f'''
    <section id="{slide.id}" class="slide slide-domain">
        <div class="slide-header">
            <h2>{icon} {slide.title}</h2>
            {metrics_html}
        </div>

        <div class="so-what">
            <div class="so-what-label">SO WHAT</div>
            <p class="so-what-text">{slide.so_what}</p>
        </div>

        <div class="slide-body">
            <div class="considerations-section">
                <h3>Key Considerations</h3>
                {considerations_html if considerations_html else '<p class="no-data">No specific considerations identified</p>'}
                {open_questions_html}
            </div>

            <div class="narrative-section">
                <h3>The Story</h3>
                <p class="narrative">{slide.narrative}</p>
                {slide.extra_content if slide.extra_content else ''}
            </div>
        </div>

        <div class="slide-footer">
            {cost_html}
            {sources_html}
        </div>
    </section>'''


def _render_work_plan_slide(data: Dict) -> str:
    """Render the work plan slide."""

    phases = data['phases']

    def render_phase(phase_name: str, phase_data: Dict, label: str) -> str:
        if not phase_data['items']:
            return f'''
            <div class="phase-section phase-{phase_name.lower().replace('_', '')}">
                <h4>{label}</h4>
                <p class="no-data">No items in this phase</p>
            </div>'''

        rows = []
        for item in phase_data['items'][:5]:  # Limit to top 5 per phase
            rows.append(f'''
            <tr>
                <td class="wi-id">{item['id']}</td>
                <td>{item['title'][:50]}{'...' if len(item['title']) > 50 else ''}</td>
                <td>{item['domain'].replace('_', ' ').title()}</td>
                <td>{item['owner'].title()}</td>
                <td class="cost">${item['cost_low']:,.0f} - ${item['cost_high']:,.0f}</td>
            </tr>''')

        more_note = ""
        if len(phase_data['items']) > 5:
            more_note = f'<p class="more-items">+ {len(phase_data["items"]) - 5} more items</p>'

        return f'''
        <div class="phase-section phase-{phase_name.lower().replace('_', '')}">
            <div class="phase-header">
                <h4>{label}</h4>
                <span class="phase-total">${phase_data['low']:,.0f} - ${phase_data['high']:,.0f}</span>
            </div>
            <table class="work-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Work Item</th>
                        <th>Domain</th>
                        <th>Owner</th>
                        <th>Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>
            {more_note}
        </div>'''

    return f'''
    <section id="work-plan" class="slide slide-workplan">
        <div class="slide-header">
            <h2>📊 Integration Work Plan</h2>
            <div class="total-cost">
                Total: <strong>${data['total']['low']:,.0f} - ${data['total']['high']:,.0f}</strong>
            </div>
        </div>

        <div class="slide-content">
            {render_phase('Day_1', phases['Day_1'], 'Day 1 - Immediate')}
            {render_phase('Day_100', phases['Day_100'], 'Day 100 - Near Term')}
            {render_phase('Post_100', phases['Post_100'], 'Post 100 - Long Term')}
        </div>

        <div class="slide-footer">
            <p class="disclaimer">Cost estimates are preliminary and subject to refinement based on additional discovery.</p>
        </div>
    </section>'''


def _render_open_questions_slide(data: Dict) -> str:
    """Render the open questions slide."""

    # Critical gaps
    critical_html = ""
    if data['critical_gaps']:
        items = [f'<li><strong>{g.domain.replace("_", " ").title()}:</strong> {g.description}</li>'
                for g in data['critical_gaps']]
        critical_html = f'''
        <div class="questions-section critical">
            <h3>🔴 Critical - Must Resolve Before Close</h3>
            <ul>{"".join(items)}</ul>
        </div>'''

    # High priority gaps
    high_html = ""
    if data['high_gaps']:
        items = [f'<li><strong>{g.domain.replace("_", " ").title()}:</strong> {g.description}</li>'
                for g in data['high_gaps'][:5]]  # Limit to 5
        more = f'<p class="more-items">+ {len(data["high_gaps"]) - 5} more</p>' if len(data['high_gaps']) > 5 else ''
        high_html = f'''
        <div class="questions-section high">
            <h3>🟠 High Priority - Impacts Planning</h3>
            <ul>{"".join(items)}</ul>
            {more}
        </div>'''

    # Summary by domain
    domain_summary = []
    for domain, gaps in data['gaps_by_domain'].items():
        domain_summary.append(f'<span class="domain-gap-count">{domain.replace("_", " ").title()}: {len(gaps)}</span>')

    return f'''
    <section id="open-questions" class="slide slide-questions">
        <div class="slide-header">
            <h2>❓ Open Questions</h2>
            <div class="gap-summary">
                {data['total_gaps']} gaps across {data['domains_with_gaps']} domains
            </div>
        </div>

        <div class="slide-content">
            {critical_html if critical_html else '<div class="questions-section"><p class="no-data">No critical gaps</p></div>'}
            {high_html if high_html else '<div class="questions-section"><p class="no-data">No high-priority gaps</p></div>'}

            <div class="domain-breakdown">
                <h3>Gaps by Domain</h3>
                <div class="domain-gap-grid">
                    {"".join(domain_summary)}
                </div>
            </div>
        </div>

        <div class="slide-footer">
            <p class="framing">These are the unknowns that could change the numbers. Resolve before finalizing estimates.</p>
        </div>
    </section>'''


def _get_presentation_css() -> str:
    """Return the CSS for the presentation."""
    return '''
        :root {
            --primary: #ea580c;
            --primary-light: #fb923c;
            --secondary: #292524;
            --accent: #f97316;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --bg: #fafaf9;
            --card-bg: #ffffff;
            --text: #1c1917;
            --text-primary: #1c1917;
            --text-muted: #78716c;
            --border: #e7e5e4;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--secondary);
            color: var(--text);
            line-height: 1.6;
        }

        .presentation {
            min-height: 100vh;
        }

        /* Navigation */
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: var(--secondary);
            color: white;
            padding: 0.75rem 2rem;
            display: flex;
            align-items: center;
            gap: 2rem;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .nav-brand {
            font-weight: 700;
            font-size: 1.1rem;
            white-space: nowrap;
        }

        .nav-items {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            flex: 1;
        }

        .nav-item {
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            padding: 0.4rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            transition: all 0.2s;
        }

        .nav-item:hover, .nav-item.active {
            background: rgba(255,255,255,0.1);
            color: white;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .nav-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
        }

        .nav-btn:hover {
            background: var(--primary-light);
        }

        .slide-counter {
            color: rgba(255,255,255,0.7);
            font-size: 0.85rem;
        }

        /* Slides */
        .slides {
            padding-top: 60px;
        }

        .slide {
            min-height: calc(100vh - 60px);
            background: var(--bg);
            padding: 2rem 3rem;
            display: flex;
            flex-direction: column;
        }

        .slide-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid var(--primary);
        }

        .slide-header h1 {
            font-size: 2.5rem;
            color: var(--secondary);
        }

        .slide-header h2 {
            font-size: 1.75rem;
            color: var(--secondary);
        }

        .slide-subtitle {
            color: var(--text-muted);
            font-size: 1.1rem;
            margin-top: 0.25rem;
        }

        .slide-content {
            flex: 1;
        }

        .slide-footer {
            margin-top: auto;
            padding-top: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .metric-card.metric-warning {
            border-left: 4px solid var(--danger);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
        }

        .metric-warning .metric-value {
            color: var(--danger);
        }

        .metric-label {
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        /* Two Column Layout */
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .column h3 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: var(--secondary);
        }

        .key-systems {
            list-style: none;
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1rem;
        }

        .key-systems li {
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
        }

        .key-systems li:last-child {
            border-bottom: none;
        }

        .source-note {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-style: italic;
        }

        /* Risks */
        .top-risks {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .risk-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: var(--card-bg);
            padding: 0.75rem 1rem;
            border-radius: 6px;
            border-left: 4px solid var(--border);
        }

        .risk-critical { border-left-color: var(--danger); }
        .risk-high { border-left-color: var(--warning); }

        .risk-badge {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            background: var(--danger);
            color: white;
        }

        .risk-high .risk-badge {
            background: var(--warning);
        }

        .risk-title {
            flex: 1;
            font-weight: 500;
        }

        .risk-domain {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        /* Cost Table */
        .cost-summary {
            margin-bottom: 2rem;
        }

        .cost-summary h3 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }

        .cost-table {
            width: 100%;
            background: var(--card-bg);
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .cost-table th, .cost-table td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .cost-table th {
            background: var(--bg);
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .cost-table .cost {
            font-family: 'SF Mono', Monaco, monospace;
            text-align: right;
        }

        .cost-table .total-row {
            background: var(--primary);
            color: white;
        }

        .cost-table .total-row td {
            border-bottom: none;
        }

        /* Bottom Line */
        .bottom-line {
            background: var(--secondary);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
        }

        .bottom-line h3 {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
            opacity: 0.8;
        }

        .assessment {
            font-size: 1.1rem;
            line-height: 1.7;
        }

        /* Domain Slides */
        .so-what {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }

        .so-what-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            opacity: 0.8;
            margin-bottom: 0.5rem;
        }

        .so-what-text {
            font-size: 1.25rem;
            font-weight: 500;
            line-height: 1.5;
        }

        .slide-body {
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .considerations-section h3,
        .narrative-section h3 {
            font-size: 1rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
        }

        .considerations {
            list-style: none;
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
        }

        .considerations li {
            padding: 0.75rem 0;
            padding-left: 1.5rem;
            position: relative;
            border-bottom: 1px solid var(--border);
        }

        .considerations li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: var(--primary);
            font-weight: bold;
        }

        .considerations li:last-child {
            border-bottom: none;
        }

        .narrative {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            font-size: 1.05rem;
            line-height: 1.8;
        }

        .slide-metrics {
            display: flex;
            gap: 1rem;
        }

        .mini-metric {
            background: var(--bg);
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .mm-value {
            font-weight: 700;
            color: var(--primary);
        }

        .cost-impact {
            background: var(--card-bg);
            padding: 0.75rem 1rem;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .cost-label {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .cost-value {
            font-family: 'SF Mono', Monaco, monospace;
            font-weight: 600;
            color: var(--primary);
        }

        .sources-callout {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .sources-label {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .source-tag {
            background: var(--bg);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Work Plan Slide */
        .total-cost {
            font-size: 1.1rem;
            color: var(--text-muted);
        }

        .total-cost strong {
            color: var(--primary);
            font-family: 'SF Mono', Monaco, monospace;
        }

        .phase-section {
            background: var(--card-bg);
            border-radius: 8px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }

        .phase-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            background: var(--bg);
            border-bottom: 1px solid var(--border);
        }

        .phase-header h4 {
            font-size: 1rem;
        }

        .phase-total {
            font-family: 'SF Mono', Monaco, monospace;
            font-weight: 600;
            color: var(--primary);
        }

        .phase-day1 .phase-header { border-left: 4px solid var(--danger); }
        .phase-day100 .phase-header { border-left: 4px solid var(--warning); }
        .phase-post100 .phase-header { border-left: 4px solid var(--success); }

        .work-table {
            width: 100%;
            border-collapse: collapse;
        }

        .work-table th, .work-table td {
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .work-table th {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            font-weight: 600;
        }

        .wi-id {
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.85rem;
            color: var(--primary);
        }

        .more-items {
            padding: 0.75rem 1.5rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            font-style: italic;
        }

        .disclaimer {
            font-size: 0.85rem;
            color: var(--text-muted);
            font-style: italic;
        }

        /* Open Questions Slide */
        .gap-summary {
            color: var(--text-muted);
        }

        .questions-section {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .questions-section.critical {
            border-left: 4px solid var(--danger);
        }

        .questions-section.high {
            border-left: 4px solid var(--warning);
        }

        .questions-section h3 {
            font-size: 1rem;
            margin-bottom: 1rem;
        }

        .questions-section ul {
            margin-left: 1.5rem;
        }

        .questions-section li {
            margin-bottom: 0.5rem;
        }

        .domain-breakdown h3 {
            font-size: 1rem;
            margin-bottom: 1rem;
            color: var(--text-muted);
        }

        .domain-gap-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .domain-gap-count {
            background: var(--bg);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }

        .framing {
            font-size: 1rem;
            color: var(--text-muted);
            font-style: italic;
        }

        .no-data {
            color: var(--text-muted);
            font-style: italic;
        }

        /* Open Questions in Domain Slides */
        .open-questions-section {
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px dashed var(--border);
        }

        .open-questions-section h4 {
            font-size: 0.9rem;
            color: var(--warning);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .open-questions-section h4::before {
            content: "⚠";
        }

        .more-gaps {
            font-weight: normal;
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .open-questions-list {
            margin: 0;
            padding-left: 1.5rem;
        }

        .open-questions-list li {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }

        /* Org Chart Styles */
        .org-chart-container {
            margin-top: 1.5rem;
        }

        .org-chart-section {
            margin-bottom: 1.5rem;
        }

        .org-chart-section h4 {
            font-size: 1rem;
            color: var(--text-primary);
            margin: 0 0 0.75rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }

        .org-chart-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }

        .org-chart-table th {
            text-align: left;
            padding: 0.5rem 0.75rem;
            background: var(--bg-alt, #f5f5f5);
            border-bottom: 2px solid var(--border);
            font-weight: 600;
            color: var(--text-muted);
        }

        .org-chart-table td {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }

        .org-chart-table td.count {
            text-align: center;
            font-weight: 600;
        }

        .org-chart-table tr:hover {
            background: var(--bg-alt, #f5f5f5);
        }

        /* App Landscape Styles */
        .app-landscape-container {
            margin-top: 1.5rem;
        }

        .app-landscape-section {
            margin-bottom: 1.5rem;
        }

        .app-landscape-section h4 {
            font-size: 1rem;
            color: var(--text-primary);
            margin: 0 0 0.75rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }

        .app-landscape-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }

        .app-landscape-table th {
            text-align: left;
            padding: 0.5rem 0.75rem;
            background: var(--bg-alt, #f5f5f5);
            border-bottom: 2px solid var(--border);
            font-weight: 600;
            color: var(--text-muted);
        }

        .app-landscape-table td {
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }

        .app-landscape-table td.count {
            text-align: center;
            font-weight: 600;
        }

        .app-landscape-table tr:hover {
            background: var(--bg-alt, #f5f5f5);
        }

        .criticality-high, .criticality-critical {
            color: var(--danger);
            font-weight: 600;
        }

        .criticality-medium {
            color: var(--warning);
        }

        .criticality-low {
            color: var(--success);
        }

        /* Cost Waterfall */
        .cost-waterfall {
            margin: 1.5rem 0;
            padding: 1rem;
            background: var(--card-bg);
            border-radius: 8px;
        }

        .cost-waterfall h3 {
            margin: 0 0 1rem 0;
            font-size: 1.1rem;
            color: var(--text-primary);
        }

        .waterfall-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }

        .waterfall-section h4 {
            margin: 0 0 0.5rem 0;
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .cost-waterfall-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }

        .cost-waterfall-table th {
            text-align: left;
            padding: 0.5rem;
            border-bottom: 2px solid var(--border);
            font-weight: 600;
            color: var(--text-muted);
        }

        .cost-waterfall-table td {
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }

        .cost-waterfall-table .total-row td {
            border-top: 2px solid var(--border);
            border-bottom: none;
            background: rgba(0,0,0,0.02);
        }

        @media (max-width: 1024px) {
            .waterfall-grid { grid-template-columns: 1fr; }
        }

        /* Print Styles */
        @media print {
            .nav { display: none; }
            .slides { padding-top: 0; }
            .slide {
                min-height: auto;
                page-break-after: always;
                padding: 1rem;
            }
            .slide:last-child { page-break-after: avoid; }
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
            .two-column { grid-template-columns: 1fr; }
            .slide-body { grid-template-columns: 1fr; }
            .nav-items { display: none; }
        }
    '''


def _get_presentation_js() -> str:
    """Return the JavaScript for the presentation."""
    return '''
        // Slide navigation
        const slides = document.querySelectorAll('.slide');
        const navItems = document.querySelectorAll('.nav-item');
        const slideCounter = document.querySelector('.slide-counter');
        let currentSlide = 0;

        function updateNavigation() {
            navItems.forEach((item, i) => {
                item.classList.toggle('active', i === currentSlide);
            });
            if (slideCounter) {
                slideCounter.textContent = `${currentSlide + 1} / ${slides.length}`;
            }
        }

        function goToSlide(index) {
            if (index >= 0 && index < slides.length) {
                currentSlide = index;
                slides[currentSlide].scrollIntoView({ behavior: 'smooth' });
                updateNavigation();
            }
        }

        function nextSlide() {
            goToSlide(currentSlide + 1);
        }

        function prevSlide() {
            goToSlide(currentSlide - 1);
        }

        // Click handlers for nav items
        navItems.forEach((item, i) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                goToSlide(i);
            });
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault();
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                prevSlide();
            }
        });

        // Scroll spy to update current slide
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const index = Array.from(slides).indexOf(entry.target);
                    if (index !== -1) {
                        currentSlide = index;
                        updateNavigation();
                    }
                }
            });
        }, { threshold: 0.5 });

        slides.forEach(slide => observer.observe(slide));

        // Initialize
        updateNavigation();
    '''


# ============================================================================
# Agent-Generated Presentation (Higher Quality)
# ============================================================================

def generate_presentation_from_narratives(
    narrative_store: NarrativeStore,
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    output_dir: Path,
    target_name: str = "Target Company",
    timestamp: str = None
) -> Path:
    """
    Generate presentation from agent-generated narratives.

    This version uses the output from narrative agents for higher quality
    domain storytelling and cost synthesis.

    Args:
        narrative_store: Agent-generated narratives
        fact_store: Discovered facts (for metrics)
        reasoning_store: Analysis findings (for metrics)
        output_dir: Where to save the presentation
        target_name: Name of the target company
        timestamp: Optional timestamp for filename

    Returns:
        Path to the generated HTML file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = output_dir / f"investment_thesis_{timestamp}.html"

    # Build presentation using agent narratives
    exec_summary = _build_exec_from_narratives(
        narrative_store, fact_store, reasoning_store, target_name
    )
    domain_slides = _build_domain_slides_from_narratives(
        narrative_store, fact_store, reasoning_store
    )
    cost_slide = _build_cost_slide_from_narrative(narrative_store)
    open_questions = _build_open_questions_slide(fact_store, reasoning_store)

    # Generate HTML
    html = _render_presentation_from_narratives(
        target_name=target_name,
        exec_summary=exec_summary,
        domain_slides=domain_slides,
        cost_slide=cost_slide,
        open_questions=open_questions,
        timestamp=timestamp
    )

    output_file.write_text(html)
    return output_file


def _build_exec_from_narratives(
    narrative_store: NarrativeStore,
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    target_name: str
) -> Dict[str, Any]:
    """Build executive summary using agent narratives."""

    # Basic metrics
    metrics = {
        'facts': len(fact_store.facts),
        'gaps': len(fact_store.gaps),
        'risks': len(reasoning_store.risks),
        'work_items': len(reasoning_store.work_items)
    }

    # Severity counts
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for risk in reasoning_store.risks:
        if risk.severity in severity_counts:
            severity_counts[risk.severity] += 1

    # Cost from narrative or calculate
    if narrative_store.cost_narrative:
        cost = narrative_store.cost_narrative.total_range
        cost_by_phase = narrative_store.cost_narrative.by_phase
        executive_summary = narrative_store.cost_narrative.executive_summary
    else:
        cost = {'low': 0, 'high': 0}
        cost_by_phase = {}
        executive_summary = "Cost analysis pending."

    # Top risks
    top_risks = [r for r in reasoning_store.risks if r.severity in ('critical', 'high')][:5]

    # Key systems from facts
    key_systems = _identify_key_systems(fact_store)

    return {
        'target_name': target_name,
        'metrics': metrics,
        'severity_counts': severity_counts,
        'key_systems': key_systems,
        'top_risks': top_risks,
        'cost': cost,
        'cost_by_phase': cost_by_phase,
        'executive_summary': executive_summary
    }


def _build_domain_slides_from_narratives(
    narrative_store: NarrativeStore,
    fact_store: FactStore,
    reasoning_store: Optional[ReasoningStore] = None,
    all_domains: Optional[List[str]] = None
) -> List[SlideContent]:
    """Build domain slides from agent-generated narratives.

    Args:
        narrative_store: Store with LLM-generated narratives
        fact_store: Store with extracted facts
        reasoning_store: Store with reasoning outputs (risks, work items)
        all_domains: List of all domains to include (generates placeholders for missing)
    """

    slides = []

    # Default to all 6 domains if not specified
    if all_domains is None:
        all_domains = ['infrastructure', 'network', 'cybersecurity',
                       'applications', 'identity_access', 'organization']

    for domain in all_domains:
        config = DOMAIN_CONFIG.get(domain, {'title': domain.replace('_', ' ').title(), 'icon': '📋'})

        # Get metrics for this domain
        domain_facts = [f for f in fact_store.facts if f.domain == domain]
        domain_gaps = [g for g in fact_store.gaps if g.domain == domain]

        # Count risks and work items if reasoning store is provided
        domain_risks = 0
        domain_work_items = 0
        if reasoning_store:
            domain_risks = len([r for r in reasoning_store.risks if r.domain == domain])
            domain_work_items = len([w for w in reasoning_store.work_items if w.domain == domain])

        # Check if we have a narrative for this domain
        narrative = narrative_store.domain_narratives.get(domain)

        # Build open questions from gaps (limit to top 5 for slide)
        open_questions = []
        for g in domain_gaps[:5]:
            open_questions.append(g.description)

        # Build extra content for specific domains
        extra_content = None
        if domain == 'organization':
            entity = _detect_primary_entity(fact_store, domain)
            extra_content = _build_org_chart_html(fact_store, entity=entity)
        elif domain == 'applications':
            entity = _detect_primary_entity(fact_store, domain)
            extra_content = _build_app_landscape_html(fact_store, entity=entity)

        if narrative:
            # Full narrative slide
            slides.append(SlideContent(
                id=domain,
                title=config['title'],
                so_what=narrative.so_what,
                considerations=narrative.considerations,
                narrative=narrative.narrative,
                cost_impact=narrative.cost_summary,
                sources=narrative.sources or [],
                metrics={
                    'facts': len(domain_facts),
                    'gaps': len(domain_gaps),
                    'risks': domain_risks,
                    'work_items': domain_work_items,
                    'confidence': narrative.confidence
                },
                open_questions=open_questions if open_questions else None,
                extra_content=extra_content
            ))
        else:
            # Generate placeholder slide for domains with no narrative
            gap_count = len(domain_gaps)
            if gap_count > 0 or len(domain_facts) == 0:
                so_what = f"Insufficient documentation to assess {config['title'].lower()} — {gap_count} information gaps identified requiring VDR follow-up."
                narrative_text = (
                    f"We were unable to complete a full assessment of {config['title'].lower()} due to "
                    f"limited documentation in the data room. {gap_count} specific information gaps have been "
                    f"flagged for VDR follow-up. Until these gaps are addressed, integration planning for this "
                    f"domain carries elevated uncertainty."
                )
                considerations = [
                    f"{gap_count} documentation gaps identified",
                    "VDR requests generated for missing information",
                    "Integration cost estimates pending additional data",
                    "Risk assessment incomplete without source documentation"
                ]
            else:
                so_what = f"No findings for {config['title'].lower()} in current analysis scope."
                narrative_text = f"This domain was not covered in the current analysis or had no material findings."
                considerations = ["No material findings in current scope"]

            slides.append(SlideContent(
                id=domain,
                title=config['title'],
                so_what=so_what,
                considerations=considerations,
                narrative=narrative_text,
                cost_impact="Cost estimates pending additional documentation",
                sources=[],
                metrics={
                    'facts': len(domain_facts),
                    'gaps': gap_count,
                    'risks': domain_risks,
                    'work_items': domain_work_items,
                    'confidence': 'low'
                },
                open_questions=open_questions if open_questions else None,
                extra_content=extra_content
            ))

    return slides


def _build_cost_slide_from_narrative(narrative_store: NarrativeStore) -> Dict[str, Any]:
    """Build cost slide from agent-generated narrative."""

    if not narrative_store.cost_narrative:
        return {
            'has_narrative': False,
            'total': {'low': 0, 'high': 0}
        }

    cn = narrative_store.cost_narrative

    return {
        'has_narrative': True,
        'total': cn.total_range,
        'by_phase': cn.by_phase,
        'by_domain': cn.by_domain,
        'by_owner': cn.by_owner,
        'executive_summary': cn.executive_summary,
        'key_drivers': cn.key_drivers,
        'assumptions': cn.assumptions,
        'risks_to_estimates': cn.risks_to_estimates
    }


def _render_presentation_from_narratives(
    target_name: str,
    exec_summary: Dict,
    domain_slides: List[SlideContent],
    cost_slide: Dict,
    open_questions: Dict,
    timestamp: str
) -> str:
    """Render HTML presentation from agent narratives."""

    # Build navigation
    nav_items = ['executive-summary']
    nav_items.extend([s.id for s in domain_slides])
    nav_items.extend(['cost-synthesis', 'open-questions'])

    nav_html = _build_nav_from_narratives(nav_items, domain_slides)

    # Build slides
    exec_html = _render_exec_from_narratives(exec_summary)
    domain_html = "\n".join(_render_domain_slide(s) for s in domain_slides)
    cost_html = _render_cost_narrative_slide(cost_slide)
    questions_html = _render_open_questions_slide(open_questions)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - IT Investment Thesis</title>
    <style>
{_get_presentation_css()}
    </style>
</head>
<body>
    <div class="presentation">
        {nav_html}

        <main class="slides">
            {exec_html}
            {domain_html}
            {cost_html}
            {questions_html}
        </main>
    </div>

    <script>
{_get_presentation_js()}
    </script>
</body>
</html>'''


def _build_nav_from_narratives(nav_items: List[str], domain_slides: List[SlideContent]) -> str:
    """Build navigation for narrative-based presentation."""

    links = ['<a href="#executive-summary" class="nav-item active">Executive Summary</a>']

    for slide in domain_slides:
        config = DOMAIN_CONFIG.get(slide.id, {})
        icon = config.get('icon', '📋')
        links.append(f'<a href="#{slide.id}" class="nav-item">{icon} {slide.title}</a>')

    links.append('<a href="#cost-synthesis" class="nav-item">💰 Cost Synthesis</a>')
    links.append('<a href="#open-questions" class="nav-item">❓ Open Questions</a>')

    return f'''
    <nav class="nav">
        <div class="nav-brand">IT Investment Thesis</div>
        <div class="nav-items">
            {"".join(links)}
        </div>
        <div class="nav-controls">
            <button onclick="prevSlide()" class="nav-btn">← Prev</button>
            <span class="slide-counter">1 / {len(nav_items)}</span>
            <button onclick="nextSlide()" class="nav-btn">Next →</button>
        </div>
    </nav>'''


def _render_exec_from_narratives(data: Dict) -> str:
    """Render executive summary slide with agent narrative."""

    metrics = data['metrics']
    severity = data['severity_counts']

    # Key systems
    systems_html = ""
    if data.get('key_systems'):
        system_items = [f'<li><strong>{sys["label"]}:</strong> {sys["system"]}</li>'
                       for sys in data['key_systems']]
        systems_html = f'<ul class="key-systems">{"".join(system_items)}</ul>'

    # Top risks
    risks_html = ""
    if data.get('top_risks'):
        risk_items = []
        for risk in data['top_risks']:
            risk_items.append(f'''
            <div class="risk-item risk-{risk.severity}">
                <span class="risk-badge">{risk.severity.upper()}</span>
                <span class="risk-title">{risk.title}</span>
            </div>''')
        risks_html = f'<div class="top-risks">{"".join(risk_items)}</div>'

    # Executive summary narrative
    exec_narrative = data.get('executive_summary', 'Analysis in progress.')

    return f'''
    <section id="executive-summary" class="slide slide-executive">
        <div class="slide-header">
            <h1>{data['target_name']}</h1>
            <p class="slide-subtitle">IT Due Diligence - Investment Thesis Summary</p>
        </div>

        <div class="slide-content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{metrics['facts']}</div>
                    <div class="metric-label">Facts Discovered</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['gaps']}</div>
                    <div class="metric-label">Information Gaps</div>
                </div>
                <div class="metric-card metric-warning">
                    <div class="metric-value">{severity['critical'] + severity['high']}</div>
                    <div class="metric-label">Critical/High Risks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['work_items']}</div>
                    <div class="metric-label">Work Items</div>
                </div>
            </div>

            <div class="two-column">
                <div class="column">
                    <h3>Key Systems</h3>
                    {systems_html if systems_html else '<p class="no-data">Pending identification</p>'}
                </div>
                <div class="column">
                    <h3>Top Risks</h3>
                    {risks_html if risks_html else '<p class="no-data">No critical risks</p>'}
                </div>
            </div>

            <div class="bottom-line">
                <h3>Cost Summary</h3>
                <p class="assessment">{exec_narrative}</p>
            </div>
        </div>
    </section>'''


def _render_cost_narrative_slide(data: Dict) -> str:
    """Render the cost synthesis slide from agent narrative."""

    if not data.get('has_narrative'):
        return '''
        <section id="cost-synthesis" class="slide slide-cost">
            <div class="slide-header">
                <h2>💰 Cost Synthesis</h2>
            </div>
            <div class="slide-content">
                <p class="no-data">Cost synthesis pending. Run narrative agents to generate.</p>
            </div>
        </section>'''

    total = data['total']

    # Helper to ensure list (LLM sometimes returns strings instead of arrays)
    def ensure_list(val):
        if isinstance(val, str):
            return [val] if val.strip() else []
        if isinstance(val, list):
            return val
        return []

    # Key drivers
    drivers_html = ""
    key_drivers = ensure_list(data.get('key_drivers', []))
    if key_drivers:
        driver_items = [f'<li>{d}</li>' for d in key_drivers]
        drivers_html = f'''
        <div class="drivers-section">
            <h3>Key Cost Drivers</h3>
            <ul class="considerations">{"".join(driver_items)}</ul>
        </div>'''

    # Assumptions
    assumptions_html = ""
    assumptions = ensure_list(data.get('assumptions', []))
    if assumptions:
        assumption_items = [f'<li>{a}</li>' for a in assumptions]
        assumptions_html = f'''
        <div class="assumptions-section">
            <h3>Key Assumptions</h3>
            <ul>{"".join(assumption_items)}</ul>
        </div>'''

    # Risks to estimates
    risks_html = ""
    risks_to_estimates = ensure_list(data.get('risks_to_estimates', []))
    if risks_to_estimates:
        risk_items = [f'<li>{r}</li>' for r in risks_to_estimates]
        risks_html = f'''
        <div class="estimate-risks-section">
            <h3>Risks to Estimates</h3>
            <ul>{"".join(risk_items)}</ul>
        </div>'''

    # Build cost waterfall tables
    by_phase = data.get('by_phase', {})
    by_domain = data.get('by_domain', {})
    by_owner = data.get('by_owner', {})

    # Phase breakdown table
    phase_rows = []
    phase_total_low, phase_total_high = 0, 0
    for phase in ['Day_1', 'Day_100', 'Post_100']:
        if phase in by_phase:
            p = by_phase[phase]
            low, high = p.get('low', 0), p.get('high', 0)
            count = p.get('count', 0)
            phase_total_low += low
            phase_total_high += high
            phase_label = phase.replace('_', ' ')
            phase_rows.append(
                f'<tr><td>{phase_label}</td><td>${low:,.0f} - ${high:,.0f}</td><td>{count} items</td></tr>'
            )

    phase_table = f'''
    <table class="cost-waterfall-table">
        <thead><tr><th>Phase</th><th>Cost Range</th><th>Items</th></tr></thead>
        <tbody>
            {"".join(phase_rows)}
            <tr class="total-row"><td><strong>Total</strong></td><td><strong>${phase_total_low:,.0f} - ${phase_total_high:,.0f}</strong></td><td></td></tr>
        </tbody>
    </table>''' if phase_rows else ''

    # Domain breakdown table
    domain_rows = []
    for domain, d in sorted(by_domain.items(), key=lambda x: x[1].get('high', 0), reverse=True):
        low, high = d.get('low', 0), d.get('high', 0)
        count = d.get('count', 0)
        domain_label = domain.replace('_', ' ').title()
        domain_rows.append(
            f'<tr><td>{domain_label}</td><td>${low:,.0f} - ${high:,.0f}</td><td>{count} items</td></tr>'
        )

    domain_table = f'''
    <table class="cost-waterfall-table">
        <thead><tr><th>Domain</th><th>Cost Range</th><th>Items</th></tr></thead>
        <tbody>{"".join(domain_rows)}</tbody>
    </table>''' if domain_rows else ''

    # Owner breakdown table
    owner_rows = []
    for owner in ['buyer', 'target', 'shared']:
        if owner in by_owner:
            o = by_owner[owner]
            low, high = o.get('low', 0), o.get('high', 0)
            if low > 0 or high > 0:
                pct_low = (low / total['low'] * 100) if total['low'] > 0 else 0
                pct_high = (high / total['high'] * 100) if total['high'] > 0 else 0
                owner_rows.append(
                    f'<tr><td>{owner.title()}</td><td>${low:,.0f} - ${high:,.0f}</td><td>{pct_low:.0f}% - {pct_high:.0f}%</td></tr>'
                )

    owner_table = f'''
    <table class="cost-waterfall-table">
        <thead><tr><th>Owner</th><th>Cost Range</th><th>% of Total</th></tr></thead>
        <tbody>{"".join(owner_rows)}</tbody>
    </table>''' if owner_rows else ''

    # Cost waterfall section
    waterfall_html = ''
    if phase_table or domain_table or owner_table:
        waterfall_html = f'''
        <div class="cost-waterfall">
            <h3>Cost Breakdown</h3>
            <div class="waterfall-grid">
                <div class="waterfall-section">
                    <h4>By Phase</h4>
                    {phase_table}
                </div>
                <div class="waterfall-section">
                    <h4>By Domain</h4>
                    {domain_table}
                </div>
                <div class="waterfall-section">
                    <h4>By Owner</h4>
                    {owner_table}
                </div>
            </div>
        </div>'''

    return f'''
    <section id="cost-synthesis" class="slide slide-cost">
        <div class="slide-header">
            <h2>💰 Cost Synthesis</h2>
            <div class="total-cost">
                Total: <strong>${total['low']:,.0f} - ${total['high']:,.0f}</strong>
            </div>
        </div>

        <div class="slide-content">
            <div class="so-what cost-narrative">
                <div class="so-what-label">THE COST PICTURE</div>
                <p class="so-what-text">{data['executive_summary']}</p>
            </div>

            {waterfall_html}

            <div class="slide-body cost-details">
                {drivers_html}
                <div class="cost-grid">
                    {assumptions_html}
                    {risks_html}
                </div>
            </div>
        </div>
    </section>'''
