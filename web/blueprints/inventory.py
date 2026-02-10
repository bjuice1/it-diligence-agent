"""
Inventory Blueprint

Routes for viewing and managing inventory data.
Includes the "So What" insights report with visualizations.
"""

import os
import logging
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash

from stores.inventory_store import InventoryStore
from tools_v2.sowhat_report import (
    generate_sowhat_report,
    analyze_inventory_for_findings,
    Finding,
    DataFlow,
)
from tools_v2.inventory_report import build_inventory_section, get_inventory_styles

logger = logging.getLogger(__name__)

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Deal-scoped inventory stores
_inventory_stores: dict = {}


def get_inventory_store() -> InventoryStore:
    """Get or create the inventory store for the current deal.

    IMPORTANT: Inventory is now deal-scoped to prevent data leakage between deals.
    The store is created WITH deal_id and uses consistent deal-specific paths.
    """
    from flask import session

    current_deal_id = session.get('current_deal_id')

    # Use deal_id as key, or 'default' for no deal
    store_key = current_deal_id or 'default'

    if store_key not in _inventory_stores:
        # Create store WITH deal_id - this auto-generates the storage path
        _inventory_stores[store_key] = InventoryStore(deal_id=current_deal_id)

        # Storage path is now auto-generated in constructor based on deal_id
        # For deal: output/deals/{deal_id}/inventory_store.json
        # For default: uses storage_path=None
        if _inventory_stores[store_key].storage_path:
            if _inventory_stores[store_key].storage_path.exists():
                try:
                    _inventory_stores[store_key].load(_inventory_stores[store_key].storage_path)
                    logger.info(f"Loaded inventory store for deal {current_deal_id} with {len(_inventory_stores[store_key])} items")
                except Exception as e:
                    logger.warning(f"Could not load deal inventory store: {e}")
            else:
                logger.debug(f"No inventory file for deal {current_deal_id}")
        else:
            # Fallback to default location for no-deal context
            default_path = Path("data/inventory_store.json")
            if default_path.exists():
                try:
                    _inventory_stores[store_key].load(default_path)
                    logger.info(f"Loaded default inventory store with {len(_inventory_stores[store_key])} items")
                except Exception as e:
                    logger.warning(f"Could not load inventory store: {e}")

    return _inventory_stores[store_key]


def save_inventory_store(store: InventoryStore) -> None:
    """Save inventory store to its deal-specific path.

    FIXED: Now uses consistent deal-specific paths for BOTH read AND write.
    """
    if store.storage_path:
        store.storage_path.parent.mkdir(parents=True, exist_ok=True)
        store.save(store.storage_path)
        logger.info(f"Saved inventory store to {store.storage_path}")
    elif store.deal_id:
        # Fallback: construct path from deal_id
        deal_path = Path(f"output/deals/{store.deal_id}/inventory_store.json")
        deal_path.parent.mkdir(parents=True, exist_ok=True)
        store.save(deal_path)
        logger.info(f"Saved inventory store to {deal_path}")
    else:
        # No deal - use default path
        default_path = Path("data/inventory_store.json")
        default_path.parent.mkdir(parents=True, exist_ok=True)
        store.save(default_path)
        logger.warning("Saved inventory to default path (no deal_id set)")


def clear_inventory_store_for_deal(deal_id: str = None):
    """Clear the cached inventory store for a specific deal."""
    store_key = deal_id or 'default'
    if store_key in _inventory_stores:
        del _inventory_stores[store_key]
        logger.debug(f"Cleared inventory store for deal {store_key}")


@inventory_bp.route('/')
def inventory_home():
    """Show inventory overview."""
    from flask import session
    from web.database import db, Fact
    from stores.inventory_store import InventoryItem

    store = get_inventory_store()

    apps = store.get_items(inventory_type="application", entity="target", status="active")
    infra = store.get_items(inventory_type="infrastructure", entity="target", status="active")
    org = store.get_items(inventory_type="organization", entity="target", status="active")
    vendors = store.get_items(inventory_type="vendor", entity="target", status="active")

    # If InventoryStore is empty, also check database Facts
    current_deal_id = session.get('current_deal_id')
    if len(store) == 0 and current_deal_id:
        logger.info(f"InventoryStore empty, loading from database for deal {current_deal_id}")

        # Query application facts from database
        db_app_facts = Fact.query.filter_by(deal_id=current_deal_id, domain='applications').all()
        for i, fact in enumerate(db_app_facts):
            details = fact.details or {}
            apps.append(InventoryItem(
                item_id=f"DB-APP-{i:04d}",
                inventory_type="application",
                entity="target",
                deal_id=current_deal_id,
                status="active",
                data={
                    'name': fact.item,
                    'vendor': details.get('vendor') or details.get('provider', ''),
                    'category': fact.category or details.get('category', ''),
                    'version': details.get('version', ''),
                    'criticality': details.get('criticality') or details.get('business_criticality', ''),
                    'deployment': details.get('deployment') or details.get('hosting', ''),
                    'user_count': details.get('user_count') or details.get('users', 0),
                    'cost': details.get('annual_cost') or details.get('cost', 0),
                },
            ))

        # Query infrastructure facts
        db_infra_facts = Fact.query.filter_by(deal_id=current_deal_id, domain='infrastructure').all()
        for i, fact in enumerate(db_infra_facts):
            details = fact.details or {}
            infra.append(InventoryItem(
                item_id=f"DB-INF-{i:04d}",
                inventory_type="infrastructure",
                entity="target",
                deal_id=current_deal_id,
                status="active",
                data={
                    'name': fact.item,
                    'type': fact.category or details.get('type', ''),
                    'os': details.get('os', ''),
                    'environment': details.get('environment', ''),
                },
            ))

        # Query organization facts
        db_org_facts = Fact.query.filter_by(deal_id=current_deal_id, domain='organization').all()
        for i, fact in enumerate(db_org_facts):
            details = fact.details or {}
            org_data = {'name': fact.item}
            org_data.update(details)
            org.append(InventoryItem(
                item_id=f"DB-ORG-{i:04d}",
                inventory_type="organization",
                entity="target",
                deal_id=current_deal_id,
                status="active",
                data=org_data,
            ))

        logger.info(f"Loaded from DB: {len(apps)} apps, {len(infra)} infra, {len(org)} org")

    # Calculate stats
    total_cost = sum(app.cost or 0 for app in apps)
    flagged = [i for i in store.get_items(entity="target") if i.needs_investigation]
    enriched = [i for i in store.get_items(entity="target") if i.is_enriched]
    total_count = len(store) if len(store) > 0 else (len(apps) + len(infra) + len(org) + len(vendors))

    return render_template('inventory/home.html',
        apps=apps,
        infra=infra,
        org=org,
        vendors=vendors,
        total_cost=total_cost,
        flagged_count=len(flagged),
        enriched_count=len(enriched),
        total_count=total_count,
    )


@inventory_bp.route('/audit')
def inventory_audit():
    """Display the inventory audit report for the current deal."""
    import json
    from flask import session

    current_deal_id = session.get('current_deal_id')
    if not current_deal_id:
        return render_template('inventory/audit.html', report=None)

    audit_path = Path(f"output/deals/{current_deal_id}/inventory_audit.json")
    if audit_path.exists():
        with open(audit_path) as f:
            report = json.load(f)
    else:
        report = None

    return render_template('inventory/audit.html', report=report)


@inventory_bp.route('/insights')
def insights():
    """Show the 'So What' insights report."""
    store = get_inventory_store()

    if len(store) == 0:
        flash("No inventory data loaded. Upload files first.", "warning")
        return redirect(url_for('inventory.inventory_home'))

    # Generate findings from inventory patterns
    findings = analyze_inventory_for_findings(store, "target")

    # Also pull real risks from findings files
    try:
        import json
        output_dir = Path(__file__).parent.parent.parent / "output"
        findings_files = sorted(output_dir.glob("findings_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

        if findings_files:
            with open(findings_files[0], 'r') as f:
                findings_data = json.load(f)

            risks = findings_data.get('risks', [])
            for risk in risks:
                findings.append(Finding(
                    title=risk.get('title', 'Unknown Risk'),
                    so_what=risk.get('so_what', '') or risk.get('description', ''),
                    evidence=[f"From {risk.get('domain', 'analysis')} domain"],
                    severity=risk.get('severity', 'medium'),
                    category="risk",
                    recommendation=risk.get('mitigation', ''),
                ))
            logger.info(f"Added {len(risks)} risks from findings file")
    except Exception as e:
        logger.warning(f"Could not load risks from findings file: {e}")

    # Infer data flows (in production, these would come from user input)
    apps = store.get_items(inventory_type="application", entity="target", status="active")
    data_flows = _infer_data_flows(apps)

    # Generate the report HTML
    report_path = generate_sowhat_report(
        inventory_store=store,
        findings=findings,
        data_flows=data_flows,
        output_dir=Path("data/reports"),
        target_name="Target Company",
        deal_type="acquisition",
    )

    # Read and return the report
    report_html = report_path.read_text()

    return report_html


@inventory_bp.route('/diagram')
def diagram():
    """Show interactive data flow diagram."""
    store = get_inventory_store()
    apps = store.get_items(inventory_type="application", entity="target", status="active")

    # Build Mermaid diagram
    mermaid_code = _build_app_diagram(apps)

    return render_template('inventory/diagram.html',
        mermaid_code=mermaid_code,
        apps=apps,
    )


@inventory_bp.route('/api/items')
def api_items():
    """API endpoint for inventory items."""
    store = get_inventory_store()
    inv_type = request.args.get('type', None)
    entity = request.args.get('entity', 'target')

    items = store.get_items(inventory_type=inv_type, entity=entity, status="active")

    return jsonify({
        'count': len(items),
        'items': [item.to_dict() for item in items]
    })


@inventory_bp.route('/api/summary')
def api_summary():
    """API endpoint for inventory summary."""
    store = get_inventory_store()

    apps = store.get_items(inventory_type="application", entity="target", status="active")
    infra = store.get_items(inventory_type="infrastructure", entity="target", status="active")

    return jsonify({
        'total': len(store),
        'by_type': {
            'application': len(apps),
            'infrastructure': len(infra),
            'organization': len(store.get_items(inventory_type="organization")),
            'vendor': len(store.get_items(inventory_type="vendor")),
        },
        'total_cost': sum(app.cost or 0 for app in apps),
        'flagged': len([i for i in store.get_items() if i.needs_investigation]),
        'enriched': len([i for i in store.get_items() if i.is_enriched]),
    })


@inventory_bp.route('/upload', methods=['POST'])
def upload_inventory():
    """Upload and ingest inventory files."""
    from tools_v2.file_router import ingest_file

    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('inventory.inventory_home'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('inventory.inventory_home'))

    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    file.save(file_path)

    # Ingest into inventory store
    store = get_inventory_store()
    try:
        result = ingest_file(file_path, store, entity="target")

        if result.errors:
            for error in result.errors:
                flash(f"Error: {error}", "error")
        else:
            flash(f"Imported {result.inventory_items_added} items from {file.filename}", "success")

            # Save the store to deal-specific path
            save_inventory_store(store)

    except Exception as e:
        logger.exception(f"Failed to ingest {file.filename}")
        flash(f"Failed to process file: {str(e)}", "error")

    return redirect(url_for('inventory.inventory_home'))


@inventory_bp.route('/enrich', methods=['POST'])
def enrich_inventory():
    """Run LLM enrichment on inventory items."""
    from tools_v2.file_router import enrich_inventory as run_enrichment

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        flash("No API key configured for enrichment", "error")
        return redirect(url_for('inventory.inventory_home'))

    store = get_inventory_store()

    try:
        results = run_enrichment(
            store,
            api_key=api_key,
            inventory_types=["application"],
            entity="target",
        )

        app_result = results.get("application")
        if app_result:
            flash(
                f"Enriched {app_result.items_enriched} items, "
                f"flagged {app_result.items_flagged} for investigation",
                "success"
            )

        # Save the store to deal-specific path
        save_inventory_store(store)

    except Exception as e:
        logger.exception("Enrichment failed")
        flash(f"Enrichment failed: {str(e)}", "error")

    return redirect(url_for('inventory.inventory_home'))


@inventory_bp.route('/clear', methods=['POST'])
def clear_inventory():
    """Clear inventory data for the current deal."""
    from flask import session

    current_deal_id = session.get('current_deal_id')
    store_key = current_deal_id or 'default'

    # Clear the cached store
    if store_key in _inventory_stores:
        store = _inventory_stores[store_key]
        # Remove the saved file if it exists
        if store.storage_path and store.storage_path.exists():
            store.storage_path.unlink()
            logger.info(f"Removed inventory file: {store.storage_path}")
        del _inventory_stores[store_key]
    else:
        # Fallback: try to remove default path
        default_path = Path("data/inventory_store.json")
        if default_path.exists():
            default_path.unlink()

    flash(f"Inventory cleared for deal {current_deal_id or 'default'}", "info")
    return redirect(url_for('inventory.inventory_home'))


def _infer_data_flows(apps):
    """Infer likely data flows from application inventory."""
    flows = []

    # Find common integration patterns
    erp_apps = [a for a in apps if any(x in a.name.lower() for x in ['sap', 'oracle', 'erp', 'netsuite'])]
    crm_apps = [a for a in apps if any(x in a.name.lower() for x in ['salesforce', 'crm', 'dynamics'])]
    hr_apps = [a for a in apps if any(x in a.name.lower() for x in ['workday', 'adp', 'payroll'])]
    core_apps = [a for a in apps if a.criticality and 'critical' in str(a.criticality).lower()]

    # Add likely flows
    for erp in erp_apps[:1]:  # Just first ERP
        for crm in crm_apps[:1]:
            flows.append(DataFlow(
                source=erp.name,
                target=crm.name,
                data_type="Customer Data",
                frequency="batch",
                critical=True,
                notes="Inferred - needs validation"
            ))
        for hr in hr_apps[:1]:
            flows.append(DataFlow(
                source=hr.name,
                target=erp.name,
                data_type="Employee Data",
                frequency="batch",
                critical=False,
                notes="Inferred - needs validation"
            ))

    return flows


def _build_app_diagram(apps):
    """Build Mermaid diagram from apps with data flow connections."""
    if not apps:
        return "flowchart TD\n    empty[No applications in inventory]"

    lines = ["flowchart LR"]

    # Helper to create safe node IDs (alphanumeric and underscores only)
    def make_id(name):
        import re
        # Remove everything except alphanumeric and spaces, then replace spaces with underscores
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', name)
        return clean.replace(" ", "_")[:20]

    # Helper to format cost for display
    def format_cost(app):
        cost = app.cost or 0
        if cost >= 1000000:
            return f"${cost/1000000:.1f}M"
        elif cost >= 1000:
            return f"${cost/1000:.0f}K"
        elif cost > 0:
            return f"${cost:.0f}"
        return ""

    # Helper to get criticality indicator
    def get_crit_indicator(app):
        crit = str(app.criticality or '').lower()
        if 'critical' in crit:
            return "🔴"
        elif 'high' in crit:
            return "🟠"
        elif 'medium' in crit:
            return "🟡"
        return ""

    # Helper to build node label with cost
    def node_label(app):
        cost_str = format_cost(app)
        crit = get_crit_indicator(app)
        if cost_str and crit:
            return f"{crit} {app.name}<br/>{cost_str}"
        elif cost_str:
            return f"{app.name}<br/>{cost_str}"
        elif crit:
            return f"{crit} {app.name}"
        return app.name

    # Group apps by category for connections
    by_category = {}
    for app in apps:
        cat = app.data.get('category', 'Other').lower()
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(app)

    # Find key apps by category
    def find_app(keywords):
        for app in apps:
            name_lower = app.name.lower()
            cat_lower = app.data.get('category', '').lower()
            for kw in keywords:
                if kw in name_lower or kw in cat_lower:
                    return app
        return None

    erp = find_app(['erp', 'sap', 'netsuite', 'oracle'])
    crm = find_app(['crm', 'salesforce', 'dynamics'])
    hr = find_app(['hr', 'hcm', 'workday', 'adp', 'payroll'])
    finance = find_app(['finance', 'blackline', 'concur'])
    policy = find_app(['policy', 'duck creek policy', 'majesco', 'guidewire policy'])
    claims = find_app(['claims', 'claimcenter'])
    identity = find_app(['identity', 'entra', 'azure ad', 'cyberark'])
    analytics = find_app(['analytics', 'power bi', 'qlik', 'databricks', 'snowflake'])
    email = find_app(['email', 'exchange', 'outlook'])
    collab = find_app(['collaboration', 'slack', 'teams', 'microsoft 365'])

    # Build subgraphs by functional area with cost in labels
    lines.append('    subgraph Core["💼 Core Business Systems"]')
    if policy:
        lines.append(f'        {make_id(policy.name)}["{node_label(policy)}"]')
    if claims:
        lines.append(f'        {make_id(claims.name)}["{node_label(claims)}"]')
    if erp:
        lines.append(f'        {make_id(erp.name)}["{node_label(erp)}"]')
    lines.append('    end')

    lines.append('    subgraph Support["🔧 Support Systems"]')
    if hr:
        lines.append(f'        {make_id(hr.name)}["{node_label(hr)}"]')
    if finance:
        lines.append(f'        {make_id(finance.name)}["{node_label(finance)}"]')
    if crm:
        lines.append(f'        {make_id(crm.name)}["{node_label(crm)}"]')
    lines.append('    end')

    lines.append('    subgraph Platform["🔐 Platform Services"]')
    if identity:
        lines.append(f'        {make_id(identity.name)}["{node_label(identity)}"]')
    if email:
        lines.append(f'        {make_id(email.name)}["{node_label(email)}"]')
    if collab:
        lines.append(f'        {make_id(collab.name)}["{node_label(collab)}"]')
    lines.append('    end')

    lines.append('    subgraph Data["📊 Data & Analytics"]')
    if analytics:
        lines.append(f'        {make_id(analytics.name)}["{node_label(analytics)}"]')
    lines.append('    end')

    # Add data flow connections (these are inferred - to be validated in calls)
    connections = []

    # Insurance-specific flows
    if policy and claims:
        connections.append((policy, claims, "Claims Data"))
    if policy and erp:
        connections.append((policy, erp, "Premium Data"))

    # Standard enterprise flows
    if erp and finance:
        connections.append((erp, finance, "GL Data"))
    if erp and hr:
        connections.append((hr, erp, "Employee Data"))
    if crm and erp:
        connections.append((crm, erp, "Customer Data"))

    # Identity feeds everything
    if identity:
        if erp:
            connections.append((identity, erp, "SSO"))
        if crm:
            connections.append((identity, crm, "SSO"))

    # Analytics pulls from core systems
    if analytics:
        if erp:
            connections.append((erp, analytics, ""))
        if policy:
            connections.append((policy, analytics, ""))

    # Add connections to diagram
    for src, tgt, label in connections:
        src_id = make_id(src.name)
        tgt_id = make_id(tgt.name)
        if label:
            lines.append(f'    {src_id} -->|"{label}"| {tgt_id}')
        else:
            lines.append(f'    {src_id} --> {tgt_id}')

    # Track which apps are actually in the diagram
    apps_in_diagram = [a for a in [policy, claims, erp, hr, finance, crm, identity, email, collab, analytics] if a]

    # Style apps by criticality level
    for app in apps_in_diagram:
        crit = str(app.criticality or '').lower()
        app_id = make_id(app.name)
        if 'critical' in crit:
            lines.append(f'    style {app_id} fill:#fecaca,stroke:#dc2626,stroke-width:3px')
        elif 'high' in crit:
            lines.append(f'    style {app_id} fill:#fed7aa,stroke:#ea580c,stroke-width:2px')
        elif 'medium' in crit:
            lines.append(f'    style {app_id} fill:#fef08a,stroke:#ca8a04,stroke-width:2px')

    return "\n".join(lines)
