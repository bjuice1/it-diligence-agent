"""
Analysis Viewer Generator
Generates a self-contained HTML viewer with embedded analysis data.
Run after analysis completes to get a single HTML file with everything.

Updated for Four-Lens DD Framework:
- Executive Summary at top (IC-ready)
- Current State section (Lens 1) - "What you're buying"
- Strategic Considerations section (Lens 3) - Deal implications
- Risks with integration_dependent filtering
- Work Items with phase tagging
"""

import json
import webbrowser
from pathlib import Path
from datetime import datetime


def generate_viewer(output_dir: str = "data/output", auto_open: bool = True) -> str:
    """
    Generate an HTML viewer with embedded analysis data.

    Args:
        output_dir: Directory containing JSON output files
        auto_open: Whether to automatically open in browser

    Returns:
        Path to generated HTML file
    """

    output_path = Path(output_dir)

    # Load all JSON files
    data = {
        "current_state": [],
        "risks": [],
        "strategic_considerations": [],
        "gaps": [],
        "assumptions": [],
        "work_items": [],
        "recommendations": [],
        "domain_summaries": {},
        "executive_summary": None,
        "validation_report": {},
        "generated_at": datetime.now().isoformat()
    }

    file_mapping = {
        "current_state.json": "current_state",
        "risks.json": "risks",
        "strategic_considerations.json": "strategic_considerations",
        "gaps.json": "gaps",
        "assumptions.json": "assumptions",
        "work_items.json": "work_items",
        "recommendations.json": "recommendations",
        "domain_summaries.json": "domain_summaries",
        "executive_summary.json": "executive_summary",
        "validation_report.json": "validation_report"
    }

    for filename, key in file_mapping.items():
        filepath = output_path / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                data[key] = json.load(f)
                print(f"  ✓ Loaded {filename}")

    # Also check for combined analysis_output.json
    combined_path = output_path / "analysis_output.json"
    if combined_path.exists():
        with open(combined_path, 'r') as f:
            combined = json.load(f)
            for key in file_mapping.values():
                if key in combined and combined[key]:
                    data[key] = combined[key]
        print("  ✓ Loaded analysis_output.json")

    # Generate HTML with embedded data
    html = generate_html(data)

    # Write to file
    viewer_path = output_path / "analysis_report.html"
    with open(viewer_path, 'w') as f:
        f.write(html)

    print(f"\n{'='*60}")
    print("📊 ANALYSIS VIEWER READY")
    print("=" * 60)
    print(f"\n  File: {viewer_path.absolute()}")
    print(f"\n  Open in browser: file://{viewer_path.absolute()}")
    print(f"\n{'='*60}\n")

    if auto_open:
        webbrowser.open(f"file://{viewer_path.absolute()}")

    return str(viewer_path)


def generate_html(data: dict) -> str:
    """Generate the complete HTML with embedded data."""

    # Serialize data for embedding
    data_json = json.dumps(data, indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Due Diligence Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid #334155;
            padding: 20px 40px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header h1 {{ font-size: 24px; font-weight: 600; color: #f8fafc; }}

        .header-meta {{
            display: flex;
            gap: 24px;
            margin-top: 8px;
            font-size: 14px;
            color: #94a3b8;
        }}

        .container {{ display: flex; min-height: calc(100vh - 80px); }}

        .sidebar {{
            width: 260px;
            background: #1e293b;
            border-right: 1px solid #334155;
            padding: 20px 0;
            position: sticky;
            top: 80px;
            height: calc(100vh - 80px);
            overflow-y: auto;
        }}

        .nav-section {{ padding: 0 16px; margin-bottom: 24px; }}

        .nav-section-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 8px;
        }}

        .nav-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s;
            margin-bottom: 2px;
        }}

        .nav-item:hover {{ background: #334155; }}
        .nav-item.active {{ background: #3b82f6; color: white; }}

        .nav-item-label {{ display: flex; align-items: center; gap: 8px; font-size: 14px; }}

        .nav-item-count {{
            font-size: 12px;
            background: rgba(255,255,255,0.1);
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .nav-item.active .nav-item-count {{ background: rgba(255,255,255,0.2); }}

        .main {{ flex: 1; padding: 32px 40px; overflow-y: auto; }}

        .section {{ display: none; }}
        .section.active {{ display: block; }}

        .section-header {{ margin-bottom: 24px; }}
        .section-title {{ font-size: 20px; font-weight: 600; margin-bottom: 8px; }}
        .section-subtitle {{ color: #94a3b8; font-size: 14px; }}

        /* Executive Summary Banner */
        .exec-summary-banner {{
            background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}

        .exec-summary-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .exec-summary-title {{ font-size: 18px; font-weight: 600; color: #93c5fd; }}

        .deal-recommendation {{
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        }}

        .rec-proceed {{ background: #14532d; color: #bbf7d0; }}
        .rec-proceed_with_caution {{ background: #713f12; color: #fef08a; }}
        .rec-significant_concerns {{ background: #7c2d12; color: #fed7aa; }}
        .rec-reconsider {{ background: #7f1d1d; color: #fecaca; }}

        .exec-summary-metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}

        .exec-metric {{
            text-align: center;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }}

        .exec-metric-value {{ font-size: 24px; font-weight: 700; color: #f1f5f9; }}
        .exec-metric-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-top: 4px; }}

        .exec-findings {{ margin-top: 16px; }}
        .exec-findings h4 {{ font-size: 13px; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase; }}
        .exec-findings ul {{ list-style: none; }}
        .exec-findings li {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-size: 14px;
            color: #e2e8f0;
        }}
        .exec-findings li:last-child {{ border-bottom: none; }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}

        .summary-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
        }}

        .summary-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}

        .summary-card-title {{
            font-size: 14px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .complexity-badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .complexity-very_high {{ background: #7f1d1d; color: #fecaca; }}
        .complexity-high {{ background: #7c2d12; color: #fed7aa; }}
        .complexity-medium {{ background: #713f12; color: #fef08a; }}
        .complexity-low {{ background: #14532d; color: #bbf7d0; }}

        .summary-card-value {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
        .summary-card-meta {{ font-size: 13px; color: #64748b; }}

        /* Current State Grid */
        .current-state-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}

        .current-state-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
        }}

        .cs-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .cs-category {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .cs-maturity {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}

        .maturity-high {{ background: #14532d; color: #bbf7d0; }}
        .maturity-medium {{ background: #713f12; color: #fef08a; }}
        .maturity-low {{ background: #7f1d1d; color: #fecaca; }}

        .cs-summary {{ font-size: 14px; color: #e2e8f0; line-height: 1.6; margin-bottom: 12px; }}

        .cs-characteristics {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }}

        .cs-char-tag {{
            font-size: 11px;
            padding: 3px 8px;
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border-radius: 4px;
        }}

        .cs-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 12px;
            border-top: 1px solid #334155;
        }}

        .cs-viability {{
            font-size: 12px;
            padding: 3px 8px;
            border-radius: 4px;
        }}

        .viability-viable {{ background: #14532d; color: #bbf7d0; }}
        .viability-constrained {{ background: #713f12; color: #fef08a; }}
        .viability-high_risk {{ background: #7f1d1d; color: #fecaca; }}

        /* Strategic Considerations */
        .strategic-grid {{
            display: grid;
            gap: 16px;
        }}

        .strategic-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-left: 4px solid #3b82f6;
            border-radius: 0 10px 10px 0;
            padding: 20px;
        }}

        .strategic-card.misaligned {{ border-left-color: #dc2626; }}
        .strategic-card.partial {{ border-left-color: #f59e0b; }}
        .strategic-card.aligned {{ border-left-color: #22c55e; }}

        .sc-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}

        .sc-theme {{ font-size: 16px; font-weight: 600; color: #f1f5f9; }}
        .sc-id {{ font-size: 11px; color: #64748b; font-family: monospace; }}

        .sc-observation {{
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #334155;
        }}

        .sc-implication {{ font-size: 14px; color: #e2e8f0; line-height: 1.6; margin-bottom: 12px; }}

        .sc-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .sc-tag {{
            font-size: 11px;
            padding: 3px 8px;
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border-radius: 4px;
        }}

        .sc-tag.integration_risk {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}
        .sc-tag.value_leakage {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; }}
        .sc-tag.tsa_dependency {{ background: rgba(168, 85, 247, 0.2); color: #c4b5fd; }}
        .sc-tag.synergy_barrier {{ background: rgba(236, 72, 153, 0.2); color: #f9a8d4; }}

        .domain-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}

        .domain-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
        }}

        .domain-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .domain-name {{ font-size: 18px; font-weight: 600; text-transform: capitalize; }}

        .domain-stats {{
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid #334155;
        }}

        .domain-stat {{ text-align: center; }}
        .domain-stat-value {{ font-size: 20px; font-weight: 600; }}
        .domain-stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; }}

        .domain-summary {{ font-size: 14px; color: #cbd5e1; line-height: 1.6; }}

        .data-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}

        .data-table th {{
            text-align: left;
            padding: 12px 16px;
            background: #1e293b;
            border-bottom: 2px solid #334155;
            font-weight: 600;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            position: sticky;
            top: 0;
        }}

        .data-table td {{
            padding: 16px;
            border-bottom: 1px solid #334155;
            vertical-align: top;
        }}

        .data-table tr:hover {{ background: rgba(59, 130, 246, 0.05); }}

        .data-table .id-cell {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            color: #64748b;
            white-space: nowrap;
        }}

        .data-table .main-cell {{ max-width: 400px; }}
        .data-table .main-cell strong {{ display: block; margin-bottom: 4px; color: #f1f5f9; }}
        .data-table .main-cell p {{ color: #94a3b8; font-size: 13px; line-height: 1.5; }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-critical {{ background: #7f1d1d; color: #fecaca; }}
        .badge-high {{ background: #7c2d12; color: #fed7aa; }}
        .badge-medium {{ background: #713f12; color: #fef08a; }}
        .badge-low {{ background: #14532d; color: #bbf7d0; }}
        .badge-domain {{ background: #1e3a5f; color: #93c5fd; }}
        .badge-standalone {{ background: #581c87; color: #e9d5ff; }}
        .badge-integration {{ background: #164e63; color: #a5f3fc; }}

        .badge-Day_1 {{ background: #7f1d1d; color: #fecaca; }}
        .badge-Day_100 {{ background: #713f12; color: #fef08a; }}
        .badge-Post_100 {{ background: #14532d; color: #bbf7d0; }}
        .badge-Optional {{ background: #1e3a5f; color: #93c5fd; }}

        .filters {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .filter-group {{ display: flex; align-items: center; gap: 8px; }}
        .filter-label {{ font-size: 12px; color: #64748b; }}

        .filter-select {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #e2e8f0;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
        }}

        .card-grid {{ display: grid; gap: 16px; }}

        .item-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 20px;
            transition: border-color 0.15s;
        }}

        .item-card:hover {{ border-color: #3b82f6; }}

        .item-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}

        .item-card-id {{ font-family: 'SF Mono', Monaco, monospace; font-size: 11px; color: #64748b; }}
        .item-card-title {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; color: #f1f5f9; }}
        .item-card-description {{ font-size: 14px; color: #94a3b8; line-height: 1.6; margin-bottom: 16px; }}

        .item-card-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            padding-top: 16px;
            border-top: 1px solid #334155;
        }}

        .meta-item {{ font-size: 13px; }}
        .meta-item-label {{ color: #64748b; margin-right: 4px; }}
        .meta-item-value {{ color: #cbd5e1; font-weight: 500; }}

        .depends-on {{
            margin-top: 8px;
            font-size: 12px;
            color: #64748b;
        }}

        .depends-on span {{
            font-family: monospace;
            background: rgba(59, 130, 246, 0.2);
            padding: 2px 6px;
            border-radius: 3px;
            margin-left: 4px;
        }}

        .critical-risks {{
            margin-top: 32px;
        }}

        .critical-risks h3 {{
            font-size: 16px;
            margin-bottom: 16px;
            color: #f1f5f9;
        }}

        .risk-alert {{
            background: #1e293b;
            border-left: 3px solid #dc2626;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 0 8px 8px 0;
        }}

        .risk-alert.standalone {{ border-left-color: #9333ea; }}

        .risk-alert-title {{ font-weight: 600; margin-bottom: 4px; }}
        .risk-alert-mitigation {{ font-size: 13px; color: #94a3b8; }}
        .risk-alert-type {{ font-size: 11px; margin-top: 8px; }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; }}
        ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}

        @media print {{
            .sidebar {{ display: none; }}
            .main {{ padding: 20px; }}
            .section {{ display: block !important; page-break-after: always; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IT Due Diligence Analysis Report</h1>
        <div class="header-meta">
            <span id="generated-date"></span>
            <span id="finding-count"></span>
        </div>
    </div>

    <div class="container">
        <div class="sidebar">
            <div class="nav-section">
                <div class="nav-section-title">Overview</div>
                <div class="nav-item active" data-section="summary">
                    <span class="nav-item-label">Executive Summary</span>
                </div>
                <div class="nav-item" data-section="domains">
                    <span class="nav-item-label">Domain Analysis</span>
                </div>
            </div>

            <div class="nav-section">
                <div class="nav-section-title">Four Lenses</div>
                <div class="nav-item" data-section="current-state">
                    <span class="nav-item-label">Current State</span>
                    <span class="nav-item-count" id="current-state-count">0</span>
                </div>
                <div class="nav-item" data-section="risks">
                    <span class="nav-item-label">Risks</span>
                    <span class="nav-item-count" id="risks-count">0</span>
                </div>
                <div class="nav-item" data-section="strategic">
                    <span class="nav-item-label">Strategic</span>
                    <span class="nav-item-count" id="strategic-count">0</span>
                </div>
                <div class="nav-item" data-section="work-items">
                    <span class="nav-item-label">Work Items</span>
                    <span class="nav-item-count" id="work-items-count">0</span>
                </div>
            </div>

            <div class="nav-section">
                <div class="nav-section-title">Supporting</div>
                <div class="nav-item" data-section="gaps">
                    <span class="nav-item-label">Gaps</span>
                    <span class="nav-item-count" id="gaps-count">0</span>
                </div>
                <div class="nav-item" data-section="assumptions">
                    <span class="nav-item-label">Assumptions</span>
                    <span class="nav-item-count" id="assumptions-count">0</span>
                </div>
                <div class="nav-item" data-section="recommendations">
                    <span class="nav-item-label">Recommendations</span>
                    <span class="nav-item-count" id="recommendations-count">0</span>
                </div>
            </div>
        </div>

        <div class="main">
            <!-- Executive Summary Section -->
            <div class="section active" id="section-summary">
                <div class="section-header">
                    <h2 class="section-title">Executive Summary</h2>
                    <p class="section-subtitle">IC-ready overview of IT due diligence findings</p>
                </div>
                <div id="exec-summary-container"></div>
                <div class="summary-grid" id="summary-cards"></div>
                <div class="critical-risks" id="top-risks-summary"></div>
            </div>

            <!-- Domain Analysis Section -->
            <div class="section" id="section-domains">
                <div class="section-header">
                    <h2 class="section-title">Domain Analysis</h2>
                    <p class="section-subtitle">Detailed assessment by IT domain</p>
                </div>
                <div class="domain-grid" id="domain-cards"></div>
            </div>

            <!-- Current State Section (Lens 1) -->
            <div class="section" id="section-current-state">
                <div class="section-header">
                    <h2 class="section-title">Current State Assessment</h2>
                    <p class="section-subtitle">What you're buying - the IT environment as-is</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Domain:</span>
                        <select class="filter-select" id="cs-domain-filter">
                            <option value="all">All Domains</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <span class="filter-label">Maturity:</span>
                        <select class="filter-select" id="cs-maturity-filter">
                            <option value="all">All</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>
                    </div>
                </div>
                <div class="current-state-grid" id="current-state-grid"></div>
            </div>

            <!-- Risks Section (Lens 2) -->
            <div class="section" id="section-risks">
                <div class="section-header">
                    <h2 class="section-title">Risk Profile</h2>
                    <p class="section-subtitle">What could go wrong - including standalone risks</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Severity:</span>
                        <select class="filter-select" id="risk-severity-filter">
                            <option value="all">All</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <span class="filter-label">Type:</span>
                        <select class="filter-select" id="risk-type-filter">
                            <option value="all">All Types</option>
                            <option value="standalone">Standalone Only</option>
                            <option value="integration">Integration Only</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <span class="filter-label">Domain:</span>
                        <select class="filter-select" id="risk-domain-filter">
                            <option value="all">All Domains</option>
                        </select>
                    </div>
                </div>
                <table class="data-table" id="risks-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Risk</th>
                            <th>Type</th>
                            <th>Severity</th>
                            <th>Domain</th>
                            <th>Mitigation</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <!-- Strategic Considerations Section (Lens 3) -->
            <div class="section" id="section-strategic">
                <div class="section-header">
                    <h2 class="section-title">Strategic Considerations</h2>
                    <p class="section-subtitle">What this means for the deal</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Alignment:</span>
                        <select class="filter-select" id="sc-alignment-filter">
                            <option value="all">All</option>
                            <option value="misaligned">Misaligned</option>
                            <option value="partial">Partial</option>
                            <option value="aligned">Aligned</option>
                        </select>
                    </div>
                </div>
                <div class="strategic-grid" id="strategic-grid"></div>
            </div>

            <!-- Work Items Section (Lens 4) -->
            <div class="section" id="section-work-items">
                <div class="section-header">
                    <h2 class="section-title">Integration Roadmap</h2>
                    <p class="section-subtitle">Phased work items for integration</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Phase:</span>
                        <select class="filter-select" id="work-phase-filter">
                            <option value="all">All Phases</option>
                            <option value="Day_1">Day 1</option>
                            <option value="Day_100">Day 100</option>
                            <option value="Post_100">Post 100</option>
                            <option value="Optional">Optional</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <span class="filter-label">Domain:</span>
                        <select class="filter-select" id="work-domain-filter">
                            <option value="all">All Domains</option>
                        </select>
                    </div>
                </div>
                <div class="card-grid" id="work-items-grid"></div>
            </div>

            <!-- Gaps Section -->
            <div class="section" id="section-gaps">
                <div class="section-header">
                    <h2 class="section-title">Knowledge Gaps</h2>
                    <p class="section-subtitle">Missing information for follow-up</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Priority:</span>
                        <select class="filter-select" id="gap-priority-filter">
                            <option value="all">All</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                </div>
                <table class="data-table" id="gaps-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Gap</th>
                            <th>Priority</th>
                            <th>Domain</th>
                            <th>Why Needed</th>
                            <th>Suggested Source</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <!-- Assumptions Section -->
            <div class="section" id="section-assumptions">
                <div class="section-header">
                    <h2 class="section-title">Assumptions</h2>
                    <p class="section-subtitle">Inferences made from available information</p>
                </div>
                <table class="data-table" id="assumptions-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Assumption</th>
                            <th>Confidence</th>
                            <th>Domain</th>
                            <th>Basis</th>
                            <th>Validation Needed</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <!-- Recommendations Section -->
            <div class="section" id="section-recommendations">
                <div class="section-header">
                    <h2 class="section-title">Strategic Recommendations</h2>
                    <p class="section-subtitle">Advice for the deal team</p>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <span class="filter-label">Priority:</span>
                        <select class="filter-select" id="rec-priority-filter">
                            <option value="all">All</option>
                            <option value="critical">Critical</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                </div>
                <div class="card-grid" id="recommendations-grid"></div>
            </div>
        </div>
    </div>

    <script>
        // Embedded analysis data
        const data = {data_json};

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('generated-date').textContent =
                'Generated: ' + new Date(data.generated_at).toLocaleString();

            const totalFindings = (data.current_state?.length || 0) + (data.risks?.length || 0) +
                                  (data.strategic_considerations?.length || 0) + (data.gaps?.length || 0);
            document.getElementById('finding-count').textContent = totalFindings + ' findings';

            updateCounts();
            renderExecutiveSummary();
            renderSummary();
            renderDomains();
            renderCurrentState();
            renderRisks();
            renderStrategic();
            renderWorkItems();
            renderGaps();
            renderAssumptions();
            renderRecommendations();
            populateFilters();
        }});

        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {{
            item.addEventListener('click', () => {{
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                document.getElementById('section-' + item.dataset.section).classList.add('active');
            }});
        }});

        function updateCounts() {{
            document.getElementById('current-state-count').textContent = data.current_state?.length || 0;
            document.getElementById('risks-count').textContent = data.risks?.length || 0;
            document.getElementById('strategic-count').textContent = data.strategic_considerations?.length || 0;
            document.getElementById('gaps-count').textContent = data.gaps?.length || 0;
            document.getElementById('assumptions-count').textContent = data.assumptions?.length || 0;
            document.getElementById('work-items-count').textContent = data.work_items?.length || 0;
            document.getElementById('recommendations-count').textContent = data.recommendations?.length || 0;
        }}

        function renderExecutiveSummary() {{
            const container = document.getElementById('exec-summary-container');
            const es = data.executive_summary;

            if (!es) {{
                container.innerHTML = '';
                return;
            }}

            const recClass = 'rec-' + (es.deal_recommendation || 'proceed_with_caution');

            container.innerHTML = `
                <div class="exec-summary-banner">
                    <div class="exec-summary-header">
                        <span class="exec-summary-title">Investment Committee Summary</span>
                        <span class="deal-recommendation ${{recClass}}">${{formatRecommendation(es.deal_recommendation)}}</span>
                    </div>
                    <div class="exec-summary-metrics">
                        <div class="exec-metric">
                            <div class="exec-metric-value">${{es.overall_complexity?.toUpperCase() || 'N/A'}}</div>
                            <div class="exec-metric-label">Complexity</div>
                        </div>
                        <div class="exec-metric">
                            <div class="exec-metric-value">${{es.total_estimated_cost_range || 'TBD'}}</div>
                            <div class="exec-metric-label">Investment</div>
                        </div>
                        <div class="exec-metric">
                            <div class="exec-metric-value">${{es.estimated_timeline || 'TBD'}}</div>
                            <div class="exec-metric-label">Timeline</div>
                        </div>
                        <div class="exec-metric">
                            <div class="exec-metric-value">${{es.confidence_level?.toUpperCase() || 'N/A'}}</div>
                            <div class="exec-metric-label">Confidence</div>
                        </div>
                    </div>
                    ${{es.key_findings?.length ? `
                        <div class="exec-findings">
                            <h4>Key Findings</h4>
                            <ul>${{es.key_findings.map(f => `<li>${{f}}</li>`).join('')}}</ul>
                        </div>
                    ` : ''}}
                    ${{es.critical_risks?.length ? `
                        <div class="exec-findings" style="margin-top: 16px;">
                            <h4>Critical Risks</h4>
                            <ul>${{es.critical_risks.map(r => `<li>${{r}}</li>`).join('')}}</ul>
                        </div>
                    ` : ''}}
                </div>
            `;
        }}

        function renderSummary() {{
            const container = document.getElementById('summary-cards');
            const crossDomain = data.domain_summaries?.['cross-domain'] || {{}};
            const standaloneRisks = (data.risks || []).filter(r => r.integration_dependent === false);

            container.innerHTML = `
                <div class="summary-card">
                    <div class="summary-card-header">
                        <span class="summary-card-title">Overall Complexity</span>
                        <span class="complexity-badge complexity-${{crossDomain.complexity_assessment || 'high'}}">
                            ${{(crossDomain.complexity_assessment || 'N/A').replace('_', ' ')}}
                        </span>
                    </div>
                    <div class="summary-card-value">${{crossDomain.estimated_cost_range || 'TBD'}}</div>
                    <div class="summary-card-meta">Estimated one-time cost</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-header">
                        <span class="summary-card-title">Current State</span>
                    </div>
                    <div class="summary-card-value">${{data.current_state?.length || 0}}</div>
                    <div class="summary-card-meta">Environment observations</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-header">
                        <span class="summary-card-title">Risks Identified</span>
                    </div>
                    <div class="summary-card-value">${{data.risks?.length || 0}}</div>
                    <div class="summary-card-meta">${{standaloneRisks.length}} standalone, ${{(data.risks?.length || 0) - standaloneRisks.length}} integration</div>
                </div>
                <div class="summary-card">
                    <div class="summary-card-header">
                        <span class="summary-card-title">Work Items</span>
                    </div>
                    <div class="summary-card-value">${{data.work_items?.length || 0}}</div>
                    <div class="summary-card-meta">${{(data.work_items || []).filter(w => w.phase === 'Day_1').length}} Day 1 items</div>
                </div>
            `;

            // Show standalone risks prominently
            if (standaloneRisks.length > 0) {{
                document.getElementById('top-risks-summary').innerHTML = `
                    <h3>Standalone Risks (Exist Without Integration)</h3>
                    ${{standaloneRisks.slice(0, 5).map(r => `
                        <div class="risk-alert standalone">
                            <div class="risk-alert-title">${{r.risk}}</div>
                            <div class="risk-alert-mitigation">${{r.standalone_exposure || r.mitigation || ''}}</div>
                            <div class="risk-alert-type">
                                <span class="badge badge-${{r.severity}}">${{r.severity}}</span>
                                <span class="badge badge-standalone" style="margin-left: 4px;">Standalone</span>
                            </div>
                        </div>
                    `).join('')}}
                `;
            }}
        }}

        function renderDomains() {{
            const container = document.getElementById('domain-cards');
            const domains = Object.entries(data.domain_summaries || {{}}).filter(([k]) => k !== 'cross-domain');

            if (domains.length === 0) {{
                container.innerHTML = '<p style="color: #64748b;">No domain data available</p>';
                return;
            }}

            container.innerHTML = domains.map(([name, domain]) => `
                <div class="domain-card">
                    <div class="domain-card-header">
                        <span class="domain-name">${{name}}</span>
                        <span class="complexity-badge complexity-${{domain.complexity_assessment || 'medium'}}">
                            ${{(domain.complexity_assessment || 'N/A').replace('_', ' ')}}
                        </span>
                    </div>
                    <div class="domain-stats">
                        <div class="domain-stat">
                            <div class="domain-stat-value">${{domain.estimated_cost_range || 'TBD'}}</div>
                            <div class="domain-stat-label">Cost Range</div>
                        </div>
                        <div class="domain-stat">
                            <div class="domain-stat-value">${{domain.estimated_timeline || 'TBD'}}</div>
                            <div class="domain-stat-label">Timeline</div>
                        </div>
                    </div>
                    <div class="domain-summary">${{domain.summary || 'No summary available'}}</div>
                </div>
            `).join('');
        }}

        function renderCurrentState() {{
            const container = document.getElementById('current-state-grid');
            const domainFilter = document.getElementById('cs-domain-filter').value;
            const maturityFilter = document.getElementById('cs-maturity-filter').value;

            let filtered = data.current_state || [];
            if (domainFilter !== 'all') filtered = filtered.filter(c => c.domain === domainFilter);
            if (maturityFilter !== 'all') filtered = filtered.filter(c => c.maturity === maturityFilter);

            container.innerHTML = filtered.map(c => `
                <div class="current-state-card">
                    <div class="cs-card-header">
                        <span class="cs-category">${{c.category?.replace(/_/g, ' ') || c.domain}}</span>
                        <span class="cs-maturity maturity-${{c.maturity}}">${{c.maturity}}</span>
                    </div>
                    <div class="cs-summary">${{c.summary}}</div>
                    ${{c.key_characteristics?.length ? `
                        <div class="cs-characteristics">
                            ${{c.key_characteristics.map(char => `<span class="cs-char-tag">${{char}}</span>`).join('')}}
                        </div>
                    ` : ''}}
                    <div class="cs-footer">
                        <span class="badge badge-domain">${{c.domain}}</span>
                        <span class="cs-viability viability-${{c.standalone_viability}}">${{c.standalone_viability?.replace(/_/g, ' ')}}</span>
                    </div>
                </div>
            `).join('');
        }}

        function renderRisks() {{
            const tbody = document.querySelector('#risks-table tbody');
            const severityFilter = document.getElementById('risk-severity-filter').value;
            const typeFilter = document.getElementById('risk-type-filter').value;
            const domainFilter = document.getElementById('risk-domain-filter').value;

            let filtered = data.risks || [];
            if (severityFilter !== 'all') filtered = filtered.filter(r => r.severity === severityFilter);
            if (typeFilter === 'standalone') filtered = filtered.filter(r => r.integration_dependent === false);
            if (typeFilter === 'integration') filtered = filtered.filter(r => r.integration_dependent !== false);
            if (domainFilter !== 'all') filtered = filtered.filter(r => r.domain === domainFilter);

            tbody.innerHTML = filtered.map(r => `
                <tr>
                    <td class="id-cell">${{r.id}}</td>
                    <td class="main-cell">
                        <strong>${{r.risk}}</strong>
                        <p>${{r.trigger || ''}}</p>
                    </td>
                    <td>
                        <span class="badge ${{r.integration_dependent === false ? 'badge-standalone' : 'badge-integration'}}">
                            ${{r.integration_dependent === false ? 'Standalone' : 'Integration'}}
                        </span>
                    </td>
                    <td><span class="badge badge-${{r.severity}}">${{r.severity}}</span></td>
                    <td><span class="badge badge-domain">${{r.domain}}</span></td>
                    <td style="max-width: 300px; font-size: 13px; color: #94a3b8;">${{r.mitigation || ''}}</td>
                </tr>
            `).join('');
        }}

        function renderStrategic() {{
            const container = document.getElementById('strategic-grid');
            const alignmentFilter = document.getElementById('sc-alignment-filter').value;

            let filtered = data.strategic_considerations || [];
            if (alignmentFilter !== 'all') filtered = filtered.filter(s => s.buyer_alignment === alignmentFilter);

            container.innerHTML = filtered.map(s => `
                <div class="strategic-card ${{s.buyer_alignment}}">
                    <div class="sc-header">
                        <span class="sc-theme">${{s.theme}}</span>
                        <span class="sc-id">${{s.id}}</span>
                    </div>
                    <div class="sc-observation">${{s.observation}}</div>
                    <div class="sc-implication">${{s.implication}}</div>
                    <div class="sc-tags">
                        ${{(s.deal_relevance || []).map(tag => `<span class="sc-tag ${{tag}}">${{tag.replace(/_/g, ' ')}}</span>`).join('')}}
                        <span class="badge badge-domain" style="margin-left: 8px;">${{s.domain}}</span>
                    </div>
                </div>
            `).join('');
        }}

        function renderWorkItems() {{
            const container = document.getElementById('work-items-grid');
            const phaseFilter = document.getElementById('work-phase-filter').value;
            const domainFilter = document.getElementById('work-domain-filter').value;

            let filtered = data.work_items || [];
            if (phaseFilter !== 'all') filtered = filtered.filter(w => w.phase === phaseFilter);
            if (domainFilter !== 'all') filtered = filtered.filter(w => w.domain === domainFilter);

            container.innerHTML = filtered.map(w => `
                <div class="item-card">
                    <div class="item-card-header">
                        <span class="item-card-id">${{w.id}}</span>
                        <span class="badge badge-${{w.phase}}">${{formatPhase(w.phase)}}</span>
                    </div>
                    <div class="item-card-title">${{w.title}}</div>
                    <div class="item-card-description">${{w.description || ''}}</div>
                    ${{w.depends_on?.length ? `
                        <div class="depends-on">
                            Depends on: ${{w.depends_on.map(d => `<span>${{d}}</span>`).join('')}}
                        </div>
                    ` : ''}}
                    <div class="item-card-meta">
                        <div class="meta-item">
                            <span class="meta-item-label">Effort:</span>
                            <span class="meta-item-value">${{w.effort_estimate || 'TBD'}}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-item-label">Cost:</span>
                            <span class="meta-item-value">${{w.cost_estimate_range || 'TBD'}}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-item-label">Domain:</span>
                            <span class="meta-item-value">${{w.domain}}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function renderGaps() {{
            const tbody = document.querySelector('#gaps-table tbody');
            const priorityFilter = document.getElementById('gap-priority-filter').value;

            let filtered = data.gaps || [];
            if (priorityFilter !== 'all') filtered = filtered.filter(g => g.priority === priorityFilter);

            tbody.innerHTML = filtered.map(g => `
                <tr>
                    <td class="id-cell">${{g.id}}</td>
                    <td class="main-cell"><strong>${{g.gap}}</strong></td>
                    <td><span class="badge badge-${{g.priority}}">${{g.priority}}</span></td>
                    <td><span class="badge badge-domain">${{g.domain}}</span></td>
                    <td style="max-width: 250px; font-size: 13px; color: #94a3b8;">${{g.why_needed || ''}}</td>
                    <td style="max-width: 200px; font-size: 13px; color: #94a3b8;">${{g.suggested_source || ''}}</td>
                </tr>
            `).join('');
        }}

        function renderAssumptions() {{
            const tbody = document.querySelector('#assumptions-table tbody');

            tbody.innerHTML = (data.assumptions || []).map(a => `
                <tr>
                    <td class="id-cell">${{a.id}}</td>
                    <td class="main-cell"><strong>${{a.assumption}}</strong></td>
                    <td><span class="badge badge-${{a.confidence === 'high' ? 'low' : a.confidence === 'low' ? 'high' : 'medium'}}">${{a.confidence}}</span></td>
                    <td><span class="badge badge-domain">${{a.domain}}</span></td>
                    <td style="max-width: 250px; font-size: 13px; color: #94a3b8;">${{a.basis || ''}}</td>
                    <td style="max-width: 200px; font-size: 13px; color: #94a3b8;">${{a.validation_needed || ''}}</td>
                </tr>
            `).join('');
        }}

        function renderRecommendations() {{
            const container = document.getElementById('recommendations-grid');
            const priorityFilter = document.getElementById('rec-priority-filter').value;

            let filtered = data.recommendations || [];
            if (priorityFilter !== 'all') filtered = filtered.filter(r => r.priority === priorityFilter);

            container.innerHTML = filtered.map(r => `
                <div class="item-card">
                    <div class="item-card-header">
                        <span class="item-card-id">${{r.id}}</span>
                        <span class="badge badge-${{r.priority}}">${{r.priority}}</span>
                    </div>
                    <div class="item-card-title">${{r.recommendation}}</div>
                    <div class="item-card-description">${{r.rationale || ''}}</div>
                    <div class="item-card-meta">
                        <div class="meta-item">
                            <span class="meta-item-label">Timing:</span>
                            <span class="meta-item-value">${{formatTiming(r.timing)}}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-item-label">Investment:</span>
                            <span class="meta-item-value">${{r.investment_required || 'TBD'}}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function formatPhase(phase) {{
            const phases = {{ 'Day_1': 'Day 1', 'Day_100': 'Day 100', 'Post_100': 'Post 100', 'Optional': 'Optional' }};
            return phases[phase] || phase;
        }}

        function formatTiming(timing) {{
            const timings = {{ 'pre_close': 'Pre-Close', 'day_1': 'Day 1', 'first_90_days': 'First 90 Days', 'ongoing': 'Ongoing' }};
            return timings[timing] || timing;
        }}

        function formatRecommendation(rec) {{
            const recs = {{
                'proceed': 'Proceed',
                'proceed_with_caution': 'Proceed with Caution',
                'significant_concerns': 'Significant Concerns',
                'reconsider': 'Reconsider'
            }};
            return recs[rec] || rec;
        }}

        function populateFilters() {{
            const domains = [...new Set([
                ...(data.current_state || []).map(c => c.domain),
                ...(data.risks || []).map(r => r.domain),
                ...(data.work_items || []).map(w => w.domain)
            ])].filter(Boolean);

            const domainOptions = '<option value="all">All Domains</option>' +
                domains.map(d => `<option value="${{d}}">${{d}}</option>`).join('');

            document.getElementById('cs-domain-filter').innerHTML = domainOptions;
            document.getElementById('risk-domain-filter').innerHTML = domainOptions;
            document.getElementById('work-domain-filter').innerHTML = domainOptions;
        }}

        // Filter listeners
        document.getElementById('cs-domain-filter').addEventListener('change', renderCurrentState);
        document.getElementById('cs-maturity-filter').addEventListener('change', renderCurrentState);
        document.getElementById('risk-severity-filter').addEventListener('change', renderRisks);
        document.getElementById('risk-type-filter').addEventListener('change', renderRisks);
        document.getElementById('risk-domain-filter').addEventListener('change', renderRisks);
        document.getElementById('sc-alignment-filter').addEventListener('change', renderStrategic);
        document.getElementById('work-phase-filter').addEventListener('change', renderWorkItems);
        document.getElementById('work-domain-filter').addEventListener('change', renderWorkItems);
        document.getElementById('gap-priority-filter').addEventListener('change', renderGaps);
        document.getElementById('rec-priority-filter').addEventListener('change', renderRecommendations);
    </script>
</body>
</html>'''


if __name__ == "__main__":
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "data/output"
    auto_open = "--no-open" not in sys.argv

    print(f"\n🔄 Generating analysis viewer from: {output_dir}\n")
    generate_viewer(output_dir, auto_open)
