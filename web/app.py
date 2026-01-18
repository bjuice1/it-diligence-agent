"""
Web interface for IT Due Diligence Agent.

Provides a browser-based UI for reviewing and adjusting analysis outputs.
Run with: python -m web.app
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from interactive.session import Session
from tools_v2.reasoning_tools import COST_RANGE_VALUES

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


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  IT Due Diligence Agent - Web Interface")
    print("="*60)
    print("\n  Starting server at: http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
