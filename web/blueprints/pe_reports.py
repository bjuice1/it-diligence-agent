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

from flask import Blueprint, render_template, jsonify, request, current_app, send_file
import zipfile
import io

logger = logging.getLogger(__name__)

pe_reports_bp = Blueprint('pe_reports', __name__, url_prefix='/reports')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_stores(deal_id: Optional[str] = None):
    """Get fact store and reasoning store for a deal."""
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

    # Try to load from session or deal
    fact_store = FactStore()
    reasoning_store = ReasoningStore()

    # In a real implementation, load from database based on deal_id
    # For now, check if there's a saved state in the session

    return fact_store, reasoning_store


def _get_deal_context(deal_id: Optional[str] = None):
    """Get deal context for a deal."""
    from tools_v2.pe_report_schemas import DealContext

    # Default context
    return DealContext(
        target_name="Target Company",
        deal_type="acquisition"
    )


# =============================================================================
# DASHBOARD ROUTE
# =============================================================================

@pe_reports_bp.route('/dashboard')
@pe_reports_bp.route('/dashboard/<deal_id>')
def dashboard(deal_id: str = None):
    """Executive dashboard landing page."""
    from tools_v2.executive_dashboard import generate_dashboard_data
    from tools_v2.renderers.dashboard_renderer import render_dashboard

    try:
        fact_store, reasoning_store = _get_stores(deal_id)
        deal_context = _get_deal_context(deal_id)

        # Generate dashboard data
        dashboard_data = generate_dashboard_data(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            target_name=deal_context.target_name
        )

        # Render to HTML
        html = render_dashboard(dashboard_data)

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

        # Generate domain data
        generator = generator_class(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context
        )
        domain_data = generator.generate()

        # Render to HTML
        html = render_domain_report(
            data=domain_data,
            target_name=deal_context.target_name
        )

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
# EDIT ENDPOINTS (for UI-first workflow)
# =============================================================================

@pe_reports_bp.route('/api/update-assessment/<domain>', methods=['POST'])
def api_update_assessment(domain: str):
    """Update benchmark assessment for a domain (human override)."""
    # In a real implementation, this would:
    # 1. Validate the input
    # 2. Store the updated assessment in the database
    # 3. Mark the assessment as human-reviewed

    data = request.get_json()

    # For now, just acknowledge the update
    logger.info(f"Assessment update received for {domain}: {data}")

    return jsonify({"status": "ok", "message": f"Assessment updated for {domain}"})


@pe_reports_bp.route('/api/update-implications/<domain>', methods=['POST'])
def api_update_implications(domain: str):
    """Update top implications for a domain (human override)."""
    data = request.get_json()
    logger.info(f"Implications update received for {domain}: {data}")
    return jsonify({"status": "ok", "message": f"Implications updated for {domain}"})


@pe_reports_bp.route('/api/update-actions/<domain>', methods=['POST'])
def api_update_actions(domain: str):
    """Update top actions for a domain (human override)."""
    data = request.get_json()
    logger.info(f"Actions update received for {domain}: {data}")
    return jsonify({"status": "ok", "message": f"Actions updated for {domain}"})
