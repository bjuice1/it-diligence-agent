"""
PE Reports Blueprint

Web routes for PE-grade executive reporting:
- /reports/dashboard - Executive dashboard landing page
- /reports/<domain> - Domain deep-dive pages
- /reports/costs - Run-rate costs report
- /reports/investment - One-time investment report
- /reports/executive-summary - Executive summary
- /reports/generate - Generate all reports as HTML files
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Blueprint, render_template, jsonify, request, current_app, send_file, session as flask_session, g
import zipfile
import io

logger = logging.getLogger(__name__)

pe_reports_bp = Blueprint('pe_reports', __name__, url_prefix='/reports')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _resolve_deal_id(deal_id: Optional[str] = None) -> Optional[str]:
    """
    Resolve deal_id from URL parameter or Flask session.

    Priority: explicit param > Flask session > None
    """
    if deal_id:
        return deal_id
    return flask_session.get('current_deal_id')


def _get_stores(deal_id: Optional[str] = None):
    """
    Get fact store and reasoning store for a deal, loaded from database.

    Returns adapter objects that provide the same interface as FactStore/ReasoningStore
    (.facts, .gaps, .risks, .work_items, .strategic_considerations, .recommendations)
    but backed by actual database data.
    """
    resolved_id = _resolve_deal_id(deal_id)

    if not resolved_id:
        # No deal selected — return empty stores as fallback
        logger.warning("PE Reports: No deal_id available, returning empty stores")
        from stores.fact_store import FactStore
        from tools_v2.reasoning_tools import ReasoningStore
        return FactStore(), ReasoningStore()

    try:
        from web.context import load_deal_context
        from web.deal_data import DealData, create_store_adapters_from_deal_data

        # Ensure flask.g has deal context (sets g.deal, g.deal_id, g.run_id)
        if not getattr(g, 'deal_id', None) or g.deal_id != resolved_id:
            load_deal_context(resolved_id)

        # Load all facts and findings from database (no entity filter here —
        # let individual generators/routes filter by entity as needed)
        data = DealData(deal_id=resolved_id)
        fact_adapter, reasoning_adapter = create_store_adapters_from_deal_data(data, entity=None)

        logger.info(
            f"PE Reports: Loaded {len(fact_adapter.facts)} facts, "
            f"{len(reasoning_adapter.risks)} risks, "
            f"{len(reasoning_adapter.work_items)} work items "
            f"for deal {resolved_id}"
        )

        return fact_adapter, reasoning_adapter

    except Exception as e:
        logger.exception(f"PE Reports: Failed to load stores from database: {e}")
        # Fallback to empty stores rather than crashing
        from stores.fact_store import FactStore
        from tools_v2.reasoning_tools import ReasoningStore
        return FactStore(), ReasoningStore()


def _get_deal_context(deal_id: Optional[str] = None):
    """
    Get deal context from database Deal record.

    Builds a typed DealContext from the Deal model fields and its
    context JSON column (which may contain financial details).
    """
    from tools_v2.pe_report_schemas import DealContext

    resolved_id = _resolve_deal_id(deal_id)

    if not resolved_id:
        return DealContext(target_name="Target Company", deal_type="acquisition")

    try:
        # Check if deal is already on flask.g (set by _get_stores -> load_deal_context)
        deal = getattr(g, 'deal', None)

        if not deal:
            from web.database import Deal
            deal = Deal.query.get(resolved_id)

        if not deal:
            logger.warning(f"PE Reports: Deal {resolved_id} not found in database")
            return DealContext(target_name="Target Company", deal_type="acquisition")

        # The Deal.context JSON column may hold additional financial details
        ctx = deal.context or {}

        return DealContext(
            target_name=deal.target_name or "Target Company",
            deal_type=deal.deal_type or "acquisition",
            buyer_name=deal.buyer_name or None,
            target_industry=deal.industry or None,
            target_revenue=ctx.get('target_revenue'),
            target_employees=ctx.get('target_employees'),
            target_it_budget=ctx.get('target_it_budget'),
            target_it_headcount=ctx.get('target_it_headcount'),
            buyer_revenue=ctx.get('buyer_revenue'),
            buyer_employees=ctx.get('buyer_employees'),
            buyer_industry=ctx.get('buyer_industry'),
            buyer_it_budget=ctx.get('buyer_it_budget'),
            deal_value=ctx.get('deal_value'),
            expected_close_date=ctx.get('expected_close_date'),
            tsa_required=ctx.get('tsa_required', False),
            tsa_duration_months=ctx.get('tsa_duration_months'),
        )

    except Exception as e:
        logger.exception(f"PE Reports: Failed to load deal context: {e}")
        return DealContext(target_name="Target Company", deal_type="acquisition")


# =============================================================================
# DASHBOARD ROUTE
# =============================================================================

@pe_reports_bp.route('/dashboard')
@pe_reports_bp.route('/dashboard/<deal_id>')
def dashboard(deal_id: str = None):
    """Executive dashboard landing page."""
    from tools_v2.executive_dashboard import generate_dashboard_data
    from tools_v2.renderers.dashboard_renderer import render_dashboard

    # Get entity from query param (Phase 7 - Entity Separation)
    entity = request.args.get('entity', 'target')
    if entity not in ['target', 'buyer', 'comparison']:
        entity = 'target'

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Generate dashboard data with entity filter
        dashboard_data = generate_dashboard_data(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            target_name=deal_context.target_name,
            entity=entity  # Pass entity through
        )

        # Render to HTML with entity context
        html = render_dashboard(dashboard_data, entity=entity)

        return html

    except Exception as e:
        logger.exception(f"Error generating dashboard: {e}")
        return f"<h1>Error generating dashboard</h1><p>{str(e)}</p>", 500


# =============================================================================
# DOMAIN ROUTES
# =============================================================================

@pe_reports_bp.route('/<domain>')
@pe_reports_bp.route('/<domain>/<deal_id>')
def domain_report(domain: str, deal_id: str = None):
    """Domain deep-dive page."""
    from tools_v2.domain_generators import DOMAIN_GENERATORS
    from tools_v2.renderers.html_renderer import render_domain_report
    from tools_v2.pe_report_schemas import DOMAIN_ORDER

    # Get entity from query param (Phase 7 - Entity Separation)
    entity = request.args.get('entity', 'target')
    if entity not in ['target', 'buyer']:
        entity = 'target'

    # Validate domain
    if domain not in DOMAIN_ORDER:
        return f"<h1>Unknown domain: {domain}</h1>", 404

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Get the appropriate generator
        generator_class = DOMAIN_GENERATORS.get(domain)
        if not generator_class:
            return f"<h1>No generator for domain: {domain}</h1>", 404

        # Generate domain data with entity filter (Phase 7)
        generator = generator_class(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            entity=entity  # Pass entity to filter facts
        )
        domain_data = generator.generate()

        # Load and apply human overrides
        resolved_id = _resolve_deal_id(deal_id)
        overrides = {}
        if resolved_id:
            overrides = _load_overrides(resolved_id, domain)
            if overrides:
                _apply_overrides(domain_data, overrides)
                logger.info(f"Applied {sum(len(v) for v in overrides.values())} overrides to {domain}")

        # Render to HTML with entity context
        html = render_domain_report(
            data=domain_data,
            target_name=deal_context.target_name,
            entity=entity
        )

        # Inject editing capabilities for web UI viewing
        editing_html = _get_editing_injection_html(domain, overrides)
        html = html.replace('</body>', editing_html + '\n</body>')

        return html

    except Exception as e:
        logger.exception(f"Error generating {domain} report: {e}")
        return f"<h1>Error generating {domain} report</h1><p>{str(e)}</p>", 500


# =============================================================================
# COSTS ROUTE
# =============================================================================

@pe_reports_bp.route('/costs')
@pe_reports_bp.route('/costs/<deal_id>')
def costs_report(deal_id: str = None):
    """Run-rate costs report."""
    from tools_v2.costs_report import generate_costs_report, render_costs_report_html

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Generate costs data
        costs_data = generate_costs_report(fact_store, deal_context)

        # Render to HTML
        html = render_costs_report_html(costs_data, deal_context.target_name)

        return html

    except Exception as e:
        logger.exception(f"Error generating costs report: {e}")
        return f"<h1>Error generating costs report</h1><p>{str(e)}</p>", 500


# =============================================================================
# INVESTMENT ROUTE
# =============================================================================

@pe_reports_bp.route('/investment')
@pe_reports_bp.route('/investment/<deal_id>')
def investment_report(deal_id: str = None):
    """One-time investment report."""
    from tools_v2.investment_report import generate_investment_report, render_investment_report_html

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Generate investment data
        investment_data = generate_investment_report(reasoning_store)

        # Render to HTML
        html = render_investment_report_html(investment_data, deal_context.target_name)

        return html

    except Exception as e:
        logger.exception(f"Error generating investment report: {e}")
        return f"<h1>Error generating investment report</h1><p>{str(e)}</p>", 500


# =============================================================================
# SEPARATION COSTS ROUTE (NEW - Driver-Based)
# =============================================================================

@pe_reports_bp.route('/separation-costs')
@pe_reports_bp.route('/separation-costs/<deal_id>')
def separation_costs_report(deal_id: str = None):
    """One-time separation/integration costs report using driver-based models."""
    from tools_v2.separation_costs_report import generate_separation_costs_report, render_separation_costs_html

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Get deal ID
        if not deal_id:
            from flask import session
            deal_id = session.get('current_deal_id', 'unknown')

        # Generate separation costs data
        costs_data = generate_separation_costs_report(deal_id, fact_store, deal_context)

        # Render to HTML
        html = render_separation_costs_html(costs_data, deal_context.target_name)

        return html

    except Exception as e:
        logger.exception(f"Error generating separation costs report: {e}")
        return f"<h1>Error generating separation costs report</h1><p>{str(e)}</p>", 500


# =============================================================================
# EXECUTIVE SUMMARY ROUTE
# =============================================================================

@pe_reports_bp.route('/executive-summary')
@pe_reports_bp.route('/executive-summary/<deal_id>')
def executive_summary(deal_id: str = None):
    """PE executive summary."""
    from tools_v2.executive_summary_pe import generate_executive_summary, render_executive_summary_html

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Generate summary data
        summary_data = generate_executive_summary(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            target_name=deal_context.target_name
        )

        # Render to HTML
        html = render_executive_summary_html(summary_data)

        return html

    except Exception as e:
        logger.exception(f"Error generating executive summary: {e}")
        return f"<h1>Error generating executive summary</h1><p>{str(e)}</p>", 500


# =============================================================================
# GENERATE ALL REPORTS
# =============================================================================

@pe_reports_bp.route('/generate', methods=['POST'])
@pe_reports_bp.route('/generate/<deal_id>', methods=['POST'])
def generate_reports(deal_id: str = None):
    """Generate all PE reports as HTML files and return as ZIP."""
    from tools_v2.domain_generators import DOMAIN_GENERATORS
    from tools_v2.renderers.dashboard_renderer import render_dashboard
    from tools_v2.renderers.html_renderer import render_domain_report
    from tools_v2.executive_dashboard import generate_dashboard_data
    from tools_v2.costs_report import generate_costs_report, render_costs_report_html
    from tools_v2.investment_report import generate_investment_report, render_investment_report_html
    from tools_v2.executive_summary_pe import generate_executive_summary, render_executive_summary_html
    from tools_v2.pe_report_schemas import DOMAIN_ORDER

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)
        target_name = deal_context.target_name

        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()

        # Resolve deal_id for loading overrides
        resolved_id = _resolve_deal_id(deal_id)

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Generate domain reports
            domain_reports = {}
            for domain in DOMAIN_ORDER:
                generator_class = DOMAIN_GENERATORS.get(domain)
                if generator_class:
                    generator = generator_class(
                        fact_store=fact_store,
                        reasoning_store=reasoning_store,
                        deal_context=deal_context
                    )
                    domain_data = generator.generate()

                    # Apply human overrides to exported reports
                    if resolved_id:
                        overrides = _load_overrides(resolved_id, domain)
                        if overrides:
                            _apply_overrides(domain_data, overrides)

                    domain_reports[domain] = domain_data

                    html = render_domain_report(domain_data, target_name)
                    zf.writestr(f"{domain}_report.html", html)

            # Generate dashboard
            dashboard_data = generate_dashboard_data(
                fact_store=fact_store,
                reasoning_store=reasoning_store,
                deal_context=deal_context,
                domain_reports=domain_reports,
                target_name=target_name
            )
            dashboard_html = render_dashboard(dashboard_data)
            zf.writestr("dashboard.html", dashboard_html)

            # Generate costs report
            costs_data = generate_costs_report(fact_store, deal_context)
            costs_html = render_costs_report_html(costs_data, target_name)
            zf.writestr("costs_report.html", costs_html)

            # Generate investment report
            investment_data = generate_investment_report(reasoning_store)
            investment_html = render_investment_report_html(investment_data, target_name)
            zf.writestr("investment_report.html", investment_html)

            # Generate separation costs report (driver-based)
            try:
                from tools_v2.separation_costs_report import generate_separation_costs_report, render_separation_costs_html
                sep_costs_data = generate_separation_costs_report(resolved_id or 'export', fact_store, deal_context)
                sep_costs_html = render_separation_costs_html(sep_costs_data, target_name)
                zf.writestr("separation_costs_report.html", sep_costs_html)
            except Exception as e:
                logger.warning(f"Could not generate separation costs report: {e}")

            # Generate executive summary
            summary_data = generate_executive_summary(
                fact_store=fact_store,
                reasoning_store=reasoning_store,
                deal_context=deal_context,
                domain_reports=domain_reports,
                target_name=target_name
            )
            summary_html = render_executive_summary_html(summary_data)
            zf.writestr("executive_summary.html", summary_html)

            # Add index file
            index_html = _generate_index_html(target_name, DOMAIN_ORDER)
            zf.writestr("index.html", index_html)

        zip_buffer.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pe_reports_{timestamp}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.exception(f"Error generating reports: {e}")
        return jsonify({"error": str(e)}), 500


def _generate_index_html(target_name: str, domains: list) -> str:
    """Generate index HTML linking to all reports."""
    domain_links = ""
    for domain in domains:
        display_name = domain.replace("_", " ").title()
        domain_links += f'<li><a href="{domain}_report.html">{display_name}</a></li>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - PE Reports</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }}
        h1 {{ color: #2563eb; }}
        ul {{ line-height: 2; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .section {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
    <h1>{target_name} - IT Due Diligence Reports</h1>

    <div class="section">
        <h2>Executive Reports</h2>
        <ul>
            <li><a href="dashboard.html">Executive Dashboard</a></li>
            <li><a href="executive_summary.html">Executive Summary</a></li>
        </ul>
    </div>

    <div class="section">
        <h2>Domain Reports</h2>
        <ul>
            {domain_links}
        </ul>
    </div>

    <div class="section">
        <h2>Financial Reports</h2>
        <ul>
            <li><a href="costs_report.html">Costs Report (Run-Rate)</a></li>
            <li><a href="investment_report.html">Investment Report (One-Time)</a></li>
            <li><a href="separation_costs_report.html">Separation Costs (Driver-Based)</a> - NEW</li>
        </ul>
    </div>

    <p><small>Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</small></p>
</body>
</html>"""


# =============================================================================
# API ENDPOINTS (JSON)
# =============================================================================

@pe_reports_bp.route('/api/dashboard-data')
@pe_reports_bp.route('/api/dashboard-data/<deal_id>')
def api_dashboard_data(deal_id: str = None):
    """Get dashboard data as JSON."""
    from tools_v2.executive_dashboard import generate_dashboard_data

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        dashboard_data = generate_dashboard_data(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            target_name=deal_context.target_name
        )

        return jsonify(dashboard_data.to_dict())

    except Exception as e:
        logger.exception(f"Error getting dashboard data: {e}")
        return jsonify({"error": str(e)}), 500


@pe_reports_bp.route('/api/domain-data/<domain>')
@pe_reports_bp.route('/api/domain-data/<domain>/<deal_id>')
def api_domain_data(domain: str, deal_id: str = None):
    """Get domain report data as JSON."""
    from tools_v2.domain_generators import DOMAIN_GENERATORS
    from tools_v2.pe_report_schemas import DOMAIN_ORDER

    if domain not in DOMAIN_ORDER:
        return jsonify({"error": f"Unknown domain: {domain}"}), 404

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        generator_class = DOMAIN_GENERATORS.get(domain)
        if not generator_class:
            return jsonify({"error": f"No generator for domain: {domain}"}), 404

        generator = generator_class(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context
        )
        domain_data = generator.generate()

        return jsonify(domain_data.to_dict())

    except Exception as e:
        logger.exception(f"Error getting {domain} data: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# OVERRIDE HELPERS
# =============================================================================

def _load_overrides(deal_id: str, domain: str) -> Dict[str, Dict[str, str]]:
    """
    Load active report overrides for a deal+domain.

    Returns:
        Dict keyed by section -> {field_name: override_value}
        e.g. {'assessment': {'tech_age_rationale': 'Human edited text...'}}
    """
    from web.database import ReportOverride

    overrides = ReportOverride.query.filter_by(
        deal_id=deal_id, domain=domain, active=True
    ).all()

    result: Dict[str, Dict[str, str]] = {}
    for o in overrides:
        if o.section not in result:
            result[o.section] = {}
        result[o.section][o.field_name] = o.override_value

    return result


def _apply_overrides(domain_data, overrides: Dict[str, Dict[str, str]]):
    """
    Apply human overrides to a DomainReportData object (mutates in place).

    Handles three sections:
    - assessment: benchmark_assessment fields (tech_age_rationale, cost_posture_rationale, etc.)
    - actions: top_actions[N].so_what fields (keyed as action_1_so_what, action_2_so_what, etc.)
    - implications: top_implications[N] (keyed as implication_1, implication_2, etc.)
    """
    # Assessment overrides
    assessment_overrides = overrides.get('assessment', {})
    if assessment_overrides and hasattr(domain_data, 'benchmark_assessment'):
        ba = domain_data.benchmark_assessment
        for field_name, value in assessment_overrides.items():
            if hasattr(ba, field_name):
                setattr(ba, field_name, value)

    # Action overrides (action_1_so_what, action_2_so_what, etc.)
    action_overrides = overrides.get('actions', {})
    if action_overrides and hasattr(domain_data, 'top_actions'):
        for field_name, value in action_overrides.items():
            if field_name.startswith('action_') and field_name.endswith('_so_what'):
                try:
                    idx = int(field_name.split('_')[1]) - 1  # 1-indexed to 0-indexed
                    if 0 <= idx < len(domain_data.top_actions):
                        domain_data.top_actions[idx].so_what = value
                except (ValueError, IndexError):
                    pass

    # Implications overrides (implication_1, implication_2, etc.)
    impl_overrides = overrides.get('implications', {})
    if impl_overrides and hasattr(domain_data, 'top_implications'):
        for field_name, value in impl_overrides.items():
            if field_name.startswith('implication_'):
                try:
                    idx = int(field_name.split('_')[1]) - 1
                    if 0 <= idx < len(domain_data.top_implications):
                        domain_data.top_implications[idx] = value
                except (ValueError, IndexError):
                    pass


def _save_overrides(deal_id: str, domain: str, section: str, edits: Dict[str, str]):
    """
    Save report overrides to database (upsert pattern).

    Args:
        deal_id: Deal ID
        domain: Domain name (e.g. 'applications')
        section: Section name ('assessment', 'actions', 'implications')
        edits: Dict of field_name -> new_value
    """
    from web.database import db, ReportOverride

    saved_count = 0
    for field_name, new_value in edits.items():
        if not field_name or not isinstance(new_value, str):
            continue

        new_value = new_value.strip()
        if not new_value:
            continue

        # Upsert: find existing or create new
        existing = ReportOverride.query.filter_by(
            deal_id=deal_id, domain=domain, section=section,
            field_name=field_name, active=True
        ).first()

        if existing:
            existing.override_value = new_value
            existing.updated_at = datetime.utcnow()
        else:
            override = ReportOverride(
                deal_id=deal_id,
                domain=domain,
                section=section,
                field_name=field_name,
                override_value=new_value,
            )
            db.session.add(override)

        saved_count += 1

    db.session.commit()
    logger.info(f"Saved {saved_count} overrides for {domain}/{section} (deal={deal_id})")
    return saved_count


def _get_editing_injection_html(domain: str, overrides: Dict[str, Dict[str, str]]) -> str:
    """
    Generate CSS/JS injection for inline editing capabilities.

    Injected into rendered HTML for web UI viewing (not ZIP export).
    """
    # Build set of overridden fields for visual indicators
    overridden_fields = set()
    for section_overrides in overrides.values():
        overridden_fields.update(section_overrides.keys())

    overridden_json = json.dumps(list(overridden_fields))

    return f'''
<!-- Inline Editing Capabilities -->
<style>
    .edit-toolbar {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        display: flex;
        gap: 8px;
        background: white;
        padding: 8px 12px;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.15);
    }}
    .edit-toolbar button {{
        padding: 6px 14px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.85em;
        font-weight: 600;
        transition: all 0.2s;
    }}
    .edit-toolbar .btn-edit {{
        background: #3b82f6;
        color: white;
    }}
    .edit-toolbar .btn-edit:hover {{
        background: #2563eb;
    }}
    .edit-toolbar .btn-edit.active {{
        background: #f59e0b;
        color: black;
    }}
    .edit-toolbar .btn-save {{
        background: #10b981;
        color: white;
        display: none;
    }}
    .edit-toolbar .btn-save:hover {{
        background: #059669;
    }}
    .edit-toolbar .btn-cancel {{
        background: #ef4444;
        color: white;
        display: none;
    }}
    .edit-toolbar .save-status {{
        align-self: center;
        font-size: 0.8em;
        color: #666;
    }}
    [contenteditable="true"] {{
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
        background: #fef3c7 !important;
        padding: 4px;
        border-radius: 4px;
        cursor: text;
    }}
    .human-edited {{
        position: relative;
        border-left: 3px solid #f59e0b !important;
        padding-left: 8px;
    }}
    .human-edited::after {{
        content: "(edited)";
        font-size: 0.7em;
        color: #f59e0b;
        font-weight: 600;
        margin-left: 6px;
    }}
</style>

<div class="edit-toolbar" id="editToolbar">
    <button class="btn-edit" id="btnEdit" onclick="toggleEditMode()">Edit Report</button>
    <button class="btn-save" id="btnSave" onclick="saveAllEdits()">Save</button>
    <button class="btn-cancel" id="btnCancel" onclick="cancelEditMode()">Cancel</button>
    <span class="save-status" id="saveStatus"></span>
</div>

<script>
(function() {{
    const DOMAIN = "{domain}";
    const OVERRIDDEN_FIELDS = {overridden_json};
    let isEditing = false;
    let originalValues = {{}};

    // Mark already-edited fields on load
    OVERRIDDEN_FIELDS.forEach(field => {{
        const el = document.querySelector('[data-field="' + field + '"]');
        if (el) el.classList.add('human-edited');
    }});

    // Make text sections identifiable for editing
    function setupEditableElements() {{
        // Section 3: Benchmark assessment rationales
        const section3 = document.querySelectorAll('.report-section')[2];
        if (section3) {{
            const rationales = section3.querySelectorAll('.rationale, .so-what-text, .implication-text');
            rationales.forEach((el, i) => {{
                const fields = ['tech_age_rationale', 'cost_posture_rationale', 'maturity_rationale', 'implication'];
                if (i < fields.length && !el.dataset.field) {{
                    el.dataset.field = fields[i];
                    el.dataset.section = 'assessment';
                }}
            }});
        }}

        // Section 4: Action so_what fields
        const section4 = document.querySelectorAll('.report-section')[3];
        if (section4) {{
            const soWhats = section4.querySelectorAll('.action-so-what, .so-what');
            soWhats.forEach((el, i) => {{
                if (!el.dataset.field) {{
                    el.dataset.field = 'action_' + (i + 1) + '_so_what';
                    el.dataset.section = 'actions';
                }}
            }});
        }}

        // Section 5: Implications
        const section5 = document.querySelectorAll('.report-section')[4];
        if (section5) {{
            const impls = section5.querySelectorAll('.implication-item, li');
            impls.forEach((el, i) => {{
                if (!el.dataset.field) {{
                    el.dataset.field = 'implication_' + (i + 1);
                    el.dataset.section = 'implications';
                }}
            }});
        }}
    }}

    setupEditableElements();

    window.toggleEditMode = function() {{
        isEditing = !isEditing;
        const editables = document.querySelectorAll('[data-field]');
        const btnEdit = document.getElementById('btnEdit');
        const btnSave = document.getElementById('btnSave');
        const btnCancel = document.getElementById('btnCancel');

        if (isEditing) {{
            // Store originals and enable editing
            editables.forEach(el => {{
                originalValues[el.dataset.field] = el.innerText;
                el.setAttribute('contenteditable', 'true');
            }});
            btnEdit.textContent = 'Editing...';
            btnEdit.classList.add('active');
            btnSave.style.display = 'inline-block';
            btnCancel.style.display = 'inline-block';
        }} else {{
            editables.forEach(el => {{
                el.removeAttribute('contenteditable');
            }});
            btnEdit.textContent = 'Edit Report';
            btnEdit.classList.remove('active');
            btnSave.style.display = 'none';
            btnCancel.style.display = 'none';
        }}
    }};

    window.cancelEditMode = function() {{
        // Restore originals
        const editables = document.querySelectorAll('[data-field]');
        editables.forEach(el => {{
            if (originalValues[el.dataset.field] !== undefined) {{
                el.innerText = originalValues[el.dataset.field];
            }}
            el.removeAttribute('contenteditable');
        }});
        isEditing = false;
        document.getElementById('btnEdit').textContent = 'Edit Report';
        document.getElementById('btnEdit').classList.remove('active');
        document.getElementById('btnSave').style.display = 'none';
        document.getElementById('btnCancel').style.display = 'none';
    }};

    window.saveAllEdits = function() {{
        const status = document.getElementById('saveStatus');
        status.textContent = 'Saving...';

        // Group edits by section
        const bySection = {{}};
        document.querySelectorAll('[data-field]').forEach(el => {{
            const field = el.dataset.field;
            const section = el.dataset.section || 'assessment';
            const value = el.innerText.trim();

            // Only save if changed
            if (value !== (originalValues[field] || '').trim()) {{
                if (!bySection[section]) bySection[section] = {{}};
                bySection[section][field] = value;
            }}
        }});

        // Map sections to endpoints
        const sectionEndpoints = {{
            'assessment': '/reports/api/update-assessment/' + DOMAIN,
            'actions': '/reports/api/update-actions/' + DOMAIN,
            'implications': '/reports/api/update-implications/' + DOMAIN
        }};

        const promises = [];
        for (const [section, edits] of Object.entries(bySection)) {{
            const url = sectionEndpoints[section];
            if (url && Object.keys(edits).length > 0) {{
                promises.push(
                    fetch(url, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(edits)
                    }}).then(r => r.json())
                );
            }}
        }}

        if (promises.length === 0) {{
            status.textContent = 'No changes to save';
            setTimeout(() => {{ status.textContent = ''; }}, 2000);
            return;
        }}

        Promise.all(promises)
            .then(results => {{
                status.textContent = 'Saved!';
                // Mark edited fields
                document.querySelectorAll('[data-field]').forEach(el => {{
                    const field = el.dataset.field;
                    if (el.innerText.trim() !== (originalValues[field] || '').trim()) {{
                        el.classList.add('human-edited');
                    }}
                }});
                // Exit edit mode
                window.toggleEditMode();
                setTimeout(() => {{ status.textContent = ''; }}, 3000);
            }})
            .catch(err => {{
                status.textContent = 'Error: ' + err.message;
                console.error('Save error:', err);
            }});
    }};
}})();
</script>
'''


# =============================================================================
# EDIT ENDPOINTS
# =============================================================================

@pe_reports_bp.route('/api/update-assessment/<domain>', methods=['POST'])
def api_update_assessment(domain: str):
    """Update benchmark assessment for a domain (human override)."""
    deal_id = _resolve_deal_id()
    if not deal_id:
        return jsonify({"error": "No deal selected"}), 400

    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data"}), 400

    count = _save_overrides(deal_id, domain, 'assessment', data)
    return jsonify({"status": "ok", "saved": count, "message": f"Assessment updated for {domain}"})


@pe_reports_bp.route('/api/update-implications/<domain>', methods=['POST'])
def api_update_implications(domain: str):
    """Update top implications for a domain (human override)."""
    deal_id = _resolve_deal_id()
    if not deal_id:
        return jsonify({"error": "No deal selected"}), 400

    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data"}), 400

    count = _save_overrides(deal_id, domain, 'implications', data)
    return jsonify({"status": "ok", "saved": count, "message": f"Implications updated for {domain}"})


@pe_reports_bp.route('/api/update-actions/<domain>', methods=['POST'])
def api_update_actions(domain: str):
    """Update top actions for a domain (human override)."""
    deal_id = _resolve_deal_id()
    if not deal_id:
        return jsonify({"error": "No deal selected"}), 400

    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data"}), 400

    count = _save_overrides(deal_id, domain, 'actions', data)
    return jsonify({"status": "ok", "saved": count, "message": f"Actions updated for {domain}"})
