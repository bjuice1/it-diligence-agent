"""
Web interface for IT Due Diligence Agent.

Provides a browser-based UI for reviewing and adjusting analysis outputs.
Run with: python -m web.app

Phase 1 Updates:
- Replaced global session with thread-safe SessionStore
- Added AnalysisTaskManager for background processing
- Connected analysis pipeline to web interface
- Fixed /analysis/status to report real progress
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session as flask_session
from interactive.session import Session
from tools_v2.reasoning_tools import COST_RANGE_VALUES

# Organization module imports
from models.organization_models import CompanyInfo, EmploymentType, RoleCategory
from models.organization_stores import OrganizationDataStore, OrganizationAnalysisResult
from services.organization_pipeline import OrganizationAnalysisPipeline

# Phase 1: New imports for task management and session handling
from web.task_manager import task_manager, AnalysisPhase, TaskStatus
from web.session_store import session_store, get_or_create_session_id
from web.analysis_runner import run_analysis, run_analysis_simple

# Configure Flask with static folder
app = Flask(__name__,
            static_folder='static',
            static_url_path='/static')

# Use environment variable for secret key, with fallback for development
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-it-dd-agent-secret-key-change-in-prod')

# Configure task manager and session store
from config_v2 import OUTPUT_DIR, DATA_DIR
task_manager.configure(
    results_dir=OUTPUT_DIR / "tasks",
    max_concurrent=2,
    timeout=1800  # 30 minutes
)
session_store.configure(
    storage_dir=DATA_DIR / "sessions",
    timeout_hours=24
)


def get_session():
    """Get the analysis session for the current user."""
    session_id = get_or_create_session_id(flask_session)
    user_session = session_store.get_session(session_id)

    if user_session and user_session.analysis_session:
        return user_session.analysis_session

    # Try to load from task results if available
    task_id = flask_session.get('current_task_id')
    if task_id:
        task = task_manager.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED and task.facts_file:
            analysis_session = session_store.load_session_from_results(
                session_id,
                task.facts_file,
                task.findings_file
            )
            if analysis_session:
                return analysis_session

    # Try to load from most recent files as fallback
    from config_v2 import FACTS_DIR, FINDINGS_DIR
    facts_files = sorted(FACTS_DIR.glob("facts_*.json"), reverse=True)
    findings_files = sorted(FINDINGS_DIR.glob("findings_*.json"), reverse=True)

    if facts_files:
        analysis_session = Session.load_from_files(
            facts_file=facts_files[0],
            findings_file=findings_files[0] if findings_files else None
        )
        # Store in session store for future access
        if user_session:
            user_session.analysis_session = analysis_session
        return analysis_session

    # Create new empty session
    analysis_session = session_store.get_or_create_analysis_session(session_id)
    return analysis_session if analysis_session else Session()


@app.route('/')
def welcome():
    """Welcome/landing page."""
    return render_template('welcome.html')


@app.route('/upload')
def upload_documents():
    """Document upload page."""
    return render_template('upload.html')


@app.route('/upload/process', methods=['POST'])
def process_upload():
    """Process uploaded documents and run analysis."""
    from pathlib import Path
    from config_v2 import DATA_DIR

    # Create upload directory
    upload_dir = DATA_DIR / 'uploads'
    upload_dir.mkdir(exist_ok=True)

    # Save uploaded files
    uploaded_files = request.files.getlist('documents')
    saved_files = []

    for file in uploaded_files:
        if file.filename:
            # Sanitize filename
            safe_filename = file.filename.replace('..', '').replace('/', '_')
            filepath = upload_dir / safe_filename
            file.save(str(filepath))
            saved_files.append(str(filepath))

    if not saved_files:
        flash('No files were uploaded', 'error')
        return redirect(url_for('upload_documents'))

    # Get deal context
    deal_type = request.form.get('deal_type', 'acquisition')
    target_name = request.form.get('target_name', 'Target Company')
    industry = request.form.get('industry', '')
    employee_count = request.form.get('employee_count', '')

    # Get selected domains (default to all if none selected)
    domains = request.form.getlist('domains')
    if not domains:
        from config_v2 import DOMAINS
        domains = DOMAINS

    # Create deal context dict
    deal_context = {
        'deal_type': deal_type,
        'target_name': target_name,
        'industry': industry,
        'employee_count': employee_count,
    }

    # Create analysis task
    task = task_manager.create_task(
        file_paths=saved_files,
        domains=domains,
        deal_context=deal_context
    )

    # Store task ID in Flask session
    flask_session['current_task_id'] = task.task_id
    flask_session['analysis_file_count'] = len(saved_files)

    # Associate task with user session
    session_id = get_or_create_session_id(flask_session)
    session_store.set_analysis_task(session_id, task.task_id)

    # Start background analysis
    # Use simple runner if full agent infrastructure has issues
    try:
        task_manager.start_task(task.task_id, run_analysis)
    except ImportError:
        # Fall back to simple runner if agent imports fail
        task_manager.start_task(task.task_id, run_analysis_simple)

    # Redirect to processing page
    return redirect(url_for('processing'))


@app.route('/processing')
def processing():
    """Processing/loading page shown while analysis runs."""
    file_count = flask_session.get('analysis_file_count', 0)
    task_id = flask_session.get('current_task_id')

    # Get initial task status if available
    initial_status = None
    if task_id:
        initial_status = task_manager.get_task_status(task_id)

    return render_template('processing.html',
                          file_count=file_count,
                          task_id=task_id,
                          initial_status=initial_status)


@app.route('/analysis/status')
def analysis_status():
    """Check analysis progress. Returns JSON for polling."""
    task_id = flask_session.get('current_task_id')

    if not task_id:
        # No task - check for existing results
        from config_v2 import FACTS_DIR
        facts_files = list(FACTS_DIR.glob("facts_*.json"))
        if facts_files:
            return jsonify({
                'complete': True,
                'success': True,
                'status': 'complete',
                'message': 'Previous analysis results available'
            })
        return jsonify({
            'complete': True,
            'success': False,
            'status': 'no_task',
            'message': 'No analysis task found'
        })

    # Get task status from task manager
    status = task_manager.get_task_status(task_id)

    if not status:
        return jsonify({
            'complete': True,
            'success': False,
            'status': 'not_found',
            'message': f'Task {task_id} not found'
        })

    # If completed successfully, load results into session
    if status['complete'] and status['success']:
        session_id = get_or_create_session_id(flask_session)
        if status.get('facts_file'):
            session_store.load_session_from_results(
                session_id,
                status['facts_file'],
                status.get('findings_file')
            )

    return jsonify(status)


@app.route('/analysis/cancel', methods=['POST'])
def cancel_analysis():
    """Cancel a running analysis."""
    task_id = flask_session.get('current_task_id')

    if not task_id:
        return jsonify({'success': False, 'message': 'No task to cancel'})

    success = task_manager.cancel_task(task_id)

    return jsonify({
        'success': success,
        'message': 'Task cancelled' if success else 'Could not cancel task'
    })


@app.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    s = get_session()
    summary = s.get_summary()

    # Get top risks
    top_risks = sorted(s.reasoning_store.risks,
                       key=lambda r: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(r.severity, 4))[:5]

    # Get recent work items by phase
    day1_items = [w for w in s.reasoning_store.work_items if w.phase == 'Day_1'][:5]

    # Get analysis metadata from current task
    analysis_metadata = None
    task_id = flask_session.get('current_task_id')
    if task_id:
        task = task_manager.get_task(task_id)
        if task:
            from datetime import datetime
            analysis_metadata = {
                'file_count': len(task.file_paths),
                'timestamp': task.completed_at[:10] if task.completed_at else None,
                'domains': task.domains,
                'task_id': task_id,
            }

    return render_template('dashboard.html',
                         summary=summary,
                         top_risks=top_risks,
                         day1_items=day1_items,
                         analysis_metadata=analysis_metadata,
                         session=s)


@app.route('/risks')
def risks():
    """List all risks with pagination."""
    s = get_session()
    severity_filter = request.args.get('severity', '')
    domain_filter = request.args.get('domain', '')
    search_query = request.args.get('q', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = 50

    risks_list = list(s.reasoning_store.risks)

    # Apply filters
    if severity_filter:
        risks_list = [r for r in risks_list if r.severity == severity_filter]
    if domain_filter:
        risks_list = [r for r in risks_list if r.domain == domain_filter]
    if search_query:
        risks_list = [r for r in risks_list if search_query in r.title.lower()
                      or search_query in (r.description or '').lower()]

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    risks_list = sorted(risks_list, key=lambda r: severity_order.get(r.severity, 4))

    # Pagination
    total = len(risks_list)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_risks = risks_list[start:end]

    domains = list(set(r.domain for r in s.reasoning_store.risks))

    return render_template('risks.html',
                         risks=paginated_risks,
                         all_risks=risks_list,
                         domains=domains,
                         severity_filter=severity_filter,
                         domain_filter=domain_filter,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         per_page=per_page)


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
    """List all work items with pagination."""
    s = get_session()
    phase_filter = request.args.get('phase', '')
    domain_filter = request.args.get('domain', '')
    search_query = request.args.get('q', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = 50

    items = list(s.reasoning_store.work_items)

    # Apply filters
    if phase_filter:
        items = [w for w in items if w.phase == phase_filter]
    if domain_filter:
        items = [w for w in items if w.domain == domain_filter]
    if search_query:
        items = [w for w in items if search_query in w.title.lower()
                 or search_query in (w.description or '').lower()]

    # Group by phase (before pagination for totals)
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

    # Pagination (on flat list)
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]

    # Re-group paginated items for display
    paginated_by_phase = {'Day_1': [], 'Day_100': [], 'Post_100': []}
    for wi in paginated_items:
        if wi.phase in paginated_by_phase:
            paginated_by_phase[wi.phase].append(wi)

    domains = list(set(w.domain for w in s.reasoning_store.work_items))

    return render_template('work_items.html',
                         by_phase=paginated_by_phase,
                         all_by_phase=by_phase,
                         totals=totals,
                         domains=domains,
                         phase_filter=phase_filter,
                         domain_filter=domain_filter,
                         cost_ranges=COST_RANGE_VALUES,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         per_page=per_page)


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
    """List all facts with pagination."""
    s = get_session()
    domain_filter = request.args.get('domain', '')
    category_filter = request.args.get('category', '')
    entity_filter = request.args.get('entity', '')
    search_query = request.args.get('q', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = 50

    facts_list = list(s.fact_store.facts)

    # Apply filters
    if domain_filter:
        facts_list = [f for f in facts_list if f.domain == domain_filter]
    if category_filter:
        facts_list = [f for f in facts_list if f.category == category_filter]
    if entity_filter:
        facts_list = [f for f in facts_list if getattr(f, 'entity', 'target') == entity_filter]
    if search_query:
        facts_list = [f for f in facts_list if search_query in f.item.lower()
                      or search_query in str(f.details or '').lower()]

    # Pagination
    total = len(facts_list)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_facts = facts_list[start:end]

    domains = list(set(f.domain for f in s.fact_store.facts))
    categories = list(set(f.category for f in s.fact_store.facts))

    return render_template('facts.html',
                         facts=paginated_facts,
                         all_facts=facts_list,
                         domains=domains,
                         categories=categories,
                         domain_filter=domain_filter,
                         category_filter=category_filter,
                         entity_filter=entity_filter,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         per_page=per_page)


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
    """List all gaps with pagination."""
    s = get_session()
    domain_filter = request.args.get('domain', '')
    importance_filter = request.args.get('importance', '')
    search_query = request.args.get('q', '').lower()
    page = request.args.get('page', 1, type=int)
    per_page = 50

    gaps_list = list(s.fact_store.gaps)

    # Apply filters
    if domain_filter:
        gaps_list = [g for g in gaps_list if g.domain == domain_filter]
    if importance_filter:
        gaps_list = [g for g in gaps_list if g.importance == importance_filter]
    if search_query:
        gaps_list = [g for g in gaps_list if search_query in g.description.lower()]

    # Sort by importance
    importance_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    gaps_list = sorted(gaps_list, key=lambda g: importance_order.get(g.importance, 4))

    # Pagination
    total = len(gaps_list)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_gaps = gaps_list[start:end]

    domains = list(set(g.domain for g in s.fact_store.gaps))

    return render_template('gaps.html',
                         gaps=paginated_gaps,
                         all_gaps=gaps_list,
                         domains=domains,
                         domain_filter=domain_filter,
                         importance_filter=importance_filter,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         per_page=per_page)


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


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error.html',
                          error_code=404,
                          error_title="Page Not Found",
                          error_message="The page you're looking for doesn't exist."), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('error.html',
                          error_code=500,
                          error_title="Internal Server Error",
                          error_message="Something went wrong on our end. Please try again."), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle uncaught exceptions."""
    # Log the error
    import traceback
    print(f"Unhandled exception: {e}")
    traceback.print_exc()

    # Return user-friendly error
    if request.accept_mimetypes.best == 'application/json':
        return jsonify({
            'error': True,
            'message': str(e),
            'type': type(e).__name__
        }), 500

    return render_template('error.html',
                          error_code=500,
                          error_title="Error",
                          error_message=str(e)), 500


# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    from config_v2 import validate_environment, get_config_summary

    env_status = validate_environment()
    config = get_config_summary()

    return jsonify({
        'status': 'healthy' if env_status['valid'] else 'degraded',
        'service': 'it-dd-agent',
        'version': '2.0',
        'environment': {
            'valid': env_status['valid'],
            'api_key_configured': env_status['api_key_configured'],
            'warnings': env_status['warnings'],
            'errors': env_status['errors']
        },
        'config': {
            'domains': config['domains'],
            'parallel_enabled': config['parallel_enabled'],
        }
    })


@app.route('/api/session/info')
def session_info():
    """Get current session information."""
    s = get_session()
    summary = s.get_summary()

    task_id = flask_session.get('current_task_id')
    task_status = None
    if task_id:
        task_status = task_manager.get_task_status(task_id)

    return jsonify({
        'summary': summary,
        'task_id': task_id,
        'task_status': task_status,
        'has_results': summary.get('facts', 0) > 0 or summary.get('risks', 0) > 0
    })


@app.route('/api/pipeline/status')
def pipeline_status():
    """Check analysis pipeline component availability."""
    from web.analysis_runner import check_pipeline_availability

    status = check_pipeline_availability()

    return jsonify({
        'ready': status['api_key'] and status['pdf_parser'],
        'components': {
            'api_key': status['api_key'],
            'pdf_parser': status['pdf_parser'],
            'fact_store': status['fact_store'],
            'discovery_agents': status['discovery_agents'],
            'reasoning_agents': status['reasoning_agents'],
        },
        'errors': status['errors'] if status['errors'] else None
    })


@app.route('/api/cleanup', methods=['POST'])
def cleanup_tasks():
    """Cleanup old tasks and sessions."""
    tasks_cleaned = 0
    sessions_cleaned = 0

    # Cleanup old tasks
    task_manager.cleanup_old_tasks(max_age_hours=24)

    # Cleanup expired sessions
    sessions_cleaned = session_store.cleanup_expired()

    return jsonify({
        'success': True,
        'tasks_cleaned': tasks_cleaned,
        'sessions_cleaned': sessions_cleaned
    })


@app.route('/api/export/json')
def export_json():
    """Export all analysis data as JSON."""
    s = get_session()

    # Compile all data
    export_data = {
        'summary': s.get_summary(),
        'facts': [
            {
                'id': f.fact_id,
                'domain': f.domain,
                'category': f.category,
                'item': f.item,
                'details': f.details,
                'status': f.status,
                'entity': getattr(f, 'entity', 'target'),
            }
            for f in s.fact_store.facts
        ],
        'gaps': [
            {
                'id': g.gap_id,
                'domain': g.domain,
                'category': g.category,
                'description': g.description,
                'importance': g.importance,
            }
            for g in s.fact_store.gaps
        ],
        'risks': [
            {
                'id': r.finding_id,
                'domain': r.domain,
                'title': r.title,
                'description': r.description,
                'severity': r.severity,
                'category': r.category,
                'mitigation': r.mitigation,
                'based_on_facts': r.based_on_facts,
            }
            for r in s.reasoning_store.risks
        ],
        'work_items': [
            {
                'id': w.finding_id,
                'domain': w.domain,
                'title': w.title,
                'description': w.description,
                'phase': w.phase,
                'priority': w.priority,
                'owner_type': w.owner_type,
                'cost_estimate': w.cost_estimate,
                'based_on_facts': w.based_on_facts,
            }
            for w in s.reasoning_store.work_items
        ],
    }

    return jsonify(export_data)


@app.route('/api/facts')
def api_facts():
    """Get facts as JSON with optional filtering."""
    s = get_session()
    domain = request.args.get('domain')
    category = request.args.get('category')

    facts = list(s.fact_store.facts)

    if domain:
        facts = [f for f in facts if f.domain == domain]
    if category:
        facts = [f for f in facts if f.category == category]

    return jsonify({
        'count': len(facts),
        'facts': [
            {
                'id': f.fact_id,
                'domain': f.domain,
                'category': f.category,
                'item': f.item,
                'details': f.details,
                'status': f.status,
            }
            for f in facts
        ]
    })


@app.route('/api/risks')
def api_risks():
    """Get risks as JSON with optional filtering."""
    s = get_session()
    domain = request.args.get('domain')
    severity = request.args.get('severity')

    risks = list(s.reasoning_store.risks)

    if domain:
        risks = [r for r in risks if r.domain == domain]
    if severity:
        risks = [r for r in risks if r.severity == severity]

    return jsonify({
        'count': len(risks),
        'risks': [
            {
                'id': r.finding_id,
                'domain': r.domain,
                'title': r.title,
                'description': r.description,
                'severity': r.severity,
                'mitigation': r.mitigation,
            }
            for r in risks
        ]
    })


@app.route('/api/export/excel')
def export_excel():
    """Export analysis data as Excel file."""
    from io import BytesIO
    from flask import send_file

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return jsonify({'error': 'openpyxl not installed'}), 500

    s = get_session()

    # Create workbook
    wb = openpyxl.Workbook()

    # Style definitions
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    summary = s.get_summary()
    summary_data = [
        ["IT Due Diligence Analysis Summary"],
        [""],
        ["Metric", "Value"],
        ["Facts Discovered", summary.get('facts', 0)],
        ["Information Gaps", summary.get('gaps', 0)],
        ["Risks Identified", summary.get('risks', 0)],
        ["Work Items", summary.get('work_items', 0)],
        [""],
        ["Risk Summary"],
        ["Critical", summary.get('risk_summary', {}).get('critical', 0)],
        ["High", summary.get('risk_summary', {}).get('high', 0)],
        ["Medium", summary.get('risk_summary', {}).get('medium', 0)],
        ["Low", summary.get('risk_summary', {}).get('low', 0)],
    ]
    for row in summary_data:
        ws_summary.append(row)

    # Risks sheet
    ws_risks = wb.create_sheet("Risks")
    risk_headers = ["ID", "Domain", "Severity", "Title", "Description", "Mitigation"]
    ws_risks.append(risk_headers)
    for col, header in enumerate(risk_headers, 1):
        cell = ws_risks.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill

    for risk in s.reasoning_store.risks:
        ws_risks.append([
            risk.finding_id,
            risk.domain,
            risk.severity.upper(),
            risk.title,
            risk.description or "",
            risk.mitigation or ""
        ])

    # Work Items sheet
    ws_items = wb.create_sheet("Work Items")
    item_headers = ["ID", "Domain", "Phase", "Priority", "Title", "Description", "Cost Estimate", "Owner"]
    ws_items.append(item_headers)
    for col, header in enumerate(item_headers, 1):
        cell = ws_items.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill

    for wi in s.reasoning_store.work_items:
        ws_items.append([
            wi.finding_id,
            wi.domain,
            wi.phase,
            wi.priority,
            wi.title,
            wi.description or "",
            wi.cost_estimate,
            wi.owner_type
        ])

    # Facts sheet
    ws_facts = wb.create_sheet("Facts")
    fact_headers = ["ID", "Domain", "Category", "Item", "Status"]
    ws_facts.append(fact_headers)
    for col, header in enumerate(fact_headers, 1):
        cell = ws_facts.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill

    for fact in s.fact_store.facts:
        ws_facts.append([
            fact.fact_id,
            fact.domain,
            fact.category,
            fact.item,
            fact.status
        ])

    # Gaps sheet
    ws_gaps = wb.create_sheet("Gaps")
    gap_headers = ["ID", "Domain", "Category", "Importance", "Description"]
    ws_gaps.append(gap_headers)
    for col, header in enumerate(gap_headers, 1):
        cell = ws_gaps.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill

    for gap in s.fact_store.gaps:
        ws_gaps.append([
            gap.gap_id,
            gap.domain,
            gap.category,
            gap.importance,
            gap.description
        ])

    # Auto-adjust column widths
    for ws in [ws_summary, ws_risks, ws_items, ws_facts, ws_gaps]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    from datetime import datetime
    filename = f"it_due_diligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  IT Due Diligence Agent - Web Interface")
    print("="*60)
    print("\n  Starting server at: http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
