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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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


# Custom Jinja filter to clean up Gap object strings in question text
import re

@app.template_filter('clean_gap_text')
def clean_gap_text(text):
    """
    Clean up Gap object strings that were accidentally serialized into question text.

    Converts: "Can you provide documentation for: Gap(gap_id='G-CYBER-001', ..., description='No explicit...', ...)"
    To: "Can you provide documentation for: No explicit..."
    """
    if not text or 'Gap(' not in text:
        return text

    # Pattern to extract description from Gap object string
    # Handles both single quotes and HTML-escaped quotes (&#39;)
    pattern = r"Gap\([^)]*description=['\"]([^'\"]+)['\"][^)]*\)"
    pattern_escaped = r"Gap\([^)]*description=(?:&#39;|')([^'&]+)(?:&#39;|')[^)]*\)"

    # Try to extract and replace with just the description
    match = re.search(pattern_escaped, text) or re.search(pattern, text)
    if match:
        description = match.group(1)
        # Replace the entire Gap(...) with just the description
        text = re.sub(pattern_escaped, description, text)
        text = re.sub(pattern, description, text)

    return text


def get_session():
    """Get the analysis session for the current user.

    IMPORTANT: This function now checks for newer files on disk and invalidates
    cached sessions if newer data exists. This fixes the stale cache issue.
    """
    import logging
    logger = logging.getLogger(__name__)

    session_id = get_or_create_session_id(flask_session)
    user_session = session_store.get_session(session_id)

    # First, find the newest valid facts file on disk
    from config_v2 import OUTPUT_DIR

    facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    findings_files = sorted(OUTPUT_DIR.glob("findings_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

    newest_facts_file = None
    newest_facts_mtime = 0

    for f in facts_files:
        if f.stat().st_size > 500:  # Skip empty files
            newest_facts_file = f
            newest_facts_mtime = f.stat().st_mtime
            break

    # Check if we have a cached session and if it's still valid
    if user_session and user_session.analysis_session:
        cached = user_session.analysis_session
        if cached.fact_store and len(cached.fact_store.facts) > 0:
            # Check if cache is newer than files (cache is valid)
            cache_time = getattr(user_session, '_cache_mtime', 0)
            if cache_time >= newest_facts_mtime:
                logger.debug(f"Using cached session with {len(cached.fact_store.facts)} facts (cache valid)")
                return cached
            else:
                logger.info(f"Cache stale: cache_time={cache_time}, newest_file_time={newest_facts_mtime}")
                # Clear stale cache
                user_session.analysis_session = None
                clear_organization_cache()  # Also clear org cache when session cache invalidated

    # Try to load from task results if available
    task_id = flask_session.get('current_task_id')
    if task_id:
        task = task_manager.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED and task.facts_file:
            logger.info(f"Loading session from task {task_id}: {task.facts_file}")
            analysis_session = session_store.load_session_from_results(
                session_id,
                task.facts_file,
                task.findings_file
            )
            if analysis_session and analysis_session.fact_store and len(analysis_session.fact_store.facts) > 0:
                logger.info(f"Loaded {len(analysis_session.fact_store.facts)} facts from task")
                # Track when this was cached
                if user_session:
                    user_session._cache_mtime = newest_facts_mtime
                return analysis_session
        elif not task:
            # Clear stale task_id if task no longer exists
            flask_session.pop('current_task_id', None)

    # Load from most recent NON-EMPTY facts file
    logger.debug(f"Found {len(facts_files)} facts files in {OUTPUT_DIR}")

    if newest_facts_file:
        logger.info(f"Loading from facts file: {newest_facts_file} ({newest_facts_file.stat().st_size} bytes)")
        analysis_session = Session.load_from_files(
            facts_file=newest_facts_file,
            findings_file=findings_files[0] if findings_files else None
        )
        if analysis_session and analysis_session.fact_store and len(analysis_session.fact_store.facts) > 0:
            logger.info(f"Loaded {len(analysis_session.fact_store.facts)} facts from {newest_facts_file.name}")
            # Store in session store for future access with timestamp
            if user_session:
                user_session.analysis_session = analysis_session
                user_session._cache_mtime = newest_facts_mtime
            return analysis_session
        else:
            logger.warning(f"File {newest_facts_file.name} had no facts")

    logger.warning("No valid facts files found, creating empty session")
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
    deal_type = request.form.get('deal_type', 'bolt_on')
    target_name = request.form.get('target_name', 'Target Company')
    industry = request.form.get('industry', '')
    sub_industry = request.form.get('sub_industry', '')
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
        'sub_industry': sub_industry,
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
        # No task - check for existing results in both locations
        from config_v2 import FACTS_DIR, OUTPUT_DIR
        facts_files = list(FACTS_DIR.glob("facts_*.json")) + list(OUTPUT_DIR.glob("facts_*.json"))
        if facts_files:
            return jsonify({
                'complete': True,
                'success': True,
                'status': 'complete',
                'message': 'Previous analysis results available',
                'redirect': '/dashboard'
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
        # Clear stale task_id from session
        flask_session.pop('current_task_id', None)
        # Redirect to dashboard instead of showing error
        return jsonify({
            'complete': True,
            'success': True,
            'status': 'redirecting',
            'message': 'Loading existing analysis results',
            'redirect': '/dashboard'
        })

    # If completed successfully, load results into session and invalidate all caches
    if status['complete'] and status['success']:
        session_id = get_or_create_session_id(flask_session)
        if status.get('facts_file'):
            # First invalidate all caches to ensure fresh data
            invalidate_all_caches()

            # Then load the new results
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


@app.route('/open-questions')
def open_questions():
    """Display open questions for the deal team."""
    from pathlib import Path
    from config_v2 import OUTPUT_DIR
    import json

    # Get deal context for display
    s = get_session()
    deal_context = s.deal_context if hasattr(s, 'deal_context') else {}

    # Find most recent open questions file
    questions = []
    questions_files = sorted(OUTPUT_DIR.glob("open_questions_*.json"), reverse=True)
    if questions_files:
        try:
            with open(questions_files[0]) as f:
                questions = json.load(f)
        except Exception as e:
            flash(f'Error loading open questions: {e}', 'error')

    # If no file exists, generate questions based on current context
    if not questions and deal_context.get('industry'):
        try:
            from tools_v2.open_questions import generate_open_questions_for_deal
            questions = generate_open_questions_for_deal(
                industry=deal_context.get('industry'),
                sub_industry=deal_context.get('sub_industry'),
                deal_type=deal_context.get('deal_type', 'bolt_on'),
                gaps=list(s.fact_store.gaps) if hasattr(s, 'fact_store') else []
            )
        except Exception as e:
            flash(f'Error generating questions: {e}', 'error')

    # Group questions by priority
    by_priority = {'critical': [], 'important': [], 'nice_to_have': []}
    for q in questions:
        priority = q.get('priority', 'important')
        if priority in by_priority:
            by_priority[priority].append(q)

    # Group by category for alternative view
    by_category = {}
    for q in questions:
        cat = q.get('category', 'operational')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)

    return render_template('open_questions.html',
                         questions=questions,
                         by_priority=by_priority,
                         by_category=by_category,
                         deal_context=deal_context,
                         total=len(questions))


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
_org_facts_count = 0  # Track fact count to detect new analyses
_org_cache_session_id = None  # Track which session the cache belongs to
_org_data_source = "unknown"  # Track data source for UI display


def get_organization_analysis():
    """Get or run the organization analysis.

    IMPORTANT: This function now ALWAYS rebuilds from the current session's facts.
    This ensures we never show stale organization data after a new analysis runs.
    """
    global _org_analysis_result, _org_facts_count, _org_data_source, _org_cache_session_id

    import logging
    logger = logging.getLogger(__name__)

    # First, get the current session (this handles cache invalidation)
    try:
        s = get_session()
        logger.info(f"get_organization_analysis: session has fact_store={s.fact_store is not None}")

        if s and s.fact_store:
            total_facts = len(s.fact_store.facts)
            org_facts = [f for f in s.fact_store.facts if f.domain == "organization"]
            current_org_count = len(org_facts)

            # Generate a session fingerprint based on fact content
            # This ensures we rebuild if facts changed, not just count
            fact_ids = sorted([f.fact_id for f in s.fact_store.facts]) if s.fact_store.facts else []
            session_fingerprint = hash(tuple(fact_ids)) if fact_ids else 0

            logger.info(f"Session has {total_facts} total facts, {current_org_count} org facts")
            logger.info(f"Session fingerprint: {session_fingerprint}, cached: {_org_cache_session_id}")

            # Check if we need to rebuild (different session or different facts)
            needs_rebuild = (
                _org_analysis_result is None or
                _org_cache_session_id != session_fingerprint or
                _org_facts_count != current_org_count
            )

            if needs_rebuild and total_facts > 0:
                logger.info(f"Rebuilding organization data (needs_rebuild={needs_rebuild})")

                from services.organization_bridge import build_organization_result
                deal_context = s.deal_context or {}
                target_name = deal_context.get('target_name', 'Target') if isinstance(deal_context, dict) else 'Target'

                logger.info(f"Building org result for target: {target_name}")
                result, status = build_organization_result(s.fact_store, s.reasoning_store, target_name)

                # Update cache with new data
                _org_cache_session_id = session_fingerprint
                _org_facts_count = current_org_count

                if status == "success" and result.total_it_headcount > 0:
                    _org_analysis_result = result
                    _org_data_source = "analysis"
                    logger.info(f"SUCCESS: Built org analysis with {result.total_it_headcount} headcount from {current_org_count} org facts")
                    return _org_analysis_result
                elif status == "no_org_facts":
                    # Analysis ran but no org data found - show empty state, not demo
                    logger.warning(f"Analysis ran with {total_facts} facts but no organization facts found")
                    _org_analysis_result = result  # Empty result
                    _org_data_source = "analysis_no_org"
                    return _org_analysis_result
                else:
                    logger.warning(f"build_organization_result returned status={status}, headcount={result.total_it_headcount}")
                    # Still cache this result to avoid rebuilding every time
                    _org_analysis_result = result
                    _org_data_source = "analysis"
                    return _org_analysis_result

            elif _org_analysis_result is not None:
                # Cache is valid, return cached result
                logger.debug(f"Using cached org result ({_org_facts_count} org facts)")
                return _org_analysis_result

    except Exception as e:
        import traceback
        logger.error(f"Could not build org from facts: {e}")
        logger.error(traceback.format_exc())

    # Fall back to demo data only if we have nothing
    if _org_analysis_result is None:
        logger.warning("Falling back to DEMO data - no real org data available")
        _org_analysis_result = _create_demo_organization_data()
        _org_data_source = "demo"
        _org_cache_session_id = None
        _org_facts_count = 0

    return _org_analysis_result


def get_org_data_source():
    """Get whether org data is from analysis or demo."""
    global _org_data_source
    return _org_data_source


def clear_organization_cache():
    """Clear the organization cache to force rebuild."""
    global _org_analysis_result, _org_facts_count, _org_cache_session_id, _org_data_source
    _org_analysis_result = None
    _org_facts_count = 0
    _org_cache_session_id = None
    _org_data_source = "unknown"


def invalidate_all_caches():
    """Invalidate all caches - call this after new analysis completes."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Invalidating all caches after analysis")

    # Clear organization cache
    clear_organization_cache()

    # Clear session store caches
    session_id = flask_session.get('session_id')
    if session_id:
        user_session = session_store.get_session(session_id)
        if user_session:
            user_session.analysis_session = None
            user_session._cache_mtime = 0
    _org_facts_count = 0


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


@app.route('/organization/refresh')
def organization_refresh():
    """Refresh organization data from current analysis.

    This forces a complete cache invalidation and reload from the latest files.
    """
    # Invalidate ALL caches to ensure we get fresh data
    invalidate_all_caches()

    # Now get fresh session data (will reload from newest files)
    s = get_session()
    if s and s.fact_store:
        total_facts = len(s.fact_store.facts)
        org_facts = len([f for f in s.fact_store.facts if f.domain == "organization"])
        flash(f'Organization data refreshed - found {org_facts} org facts (of {total_facts} total)', 'success')
    else:
        flash('Organization cache cleared - no analysis session found', 'warning')

    return redirect(url_for('organization_overview'))


@app.route('/organization')
def organization_overview():
    """Organization module overview."""
    result = get_organization_analysis()
    data_source = get_org_data_source()

    return render_template('organization/overview.html',
                         result=result,
                         store=result.data_store,
                         comparison=result.benchmark_comparison,
                         msp_summary=result.msp_summary,
                         ss_summary=result.shared_services_summary,
                         data_source=data_source)


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

    # Get MSP relationships for the org chart
    msp_relationships = store.msp_relationships if hasattr(store, 'msp_relationships') else []

    return render_template('organization/staffing_tree.html',
                         categories=categories_by_name,
                         total_headcount=store.get_target_headcount(),
                         total_compensation=store.total_compensation,
                         fte_count=store.total_internal_fte,
                         contractor_count=store.total_contractor,
                         key_person_count=len(store.get_key_persons()),
                         msp_relationships=msp_relationships)


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


# Organization manual analysis endpoint removed - organization data now comes directly from document analysis


# =============================================================================
# Applications Inventory Routes
# =============================================================================

@app.route('/applications')
def applications_overview():
    """Applications inventory overview."""
    from services.applications_bridge import build_applications_inventory

    session = get_session()

    if session and session.fact_store:
        inventory, status = build_applications_inventory(session.fact_store)
        data_source = "analysis"
    else:
        # Return empty inventory
        from services.applications_bridge import ApplicationsInventory
        inventory = ApplicationsInventory()
        status = "no_facts"
        data_source = "none"

    return render_template('applications/overview.html',
                          inventory=inventory,
                          status=status,
                          data_source=data_source)


@app.route('/applications/<category>')
def applications_category(category):
    """View applications in a specific category."""
    from services.applications_bridge import build_applications_inventory

    session = get_session()

    if session and session.fact_store:
        inventory, status = build_applications_inventory(session.fact_store)
    else:
        from services.applications_bridge import ApplicationsInventory
        inventory = ApplicationsInventory()
        status = "no_facts"

    # Get category summary
    cat_summary = inventory.by_category.get(category)
    if not cat_summary:
        flash(f'Category "{category}" not found', 'warning')
        return redirect(url_for('applications_overview'))

    return render_template('applications/category.html',
                          category=cat_summary,
                          inventory=inventory)


# =============================================================================
# Infrastructure Inventory Routes
# =============================================================================

@app.route('/infrastructure')
def infrastructure_overview():
    """Infrastructure inventory overview."""
    from services.infrastructure_bridge import build_infrastructure_inventory

    session = get_session()

    if session and session.fact_store:
        inventory, status = build_infrastructure_inventory(session.fact_store)
        data_source = "analysis"
    else:
        # Return empty inventory
        from services.infrastructure_bridge import InfrastructureInventory
        inventory = InfrastructureInventory()
        status = "no_facts"
        data_source = "none"

    return render_template('infrastructure/overview.html',
                          inventory=inventory,
                          status=status,
                          data_source=data_source)


@app.route('/infrastructure/<category>')
def infrastructure_category(category):
    """View infrastructure in a specific category."""
    from services.infrastructure_bridge import build_infrastructure_inventory

    session = get_session()

    if session and session.fact_store:
        inventory, status = build_infrastructure_inventory(session.fact_store)
    else:
        from services.infrastructure_bridge import InfrastructureInventory
        inventory = InfrastructureInventory()
        status = "no_facts"

    # Get category summary
    cat_summary = inventory.by_category.get(category)
    if not cat_summary:
        flash(f'Category "{category}" not found', 'warning')
        return redirect(url_for('infrastructure_overview'))

    return render_template('infrastructure/category.html',
                          category=cat_summary,
                          inventory=inventory)


# =============================================================================
# Fact Review Queue (Phase 1 - Validation Workflow)
# =============================================================================

@app.route('/review')
def review_queue_page():
    """
    Fact validation review queue page.

    Displays facts needing human review, prioritized by importance.
    """
    s = get_session()

    # Get review queue stats
    stats = s.fact_store.get_review_stats()

    # Get initial queue (first 50 highest priority)
    queue = s.fact_store.get_review_queue(limit=50)

    # Get domain list for filtering
    domains = list(stats.get('by_domain', {}).keys())

    return render_template(
        'review/queue.html',
        stats=stats,
        queue=queue,
        domains=domains,
        data_source='analysis' if len(s.fact_store.facts) > 0 else 'none'
    )


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
                'source_document': f.source_document,
                'confidence_score': f.confidence_score,
                'verified': f.verified,
                'verified_by': f.verified_by,
                'verified_at': f.verified_at,
            }
            for f in facts
        ]
    })


@app.route('/api/facts/<fact_id>/verify', methods=['POST'])
def verify_fact(fact_id):
    """Mark a fact as verified by a human reviewer."""
    s = get_session()

    # Get the verified_by from request data or default
    data = request.get_json() or {}
    verified_by = data.get('verified_by', 'web_user')

    # Attempt to verify the fact
    success = s.fact_store.verify_fact(fact_id, verified_by)

    if success:
        # Save the updated fact store
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        return jsonify({
            'status': 'success',
            'message': f'Fact {fact_id} verified by {verified_by}',
            'fact_id': fact_id,
            'verified': True,
            'verified_by': verified_by
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/<fact_id>/unverify', methods=['POST'])
def unverify_fact(fact_id):
    """Remove verification status from a fact."""
    s = get_session()

    success = s.fact_store.unverify_fact(fact_id)

    if success:
        # Save the updated fact store
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        return jsonify({
            'status': 'success',
            'message': f'Verification removed from {fact_id}',
            'fact_id': fact_id,
            'verified': False
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/verification-stats')
def verification_stats():
    """Get verification statistics for all facts."""
    s = get_session()
    stats = s.fact_store.get_verification_stats()
    return jsonify(stats)


@app.route('/api/facts/confidence-summary')
def confidence_summary():
    """Get confidence score summary for all facts."""
    s = get_session()
    summary = s.fact_store.get_confidence_summary()
    return jsonify(summary)


# =============================================================================
# REVIEW QUEUE API (Phase 1 - Validation Workflow)
# =============================================================================

@app.route('/api/review/queue')
def review_queue():
    """
    Get facts needing review, sorted by priority.

    Query params:
        domain: Filter by domain
        limit: Max facts to return (default 50)
        include_skipped: Include previously skipped facts (default false)
    """
    s = get_session()

    domain = request.args.get('domain')
    limit = int(request.args.get('limit', 50))
    include_skipped = request.args.get('include_skipped', 'false').lower() == 'true'

    facts = s.fact_store.get_review_queue(
        domain=domain,
        limit=limit,
        include_skipped=include_skipped
    )

    return jsonify({
        'count': len(facts),
        'facts': [
            {
                'fact_id': f.fact_id,
                'domain': f.domain,
                'category': f.category,
                'item': f.item,
                'details': f.details,
                'evidence': f.evidence,
                'source_document': f.source_document,
                'confidence_score': f.confidence_score,
                'review_priority': f.review_priority,
                'verification_status': f.verification_status,
                'verification_note': f.verification_note,
                'entity': f.entity
            }
            for f in facts
        ]
    })


@app.route('/api/review/stats')
def review_stats():
    """Get comprehensive review queue statistics."""
    s = get_session()
    stats = s.fact_store.get_review_stats()
    return jsonify(stats)


@app.route('/api/review/export-report')
def export_verification_report():
    """Export verification report as markdown."""
    s = get_session()
    stats = s.fact_store.get_review_stats()

    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    report = f"""# Fact Verification Report

**Generated:** {date}

## Summary

| Metric | Count |
|--------|-------|
| Total Facts | {stats['total_facts']} |
| Confirmed | {stats['confirmed']} |
| Flagged Incorrect | {stats['incorrect']} |
| Needs Information | {stats['needs_info']} |
| Skipped | {stats['skipped']} |
| **Completion Rate** | **{int(stats['completion_rate'] * 100)}%** |

## Progress by Domain

| Domain | Confirmed | Total | Rate |
|--------|-----------|-------|------|
"""
    for domain, dstats in stats.get('by_domain', {}).items():
        rate = int((dstats['confirmed'] / dstats['total']) * 100) if dstats['total'] > 0 else 0
        report += f"| {domain.replace('_', ' ')} | {dstats['confirmed']} | {dstats['total']} | {rate}% |\n"

    conf = stats.get('confidence_breakdown', {})
    report += f"""
## Confidence Distribution

- **High Confidence (80%+):** {conf.get('high', 0)} facts
- **Medium Confidence (50-80%):** {conf.get('medium', 0)} facts
- **Low Confidence (<50%):** {conf.get('low', 0)} facts

## Quality Notes

- Average confidence score: {int((stats.get('average_confidence', 0)) * 100)}%
- Critical items remaining: {stats.get('remaining_critical', 0)}
- Verified today: {stats.get('verified_today', 0)}

---
*Report generated by IT Due Diligence Agent*
"""

    from flask import Response
    return Response(
        report,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename=verification_report_{date}.md'}
    )


@app.route('/api/facts/<fact_id>/status', methods=['POST'])
def update_fact_status(fact_id):
    """
    Update verification status for a fact.

    JSON body:
        status: pending, confirmed, incorrect, needs_info, skipped
        reviewer_id: Who is making this update
        note: Optional verification note
    """
    s = get_session()
    data = request.get_json() or {}

    status = data.get('status')
    reviewer_id = data.get('reviewer_id', 'web_user')
    note = data.get('note', '')

    if not status:
        return jsonify({
            'status': 'error',
            'message': 'status field is required'
        }), 400

    try:
        success = s.fact_store.update_verification_status(
            fact_id=fact_id,
            status=status,
            reviewer_id=reviewer_id,
            note=note
        )
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

    if success:
        # Save the updated fact store
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        # Get updated fact for response
        fact = s.fact_store.get_fact(fact_id)

        return jsonify({
            'status': 'success',
            'message': f'Fact {fact_id} status updated to {status}',
            'fact_id': fact_id,
            'verification_status': fact.verification_status,
            'confidence_score': fact.confidence_score,
            'verified': fact.verified
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/<fact_id>/skip', methods=['POST'])
def skip_fact(fact_id):
    """Mark a fact as skipped (will revisit later)."""
    s = get_session()
    data = request.get_json() or {}
    reviewer_id = data.get('reviewer_id', 'web_user')

    success = s.fact_store.update_verification_status(
        fact_id=fact_id,
        status='skipped',
        reviewer_id=reviewer_id,
        note=data.get('note', 'Skipped for later review')
    )

    if success:
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        return jsonify({
            'status': 'success',
            'message': f'Fact {fact_id} skipped',
            'fact_id': fact_id
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/<fact_id>/flag-incorrect', methods=['POST'])
def flag_incorrect(fact_id):
    """Mark a fact as incorrect."""
    s = get_session()
    data = request.get_json() or {}
    reviewer_id = data.get('reviewer_id', 'web_user')
    reason = data.get('reason', '')

    if not reason:
        return jsonify({
            'status': 'error',
            'message': 'reason field is required when flagging as incorrect'
        }), 400

    success = s.fact_store.update_verification_status(
        fact_id=fact_id,
        status='incorrect',
        reviewer_id=reviewer_id,
        note=f"INCORRECT: {reason}"
    )

    if success:
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        return jsonify({
            'status': 'success',
            'message': f'Fact {fact_id} flagged as incorrect',
            'fact_id': fact_id
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/<fact_id>/needs-info', methods=['POST'])
def needs_more_info(fact_id):
    """Mark a fact as needing more information and optionally create a question."""
    s = get_session()
    data = request.get_json() or {}
    reviewer_id = data.get('reviewer_id', 'web_user')
    question = data.get('question', '')
    recipient = data.get('recipient', '')

    # Build the note
    note_parts = ["NEEDS INFO"]
    if question:
        note_parts.append(f"Question: {question}")
    if recipient:
        note_parts.append(f"Ask: {recipient}")
    note = " | ".join(note_parts)

    success = s.fact_store.update_verification_status(
        fact_id=fact_id,
        status='needs_info',
        reviewer_id=reviewer_id,
        note=note
    )

    if success:
        from config_v2 import OUTPUT_DIR
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

        # Create an OpenQuestion if we have a question (Phase 2 integration)
        question_id = None
        if question:
            try:
                from tools_v2.open_questions import OpenQuestionsStore
                fact = s.fact_store.get_fact(fact_id)
                if fact:
                    questions_store = OpenQuestionsStore()
                    question_id = questions_store.add_question(
                        domain=fact.domain,
                        question=question,
                        context=f"Generated from fact review. Fact: {fact.item}",
                        suggested_recipient=recipient,
                        source_fact_id=fact_id
                    )
            except Exception as e:
                # Don't fail the whole operation if question creation fails
                import logging
                logging.getLogger(__name__).warning(f"Could not create OpenQuestion: {e}")

        return jsonify({
            'status': 'success',
            'message': f'Fact {fact_id} marked as needing more info',
            'fact_id': fact_id,
            'question_id': question_id
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404


@app.route('/api/facts/<fact_id>/note', methods=['PATCH'])
def update_fact_note(fact_id):
    """Update just the note for a fact without changing status."""
    s = get_session()
    data = request.get_json() or {}
    note = data.get('note', '')
    reviewer_id = data.get('reviewer_id', 'web_user')

    fact = s.fact_store.get_fact(fact_id)
    if not fact:
        return jsonify({
            'status': 'error',
            'message': f'Fact {fact_id} not found'
        }), 404

    # Update just the note
    fact.verification_note = note
    fact.reviewer_id = reviewer_id
    from tools_v2.fact_store import _generate_timestamp
    fact.updated_at = _generate_timestamp()

    # Save
    from config_v2 import OUTPUT_DIR
    facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if facts_files:
        s.fact_store.save(str(facts_files[0]))

    return jsonify({
        'status': 'success',
        'message': f'Note updated for {fact_id}',
        'fact_id': fact_id
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


# =============================================================================
# Document Management & Incremental Updates
# =============================================================================

@app.route('/documents')
def documents_page():
    """Document management and incremental update page."""
    s = get_session()

    # Get or create document registry
    if not hasattr(s, 'document_registry'):
        from tools_v2.document_registry import DocumentRegistry
        s.document_registry = DocumentRegistry()

    docs = s.document_registry.get_all_documents()
    stats = s.document_registry.get_stats()
    runs = s.document_registry.get_analysis_runs()

    # Get "What's New" data if we have a fact merger
    whats_new = {"new": [], "updated": [], "conflicts": []}
    pending_conflicts = []
    if hasattr(s, 'fact_merger'):
        whats_new = s.fact_merger.get_whats_new()
        pending_conflicts = s.fact_merger.get_pending_conflicts()

    # Get pending changes from document processor
    pending_changes = getattr(s, 'pending_changes', {"tier1": [], "tier2": [], "tier3": []})

    # Also check document processor for pending changes
    if hasattr(s, 'document_processor'):
        for tier in ["tier1", "tier2", "tier3"]:
            proc_changes = s.document_processor.pending_changes.get(tier, [])
            if proc_changes:
                if tier not in pending_changes:
                    pending_changes[tier] = []
                pending_changes[tier].extend(proc_changes)
        # Sync back to session
        s.pending_changes = pending_changes

    tier_stats = {
        "tier1": len(pending_changes.get("tier1", [])),
        "tier2": len(pending_changes.get("tier2", [])),
        "tier3": len(pending_changes.get("tier3", [])),
        "total": sum(len(pending_changes.get(t, [])) for t in ["tier1", "tier2", "tier3"])
    }

    return render_template('documents/manage.html',
                          documents=docs,
                          stats=stats,
                          analysis_runs=runs,
                          whats_new=whats_new,
                          pending_conflicts=pending_conflicts,
                          tier_stats=tier_stats,
                          data_source='analysis' if docs else 'none')


@app.route('/api/documents')
def api_documents():
    """Get all registered documents."""
    from tools_v2.document_registry import DocumentRegistry
    from config_v2 import OUTPUT_DIR

    s = get_session()

    # Load document registry from file if not in session
    if not hasattr(s, 'document_registry'):
        registry_file = OUTPUT_DIR / "document_registry.json"
        if registry_file.exists():
            try:
                s.document_registry = DocumentRegistry()
                s.document_registry.load_from_file(str(registry_file))
            except Exception as e:
                logger.warning(f"Failed to load document registry: {e}")
                return jsonify({"documents": [], "stats": {}})
        else:
            return jsonify({"documents": [], "stats": {}})

    docs = [d.to_dict() for d in s.document_registry.get_all_documents()]
    stats = s.document_registry.get_stats()

    return jsonify({"documents": docs, "stats": stats})


@app.route('/api/documents/upload', methods=['POST'])
def api_upload_documents():
    """Upload new documents for incremental analysis."""
    from tools_v2.document_registry import DocumentRegistry, ChangeType
    from tools_v2.fact_merger import FactMerger
    from tools_v2.document_processor import DocumentProcessor, ProcessingPriority
    from config_v2 import OUTPUT_DIR

    s = get_session()

    # Registry file path for persistence
    registry_file = OUTPUT_DIR / "document_registry.json"

    # Initialize document registry - load from file if exists
    if not hasattr(s, 'document_registry'):
        s.document_registry = DocumentRegistry()
        if registry_file.exists():
            try:
                s.document_registry.load_from_file(str(registry_file))
                logger.info(f"Loaded document registry with {len(s.document_registry.documents)} documents")
            except Exception as e:
                logger.warning(f"Failed to load document registry: {e}")

    if not hasattr(s, 'fact_merger'):
        s.fact_merger = FactMerger(s.fact_store)

    if not hasattr(s, 'document_processor'):
        s.document_processor = DocumentProcessor(
            document_registry=s.document_registry,
            fact_store=s.fact_store,
            fact_merger=s.fact_merger
        )
        # Load pending changes from file
        s.document_processor.load_pending_changes()
        # Start background worker
        s.document_processor.start_worker()

    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No files provided"}), 400

    files = request.files.getlist('files')
    results = []

    # Create uploads directory if needed
    uploads_dir = DATA_DIR / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        if file.filename:
            # Save file to disk
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = uploads_dir / safe_filename
            file.save(str(file_path))

            # Read content for hash
            with open(file_path, 'rb') as f:
                content = f.read()
            content_text = content.decode('utf-8', errors='ignore')

            # Register document
            record, change_type = s.document_registry.register_document(
                filename=file.filename,
                content=content_text,
                file_path=str(file_path),
                file_size=len(content)
            )

            # Queue for processing if new or updated
            if change_type in [ChangeType.NEW, ChangeType.UPDATED]:
                priority = ProcessingPriority.NORMAL
                s.document_processor.queue_document(
                    doc_id=record.doc_id,
                    filename=file.filename,
                    file_path=str(file_path),
                    priority=priority
                )

            results.append({
                "filename": file.filename,
                "doc_id": record.doc_id,
                "change_type": change_type.value,
                "version": record.version,
                "queued": change_type in [ChangeType.NEW, ChangeType.UPDATED]
            })

    # Save document registry to file for persistence
    try:
        s.document_registry.save_to_file(str(registry_file))
    except Exception as e:
        logger.error(f"Failed to save document registry: {e}")

    return jsonify({
        "status": "success",
        "documents": results,
        "message": f"Registered {len(results)} documents"
    })


@app.route('/api/documents/processing/status')
def processing_status():
    """Get processing status for all documents in queue."""
    s = get_session()

    if not hasattr(s, 'document_processor'):
        return jsonify({"queue": [], "stats": {}})

    all_status = s.document_processor.get_all_status()
    stats = s.document_processor.get_queue_stats()

    return jsonify({
        "queue": all_status,
        "stats": stats
    })


@app.route('/api/documents/<doc_id>/processing-status')
def document_processing_status(doc_id):
    """Get processing status for a specific document."""
    s = get_session()

    if not hasattr(s, 'document_processor'):
        return jsonify({"status": "error", "message": "No processor initialized"}), 400

    status = s.document_processor.get_status(doc_id)
    if not status:
        return jsonify({"status": "not_found", "message": "Document not in processing queue"})

    return jsonify({"status": "success", "processing": status})


@app.route('/api/documents/<doc_id>/process', methods=['POST'])
def process_document_now(doc_id):
    """Manually trigger processing for a document."""
    from tools_v2.document_processor import ProcessingPriority

    s = get_session()

    if not hasattr(s, 'document_registry'):
        return jsonify({"status": "error", "message": "No documents registered"}), 400

    doc = s.document_registry.get_document(doc_id)
    if not doc:
        return jsonify({"status": "error", "message": "Document not found"}), 404

    # Initialize processor if needed
    if not hasattr(s, 'document_processor'):
        from tools_v2.document_processor import DocumentProcessor
        from tools_v2.fact_merger import FactMerger
        if not hasattr(s, 'fact_merger'):
            s.fact_merger = FactMerger(s.fact_store)
        s.document_processor = DocumentProcessor(
            document_registry=s.document_registry,
            fact_store=s.fact_store,
            fact_merger=s.fact_merger
        )
        s.document_processor.start_worker()

    # Get priority from request
    data = request.get_json() or {}
    priority_str = data.get('priority', 'normal').upper()
    priority = getattr(ProcessingPriority, priority_str, ProcessingPriority.NORMAL)

    # Queue document
    s.document_processor.queue_document(
        doc_id=doc.doc_id,
        filename=doc.filename,
        file_path=doc.file_path,
        priority=priority
    )

    return jsonify({
        "status": "success",
        "message": f"Document queued for processing",
        "doc_id": doc_id
    })


@app.route('/api/documents/<doc_id>')
def get_document(doc_id):
    """Get document details."""
    s = get_session()

    if not hasattr(s, 'document_registry'):
        return jsonify({"status": "error", "message": "No documents registered"}), 404

    doc = s.document_registry.get_document(doc_id)
    if not doc:
        return jsonify({"status": "error", "message": "Document not found"}), 404

    return jsonify({"status": "success", "document": doc.to_dict()})


@app.route('/api/documents/<doc_id>/facts')
def get_document_facts(doc_id):
    """Get all facts linked to a document."""
    s = get_session()

    if not hasattr(s, 'document_registry'):
        return jsonify({"facts": []})

    fact_ids = s.document_registry.get_facts_for_document(doc_id)
    facts = [s.fact_store.get_fact(fid).to_dict() for fid in fact_ids if s.fact_store.get_fact(fid)]

    return jsonify({"facts": facts, "count": len(facts)})


@app.route('/api/documents/whats-new')
def whats_new():
    """Get facts that are new or changed since last review."""
    s = get_session()

    if not hasattr(s, 'fact_merger'):
        return jsonify({"new": [], "updated": [], "conflicts": []})

    data = s.fact_merger.get_whats_new()

    return jsonify({
        "new": [f.to_dict() for f in data["new"]],
        "updated": [f.to_dict() for f in data["updated"]],
        "conflicts": [f.to_dict() for f in data["conflicts"]],
        "new_count": len(data["new"]),
        "updated_count": len(data["updated"]),
        "conflict_count": len(data["conflicts"])
    })


@app.route('/api/documents/conflicts')
def get_conflicts():
    """Get pending merge conflicts."""
    s = get_session()

    if not hasattr(s, 'fact_merger'):
        return jsonify({"conflicts": []})

    conflicts = s.fact_merger.get_pending_conflicts()
    return jsonify({
        "conflicts": [c.to_dict() for c in conflicts],
        "count": len(conflicts)
    })


@app.route('/api/documents/conflicts/<conflict_id>/resolve', methods=['POST'])
def resolve_conflict(conflict_id):
    """Resolve a merge conflict."""
    s = get_session()

    if not hasattr(s, 'fact_merger'):
        return jsonify({"status": "error", "message": "No merger initialized"}), 400

    data = request.get_json() or {}
    resolution = data.get('resolution')  # keep_existing, use_new, merge
    resolved_by = data.get('resolved_by', 'web_user')
    notes = data.get('notes', '')

    if not resolution:
        return jsonify({"status": "error", "message": "resolution is required"}), 400

    success = s.fact_merger.resolve_conflict(conflict_id, resolution, resolved_by, notes)

    if success:
        return jsonify({"status": "success", "message": "Conflict resolved"})
    else:
        return jsonify({"status": "error", "message": "Failed to resolve conflict"}), 400


@app.route('/api/documents/clear-markers', methods=['POST'])
def clear_change_markers():
    """Clear [NEW] and [UPDATED] markers after user has reviewed."""
    s = get_session()

    if hasattr(s, 'fact_merger'):
        s.fact_merger.clear_change_markers()
        return jsonify({"status": "success", "message": "Change markers cleared"})

    return jsonify({"status": "error", "message": "No merger initialized"}), 400


@app.route('/api/documents/analysis-runs')
def get_analysis_runs():
    """Get history of analysis runs."""
    s = get_session()

    if not hasattr(s, 'document_registry'):
        return jsonify({"runs": []})

    runs = s.document_registry.get_analysis_runs()
    return jsonify({"runs": runs})


# === Tiered Review API Endpoints (Phase 3) ===

@app.route('/api/changes/pending')
def get_pending_changes():
    """Get all pending changes organized by tier."""
    from config_v2 import OUTPUT_DIR
    import json as json_module

    s = get_session()

    # Load pending changes from file (primary source of truth)
    pending_file = OUTPUT_DIR / "pending_changes.json"
    if pending_file.exists():
        try:
            with open(pending_file, 'r') as f:
                changes = json_module.load(f)
        except Exception as e:
            logger.error(f"Failed to load pending changes: {e}")
            changes = {"tier1": [], "tier2": [], "tier3": []}
    else:
        changes = {"tier1": [], "tier2": [], "tier3": []}

    stats = {
        "total": len(changes.get("tier1", [])) + len(changes.get("tier2", [])) + len(changes.get("tier3", [])),
        "tier1": len(changes.get("tier1", [])),
        "tier2": len(changes.get("tier2", [])),
        "tier3": len(changes.get("tier3", []))
    }

    return jsonify({
        "tier1": changes.get("tier1", []),
        "tier2": changes.get("tier2", []),
        "tier3": changes.get("tier3", []),
        "stats": stats
    })


@app.route('/api/changes/auto-apply', methods=['POST'])
def auto_apply_changes():
    """Auto-apply all Tier 1 eligible changes."""
    s = get_session()

    if not hasattr(s, 'pending_changes') or not hasattr(s, 'fact_merger'):
        return jsonify({"status": "error", "message": "No pending changes"}), 400

    tier1_changes = s.pending_changes.get("tier1", [])
    auto_eligible = [c for c in tier1_changes if c.get("classification", {}).get("auto_apply_eligible")]

    applied = []
    for change in auto_eligible:
        fact_data = change.get("fact", {})
        try:
            from tools_v2.fact_merger import MergeAction
            action, fact_id = s.fact_merger.merge_fact(fact_data, fact_data.get("source_document", ""))
            if action in [MergeAction.ADD, MergeAction.UPDATE]:
                applied.append({
                    "fact_id": fact_id,
                    "item": fact_data.get("item"),
                    "action": action.value
                })
        except Exception as e:
            logger.error(f"Auto-apply failed for fact: {e}")

    # Remove applied changes from pending
    remaining = [c for c in tier1_changes if c not in auto_eligible or c.get("fact", {}).get("temp_id") not in [a.get("temp_id") for a in applied]]
    s.pending_changes["tier1"] = remaining

    # Save fact store
    if hasattr(s, 'fact_store'):
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

    return jsonify({
        "status": "success",
        "applied_count": len(applied),
        "applied": applied
    })


@app.route('/api/changes/batch-accept', methods=['POST'])
def batch_accept_changes():
    """Accept multiple changes at once (Tier 2 batch review)."""
    from config_v2 import OUTPUT_DIR
    import json as json_module
    from tools_v2.fact_merger import FactMerger, MergeAction

    s = get_session()

    data = request.get_json() or {}
    change_ids = data.get("change_ids", [])
    tier = data.get("tier", "tier2")

    # Load pending changes from file
    pending_file = OUTPUT_DIR / "pending_changes.json"
    if not pending_file.exists():
        return jsonify({"status": "error", "message": "No pending changes file"}), 404

    try:
        with open(pending_file, 'r') as f:
            pending_changes = json_module.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load pending changes: {e}"}), 500

    # Initialize fact_merger if needed
    if not hasattr(s, 'fact_merger') and hasattr(s, 'fact_store'):
        s.fact_merger = FactMerger(s.fact_store)

    if not hasattr(s, 'fact_merger'):
        return jsonify({"status": "error", "message": "Cannot initialize merger"}), 400

    tier_changes = pending_changes.get(tier, [])

    accepted = []
    rejected_ids = set()

    for change in tier_changes:
        fact_data = change.get("fact", {})
        temp_id = fact_data.get("temp_id")

        if not change_ids or temp_id in change_ids:
            try:
                action, fact_id = s.fact_merger.merge_fact(fact_data, fact_data.get("source_document", ""))
                if action in [MergeAction.ADD, MergeAction.UPDATE]:
                    accepted.append({
                        "fact_id": fact_id,
                        "temp_id": temp_id,
                        "item": fact_data.get("item"),
                        "action": action.value
                    })
            except Exception as e:
                logger.error(f"Batch accept failed: {e}")
                rejected_ids.add(temp_id)

    # Remove accepted changes from pending
    accepted_temp_ids = {a["temp_id"] for a in accepted}
    pending_changes[tier] = [
        c for c in tier_changes
        if c.get("fact", {}).get("temp_id") not in accepted_temp_ids
    ]

    # Save updated pending changes to file
    with open(pending_file, 'w') as f:
        json_module.dump(pending_changes, f, indent=2, default=str)

    # Save fact store
    if hasattr(s, 'fact_store'):
        facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if facts_files:
            s.fact_store.save(str(facts_files[0]))

    return jsonify({
        "status": "success",
        "accepted_count": len(accepted),
        "accepted": accepted
    })


@app.route('/api/changes/<change_id>/accept', methods=['POST'])
def accept_single_change(change_id):
    """Accept a single change (Tier 3 individual review)."""
    from config_v2 import OUTPUT_DIR
    import json as json_module
    from tools_v2.fact_merger import FactMerger, MergeAction

    s = get_session()

    data = request.get_json() or {}
    resolution = data.get("resolution", "accept")  # accept, reject, modify
    modifications = data.get("modifications", {})
    notes = data.get("notes", "")

    # Load pending changes from file (primary source of truth)
    pending_file = OUTPUT_DIR / "pending_changes.json"
    if not pending_file.exists():
        return jsonify({"status": "error", "message": "No pending changes file"}), 404

    try:
        with open(pending_file, 'r') as f:
            pending_changes = json_module.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load pending changes: {e}"}), 500

    # Find the change across all tiers
    change = None
    change_tier = None
    for tier in ["tier1", "tier2", "tier3"]:
        for c in pending_changes.get(tier, []):
            if c.get("fact", {}).get("temp_id") == change_id:
                change = c
                change_tier = tier
                break
        if change:
            break

    if not change:
        return jsonify({"status": "error", "message": "Change not found"}), 404

    fact_data = change.get("fact", {})

    # Remove from pending changes file
    pending_changes[change_tier] = [
        c for c in pending_changes[change_tier]
        if c.get("fact", {}).get("temp_id") != change_id
    ]

    if resolution == "reject":
        # Save updated pending changes
        with open(pending_file, 'w') as f:
            json_module.dump(pending_changes, f, indent=2, default=str)
        return jsonify({"status": "success", "action": "rejected"})

    # Apply modifications if any
    if modifications:
        fact_data.update(modifications)

    # Initialize fact_merger
    if not hasattr(s, 'fact_merger') and hasattr(s, 'fact_store'):
        s.fact_merger = FactMerger(s.fact_store)

    if not hasattr(s, 'fact_merger'):
        return jsonify({"status": "error", "message": "Cannot initialize merger"}), 400

    # Merge the fact
    try:
        action, fact_id = s.fact_merger.merge_fact(fact_data, fact_data.get("source_document", ""))

        # Add review note
        if notes and fact_id and hasattr(s, 'fact_store'):
            fact = s.fact_store.get_fact(fact_id)
            if fact:
                fact.verification_note = f"{fact.verification_note or ''} [Review: {notes}]"

        # Save updated pending changes to file
        with open(pending_file, 'w') as f:
            json_module.dump(pending_changes, f, indent=2, default=str)

        # Save fact store
        if hasattr(s, 'fact_store'):
            facts_files = sorted(OUTPUT_DIR.glob("facts_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            if facts_files:
                s.fact_store.save(str(facts_files[0]))

        return jsonify({
            "status": "success",
            "action": action.value,
            "fact_id": fact_id
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/review/batch')
def batch_review_page():
    """Batch review page for Tier 2 changes."""
    from config_v2 import OUTPUT_DIR
    import json as json_module

    s = get_session()

    # Load pending changes from file
    pending_file = OUTPUT_DIR / "pending_changes.json"
    if pending_file.exists():
        try:
            with open(pending_file, 'r') as f:
                pending = json_module.load(f)
        except Exception:
            pending = {"tier1": [], "tier2": [], "tier3": []}
    else:
        pending = {"tier1": [], "tier2": [], "tier3": []}

    tier2_changes = pending.get("tier2", [])

    # Group by source document
    by_document = {}
    for change in tier2_changes:
        doc = change.get("fact", {}).get("source_document", "Unknown")
        if doc not in by_document:
            by_document[doc] = []
        by_document[doc].append(change)

    return render_template('review/batch.html',
                          changes=tier2_changes,
                          by_document=by_document,
                          total_count=len(tier2_changes))


@app.route('/review/conflicts')
def conflicts_review_page():
    """Individual review page for Tier 3 conflicts."""
    from config_v2 import OUTPUT_DIR
    import json as json_module

    s = get_session()

    # Load pending changes from file
    pending_file = OUTPUT_DIR / "pending_changes.json"
    if pending_file.exists():
        try:
            with open(pending_file, 'r') as f:
                pending = json_module.load(f)
        except Exception:
            pending = {"tier1": [], "tier2": [], "tier3": []}
    else:
        pending = {"tier1": [], "tier2": [], "tier3": []}

    tier3_changes = pending.get("tier3", [])

    # Get existing facts for comparison
    conflicts_with_existing = []
    for change in tier3_changes:
        existing_id = change.get("existing_fact_id")
        existing_fact = None
        if existing_id and hasattr(s, 'fact_store'):
            existing_fact = s.fact_store.get_fact(existing_id)

        conflicts_with_existing.append({
            "change": change,
            "existing": existing_fact.to_dict() if existing_fact else None
        })

    return render_template('review/conflicts.html',
                          conflicts=conflicts_with_existing,
                          total_count=len(tier3_changes))


# === Stale Items API (Phase 4) ===

@app.route('/api/stale-items')
def get_stale_items():
    """Get all stale items that need review."""
    from tools_v2.dependency_tracker import DependencyTracker
    from tools_v2.inventory_updater import InventoryUpdater

    s = get_session()

    if not hasattr(s, 'dependency_tracker'):
        s.dependency_tracker = DependencyTracker()

    updater = InventoryUpdater(
        fact_store=s.fact_store if hasattr(s, 'fact_store') else None,
        dependency_tracker=s.dependency_tracker,
        session=s
    )

    dashboard = updater.get_stale_dashboard()
    return jsonify(dashboard)


@app.route('/api/stale-items/<item_type>/<item_id>/review', methods=['POST'])
def review_stale_item(item_type, item_id):
    """Mark a stale item as reviewed."""
    from tools_v2.dependency_tracker import DependencyTracker, DependentItemType

    s = get_session()

    if not hasattr(s, 'dependency_tracker'):
        return jsonify({"status": "error", "message": "No tracker initialized"}), 400

    data = request.get_json() or {}
    reviewer = data.get("reviewer", "web_user")
    notes = data.get("notes", "")

    try:
        item_type_enum = DependentItemType(item_type)
    except ValueError:
        return jsonify({"status": "error", "message": f"Invalid item type: {item_type}"}), 400

    success = s.dependency_tracker.mark_reviewed(
        item_type=item_type_enum,
        item_id=item_id,
        reviewed_by=reviewer,
        notes=notes
    )

    if success:
        return jsonify({"status": "success", "message": "Item marked as reviewed"})
    else:
        return jsonify({"status": "error", "message": "Item not found"}), 404


@app.route('/api/stale-items/bulk-revalidate', methods=['POST'])
def bulk_revalidate_stale():
    """Bulk revalidate stale items."""
    from tools_v2.dependency_tracker import DependencyTracker, DependentItemType
    from tools_v2.inventory_updater import InventoryUpdater

    s = get_session()

    if not hasattr(s, 'dependency_tracker'):
        s.dependency_tracker = DependencyTracker()

    data = request.get_json() or {}
    item_type_str = data.get("item_type")  # Optional filter
    reviewer = data.get("reviewer", "web_user")
    notes = data.get("notes", "Bulk revalidation")

    updater = InventoryUpdater(
        fact_store=s.fact_store if hasattr(s, 'fact_store') else None,
        dependency_tracker=s.dependency_tracker,
        session=s
    )

    item_type = None
    if item_type_str:
        try:
            item_type = DependentItemType(item_type_str)
        except ValueError:
            return jsonify({"status": "error", "message": f"Invalid item type: {item_type_str}"}), 400

    count = updater.bulk_revalidate(item_type, reviewer, notes) if item_type else 0

    # If no type specified, do all types
    if not item_type:
        for t in DependentItemType:
            count += updater.bulk_revalidate(t, reviewer, notes)

    return jsonify({
        "status": "success",
        "revalidated_count": count
    })


@app.route('/api/propagate-changes', methods=['POST'])
def propagate_fact_changes():
    """Propagate fact changes to downstream items."""
    from tools_v2.dependency_tracker import DependencyTracker
    from tools_v2.inventory_updater import InventoryUpdater

    s = get_session()

    data = request.get_json() or {}
    fact_ids = data.get("fact_ids", [])
    change_type = data.get("change_type", "updated")

    if not fact_ids:
        return jsonify({"status": "error", "message": "No fact_ids provided"}), 400

    if not hasattr(s, 'dependency_tracker'):
        s.dependency_tracker = DependencyTracker()

    updater = InventoryUpdater(
        fact_store=s.fact_store if hasattr(s, 'fact_store') else None,
        dependency_tracker=s.dependency_tracker,
        session=s
    )

    result = updater.propagate_changes(fact_ids, change_type)

    return jsonify({
        "status": "success",
        "result": result.to_dict()
    })


# === Settings API (Phase 5) ===

@app.route('/api/settings/incremental')
def get_incremental_settings():
    """Get incremental update settings."""
    s = get_session()

    # Get or initialize settings
    if not hasattr(s, 'incremental_settings'):
        s.incremental_settings = {
            "auto_apply_enabled": True,
            "auto_apply_min_confidence": 0.9,
            "critical_domains": ["security", "compliance", "data"],
            "batch_review_threshold": 0.6,
            "auto_propagate": False
        }

    return jsonify(s.incremental_settings)


@app.route('/api/settings/incremental', methods=['POST'])
def update_incremental_settings():
    """Update incremental update settings."""
    s = get_session()

    data = request.get_json() or {}

    if not hasattr(s, 'incremental_settings'):
        s.incremental_settings = {}

    # Update settings
    valid_keys = [
        "auto_apply_enabled",
        "auto_apply_min_confidence",
        "critical_domains",
        "batch_review_threshold",
        "auto_propagate"
    ]

    for key in valid_keys:
        if key in data:
            s.incremental_settings[key] = data[key]

    # Apply to tier classifier if exists
    if hasattr(s, 'document_processor'):
        from tools_v2.tier_classifier import TierClassifier
        # Classifier settings will be read on next classification

    return jsonify({
        "status": "success",
        "settings": s.incremental_settings
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  IT Due Diligence Agent - Web Interface")
    print("="*60)
    print("\n  Starting server at: http://127.0.0.1:5001")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5001)
