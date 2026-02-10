"""
HTML Report Generator for IT Due Diligence Agent.

Generates static HTML reports that can be opened in any browser.

COST CALCULATION:
- Uses the consistency_engine for deterministic cost calculations
- Base costs are mid-market benchmarks (250-500 employees)
- Adjusted by company profile: size × industry × geography × IT maturity
- AI's cost_estimate field is shown for reference but NOT used for totals
"""

from pathlib import Path
from typing import List
from datetime import datetime
from stores.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore
from tools_v2.reasoning_tools import COST_RANGE_VALUES
from tools_v2.consistency_engine import (
    calculate_total_costs,
    CompanyProfile,
    categorize_work_item
)
from tools_v2.cost_database import get_database_stats

# Report version for tracking
REPORT_VERSION = "2.1.0"
METHODOLOGY_VERSION = "January 2026"


def generate_html_report(
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    output_dir: Path,
    timestamp: str = None,
    target_name: str = None,
    company_profile: CompanyProfile = None
) -> Path:
    """
    Generate a complete HTML report.

    Args:
        fact_store: FactStore with extracted facts
        reasoning_store: ReasoningStore with risks, gaps, work items
        output_dir: Directory to save the report
        timestamp: Optional timestamp for filename
        target_name: Name of the target company
        company_profile: Optional CompanyProfile for cost adjustments

    Returns:
        Path to the generated HTML file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = output_dir / f"it_dd_report_{timestamp}.html"

    html = _build_html(fact_store, reasoning_store, timestamp, target_name, company_profile)
    output_file.write_text(html)

    return output_file


def _severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        'critical': '#dc2626',
        'high': '#ea580c',
        'medium': '#ca8a04',
        'low': '#16a34a'
    }
    return colors.get(severity, '#6b7280')


def _phase_color(phase: str) -> str:
    """Get color for phase."""
    colors = {
        'Day_1': '#1e40af',
        'Day_100': '#92400e',
        'Post_100': '#3730a3'
    }
    return colors.get(phase, '#6b7280')


def _build_html(
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    timestamp: str,
    target_name: str = None,
    company_profile: CompanyProfile = None
) -> str:
    """Build the complete HTML document."""

    # Use target name or default
    company_name = target_name or "Target Company"

    # Use default mid-market profile if none provided
    if company_profile is None:
        company_profile = CompanyProfile()

    # Calculate summary stats
    total_facts = len(fact_store.facts)
    total_gaps = len(fact_store.gaps)
    total_risks = len(reasoning_store.risks)
    total_work_items = len(reasoning_store.work_items)

    # ==========================================================================
    # DETERMINISTIC COST CALCULATION (via consistency_engine)
    # ==========================================================================
    # Convert work items to dict format for consistency engine
    work_items_for_calc = [
        {
            "title": wi.title,
            "description": wi.description,
            "phase": wi.phase
        }
        for wi in reasoning_store.work_items
    ]

    # Calculate costs using consistency engine (deterministic)
    cost_result = calculate_total_costs(work_items_for_calc, company_profile)
    cost_by_phase = cost_result["by_phase"]
    total_low = cost_result["total"]["low"]
    total_high = cost_result["total"]["high"]
    _ = cost_result.get("methodology", {})
    cost_multiplier = cost_result.get("multiplier_applied", 1.0)

    # Get company profile breakdown for display
    profile_mult, profile_breakdown = company_profile.get_total_multiplier()

    # Get database stats for methodology disclosure
    db_stats = get_database_stats()

    # Count risks by severity
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for risk in reasoning_store.risks:
        if risk.severity in severity_counts:
            severity_counts[risk.severity] += 1

    # Build risks HTML
    risks_html = _build_risks_section(reasoning_store.risks, fact_store)

    # Build work items HTML (with deterministic cost calculations)
    work_items_html = _build_work_items_section(
        reasoning_store.work_items, reasoning_store.risks, fact_store, company_profile
    )

    # Build facts HTML
    facts_html = _build_facts_section(fact_store.facts)

    # Build gaps HTML
    gaps_html = _build_gaps_section(fact_store.gaps)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Due Diligence Report - {company_name}</title>
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

        .subtitle {{
            color: var(--text-muted);
            margin-bottom: 2rem;
        }}

        .nav {{
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            position: sticky;
            top: 1rem;
            z-index: 100;
        }}

        .nav a {{
            color: var(--primary);
            text-decoration: none;
            margin-right: 1.5rem;
            font-weight: 500;
        }}

        .nav a:hover {{
            text-decoration: underline;
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

        section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border);
        }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }}

        .item {{
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        .item-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }}

        .item-id {{
            font-weight: 700;
            color: var(--primary);
        }}

        .item-title {{
            font-weight: 600;
        }}

        .item-meta {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}

        .item-description {{
            margin-bottom: 0.75rem;
        }}

        .item-details {{
            background: var(--bg);
            padding: 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
        }}

        .item-details dt {{
            font-weight: 600;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}

        .item-details dd {{
            margin-left: 0;
        }}

        .related {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}

        .related-title {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .related-link {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: var(--bg);
            border-radius: 4px;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            text-decoration: none;
            color: var(--primary);
            font-size: 0.85rem;
        }}

        .related-link:hover {{
            background: var(--border);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            font-weight: 600;
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
        }}

        .cost {{
            font-family: monospace;
        }}

        .domain-section {{
            margin-bottom: 1.5rem;
        }}

        .domain-section h3 {{
            font-size: 1.1rem;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
            text-transform: uppercase;
        }}

        /* Filter controls */
        .filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--bg);
            border-radius: 8px;
        }}

        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .filter-group label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .filter-select {{
            padding: 0.4rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: white;
            font-size: 0.85rem;
            cursor: pointer;
        }}

        .filter-select:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .filter-count {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-left: auto;
        }}

        .item.hidden {{
            display: none;
        }}

        .no-results {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-style: italic;
        }}

        .clear-filters {{
            background: none;
            border: 1px solid var(--border);
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            cursor: pointer;
            color: var(--text-muted);
        }}

        .clear-filters:hover {{
            background: var(--border);
        }}

        @media print {{
            .nav, .filters {{
                display: none;
            }}
            body {{
                padding: 0;
            }}
            section {{
                break-inside: avoid;
            }}
            .item.hidden {{
                display: block;
            }}
        }}

        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .filters {{
                flex-direction: column;
            }}
        }}

        /* Chart styles */
        .chart-container {{
            margin: 1.5rem 0;
            padding: 1rem;
            background: var(--bg);
            border-radius: 8px;
        }}

        .bar-chart {{
            display: flex;
            align-items: flex-end;
            justify-content: space-around;
            height: 200px;
            padding: 1rem;
            gap: 2rem;
        }}

        .bar-group {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
        }}

        .bar {{
            width: 60px;
            background: linear-gradient(180deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 4px 4px 0 0;
            position: relative;
            transition: all 0.3s ease;
        }}

        .bar:hover {{
            transform: scaleY(1.02);
        }}

        .bar-label {{
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .bar-value {{
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.75rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        /* Mermaid diagram styles */
        .mermaid {{
            display: flex;
            justify-content: center;
            margin: 1rem 0;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{ useMaxWidth: true }}
        }});
    </script>
</head>
<body>
    <div class="container">
        <h1>IT Due Diligence Report</h1>
        <p class="subtitle"><strong>{company_name}</strong> &nbsp;|&nbsp; Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")} &nbsp;|&nbsp; Report v{REPORT_VERSION}</p>

        <nav class="nav">
            <a href="#summary">Summary</a>
            <a href="#risks">Risks ({total_risks})</a>
            <a href="#work-items">Work Items ({total_work_items})</a>
            <a href="#facts">Facts ({total_facts})</a>
            <a href="#gaps">Gaps ({total_gaps})</a>
        </nav>

        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; font-size: 0.85rem;">
            <div style="display: flex; align-items: start; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">📊</span>
                <div>
                    <strong style="color: #92400e;">About This Report</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #78350f;">
                        Cost estimates are calculated using a <strong>deterministic methodology</strong> based on {db_stats['total_activities']} researched IT integration activities.
                        The same inputs will always produce the same outputs. All estimates can be traced back to industry benchmarks and adjusted by company profile factors.
                        <a href="#summary" style="color: #92400e;">See methodology details below.</a>
                    </p>
                </div>
            </div>
        </div>

        <section id="summary">
            <h2>Executive Summary</h2>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_facts}</div>
                    <div class="stat-label">Facts Discovered</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_gaps}</div>
                    <div class="stat-label">Information Gaps</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_risks}</div>
                    <div class="stat-label">Risks Identified</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_work_items}</div>
                    <div class="stat-label">Work Items</div>
                </div>
            </div>

            <h3 style="margin: 1.5rem 0 1rem;">Risk Distribution</h3>
            <table>
                <tr>
                    <th>Severity</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td><span class="badge" style="background: var(--critical);">Critical</span></td>
                    <td>{severity_counts['critical']}</td>
                </tr>
                <tr>
                    <td><span class="badge" style="background: var(--high);">High</span></td>
                    <td>{severity_counts['high']}</td>
                </tr>
                <tr>
                    <td><span class="badge" style="background: var(--medium);">Medium</span></td>
                    <td>{severity_counts['medium']}</td>
                </tr>
                <tr>
                    <td><span class="badge" style="background: var(--low);">Low</span></td>
                    <td>{severity_counts['low']}</td>
                </tr>
            </table>

            <h3 style="margin: 1.5rem 0 1rem;">Cost Estimates by Phase</h3>

            <!-- Visual Cost Chart -->
            <div class="chart-container">
                <div class="bar-chart">
                    <div class="bar-group">
                        <div class="bar" style="height: {min(150, max(20, cost_by_phase['Day_1']['high'] / max(total_high, 1) * 150))}px;">
                            <span class="bar-value">${cost_by_phase['Day_1']['high']/1000:.0f}K</span>
                        </div>
                        <span class="bar-label">Day 1</span>
                    </div>
                    <div class="bar-group">
                        <div class="bar" style="height: {min(150, max(20, cost_by_phase['Day_100']['high'] / max(total_high, 1) * 150))}px;">
                            <span class="bar-value">${cost_by_phase['Day_100']['high']/1000:.0f}K</span>
                        </div>
                        <span class="bar-label">Day 100</span>
                    </div>
                    <div class="bar-group">
                        <div class="bar" style="height: {min(150, max(20, cost_by_phase['Post_100']['high'] / max(total_high, 1) * 150))}px;">
                            <span class="bar-value">${cost_by_phase['Post_100']['high']/1000:.0f}K</span>
                        </div>
                        <span class="bar-label">Post 100</span>
                    </div>
                </div>
            </div>

            <table>
                <tr>
                    <th>Phase</th>
                    <th>Items</th>
                    <th>Cost Range</th>
                </tr>
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
                <tr style="font-weight: 700;">
                    <td>Total</td>
                    <td>{total_work_items}</td>
                    <td class="cost">${total_low:,.0f} - ${total_high:,.0f}</td>
                </tr>
            </table>

            <div style="margin-top: 1.5rem; padding: 1.25rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #7dd3fc; border-radius: 8px; font-size: 0.875rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                    <strong style="color: #0369a1;">Cost Methodology</strong>
                    <span style="font-size: 0.75rem; color: #0369a1; background: white; padding: 2px 8px; border-radius: 4px;">Database: {db_stats['total_activities']} activities | {db_stats['last_updated']}</span>
                </div>

                <div style="margin-bottom: 1rem;">
                    <strong>Formula:</strong> <code style="background: white; padding: 2px 6px; border-radius: 3px;">Base Cost × Size × Industry × Geography × IT Maturity</code>
                </div>

                <table style="width: 100%; font-size: 0.8rem; margin-bottom: 1rem;">
                    <tr style="background: rgba(255,255,255,0.5);">
                        <th style="text-align: left; padding: 6px;">Factor</th>
                        <th style="text-align: left; padding: 6px;">Value</th>
                        <th style="text-align: right; padding: 6px;">Multiplier</th>
                    </tr>
                    <tr>
                        <td style="padding: 6px;">Company Size</td>
                        <td style="padding: 6px;">{company_profile.employee_count:,} employees</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">{profile_breakdown['size']['multiplier']}x</td>
                    </tr>
                    <tr style="background: rgba(255,255,255,0.3);">
                        <td style="padding: 6px;">Industry</td>
                        <td style="padding: 6px;">{company_profile.industry.replace('_', ' ').title()}</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">{profile_breakdown['industry']['multiplier']}x</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px;">Geography</td>
                        <td style="padding: 6px;">{company_profile.geography.replace('_', ' ').title()}</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">{profile_breakdown['geography']['multiplier']}x</td>
                    </tr>
                    <tr style="background: rgba(255,255,255,0.3);">
                        <td style="padding: 6px;">IT Maturity</td>
                        <td style="padding: 6px;">{company_profile.it_maturity.replace('_', ' ').title()}</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">{profile_breakdown['it_maturity']['multiplier']}x</td>
                    </tr>
                    <tr style="background: #0369a1; color: white;">
                        <td colspan="2" style="padding: 6px; font-weight: 600;">Total Adjustment</td>
                        <td style="text-align: right; padding: 6px; font-weight: 700;">{cost_multiplier}x</td>
                    </tr>
                </table>

                <div style="font-size: 0.75rem; color: #475569; border-top: 1px solid #7dd3fc; padding-top: 0.75rem;">
                    <strong>Sources:</strong> Vendor pricing guides, Gartner/Forrester research, M&A integration benchmarks, implementation partner data.<br>
                    <strong>Note:</strong> These are planning estimates. Actual costs vary by vendor, scope, and deal-specific factors. Validate against your deal context.
                </div>
            </div>
        </section>

        {risks_html}

        {work_items_html}

        {facts_html}

        {gaps_html}

    </div>

    <script>
    // Filtering functionality
    function initFilters(sectionId) {{
        const section = document.getElementById(sectionId);
        if (!section) return;

        const filters = section.querySelectorAll('.filter-select');
        const items = section.querySelectorAll('.item[data-domain]');
        const countEl = section.querySelector('.filter-count');

        function applyFilters() {{
            const filterValues = {{}};
            filters.forEach(f => {{
                filterValues[f.dataset.filter] = f.value;
            }});

            let visible = 0;
            items.forEach(item => {{
                let show = true;
                for (const [key, val] of Object.entries(filterValues)) {{
                    if (val && item.dataset[key] !== val) {{
                        show = false;
                        break;
                    }}
                }}
                item.classList.toggle('hidden', !show);
                if (show) visible++;
            }});

            if (countEl) {{
                countEl.textContent = `Showing ${{visible}} of ${{items.length}}`;
            }}

            // Show/hide domain sections based on visible items
            section.querySelectorAll('.domain-section').forEach(ds => {{
                const hasVisible = ds.querySelector('.item:not(.hidden)');
                ds.style.display = hasVisible ? 'block' : 'none';
            }});
        }}

        filters.forEach(f => f.addEventListener('change', applyFilters));

        // Clear filters button
        const clearBtn = section.querySelector('.clear-filters');
        if (clearBtn) {{
            clearBtn.addEventListener('click', () => {{
                filters.forEach(f => f.value = '');
                applyFilters();
            }});
        }}
    }}

    // Initialize all sections
    document.addEventListener('DOMContentLoaded', () => {{
        initFilters('risks');
        initFilters('work-items');
        initFilters('facts');
        initFilters('gaps');
    }});
    </script>
</body>
</html>'''


def _build_risks_section(risks: List, fact_store: FactStore) -> str:
    """Build the risks section HTML."""
    if not risks:
        return '<section id="risks"><h2>Risks</h2><p>No risks identified.</p></section>'

    # Collect unique values for filters
    domains = sorted(set(r.domain for r in risks))
    severities = ['critical', 'high', 'medium', 'low']
    categories = sorted(set(r.category for r in risks))

    # Build filter dropdowns
    domain_options = '<option value="">All Domains</option>' + ''.join(
        f'<option value="{d}">{d.replace("_", " ").title()}</option>' for d in domains)
    severity_options = '<option value="">All Severities</option>' + ''.join(
        f'<option value="{s}">{s.title()}</option>' for s in severities)
    category_options = '<option value="">All Categories</option>' + ''.join(
        f'<option value="{c}">{c.replace("_", " ").title()}</option>' for c in categories)

    filters_html = f'''
        <div class="filters">
            <div class="filter-group">
                <label>Domain:</label>
                <select class="filter-select" data-filter="domain">{domain_options}</select>
            </div>
            <div class="filter-group">
                <label>Severity:</label>
                <select class="filter-select" data-filter="severity">{severity_options}</select>
            </div>
            <div class="filter-group">
                <label>Category:</label>
                <select class="filter-select" data-filter="category">{category_options}</select>
            </div>
            <button class="clear-filters">Clear Filters</button>
            <span class="filter-count">Showing {len(risks)} of {len(risks)}</span>
        </div>'''

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    sorted_risks = sorted(risks, key=lambda r: severity_order.get(r.severity, 4))

    items_html = []
    for risk in sorted_risks:
        # Get related facts
        related_facts = ""
        if risk.based_on_facts:
            fact_links = [f'<a href="#fact-{fid}" class="related-link">{fid}</a>'
                         for fid in risk.based_on_facts]
            related_facts = f'''
            <div class="related">
                <div class="related-title">Based on Facts:</div>
                {" ".join(fact_links)}
            </div>'''

        # Add data attributes for filtering
        items_html.append(f'''
        <div class="item" id="risk-{risk.finding_id}"
             data-domain="{risk.domain}"
             data-severity="{risk.severity}"
             data-category="{risk.category}">
            <div class="item-header">
                <span class="badge" style="background: {_severity_color(risk.severity)};">{risk.severity}</span>
                <span class="item-id">{risk.finding_id}</span>
                <span class="item-title">{risk.title}</span>
            </div>
            <div class="item-meta">Domain: {risk.domain.replace("_", " ").title()} | Category: {risk.category.replace("_", " ").title()}</div>
            <div class="item-description">{risk.description}</div>
            <div class="item-details">
                <dl>
                    <dt>Reasoning</dt>
                    <dd>{risk.reasoning}</dd>
                    <dt>Mitigation</dt>
                    <dd>{risk.mitigation}</dd>
                    <dt>Integration Dependent</dt>
                    <dd>{'Yes' if risk.integration_dependent else 'No'}</dd>
                </dl>
            </div>
            {related_facts}
        </div>''')

    return f'''
    <section id="risks">
        <h2>Risks ({len(risks)})</h2>
        {filters_html}
        {"".join(items_html)}
    </section>'''


def _build_work_items_section(
    work_items: List,
    risks: List,
    fact_store: FactStore,
    company_profile: CompanyProfile = None
) -> str:
    """Build the work items section HTML with deterministic cost calculations."""
    if not work_items:
        return '<section id="work-items"><h2>Work Items</h2><p>No work items.</p></section>'

    # Use default profile if none provided
    if company_profile is None:
        company_profile = CompanyProfile()

    # Collect unique values for filters
    domains = sorted(set(wi.domain for wi in work_items))
    phases = ['Day_1', 'Day_100', 'Post_100']
    owners = sorted(set(wi.owner_type for wi in work_items))
    _ = sorted(set(wi.cost_estimate for wi in work_items))

    # Build filter dropdowns
    domain_options = '<option value="">All Domains</option>' + ''.join(
        f'<option value="{d}">{d.replace("_", " ").title()}</option>' for d in domains)
    phase_options = '<option value="">All Phases</option>' + ''.join(
        f'<option value="{p}">{p.replace("_", " ")}</option>' for p in phases)
    owner_options = '<option value="">All Owners</option>' + ''.join(
        f'<option value="{o}">{o.title()}</option>' for o in owners)

    filters_html = f'''
        <div class="filters">
            <div class="filter-group">
                <label>Domain:</label>
                <select class="filter-select" data-filter="domain">{domain_options}</select>
            </div>
            <div class="filter-group">
                <label>Phase:</label>
                <select class="filter-select" data-filter="phase">{phase_options}</select>
            </div>
            <div class="filter-group">
                <label>Owner:</label>
                <select class="filter-select" data-filter="owner">{owner_options}</select>
            </div>
            <button class="clear-filters">Clear Filters</button>
            <span class="filter-count">Showing {len(work_items)} of {len(work_items)}</span>
        </div>'''

    # Build all items (not grouped by phase for filtering to work)
    items_html = []
    for wi in work_items:
        # AI's vague estimate (for reference)
        ai_cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {'low': 0, 'high': 0})

        # Deterministic calculation (used for totals)
        from tools_v2.consistency_engine import calculate_work_item_cost
        det_low, det_high = calculate_work_item_cost(
            wi.title, wi.description, wi.phase, company_profile
        )
        category = categorize_work_item(wi.title, wi.description)

        # Related facts
        related_facts = ""
        if wi.triggered_by:
            fact_links = [f'<a href="#fact-{fid}" class="related-link">{fid}</a>'
                         for fid in wi.triggered_by]
            related_facts = f'''
            <div class="related-title">Triggered by Facts:</div>
            {" ".join(fact_links)}'''

        # Related risks
        related_risks = ""
        if wi.triggered_by_risks:
            risk_links = [f'<a href="#risk-{rid}" class="related-link">{rid}</a>'
                         for rid in wi.triggered_by_risks]
            related_risks = f'''
            <div class="related-title">Triggered by Risks:</div>
            {" ".join(risk_links)}'''

        related_section = ""
        if related_facts or related_risks:
            related_section = f'''
            <div class="related">
                {related_facts}
                {related_risks}
            </div>'''

        # Build cost buildup detail section if available
        cost_buildup_html = ""
        if hasattr(wi, 'cost_buildup') and wi.cost_buildup:
            cb = wi.cost_buildup
            assumptions_text = "; ".join(cb.assumptions) if cb.assumptions else "None stated"
            cost_buildup_html = f'''
                    <dt>Cost Buildup (Anchor-Based)</dt>
                    <dd>
                        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 0.75rem; margin: 0.25rem 0;">
                            <strong>Basis:</strong> {cb.anchor_name} (<code>{cb.anchor_key}</code>)<br>
                            <strong>Method:</strong> {cb.estimation_method} &times; {cb.quantity} {cb.unit_label}<br>
                            <strong>Unit Range:</strong> ${cb.unit_cost_low:,.0f} - ${cb.unit_cost_high:,.0f} per {cb.unit_label}<br>
                            <strong>Total:</strong> <span style="font-weight: 700; color: #166534;">${cb.total_low:,.0f} - ${cb.total_high:,.0f}</span><br>
                            <strong>Confidence:</strong> {cb.confidence} ({cb.estimation_source})<br>
                            <strong>Assumptions:</strong> {assumptions_text}
                        </div>
                    </dd>'''

        items_html.append(f'''
        <div class="item" id="wi-{wi.finding_id}"
             data-domain="{wi.domain}"
             data-phase="{wi.phase}"
             data-owner="{wi.owner_type}">
            <div class="item-header">
                <span class="badge" style="background: {_phase_color(wi.phase)};">{wi.phase.replace('_', ' ')}</span>
                <span class="item-id">{wi.finding_id}</span>
                <span class="item-title">{wi.title}</span>
            </div>
            <div class="item-meta">Domain: {wi.domain.replace("_", " ").title()} | Owner: {wi.owner_type.title()} | Priority: {wi.priority}</div>
            <div class="item-description">{wi.description}</div>
            <div class="item-details">
                <dl>
                    <dt>Cost Estimate (Calculated)</dt>
                    <dd class="cost"><strong>${det_low:,.0f} - ${det_high:,.0f}</strong> <span style="font-size: 0.8em; color: #666;">({category})</span></dd>
                    <dt>AI Initial Estimate</dt>
                    <dd style="color: #888; font-size: 0.9em;">{wi.cost_estimate.replace("_", " ")} (${ai_cost_range['low']:,.0f} - ${ai_cost_range['high']:,.0f})</dd>
                    {cost_buildup_html}
                    <dt>Reasoning</dt>
                    <dd>{wi.reasoning}</dd>
                </dl>
            </div>
            {related_section}
        </div>''')

    return f'''
    <section id="work-items">
        <h2>Work Items ({len(work_items)})</h2>
        {filters_html}
        {"".join(items_html)}
    </section>'''


def _synthesize_fact_statement(fact) -> str:
    """
    Generate a human-readable sentence from fact components.

    Examples:
    - "Primary Data Center in Dallas (Colocation, Tier 3) with 24 racks capacity, costing $992,625/year"
    - "Uses Microsoft Entra ID for identity management, serving 4,296 users"
    - "AWS cloud infrastructure in us-east-1 with 25 accounts, spending $1.48M annually"
    """
    item = fact.item
    details = fact.details or {}
    category = fact.category
    _ = fact.domain

    # Helper to format currency
    def format_currency(val):
        if isinstance(val, str):
            # Already formatted like "$992,625"
            if val.startswith('$'):
                return val
            # Try to parse
            try:
                val = float(val.replace(',', '').replace('$', ''))
            except (ValueError, AttributeError):
                return val
        if isinstance(val, (int, float)):
            if val >= 1_000_000:
                return f"${val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"${val/1_000:.0f}K"
            else:
                return f"${val:,.0f}"
        return str(val)

    # Build the statement based on category/domain patterns
    parts = []

    # === INFRASTRUCTURE / HOSTING ===
    if category in ('hosting', 'datacenter', 'data_center'):
        # "Primary Data Center in Dallas (Colocation, Tier 3) with 24 racks, $992K/year"
        dc_type = details.get('type', '')
        tier = details.get('tier', '')
        capacity = details.get('capacity', '')
        cost = details.get('annual_cost', '')

        qualifiers = [q for q in [dc_type, tier] if q]
        if qualifiers:
            parts.append(f"({', '.join(qualifiers)})")
        if capacity:
            parts.append(f"with {capacity} capacity")
        if cost:
            parts.append(f"costing {format_currency(cost)}/year")

    # === CLOUD ===
    elif category == 'cloud':
        region = details.get('region', '')
        accounts = details.get('accounts', '')
        spend = details.get('annual_spend', details.get('monthly_spend', ''))

        if region:
            parts.append(f"in {region}")
        if accounts:
            parts.append(f"with {accounts} accounts")
        if spend:
            # Parse the spend value and format nicely
            spend_val = spend
            if isinstance(spend, str):
                spend_val = float(spend.replace(',', '').replace('$', ''))
            spend_formatted = format_currency(spend_val)
            period = "annually" if 'annual_spend' in details else "monthly"
            parts.append(f"spending {spend_formatted} {period}")

    # === BACKUP/DR ===
    elif category in ('backup', 'backup_dr', 'disaster_recovery'):
        rpo = details.get('rpo', '')
        rto = details.get('rto', '')
        retention = details.get('backup_retention', '')
        tier = details.get('dr_tier', '')

        if tier:
            parts.append(f"({tier})")
        if rpo or rto:
            dr_metrics = []
            if rpo:
                dr_metrics.append(f"RPO: {rpo}")
            if rto:
                dr_metrics.append(f"RTO: {rto}")
            parts.append(f"with {', '.join(dr_metrics)}")
        if retention:
            parts.append(f"{retention} retention")

    # === NETWORK / FIREWALL ===
    elif category in ('firewall', 'network', 'wan', 'lan', 'vpn'):
        vendor = details.get('vendor', '')
        if vendor and vendor.lower() != 'not_stated':
            # Put vendor first if item doesn't already contain it
            if vendor.lower() not in item.lower():
                item = f"{vendor} {item}"

    # === IDENTITY / SSO / MFA ===
    elif category in ('identity', 'sso', 'mfa', 'pam', 'authentication', 'api_identity'):
        users = details.get('users', details.get('user_count', details.get('seats', '')))
        product = details.get('product', details.get('platform', ''))

        if product and product.lower() not in item.lower():
            item = f"{product}"
        if users:
            parts.append(f"serving {users:,} users" if isinstance(users, int) else f"serving {users} users")

    # === TOOLING / ITSM ===
    elif category == 'tooling':
        product = details.get('product', '')
        version = details.get('version', '')
        services = details.get('services', [])
        contract = details.get('annual_contract_value', '')

        if product and product.lower() not in item.lower():
            item = product
        if version:
            parts.append(f"({version})")
        if services:
            if isinstance(services, list):
                parts.append(f"providing {', '.join(services)}")
        if contract:
            parts.append(f"at {format_currency(contract)}/year")

    # === COMPUTE / VIRTUALIZATION ===
    elif category in ('compute', 'virtualization'):
        platform = details.get('platform', details.get('vendor', ''))
        version = details.get('version', '')
        vm_count = details.get('vm_count', '')

        if platform and platform.lower() not in item.lower():
            item = f"{platform} {item}"
        if version:
            parts.append(f"version {version}")
        if vm_count:
            parts.append(f"running {vm_count} VMs")

    # === ORGANIZATION / STAFFING ===
    elif category in ('staffing', 'team', 'teams', 'central_it', 'leadership', 'budget'):
        headcount = details.get('headcount', details.get('fte', ''))
        cost = details.get('annual_cost', details.get('budget', ''))
        outsourced = details.get('outsourced_percent', details.get('outsourced', ''))

        if headcount:
            parts.append(f"with {headcount} staff")
        if outsourced:
            parts.append(f"({outsourced}% outsourced)" if isinstance(outsourced, (int, float)) else f"({outsourced} outsourced)")
        if cost:
            parts.append(f"costing {format_currency(cost)}/year")

    # === APPLICATIONS ===
    elif category in ('application', 'applications', 'erp', 'crm', 'core_systems'):
        vendor = details.get('vendor', '')
        users = details.get('users', details.get('seats', ''))
        cost = details.get('annual_cost', '')

        if vendor and vendor.lower() not in item.lower():
            item = f"{vendor} {item}"
        if users:
            parts.append(f"with {users} users")
        if cost:
            parts.append(f"costing {format_currency(cost)}/year")

    # === GENERIC FALLBACK ===
    else:
        # Include any meaningful details
        for key in ['vendor', 'platform', 'product']:
            val = details.get(key, '')
            # Ensure val is a string before calling .lower()
            if isinstance(val, list):
                val = ', '.join(str(v) for v in val) if val else ''
            val = str(val) if val else ''
            if val and val.lower() not in item.lower() and val.lower() != 'not_stated':
                item = f"{val} {item}"
                break

        version = details.get('version', '')
        if isinstance(version, list):
            version = ', '.join(str(v) for v in version) if version else ''
        version = str(version) if version else ''
        if version and version.lower() not in ('evergreen', 'not_stated', 'n/a'):
            parts.append(f"version {version}")

        for key in ['users', 'headcount', 'capacity', 'accounts']:
            if key in details:
                parts.append(f"with {details[key]} {key}")
                break

        for key in ['annual_cost', 'monthly_cost', 'annual_spend']:
            if key in details:
                parts.append(f"at {format_currency(details[key])}/year")
                break

    # Construct final sentence
    if parts:
        statement = f"{item} {' '.join(parts)}"
    else:
        statement = item

    # Clean up any double spaces
    statement = ' '.join(statement.split())

    # Add status indicator for incomplete info
    if fact.status == 'partial':
        statement += " — incomplete documentation"

    return statement


def _build_facts_section(facts: List) -> str:
    """Build the facts section HTML."""
    if not facts:
        return '<section id="facts"><h2>Facts</h2><p>No facts discovered.</p></section>'

    # Collect unique values for filters
    domains = sorted(set(f.domain for f in facts))
    categories = sorted(set(f.category for f in facts))
    statuses = sorted(set(f.status for f in facts))

    # Build filter dropdowns
    domain_options = '<option value="">All Domains</option>' + ''.join(
        f'<option value="{d}">{d.replace("_", " ").title()}</option>' for d in domains)
    category_options = '<option value="">All Categories</option>' + ''.join(
        f'<option value="{c}">{c.replace("_", " ").title()}</option>' for c in categories)
    status_options = '<option value="">All Statuses</option>' + ''.join(
        f'<option value="{s}">{s.title()}</option>' for s in statuses)

    filters_html = f'''
        <div class="filters">
            <div class="filter-group">
                <label>Domain:</label>
                <select class="filter-select" data-filter="domain">{domain_options}</select>
            </div>
            <div class="filter-group">
                <label>Category:</label>
                <select class="filter-select" data-filter="category">{category_options}</select>
            </div>
            <div class="filter-group">
                <label>Status:</label>
                <select class="filter-select" data-filter="status">{status_options}</select>
            </div>
            <button class="clear-filters">Clear Filters</button>
            <span class="filter-count">Showing {len(facts)} of {len(facts)}</span>
        </div>'''

    # Build all items with data attributes for filtering
    items_html = []
    for fact in facts:
        # Synthesize a readable fact statement
        fact_statement = _synthesize_fact_statement(fact)

        # Build details as supplementary info
        details_html = ""
        if fact.details:
            details_items = [f"<dt>{k.replace('_', ' ').title()}</dt><dd>{v}</dd>"
                           for k, v in fact.details.items()]
            details_html = f"<dl>{''.join(details_items)}</dl>"

        evidence_html = ""
        if fact.evidence:
            evidence_html = f'''
            <dt>Source Evidence</dt>
            <dd>
                <em>"{fact.evidence.get('exact_quote', 'N/A')}"</em><br>
                <small>Source: {fact.evidence.get('source_section', 'N/A')}</small>
            </dd>'''

        items_html.append(f'''
        <div class="item" id="fact-{fact.fact_id}"
             data-domain="{fact.domain}"
             data-category="{fact.category}"
             data-status="{fact.status}">
            <div class="item-header">
                <span class="item-id">{fact.fact_id}</span>
                <span style="margin-left: auto; font-size: 0.8rem; color: var(--text-muted);">{fact.domain.replace("_", " ").title()}</span>
            </div>
            <div class="item-description" style="font-size: 1.1rem; margin-bottom: 0.75rem;">
                {fact_statement}
            </div>
            <div class="item-meta">Category: {fact.category.replace('_', ' ').title()} | Status: {fact.status}</div>
            <div class="item-details">
                {details_html}
                {evidence_html}
            </div>
        </div>''')

    return f'''
    <section id="facts">
        <h2>Facts ({len(facts)})</h2>
        {filters_html}
        {"".join(items_html)}
    </section>'''


def _build_gaps_section(gaps: List) -> str:
    """Build the gaps section HTML."""
    if not gaps:
        return '<section id="gaps"><h2>Information Gaps</h2><p>No gaps identified.</p></section>'

    # Collect unique values for filters
    domains = sorted(set(g.domain for g in gaps))
    categories = sorted(set(g.category for g in gaps))
    importances = ['critical', 'high', 'medium', 'low']

    # Build filter dropdowns
    domain_options = '<option value="">All Domains</option>' + ''.join(
        f'<option value="{d}">{d.replace("_", " ").title()}</option>' for d in domains)
    category_options = '<option value="">All Categories</option>' + ''.join(
        f'<option value="{c}">{c.replace("_", " ").title()}</option>' for c in categories)
    importance_options = '<option value="">All Importance</option>' + ''.join(
        f'<option value="{i}">{i.title()}</option>' for i in importances)

    filters_html = f'''
        <div class="filters">
            <div class="filter-group">
                <label>Domain:</label>
                <select class="filter-select" data-filter="domain">{domain_options}</select>
            </div>
            <div class="filter-group">
                <label>Category:</label>
                <select class="filter-select" data-filter="category">{category_options}</select>
            </div>
            <div class="filter-group">
                <label>Importance:</label>
                <select class="filter-select" data-filter="importance">{importance_options}</select>
            </div>
            <button class="clear-filters">Clear Filters</button>
            <span class="filter-count">Showing {len(gaps)} of {len(gaps)}</span>
        </div>'''

    # Build all items with data attributes for filtering
    items_html = []
    for gap in gaps:
        importance_color = _severity_color(gap.importance)  # Reuse severity colors
        items_html.append(f'''
        <div class="item" id="gap-{gap.gap_id}"
             data-domain="{gap.domain}"
             data-category="{gap.category}"
             data-importance="{gap.importance}">
            <div class="item-header">
                <span class="badge" style="background: {importance_color};">{gap.importance}</span>
                <span class="item-id">{gap.gap_id}</span>
                <span style="margin-left: auto; font-size: 0.8rem; color: var(--text-muted);">{gap.domain.replace("_", " ").title()}</span>
            </div>
            <div class="item-description">{gap.description}</div>
            <div class="item-meta">Category: {gap.category.replace("_", " ").title()}</div>
        </div>''')

    return f'''
    <section id="gaps">
        <h2>Information Gaps ({len(gaps)})</h2>
        {filters_html}
        {"".join(items_html)}
    </section>'''
