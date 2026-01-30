"""
"So What" Report Generator

Leadership-focused report that leads with insights, not data.

Structure:
1. Key Findings (the "so what")
2. Data Flow & Connectivity (visual)
3. Deal Implications
4. Recommended Actions
5. Appendix: Supporting Inventory

Philosophy: Don't tell them what they have. Tell them what it MEANS.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem


@dataclass
class Finding:
    """A key finding with supporting evidence."""
    title: str
    so_what: str  # The implication - why this matters
    evidence: List[str] = field(default_factory=list)  # Inventory item IDs
    severity: str = "medium"  # critical, high, medium, low
    category: str = "general"  # integration, cost, risk, opportunity
    recommendation: str = ""


@dataclass
class DataFlow:
    """A data flow between systems."""
    source: str
    target: str
    data_type: str = "data"  # data, api, file, manual
    frequency: str = "unknown"  # realtime, batch, manual
    critical: bool = False
    notes: str = ""


def generate_sowhat_report(
    inventory_store: InventoryStore,
    findings: List[Finding],
    data_flows: List[DataFlow] = None,
    output_dir: Path = None,
    target_name: str = "Target Company",
    deal_type: str = "acquisition",
    entity: str = "target",
) -> Path:
    """
    Generate a "So What" focused report.

    Args:
        inventory_store: The inventory data (for evidence/appendix)
        findings: List of key findings with implications
        data_flows: Optional list of data flows for diagrams
        output_dir: Where to save the report
        target_name: Name of target company
        deal_type: acquisition, carve-out, merger
        entity: target or buyer

    Returns:
        Path to generated HTML file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_dir is None:
        output_dir = Path(".")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"it_dd_insights_{timestamp}.html"

    # Get inventory stats for context
    apps = inventory_store.get_items(inventory_type="application", entity=entity, status="active")
    infra = inventory_store.get_items(inventory_type="infrastructure", entity=entity, status="active")
    total_cost = sum(app.cost or 0 for app in apps)

    # Build sections
    findings_html = _build_findings_section(findings, inventory_store)
    dataflow_html = _build_dataflow_section(data_flows, apps) if data_flows else _build_inferred_dataflow(apps)
    implications_html = _build_implications_section(findings, deal_type)
    actions_html = _build_actions_section(findings)
    appendix_html = _build_appendix(inventory_store, entity)

    # Executive summary stats
    critical_count = len([f for f in findings if f.severity == "critical"])
    high_count = len([f for f in findings if f.severity == "high"])

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Due Diligence Insights - {target_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
    <style>
        :root {{
            --primary: #1e40af;
            --critical: #dc2626;
            --high: #ea580c;
            --medium: #ca8a04;
            --low: #16a34a;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
            --border: #e2e8f0;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 3rem 2rem;
            margin-bottom: 2rem;
        }}

        header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .executive-summary {{
            background: var(--card);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 4px solid var(--primary);
        }}

        .executive-summary h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--primary);
        }}

        .stat-row {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
        }}

        .stat-value.critical {{ color: var(--critical); }}
        .stat-value.high {{ color: var(--high); }}
        .stat-value.cost {{ color: var(--primary); }}

        .stat-label {{
            font-size: 0.85rem;
            color: var(--muted);
        }}

        section {{
            background: var(--card);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}

        section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border);
        }}

        .finding {{
            border-left: 4px solid var(--medium);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            background: #fafafa;
            border-radius: 0 8px 8px 0;
        }}

        .finding.critical {{ border-left-color: var(--critical); background: #fef2f2; }}
        .finding.high {{ border-left-color: var(--high); background: #fff7ed; }}
        .finding.medium {{ border-left-color: var(--medium); background: #fefce8; }}
        .finding.low {{ border-left-color: var(--low); background: #f0fdf4; }}

        .finding-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }}

        .severity-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .severity-badge.critical {{ background: var(--critical); color: white; }}
        .severity-badge.high {{ background: var(--high); color: white; }}
        .severity-badge.medium {{ background: var(--medium); color: white; }}
        .severity-badge.low {{ background: var(--low); color: white; }}

        .finding h3 {{
            font-size: 1.1rem;
            margin: 0;
        }}

        .so-what {{
            font-size: 1rem;
            margin: 0.75rem 0;
            color: var(--text);
        }}

        .so-what strong {{
            color: var(--primary);
        }}

        .evidence {{
            font-size: 0.85rem;
            color: var(--muted);
            margin-top: 0.75rem;
        }}

        .evidence code {{
            background: #e2e8f0;
            padding: 0.125rem 0.375rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}

        .mermaid {{
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}

        .diagram-caption {{
            text-align: center;
            font-size: 0.9rem;
            color: var(--muted);
            margin-top: 0.5rem;
        }}

        .action-item {{
            display: flex;
            gap: 1rem;
            padding: 1rem;
            background: #f8fafc;
            border-radius: 8px;
            margin-bottom: 0.75rem;
            align-items: flex-start;
        }}

        .action-number {{
            background: var(--primary);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            flex-shrink: 0;
        }}

        .action-content h4 {{
            margin: 0 0 0.25rem 0;
            font-size: 1rem;
        }}

        .action-content p {{
            margin: 0;
            font-size: 0.9rem;
            color: var(--muted);
        }}

        .appendix {{
            background: #f8fafc;
        }}

        .appendix h2 {{
            color: var(--muted);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 0.625rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: #f1f5f9;
            font-weight: 600;
            color: var(--muted);
        }}

        .nav {{
            position: sticky;
            top: 0;
            background: white;
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border);
            z-index: 100;
            display: flex;
            gap: 1.5rem;
        }}

        .nav a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}

        .nav a:hover {{
            text-decoration: underline;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>IT Due Diligence Insights</h1>
            <p class="subtitle">{target_name} • {deal_type.title()} Analysis • {datetime.now().strftime("%B %d, %Y")}</p>
        </div>
    </header>

    <nav class="nav">
        <a href="#findings">Key Findings</a>
        <a href="#dataflow">Data & Connectivity</a>
        <a href="#implications">Deal Implications</a>
        <a href="#actions">Recommended Actions</a>
        <a href="#appendix">Appendix</a>
    </nav>

    <div class="container">
        <div class="executive-summary">
            <h2>Executive Summary</h2>
            <p>Analysis of {len(apps)} applications and {len(infra)} infrastructure components reveals {len(findings)} key findings requiring attention.</p>
            <div class="stat-row">
                <div class="stat">
                    <div class="stat-value critical">{critical_count}</div>
                    <div class="stat-label">Critical Findings</div>
                </div>
                <div class="stat">
                    <div class="stat-value high">{high_count}</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat">
                    <div class="stat-value cost">${total_cost:,.0f}</div>
                    <div class="stat-label">Annual IT Spend</div>
                </div>
            </div>
        </div>

        {findings_html}

        {dataflow_html}

        {implications_html}

        {actions_html}

        {appendix_html}
    </div>

    <footer>
        <p>Generated by IT Due Diligence Agent • "So What" Report v1.0</p>
        <p>Data is deterministic from inventory import. Analysis is AI-assisted.</p>
    </footer>
</body>
</html>'''

    output_file.write_text(html)
    return output_file


def _build_findings_section(findings: List[Finding], inventory_store: InventoryStore) -> str:
    """Build the key findings section."""
    if not findings:
        return '''
        <section id="findings">
            <h2>🎯 Key Findings</h2>
            <p style="color: var(--muted);">No findings generated yet. Run analysis to identify key insights.</p>
        </section>
        '''

    findings_html = []
    for i, finding in enumerate(findings, 1):
        # Get evidence items
        evidence_items = []
        for item_id in finding.evidence:
            item = inventory_store.get_item(item_id)
            if item:
                evidence_items.append(f'<code>{item_id}</code> {item.name}')

        evidence_str = ", ".join(evidence_items) if evidence_items else "Based on inventory analysis"

        findings_html.append(f'''
            <div class="finding {finding.severity}">
                <div class="finding-header">
                    <span class="severity-badge {finding.severity}">{finding.severity}</span>
                    <h3>{finding.title}</h3>
                </div>
                <p class="so-what"><strong>So What:</strong> {finding.so_what}</p>
                {f'<p class="recommendation"><strong>Recommendation:</strong> {finding.recommendation}</p>' if finding.recommendation else ''}
                <p class="evidence"><strong>Evidence:</strong> {evidence_str}</p>
            </div>
        ''')

    return f'''
    <section id="findings">
        <h2>🎯 Key Findings</h2>
        {''.join(findings_html)}
    </section>
    '''


def _build_dataflow_section(data_flows: List[DataFlow], apps: List[InventoryItem]) -> str:
    """Build data flow diagram section with explicit flows."""
    if not data_flows:
        return _build_inferred_dataflow(apps)

    # Build Mermaid diagram
    mermaid_lines = ["flowchart LR"]

    # Group by criticality
    critical_flows = [f for f in data_flows if f.critical]
    normal_flows = [f for f in data_flows if not f.critical]

    for flow in data_flows:
        source_id = flow.source.replace(" ", "_").replace("-", "_")
        target_id = flow.target.replace(" ", "_").replace("-", "_")

        if flow.critical:
            mermaid_lines.append(f'    {source_id}["{flow.source}"] ==>|"{flow.data_type}"| {target_id}["{flow.target}"]')
        else:
            mermaid_lines.append(f'    {source_id}["{flow.source}"] -->|"{flow.data_type}"| {target_id}["{flow.target}"]')

    mermaid_code = "\n".join(mermaid_lines)

    return f'''
    <section id="dataflow">
        <h2>🔄 Data Flow & Connectivity</h2>
        <p>Critical data flows are shown with bold arrows. These represent the highest separation complexity.</p>

        <div class="mermaid">
{mermaid_code}
        </div>
        <p class="diagram-caption">Application connectivity map • {len(critical_flows)} critical flows identified</p>

        <h3 style="margin-top: 1.5rem;">Critical Data Flows</h3>
        <table>
            <thead>
                <tr>
                    <th>Source</th>
                    <th>Target</th>
                    <th>Data Type</th>
                    <th>Frequency</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"""
                <tr>
                    <td>{f.source}</td>
                    <td>{f.target}</td>
                    <td>{f.data_type}</td>
                    <td>{f.frequency}</td>
                    <td>{f.notes}</td>
                </tr>
                """ for f in critical_flows)}
            </tbody>
        </table>
    </section>
    '''


def _build_inferred_dataflow(apps: List[InventoryItem]) -> str:
    """Build inferred data flow from inventory when explicit flows not provided."""
    if not apps:
        return '''
        <section id="dataflow">
            <h2>🔄 Data Flow & Connectivity</h2>
            <p style="color: var(--muted);">No application data available for connectivity analysis.</p>
        </section>
        '''

    # Infer connections based on common patterns
    # Group apps by likely integration points
    erp_apps = [a for a in apps if any(x in a.name.lower() for x in ['sap', 'oracle', 'erp', 'netsuite'])]
    crm_apps = [a for a in apps if any(x in a.name.lower() for x in ['salesforce', 'crm', 'hubspot', 'dynamics'])]
    hr_apps = [a for a in apps if any(x in a.name.lower() for x in ['workday', 'adp', 'payroll', 'hr'])]
    core_apps = [a for a in apps if a.criticality and 'critical' in str(a.criticality).lower()]

    # Build a simple inferred diagram
    mermaid_lines = ["flowchart TD"]
    mermaid_lines.append('    subgraph Core["Core Business Systems"]')

    for app in core_apps[:5]:  # Limit to top 5
        app_id = app.name.replace(" ", "_").replace("-", "_")[:20]
        mermaid_lines.append(f'        {app_id}["{app.name}"]')

    mermaid_lines.append('    end')

    if erp_apps:
        mermaid_lines.append('    subgraph ERP["ERP / Finance"]')
        for app in erp_apps[:3]:
            app_id = app.name.replace(" ", "_").replace("-", "_")[:20]
            mermaid_lines.append(f'        {app_id}["{app.name}"]')
        mermaid_lines.append('    end')

    if crm_apps:
        mermaid_lines.append('    subgraph CRM["CRM / Sales"]')
        for app in crm_apps[:3]:
            app_id = app.name.replace(" ", "_").replace("-", "_")[:20]
            mermaid_lines.append(f'        {app_id}["{app.name}"]')
        mermaid_lines.append('    end')

    # Add a note about inference
    mermaid_lines.append('    subgraph Note["⚠️ Inferred - Needs Validation"]')
    mermaid_lines.append('        note["Data flows not documented"]')
    mermaid_lines.append('    end')

    mermaid_code = "\n".join(mermaid_lines)

    return f'''
    <section id="dataflow">
        <h2>🔄 Data Flow & Connectivity</h2>

        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <strong>⚠️ Data flows not documented in inventory.</strong>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">The diagram below shows application groupings based on type. Actual data flows require VDR request for integration documentation.</p>
        </div>

        <div class="mermaid">
{mermaid_code}
        </div>
        <p class="diagram-caption">Inferred application groupings • Request integration architecture for accurate flows</p>

        <h3 style="margin-top: 1.5rem;">Recommended VDR Request</h3>
        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
            <li>System integration architecture diagram</li>
            <li>Data flow documentation between core systems</li>
            <li>API inventory and middleware documentation</li>
            <li>Shared database / data warehouse architecture</li>
        </ul>
    </section>
    '''


def _build_implications_section(findings: List[Finding], deal_type: str) -> str:
    """Build deal implications section."""

    # Categorize findings
    integration_findings = [f for f in findings if f.category == "integration"]
    cost_findings = [f for f in findings if f.category == "cost"]
    risk_findings = [f for f in findings if f.category == "risk"]

    implications = []

    if deal_type == "carve-out":
        implications.append('''
            <div class="action-item">
                <div class="action-number">!</div>
                <div class="action-content">
                    <h4>TSA Dependency</h4>
                    <p>Carve-outs typically require 12-24 month TSAs for shared systems. Each undocumented integration extends this timeline.</p>
                </div>
            </div>
        ''')

    if integration_findings:
        implications.append(f'''
            <div class="action-item">
                <div class="action-number">!</div>
                <div class="action-content">
                    <h4>Integration Complexity</h4>
                    <p>{len(integration_findings)} findings relate to system integration. Budget for integration discovery before Day 1 planning.</p>
                </div>
            </div>
        ''')

    if cost_findings:
        implications.append(f'''
            <div class="action-item">
                <div class="action-number">$</div>
                <div class="action-content">
                    <h4>Cost Implications</h4>
                    <p>{len(cost_findings)} findings have direct cost impact. Factor into deal model.</p>
                </div>
            </div>
        ''')

    if not implications:
        implications.append('''
            <div class="action-item">
                <div class="action-number">i</div>
                <div class="action-content">
                    <h4>Standard Due Diligence</h4>
                    <p>No unusual implications identified. Proceed with standard integration planning.</p>
                </div>
            </div>
        ''')

    return f'''
    <section id="implications">
        <h2>💼 Deal Implications</h2>
        {''.join(implications)}
    </section>
    '''


def _build_actions_section(findings: List[Finding]) -> str:
    """Build recommended actions section."""

    # Extract recommendations from findings
    actions = []
    for i, finding in enumerate(findings, 1):
        if finding.recommendation:
            actions.append((finding.severity, finding.recommendation))

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    actions.sort(key=lambda x: severity_order.get(x[0], 4))

    if not actions:
        actions = [
            ('high', 'Request system integration documentation from VDR'),
            ('medium', 'Schedule technical deep-dive with target IT leadership'),
            ('medium', 'Validate application inventory against actual environment'),
        ]

    actions_html = []
    for i, (severity, action) in enumerate(actions[:7], 1):  # Limit to 7
        actions_html.append(f'''
            <div class="action-item">
                <div class="action-number">{i}</div>
                <div class="action-content">
                    <h4>{action}</h4>
                    <p>Priority: {severity.title()}</p>
                </div>
            </div>
        ''')

    return f'''
    <section id="actions">
        <h2>✅ Recommended Actions</h2>
        {''.join(actions_html)}
    </section>
    '''


def _build_appendix(inventory_store: InventoryStore, entity: str) -> str:
    """Build appendix with supporting inventory data."""

    apps = inventory_store.get_items(inventory_type="application", entity=entity, status="active")

    if not apps:
        return '''
        <section id="appendix" class="appendix">
            <h2>📎 Appendix: Supporting Inventory</h2>
            <p>No inventory data available.</p>
        </section>
        '''

    rows = []
    for app in sorted(apps, key=lambda x: (x.cost or 0), reverse=True)[:20]:  # Top 20 by cost
        cost_str = f"${app.cost:,.0f}" if app.cost else "—"
        rows.append(f'''
            <tr>
                <td><code>{app.item_id}</code></td>
                <td>{app.name}</td>
                <td>{app.data.get('vendor', '—')}</td>
                <td style="text-align: right;">{cost_str}</td>
                <td>{app.data.get('criticality', '—')}</td>
            </tr>
        ''')

    return f'''
    <section id="appendix" class="appendix">
        <h2>📎 Appendix: Supporting Inventory</h2>
        <p style="color: var(--muted); margin-bottom: 1rem;">Top {len(rows)} applications by cost. Full inventory available in separate export.</p>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Application</th>
                    <th>Vendor</th>
                    <th style="text-align: right;">Annual Cost</th>
                    <th>Criticality</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </section>
    '''


# Convenience function to generate findings from inventory analysis
def analyze_inventory_for_findings(
    inventory_store: InventoryStore,
    entity: str = "target",
) -> List[Finding]:
    """
    Analyze inventory and generate key findings.

    This is a rule-based analysis that identifies common patterns.
    For deeper analysis, use the LLM reasoning agents.
    """
    findings = []

    apps = inventory_store.get_items(inventory_type="application", entity=entity, status="active")

    if not apps:
        return findings

    # Finding: Cost concentration
    total_cost = sum(app.cost or 0 for app in apps)
    if total_cost > 0:
        sorted_by_cost = sorted(apps, key=lambda x: x.cost or 0, reverse=True)
        top_3_cost = sum(app.cost or 0 for app in sorted_by_cost[:3])
        if top_3_cost / total_cost > 0.5:
            findings.append(Finding(
                title="High Cost Concentration in Top Applications",
                so_what=f"Top 3 applications represent {top_3_cost/total_cost:.0%} of total IT spend (${top_3_cost:,.0f}). Contract renegotiation or migration of any of these creates significant budget impact.",
                evidence=[app.item_id for app in sorted_by_cost[:3]],
                severity="high",
                category="cost",
                recommendation="Review contract terms and renewal dates for top-cost applications before close.",
            ))

    # Finding: Critical apps without documented vendor
    critical_apps = [a for a in apps if a.criticality and 'critical' in str(a.criticality).lower()]
    critical_no_vendor = [a for a in critical_apps if not a.data.get('vendor')]
    if critical_no_vendor:
        findings.append(Finding(
            title=f"{len(critical_no_vendor)} Critical Applications Without Vendor Documentation",
            so_what="Critical applications without documented vendors may be custom-built or have unclear support arrangements. This creates Day 1 continuity risk.",
            evidence=[app.item_id for app in critical_no_vendor],
            severity="critical",
            category="risk",
            recommendation="Identify vendor/support arrangements for all critical applications.",
        ))

    # Finding: Flagged items needing investigation
    flagged = [a for a in apps if a.needs_investigation]
    if flagged:
        findings.append(Finding(
            title=f"{len(flagged)} Applications Could Not Be Identified",
            so_what="These applications are not recognized and may be custom, legacy, or incorrectly named. Each represents unknown integration and support risk.",
            evidence=[app.item_id for app in flagged],
            severity="medium",
            category="risk",
            recommendation="Request documentation or conduct interviews to identify unknown applications.",
        ))

    # Finding: No infrastructure data
    infra = inventory_store.get_items(inventory_type="infrastructure", entity=entity, status="active")
    if not infra and apps:
        findings.append(Finding(
            title="No Infrastructure Inventory Provided",
            so_what="Application inventory exists but infrastructure (servers, databases, network) is not documented. Cannot assess hosting costs, migration complexity, or technical debt.",
            evidence=[],
            severity="high",
            category="integration",
            recommendation="Request infrastructure inventory including servers, databases, and network topology.",
        ))

    return findings
