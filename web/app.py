"""
Web interface for IT Due Diligence Agent.

Provides a browser-based UI for reviewing and adjusting analysis outputs.
Run with: python -m web.app
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, flash
from interactive.session import Session
from tools_v2.reasoning_tools import COST_RANGE_VALUES

# Organization module imports
from models.organization_models import CompanyInfo, EmploymentType, RoleCategory
from models.organization_stores import OrganizationDataStore, OrganizationAnalysisResult
from services.organization_pipeline import OrganizationAnalysisPipeline

# Configure Flask with static folder
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')
app.secret_key = 'it-dd-agent-secret-key'

# Global session - in production would use proper session management
session = None


def get_session():
    """Get or create the session."""
    global session
    if session is None:
        # Try to load from most recent files
        from config_v2 import FACTS_DIR, FINDINGS_DIR
        facts_files = sorted(FACTS_DIR.glob("facts_*.json"), reverse=True)
        findings_files = sorted(FINDINGS_DIR.glob("findings_*.json"), reverse=True)

        if facts_files:
            session = Session.load_from_files(
                facts_file=facts_files[0],
                findings_file=findings_files[0] if findings_files else None
            )
        else:
            session = Session()
    return session


@app.route('/')
def dashboard():
    """Main dashboard view."""
    s = get_session()
    summary = s.get_summary()

    # Get top risks
    top_risks = sorted(s.reasoning_store.risks,
                       key=lambda r: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(r.severity, 4))[:5]

    # Get recent work items by phase
    day1_items = [w for w in s.reasoning_store.work_items if w.phase == 'Day_1'][:5]

    return render_template('dashboard.html',
                         summary=summary,
                         top_risks=top_risks,
                         day1_items=day1_items,
                         session=s)


@app.route('/risks')
def risks():
    """List all risks."""
    s = get_session()
    severity_filter = request.args.get('severity', '')
    domain_filter = request.args.get('domain', '')

    risks_list = s.reasoning_store.risks

    if severity_filter:
        risks_list = [r for r in risks_list if r.severity == severity_filter]
    if domain_filter:
        risks_list = [r for r in risks_list if r.domain == domain_filter]

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    risks_list = sorted(risks_list, key=lambda r: severity_order.get(r.severity, 4))

    domains = list(set(r.domain for r in s.reasoning_store.risks))

    return render_template('risks.html',
                         risks=risks_list,
                         domains=domains,
                         severity_filter=severity_filter,
                         domain_filter=domain_filter)


@app.route('/risk/<risk_id>')
def risk_detail(risk_id):
    """Risk detail view with connected items."""
    s = get_session()

    risk = s.get_risk(risk_id)
    if not risk:
        flash(f'Risk {risk_id} not found', 'error')
        return redirect(url_for('risks'))

    # Get supporting facts
    facts = []
    for fact_id in (risk.based_on_facts or []):
        fact = s.get_fact(fact_id)
        if fact:
            facts.append(fact)

    # Get related work items
    related_wi = []
    for wi in s.reasoning_store.work_items:
        if hasattr(wi, 'triggered_by_risks') and wi.triggered_by_risks:
            if risk_id in wi.triggered_by_risks:
                related_wi.append(wi)

    return render_template('risk_detail.html',
                         risk=risk,
                         facts=facts,
                         related_work_items=related_wi)


@app.route('/risk/<risk_id>/adjust', methods=['POST'])
def adjust_risk(risk_id):
    """Adjust a risk's severity."""
    s = get_session()
    new_severity = request.form.get('severity')

    if new_severity and s.adjust_risk(risk_id, 'severity', new_severity):
        flash(f'Updated {risk_id} severity to {new_severity}', 'success')
    else:
        flash(f'Failed to update {risk_id}', 'error')

    return redirect(url_for('risk_detail', risk_id=risk_id))


@app.route('/risk/<risk_id>/note', methods=['POST'])
def add_risk_note(risk_id):
    """Add a note to a risk."""
    s = get_session()
    note_text = request.form.get('note')

    if note_text:
        risk = s.get_risk(risk_id)
        if risk:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            old_reasoning = risk.reasoning
            risk.reasoning = f"{old_reasoning}\n\n[Note {timestamp}]: {note_text}"
            s.record_modification('risk', risk_id, 'reasoning', old_reasoning, risk.reasoning)
            flash(f'Note added to {risk_id}', 'success')

    return redirect(url_for('risk_detail', risk_id=risk_id))


@app.route('/work-items')
def work_items():
    """List all work items."""
    s = get_session()
    phase_filter = request.args.get('phase', '')
    domain_filter = request.args.get('domain', '')

    items = s.reasoning_store.work_items

    if phase_filter:
        items = [w for w in items if w.phase == phase_filter]
    if domain_filter:
        items = [w for w in items if w.domain == domain_filter]

    # Group by phase
    by_phase = {'Day_1': [], 'Day_100': [], 'Post_100': []}
    for wi in items:
        if wi.phase in by_phase:
            by_phase[wi.phase].append(wi)

    # Calculate totals
    totals = {}
    for phase, items_list in by_phase.items():
        low = sum(COST_RANGE_VALUES.get(w.cost_estimate, {}).get('low', 0) for w in items_list)
        high = sum(COST_RANGE_VALUES.get(w.cost_estimate, {}).get('high', 0) for w in items_list)
        totals[phase] = {'low': low, 'high': high, 'count': len(items_list)}

    domains = list(set(w.domain for w in s.reasoning_store.work_items))

    return render_template('work_items.html',
                         by_phase=by_phase,
                         totals=totals,
                         domains=domains,
                         phase_filter=phase_filter,
                         domain_filter=domain_filter,
                         cost_ranges=COST_RANGE_VALUES)


@app.route('/work-item/<wi_id>')
def work_item_detail(wi_id):
    """Work item detail view."""
    s = get_session()

    wi = s.get_work_item(wi_id)
    if not wi:
        flash(f'Work item {wi_id} not found', 'error')
        return redirect(url_for('work_items'))

    # Get triggering facts
    facts = []
    for fact_id in (wi.triggered_by or []):
        fact = s.get_fact(fact_id)
        if fact:
            facts.append(fact)

    # Get triggering risks
    risks = []
    for risk_id in (wi.triggered_by_risks or []):
        risk = s.get_risk(risk_id)
        if risk:
            risks.append(risk)

    cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})

    return render_template('work_item_detail.html',
                         wi=wi,
                         facts=facts,
                         risks=risks,
                         cost_range=cost_range)


@app.route('/work-item/<wi_id>/adjust', methods=['POST'])
def adjust_work_item(wi_id):
    """Adjust a work item."""
    s = get_session()

    field = request.form.get('field')
    value = request.form.get('value')

    if field and value:
        if s.adjust_work_item(wi_id, field, value):
            flash(f'Updated {wi_id} {field} to {value}', 'success')
        else:
            flash(f'Failed to update {wi_id}', 'error')

    return redirect(url_for('work_item_detail', wi_id=wi_id))


@app.route('/facts')
def facts():
    """List all facts."""
    s = get_session()
    domain_filter = request.args.get('domain', '')
    category_filter = request.args.get('category', '')
    entity_filter = request.args.get('entity', '')

    facts_list = list(s.fact_store.facts)

    if domain_filter:
        facts_list = [f for f in facts_list if f.domain == domain_filter]
    if category_filter:
        facts_list = [f for f in facts_list if f.category == category_filter]
    if entity_filter:
        facts_list = [f for f in facts_list if getattr(f, 'entity', 'target') == entity_filter]

    domains = list(set(f.domain for f in s.fact_store.facts))
    categories = list(set(f.category for f in s.fact_store.facts))

    return render_template('facts.html',
                         facts=facts_list,
                         domains=domains,
                         categories=categories,
                         domain_filter=domain_filter,
                         category_filter=category_filter,
                         entity_filter=entity_filter)


@app.route('/fact/<fact_id>')
def fact_detail(fact_id):
    """Fact detail view with items that cite it."""
    s = get_session()

    fact = s.get_fact(fact_id)
    if not fact:
        flash(f'Fact {fact_id} not found', 'error')
        return redirect(url_for('facts'))

    # Find risks citing this fact
    citing_risks = []
    for risk in s.reasoning_store.risks:
        if hasattr(risk, 'based_on_facts') and risk.based_on_facts:
            if fact_id in risk.based_on_facts:
                citing_risks.append(risk)

    # Find work items citing this fact
    citing_wi = []
    for wi in s.reasoning_store.work_items:
        if hasattr(wi, 'triggered_by') and wi.triggered_by:
            if fact_id in wi.triggered_by:
                citing_wi.append(wi)

    return render_template('fact_detail.html',
                         fact=fact,
                         citing_risks=citing_risks,
                         citing_work_items=citing_wi)


@app.route('/gaps')
def gaps():
    """List all gaps."""
    s = get_session()
    domain_filter = request.args.get('domain', '')
    importance_filter = request.args.get('importance', '')

    gaps_list = list(s.fact_store.gaps)

    if domain_filter:
        gaps_list = [g for g in gaps_list if g.domain == domain_filter]
    if importance_filter:
        gaps_list = [g for g in gaps_list if g.importance == importance_filter]

    # Sort by importance
    importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    gaps_list = sorted(gaps_list, key=lambda g: importance_order.get(g.importance, 4))

    domains = list(set(g.domain for g in s.fact_store.gaps))

    return render_template('gaps.html',
                         gaps=gaps_list,
                         domains=domains,
                         domain_filter=domain_filter,
                         importance_filter=importance_filter)


@app.route('/export-vdr')
def export_vdr():
    """Export VDR request list."""
    s = get_session()
    from datetime import datetime
    from config_v2 import OUTPUT_DIR

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate VDR markdown
    vdr_content = "# VDR Request List\n\n"
    for gap in s.fact_store.gaps:
        vdr_content += f"## [{gap.importance.upper()}] {gap.gap_id}\n"
        vdr_content += f"**Domain:** {gap.domain}\n"
        vdr_content += f"**Category:** {gap.category}\n"
        vdr_content += f"**Description:** {gap.description}\n\n"

    vdr_file = OUTPUT_DIR / f"vdr_requests_{timestamp}.md"
    with open(vdr_file, 'w') as f:
        f.write(vdr_content)

    flash(f'VDR requests exported to {vdr_file.name}', 'success')
    return redirect(url_for('gaps'))


@app.route('/context', methods=['GET', 'POST'])
def context():
    """Manage deal context."""
    s = get_session()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            text = request.form.get('context_text')
            if text:
                s.add_deal_context(text)
                flash('Deal context added', 'success')
        elif action == 'clear':
            s.clear_deal_context()
            flash('Deal context cleared', 'success')
        return redirect(url_for('context'))

    return render_template('context.html', deal_context=s.deal_context)


@app.route('/export', methods=['POST'])
def export():
    """Export current session."""
    s = get_session()
    from datetime import datetime
    from config_v2 import OUTPUT_DIR

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = s.save_to_files(OUTPUT_DIR, timestamp)

    flash(f'Exported to {len(saved_files)} files', 'success')
    return redirect(url_for('dashboard'))


@app.route('/search')
def search():
    """Search across all items."""
    s = get_session()
    query = request.args.get('q', '').lower()

    results = {'risks': [], 'work_items': [], 'facts': [], 'gaps': []}

    if query:
        # Search risks
        for risk in s.reasoning_store.risks:
            if query in risk.title.lower() or query in risk.description.lower():
                results['risks'].append(risk)

        # Search work items
        for wi in s.reasoning_store.work_items:
            if query in wi.title.lower() or query in wi.description.lower():
                results['work_items'].append(wi)

        # Search facts
        for fact in s.fact_store.facts:
            if query in fact.item.lower() or query in str(fact.details).lower():
                results['facts'].append(fact)

        # Search gaps
        for gap in s.fact_store.gaps:
            if query in gap.description.lower():
                results['gaps'].append(gap)

    total = sum(len(v) for v in results.values())

    return render_template('search.html', query=query, results=results, total=total)


# =============================================================================
# Organization Module Routes
# =============================================================================

# Global organization analysis result cache
_org_analysis_result = None


def get_organization_analysis():
    """Get or run the organization analysis."""
    global _org_analysis_result
    if _org_analysis_result is None:
        # Try to load existing analysis or create demo data
        _org_analysis_result = _create_demo_organization_data()
    return _org_analysis_result


def _create_demo_organization_data():
    """Create demo organization data for UI testing."""
    from models.organization_models import (
        StaffMember, RoleSummary, CategorySummary,
        MSPService, MSPRelationship, SharedServiceDependency,
        TSAItem, StaffingNeed, DependencyLevel
    )
    from models.organization_stores import (
        OrganizationDataStore, StaffingComparisonResult,
        CategoryComparison, MissingRole, RatioComparison,
        MSPSummary, SharedServicesSummary, OrganizationAnalysisResult
    )
    from datetime import datetime
    import uuid

    def gen_id(prefix):
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    # Create data store
    store = OrganizationDataStore()

    # Add demo staff members
    demo_staff = [
        StaffMember(
            id=gen_id("staff"), name="John Smith", role_title="IT Director",
            role_category=RoleCategory.LEADERSHIP, department="IT",
            employment_type=EmploymentType.FTE, base_compensation=180000,
            entity="target", hire_date="2018-03-15", location="HQ",
            is_key_person=True, key_person_reason="Single point of IT leadership"
        ),
        StaffMember(
            id=gen_id("staff"), name="Sarah Johnson", role_title="Sr. Systems Administrator",
            role_category=RoleCategory.INFRASTRUCTURE, department="IT Infrastructure",
            employment_type=EmploymentType.FTE, base_compensation=95000,
            entity="target", hire_date="2019-06-01", location="HQ",
            is_key_person=True, key_person_reason="Critical infrastructure knowledge"
        ),
        StaffMember(
            id=gen_id("staff"), name="Mike Chen", role_title="Network Engineer",
            role_category=RoleCategory.INFRASTRUCTURE, department="IT Infrastructure",
            employment_type=EmploymentType.FTE, base_compensation=85000,
            entity="target", hire_date="2021-01-10", location="HQ"
        ),
        StaffMember(
            id=gen_id("staff"), name="Emily Davis", role_title="Help Desk Analyst",
            role_category=RoleCategory.SERVICE_DESK, department="IT Support",
            employment_type=EmploymentType.FTE, base_compensation=55000,
            entity="target", hire_date="2022-04-01", location="HQ"
        ),
        StaffMember(
            id=gen_id("staff"), name="David Wilson", role_title="Help Desk Analyst",
            role_category=RoleCategory.SERVICE_DESK, department="IT Support",
            employment_type=EmploymentType.CONTRACTOR, base_compensation=60000,
            entity="target", hire_date="2023-01-15", location="Remote"
        ),
        StaffMember(
            id=gen_id("staff"), name="Lisa Brown", role_title="Application Developer",
            role_category=RoleCategory.APPLICATIONS, department="IT Development",
            employment_type=EmploymentType.FTE, base_compensation=110000,
            entity="target", hire_date="2020-08-01", location="HQ"
        ),
        StaffMember(
            id=gen_id("staff"), name="Tom Garcia", role_title="Security Analyst",
            role_category=RoleCategory.SECURITY, department="IT Security",
            employment_type=EmploymentType.CONTRACTOR, base_compensation=95000,
            entity="target", hire_date="2023-06-01", location="Remote"
        ),
    ]

    for staff in demo_staff:
        store.add_staff_member(staff)

    # Add demo MSP relationships
    msp1 = MSPRelationship(
        id=gen_id("msp"),
        vendor_name="SecureIT Partners",
        services=[
            MSPService(service_name="24/7 SOC Monitoring", fte_equivalent=2.0,
                      coverage="24x7", criticality="critical", internal_backup=False),
            MSPService(service_name="Vulnerability Scanning", fte_equivalent=0.5,
                      coverage="business_hours", criticality="high", internal_backup=False),
        ],
        contract_value_annual=180000,
        contract_expiry="2025-12-31",
        notice_period_days=90,
        dependency_level=DependencyLevel.FULL
    )

    msp2 = MSPRelationship(
        id=gen_id("msp"),
        vendor_name="CloudManage Inc",
        services=[
            MSPService(service_name="Cloud Infrastructure Management", fte_equivalent=1.5,
                      coverage="business_hours", criticality="high", internal_backup=True),
            MSPService(service_name="Backup Management", fte_equivalent=0.5,
                      coverage="business_hours", criticality="critical", internal_backup=False),
        ],
        contract_value_annual=120000,
        contract_expiry="2024-06-30",
        notice_period_days=60,
        dependency_level=DependencyLevel.PARTIAL
    )

    store.add_msp_relationship(msp1)
    store.add_msp_relationship(msp2)

    # Add demo shared services (using correct field names from model)
    ss1 = SharedServiceDependency(
        id=gen_id("ss"),
        service_name="Active Directory / Identity Management",
        provider="Parent Corp",
        fte_equivalent=1.0,
        criticality="critical",
        will_transfer=False,
        tsa_candidate=True
    )

    ss2 = SharedServiceDependency(
        id=gen_id("ss"),
        service_name="Email & Collaboration (M365)",
        provider="Parent Corp",
        fte_equivalent=0.5,
        criticality="high",
        will_transfer=False,
        tsa_candidate=True
    )

    ss3 = SharedServiceDependency(
        id=gen_id("ss"),
        service_name="ERP System Support",
        provider="Parent Corp",
        fte_equivalent=0.5,
        criticality="high",
        will_transfer=True,
        tsa_candidate=False
    )

    store.add_shared_service(ss1)
    store.add_shared_service(ss2)
    store.add_shared_service(ss3)

    # Create benchmark comparison result (using correct field names from model)
    comparison = StaffingComparisonResult(
        benchmark_profile_id="mid_market_manufacturing",
        benchmark_profile_name="Mid-Market Manufacturing",
        comparison_date=datetime.now().isoformat(),
        total_actual=7,
        total_expected_min=8,
        total_expected_typical=10,
        total_expected_max=12,
        overall_status="understaffed",
        category_comparisons=[
            CategoryComparison(
                category="leadership",
                category_display="IT Leadership",
                actual_count=1,
                benchmark_min=1,
                benchmark_typical=1,
                benchmark_max=2,
                variance=0,
                status="in_range"
            ),
            CategoryComparison(
                category="infrastructure",
                category_display="Infrastructure & Operations",
                actual_count=2,
                benchmark_min=2,
                benchmark_typical=3,
                benchmark_max=4,
                variance=0,
                status="in_range"
            ),
            CategoryComparison(
                category="security",
                category_display="Security",
                actual_count=1,
                benchmark_min=1,
                benchmark_typical=1,
                benchmark_max=2,
                variance=0,
                status="in_range"
            ),
            CategoryComparison(
                category="service_desk",
                category_display="Service Desk / End User Support",
                actual_count=2,
                benchmark_min=2,
                benchmark_typical=2,
                benchmark_max=3,
                variance=0,
                status="in_range"
            ),
            CategoryComparison(
                category="applications",
                category_display="Applications",
                actual_count=1,
                benchmark_min=2,
                benchmark_typical=2,
                benchmark_max=3,
                variance=-1,
                status="understaffed"
            ),
        ],
        missing_roles=[
            MissingRole(
                role_title="DBA / Data Engineer",
                category=RoleCategory.DATA,
                importance="high",
                impact="No dedicated database expertise; relying on developers for DB tasks",
                recommendation="Consider hiring or contracting a DBA, especially if data-intensive operations grow",
                current_coverage="Ad-hoc by application developers"
            ),
        ],
        ratio_comparisons=[
            RatioComparison(
                ratio_name="IT Staff to Employee Ratio",
                actual_value=0.035,
                benchmark_min=0.03,
                benchmark_typical=0.04,
                benchmark_max=0.05,
                status="in_range"
            ),
        ],
        key_findings=[
            "Overall staffing is at the lower end of the expected range",
            "Application Development team appears understaffed for company size",
            "Security coverage relies heavily on MSP - key dependency",
            "No dedicated DBA role identified",
        ],
        recommendations=[
            "Consider adding 1 application developer to support growth",
            "Evaluate MSP dependency for security operations",
            "Plan for database administration coverage",
        ]
    )

    # Create MSP summary (using correct field names from model)
    msp_summary = MSPSummary(
        total_msp_count=2,
        total_fte_equivalent=4.5,
        total_annual_cost=300000,
        total_replacement_cost=450000,
        high_risk_count=1,
        critical_services_count=2,
        services_without_backup=3,
        earliest_expiry="2024-06-30"
    )

    # Create shared services summary (using correct field names from model)
    ss_summary = SharedServicesSummary(
        total_dependencies=3,
        total_fte_equivalent=2.0,
        transferring_fte=0.5,
        non_transferring_fte=1.5,
        hidden_headcount_need=1.5,
        hidden_cost_annual=150000,
        tsa_candidate_count=2,
        critical_dependencies=1
    )

    # Create TSA recommendations (using correct field names from model)
    tsa_recs = [
        TSAItem(
            id=gen_id("tsa"),
            service="Active Directory / Identity Management",
            provider="Parent Corp",
            duration_months=12,
            estimated_monthly_cost=10000,
            exit_criteria="Standalone AD or Azure AD tenant operational",
            replacement_plan="Deploy new Azure AD tenant, migrate users and groups"
        ),
        TSAItem(
            id=gen_id("tsa"),
            service="Email & Collaboration (M365)",
            provider="Parent Corp",
            duration_months=6,
            estimated_monthly_cost=7000,
            exit_criteria="Separate M365 tenant with mail migration complete",
            replacement_plan="Provision new M365 tenant, migrate mailboxes and SharePoint"
        ),
    ]

    # Create staffing needs (using correct field names from model)
    staffing_needs = [
        StaffingNeed(
            id=gen_id("need"),
            role="Identity & Access Management Specialist",
            category=RoleCategory.SECURITY,
            fte_count=1.0,
            urgency="day_100",
            estimated_salary=95000,
            reason="Required to manage standalone identity infrastructure post-TSA",
            source="shared_services"
        ),
    ]

    # Create final result (using correct field names from model)
    result = OrganizationAnalysisResult(
        benchmark_comparison=comparison,
        msp_summary=msp_summary,
        shared_services_summary=ss_summary,
        tsa_recommendations=tsa_recs,
        hiring_recommendations=staffing_needs
    )

    # Store the data store reference as a custom attribute for template access
    result.data_store = store

    return result


@app.route('/organization')
def organization_overview():
    """Organization module overview."""
    result = get_organization_analysis()

    return render_template('organization/overview.html',
                         result=result,
                         store=result.data_store,
                         comparison=result.benchmark_comparison,
                         msp_summary=result.msp_summary,
                         ss_summary=result.shared_services_summary)


@app.route('/organization/staffing')
def organization_staffing():
    """Staffing tree view."""
    result = get_organization_analysis()
    store = result.data_store

    # Build categories dict for template by grouping staff members
    categories = {}
    role_groups = {}  # role_title -> list of members

    # Group by role first
    for member in store.staff_members:
        if member.role_title not in role_groups:
            role_groups[member.role_title] = []
        role_groups[member.role_title].append(member)

    # Now group roles by category
    for role_title, members in role_groups.items():
        if not members:
            continue
        cat = members[0].role_category

        if cat not in categories:
            categories[cat] = {
                'display_name': cat.value.replace('_', ' ').title(),
                'total_headcount': 0,
                'total_compensation': 0,
                'roles': []
            }

        role_data = {
            'role_title': role_title,
            'headcount': len(members),
            'avg_compensation': sum(m.base_compensation for m in members) / len(members),
            'members': members
        }
        categories[cat]['roles'].append(role_data)
        categories[cat]['total_headcount'] += len(members)
        categories[cat]['total_compensation'] += sum(m.base_compensation for m in members)

    # Convert keys to strings for template
    categories_by_name = {cat.value: data for cat, data in categories.items()}

    return render_template('organization/staffing_tree.html',
                         categories=categories_by_name,
                         total_headcount=store.get_target_headcount(),
                         total_compensation=store.total_compensation,
                         fte_count=store.total_internal_fte,
                         contractor_count=store.total_contractor,
                         key_person_count=len(store.get_key_persons()))


@app.route('/organization/benchmark')
def organization_benchmark():
    """Benchmark comparison view."""
    result = get_organization_analysis()

    return render_template('organization/benchmark.html',
                         comparison=result.benchmark_comparison)


@app.route('/organization/msp')
def organization_msp():
    """MSP dependency analysis view."""
    result = get_organization_analysis()
    store = result.data_store

    return render_template('organization/msp_analysis.html',
                         msp_relationships=store.msp_relationships,
                         msp_summary=result.msp_summary)


@app.route('/organization/shared-services')
def organization_shared_services():
    """Shared services analysis view."""
    result = get_organization_analysis()
    store = result.data_store

    return render_template('organization/shared_services.html',
                         dependencies=store.shared_service_dependencies,
                         summary=result.shared_services_summary,
                         tsa_recommendations=result.tsa_recommendations,
                         staffing_needs=result.hiring_recommendations)


@app.route('/organization/run-analysis', methods=['POST'])
def run_organization_analysis():
    """Run organization analysis from uploaded census."""
    global _org_analysis_result

    # Get company info from form
    company_name = request.form.get('company_name', 'Target Company')
    employee_count = int(request.form.get('employee_count', 200))
    revenue = float(request.form.get('revenue', 50000000))
    industry = request.form.get('industry', 'manufacturing')

    company_info = CompanyInfo(
        name=company_name,
        employee_count=employee_count,
        revenue=revenue,
        industry=industry
    )

    # Get session for fact store access
    s = get_session()

    # Run the pipeline
    pipeline = OrganizationAnalysisPipeline()

    # Check for uploaded census file
    census_file = request.files.get('census_file')
    census_path = None
    if census_file and census_file.filename:
        from pathlib import Path
        from config_v2 import DATA_DIR
        census_path = DATA_DIR / 'uploads' / census_file.filename
        census_path.parent.mkdir(exist_ok=True)
        census_file.save(str(census_path))

    try:
        _org_analysis_result = pipeline.run_full_analysis(
            company_info=company_info,
            census_path=census_path,
            fact_store=s.fact_store,
            reasoning_store=s.reasoning_store
        )
        flash('Organization analysis completed successfully', 'success')
    except Exception as e:
        flash(f'Analysis error: {str(e)}', 'error')

    return redirect(url_for('organization_overview'))


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  IT Due Diligence Agent - Web Interface")
    print("="*60)
    print("\n  Starting server at: http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
