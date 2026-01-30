"""
Inventory Report Builder

Builds HTML sections for inventory data in reports.
Integrates with the main html_report.py generator.

Features:
- Inventory summary section with counts and costs
- Application inventory table with enrichment
- Infrastructure inventory table
- Flagged items highlight section
- Inventory-linked findings

Usage:
    from tools_v2.inventory_report import generate_inventory_report
    from stores.inventory_store import InventoryStore

    store = InventoryStore()
    # ... add items ...

    html_path = generate_inventory_report(store, output_dir, "Acme Corp")
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem


def build_inventory_nav_link(inventory_store: InventoryStore) -> str:
    """Build navigation link for inventory section."""
    total = len(inventory_store)
    return f'<a href="#inventory">Inventory ({total})</a>'


def build_inventory_stat_card(inventory_store: InventoryStore, entity: str = "target") -> str:
    """Build stat card showing inventory counts."""
    total = len([i for i in inventory_store.get_items(entity=entity) if i.is_active])
    flagged = len([i for i in inventory_store.get_items(entity=entity) if i.needs_investigation])

    flag_indicator = f' <span style="color: #ea580c;">({flagged} flagged)</span>' if flagged > 0 else ''

    return f'''
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Inventory Items{flag_indicator}</div>
        </div>
    '''


def build_inventory_section(
    inventory_store: InventoryStore,
    entity: str = "target",
) -> str:
    """
    Build complete inventory section HTML.

    Args:
        inventory_store: The inventory store
        entity: "target" or "buyer"

    Returns:
        HTML string for inventory section
    """
    apps = inventory_store.get_items(inventory_type="application", entity=entity, status="active")
    infra = inventory_store.get_items(inventory_type="infrastructure", entity=entity, status="active")
    org = inventory_store.get_items(inventory_type="organization", entity=entity, status="active")
    vendors = inventory_store.get_items(inventory_type="vendor", entity=entity, status="active")

    # Build subsections
    apps_html = _build_applications_table(apps) if apps else '<p class="text-muted">No applications in inventory.</p>'
    infra_html = _build_infrastructure_table(infra) if infra else '<p class="text-muted">No infrastructure in inventory.</p>'
    org_html = _build_organization_table(org) if org else '<p class="text-muted">No organization data in inventory.</p>'
    vendors_html = _build_vendors_table(vendors) if vendors else '<p class="text-muted">No vendor contracts in inventory.</p>'

    # Build flagged items section
    flagged = [i for i in inventory_store.get_items(entity=entity) if i.needs_investigation]
    flagged_html = _build_flagged_section(flagged) if flagged else ''

    # Calculate total cost
    total_cost = sum(app.cost or 0 for app in apps)
    cost_str = f"${total_cost:,.0f}" if total_cost > 0 else "N/A"

    return f'''
    <section id="inventory">
        <h2>📦 Inventory</h2>

        <div class="inventory-summary" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
            <div class="mini-stat">
                <div class="mini-stat-value">{len(apps)}</div>
                <div class="mini-stat-label">Applications</div>
            </div>
            <div class="mini-stat">
                <div class="mini-stat-value">{len(infra)}</div>
                <div class="mini-stat-label">Infrastructure</div>
            </div>
            <div class="mini-stat">
                <div class="mini-stat-value">{len(org)}</div>
                <div class="mini-stat-label">Organization</div>
            </div>
            <div class="mini-stat">
                <div class="mini-stat-value">{cost_str}</div>
                <div class="mini-stat-label">Total App Cost</div>
            </div>
        </div>

        {flagged_html}

        <h3 style="margin-top: 1.5rem; margin-bottom: 1rem;">Applications ({len(apps)})</h3>
        {apps_html}

        <h3 style="margin-top: 2rem; margin-bottom: 1rem;">Infrastructure ({len(infra)})</h3>
        {infra_html}

        <h3 style="margin-top: 2rem; margin-bottom: 1rem;">Organization ({len(org)})</h3>
        {org_html}

        <h3 style="margin-top: 2rem; margin-bottom: 1rem;">Vendor Contracts ({len(vendors)})</h3>
        {vendors_html}
    </section>
    '''


def _build_applications_table(apps: List[InventoryItem]) -> str:
    """Build HTML table for applications."""
    rows = []

    for app in sorted(apps, key=lambda x: x.name.lower()):
        name = app.name
        vendor = app.data.get("vendor", "—")
        version = app.data.get("version", "—")
        hosting = app.data.get("hosting", "—")
        cost = f"${app.cost:,.0f}" if app.cost else "—"
        criticality = app.data.get("criticality", "—")

        # Enrichment badge
        enrichment_badge = ""
        if app.is_enriched:
            note = app.enrichment.get("note", "")
            if note:
                # Truncate long notes
                short_note = note[:100] + "..." if len(note) > 100 else note
                enrichment_badge = f'<span class="tooltip" title="{note}">ℹ️</span>'

        # Flag badge
        flag_badge = ""
        if app.needs_investigation:
            flag_badge = '<span class="badge badge-warning">⚠️ Investigate</span>'

        row = f'''
        <tr>
            <td><code style="font-size: 0.75rem;">{app.item_id}</code></td>
            <td><strong>{name}</strong> {enrichment_badge} {flag_badge}</td>
            <td>{vendor}</td>
            <td>{version}</td>
            <td>{hosting}</td>
            <td style="text-align: right;">{cost}</td>
            <td>{_criticality_badge(criticality)}</td>
        </tr>
        '''
        rows.append(row)

    return f'''
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Application</th>
                    <th>Vendor</th>
                    <th>Version</th>
                    <th>Hosting</th>
                    <th style="text-align: right;">Cost</th>
                    <th>Criticality</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    '''


def _build_infrastructure_table(infra: List[InventoryItem]) -> str:
    """Build HTML table for infrastructure."""
    rows = []

    for item in sorted(infra, key=lambda x: x.name.lower()):
        name = item.name
        item_type = item.data.get("type", "—")
        os = item.data.get("os", "—")
        env = item.data.get("environment", "—")
        location = item.data.get("location", "—")

        # Environment badge
        env_badge = _environment_badge(env)

        row = f'''
        <tr>
            <td><code style="font-size: 0.75rem;">{item.item_id}</code></td>
            <td><strong>{name}</strong></td>
            <td>{item_type}</td>
            <td>{os}</td>
            <td>{env_badge}</td>
            <td>{location}</td>
        </tr>
        '''
        rows.append(row)

    return f'''
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>OS</th>
                    <th>Environment</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    '''


def _build_organization_table(org: List[InventoryItem]) -> str:
    """Build HTML table for organization."""
    rows = []

    for item in sorted(org, key=lambda x: x.name.lower()):
        role = item.data.get("role", item.data.get("title", item.name))
        team = item.data.get("team", "—")
        headcount = item.data.get("headcount", "—")
        reports_to = item.data.get("reports_to", "—")

        row = f'''
        <tr>
            <td><code style="font-size: 0.75rem;">{item.item_id}</code></td>
            <td><strong>{role}</strong></td>
            <td>{team}</td>
            <td style="text-align: center;">{headcount}</td>
            <td>{reports_to}</td>
        </tr>
        '''
        rows.append(row)

    return f'''
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Role</th>
                    <th>Team</th>
                    <th style="text-align: center;">Headcount</th>
                    <th>Reports To</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    '''


def _build_vendors_table(vendors: List[InventoryItem]) -> str:
    """Build HTML table for vendor contracts."""
    rows = []

    for item in sorted(vendors, key=lambda x: x.name.lower()):
        name = item.name
        contract_type = item.data.get("contract_type", "—")
        start_date = item.data.get("start_date", "—")
        end_date = item.data.get("end_date", "—")
        acv = item.data.get("acv", "")
        acv_str = f"${float(acv):,.0f}" if acv else "—"

        row = f'''
        <tr>
            <td><code style="font-size: 0.75rem;">{item.item_id}</code></td>
            <td><strong>{name}</strong></td>
            <td>{contract_type}</td>
            <td>{start_date}</td>
            <td>{end_date}</td>
            <td style="text-align: right;">{acv_str}</td>
        </tr>
        '''
        rows.append(row)

    return f'''
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Vendor</th>
                    <th>Contract Type</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                    <th style="text-align: right;">ACV</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    '''


def _build_flagged_section(flagged: List[InventoryItem]) -> str:
    """Build section highlighting flagged items."""
    if not flagged:
        return ""

    items_html = []
    for item in flagged:
        reason = item.enrichment.get("note", "Needs investigation")
        items_html.append(f'''
            <li>
                <strong>{item.name}</strong>
                <code style="font-size: 0.75rem; margin-left: 0.5rem;">{item.item_id}</code>
                <span style="color: #64748b; margin-left: 0.5rem;">— {reason}</span>
            </li>
        ''')

    return f'''
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: start; gap: 0.75rem;">
            <span style="font-size: 1.25rem;">⚠️</span>
            <div>
                <strong style="color: #92400e;">Items Requiring Investigation ({len(flagged)})</strong>
                <p style="margin: 0.5rem 0 0 0; color: #78350f; font-size: 0.9rem;">
                    The following items could not be identified and may need manual review:
                </p>
                <ul style="margin: 0.5rem 0 0 0; padding-left: 1.5rem; color: #78350f;">
                    {''.join(items_html)}
                </ul>
            </div>
        </div>
    </div>
    '''


def _criticality_badge(criticality: str) -> str:
    """Generate badge HTML for criticality level."""
    if not criticality or criticality == "—":
        return "—"

    crit_lower = str(criticality).lower()
    colors = {
        "critical": ("#dc2626", "#fef2f2"),
        "high": ("#ea580c", "#fff7ed"),
        "medium": ("#ca8a04", "#fefce8"),
        "low": ("#16a34a", "#f0fdf4"),
    }
    text_color, bg_color = colors.get(crit_lower, ("#64748b", "#f1f5f9"))

    return f'''<span style="
        background: {bg_color};
        color: {text_color};
        padding: 0.125rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
    ">{criticality}</span>'''


def _environment_badge(env: str) -> str:
    """Generate badge HTML for environment."""
    if not env or env == "—":
        return "—"

    env_lower = str(env).lower()
    if "prod" in env_lower:
        return f'''<span style="
            background: #dcfce7;
            color: #166534;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        ">{env}</span>'''
    elif "dev" in env_lower:
        return f'''<span style="
            background: #dbeafe;
            color: #1e40af;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        ">{env}</span>'''
    elif "test" in env_lower or "qa" in env_lower:
        return f'''<span style="
            background: #fef3c7;
            color: #92400e;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        ">{env}</span>'''
    else:
        return f'''<span style="
            background: #f1f5f9;
            color: #64748b;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        ">{env}</span>'''


def get_inventory_styles() -> str:
    """Get additional CSS styles for inventory section."""
    return '''
        .mini-stat {
            background: #f8fafc;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }

        .mini-stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2563eb;
        }

        .mini-stat-label {
            font-size: 0.85rem;
            color: #64748b;
        }

        .badge {
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 500;
            margin-left: 0.25rem;
        }

        .badge-warning {
            background: #fef3c7;
            color: #92400e;
        }

        .tooltip {
            cursor: help;
        }

        #inventory h3 {
            color: #1e293b;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.5rem;
        }
    '''


def generate_inventory_report(
    inventory_store: InventoryStore,
    output_dir: Path,
    target_name: str = "Target Company",
    entity: str = "target",
    timestamp: str = None,
) -> Path:
    """
    Generate a standalone inventory report.

    Creates a self-contained HTML file with the inventory data.

    Args:
        inventory_store: The inventory store
        output_dir: Directory to save the report
        target_name: Name of the target company
        entity: "target" or "buyer"
        timestamp: Optional timestamp for filename

    Returns:
        Path to the generated HTML file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"inventory_report_{timestamp}.html"

    # Get counts
    apps = inventory_store.get_items(inventory_type="application", entity=entity, status="active")
    infra = inventory_store.get_items(inventory_type="infrastructure", entity=entity, status="active")
    org = inventory_store.get_items(inventory_type="organization", entity=entity, status="active")
    vendors = inventory_store.get_items(inventory_type="vendor", entity=entity, status="active")
    total = len(apps) + len(infra) + len(org) + len(vendors)

    # Calculate total cost
    total_cost = sum(app.cost or 0 for app in apps)

    # Build inventory section
    inventory_html = build_inventory_section(inventory_store, entity)

    # Build complete HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Inventory Report - {target_name}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --critical: #dc2626;
            --high: #ea580c;
            --medium: #ca8a04;
            --low: #16a34a;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: var(--text);
        }}

        .subtitle {{
            color: var(--text-muted);
            margin-bottom: 2rem;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .stat-label {{
            color: var(--text-muted);
        }}

        section {{
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: #f8fafc;
            font-weight: 600;
            color: var(--text-muted);
        }}

        tr:hover {{
            background: #f8fafc;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        code {{
            background: #f1f5f9;
            padding: 0.125rem 0.375rem;
            border-radius: 4px;
            font-family: monospace;
        }}

        {get_inventory_styles()}
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 IT Inventory Report</h1>
        <p class="subtitle">{target_name} • Generated {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(apps)}</div>
                <div class="stat-label">Applications</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(infra)}</div>
                <div class="stat-label">Infrastructure</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${total_cost:,.0f}</div>
                <div class="stat-label">Total App Cost</div>
            </div>
        </div>

        {inventory_html}

        <footer style="text-align: center; color: var(--text-muted); margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--border);">
            <p>Generated by IT Due Diligence Agent • Inventory System v1.0</p>
        </footer>
    </div>
</body>
</html>'''

    output_file.write_text(html)
    return output_file
