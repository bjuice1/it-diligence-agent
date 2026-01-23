"""
Excel Export Module for V2 Architecture

Exports IT Due Diligence findings to client-ready Excel workbooks.
Works with FactStore and ReasoningStore from V2 pipeline.

Features:
- Multiple worksheets (Summary, Facts, Risks, Work Items, VDR Requests)
- Professional formatting with severity/priority coloring
- Evidence citations and fact references
- Sortable/filterable columns
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import openpyxl components
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not installed. Install with: pip install openpyxl")


def export_to_excel(
    fact_store: Any,
    reasoning_store: Any,
    output_path: Path,
    target_name: str = "Target Company",
    include_vdr: bool = True,
    vdr_pack: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Export V2 analysis results to formatted Excel workbook.

    Args:
        fact_store: FactStore with extracted facts
        reasoning_store: ReasoningStore with findings
        output_path: Path to save Excel file
        target_name: Target company name for headers
        include_vdr: Whether to include VDR requests sheet
        vdr_pack: Optional VDRPack for VDR requests

    Returns:
        Dict with output_path and counts
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl required for Excel export. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    styles = _get_styles()

    # Create worksheets
    _create_summary_sheet(wb, fact_store, reasoning_store, target_name, styles)
    _create_facts_sheet(wb, fact_store, styles)
    _create_risks_sheet(wb, reasoning_store, styles)
    _create_work_items_sheet(wb, reasoning_store, styles)
    _create_recommendations_sheet(wb, reasoning_store, styles)
    _create_strategic_sheet(wb, reasoning_store, styles)

    if include_vdr and vdr_pack:
        _create_vdr_sheet(wb, vdr_pack, styles)

    # Remove default empty sheet
    if 'Sheet' in wb.sheetnames:
        del wb['Sheet']

    # Save
    wb.save(str(output_path))
    logger.info(f"Exported to {output_path}")

    return {
        'output_path': str(output_path),
        'counts': {
            'facts': len(fact_store.facts),
            'gaps': len(fact_store.gaps),
            'risks': len(reasoning_store.risks),
            'work_items': len(reasoning_store.work_items),
            'recommendations': len(reasoning_store.recommendations)
        }
    }


def _get_styles():
    """Define Excel styles."""
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    return {
        'header_font': Font(bold=True, color="FFFFFF", size=11),
        'header_fill': PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid"),
        'header_alignment': Alignment(horizontal="center", vertical="center", wrap_text=True),

        'title_font': Font(bold=True, size=14),
        'section_font': Font(bold=True, size=12),

        'data_alignment': Alignment(vertical="top", wrap_text=True),
        'center_alignment': Alignment(horizontal="center", vertical="top"),
        'border': thin_border,

        # Severity colors
        'critical_fill': PatternFill(start_color="C00000", end_color="C00000", fill_type="solid"),
        'critical_font': Font(color="FFFFFF", bold=True),
        'high_fill': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'medium_fill': PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid"),
        'low_fill': PatternFill(start_color="6BCB77", end_color="6BCB77", fill_type="solid"),

        # Phase colors
        'day1_fill': PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid"),
        'day100_fill': PatternFill(start_color="FFD93D", end_color="FFD93D", fill_type="solid"),
        'post100_fill': PatternFill(start_color="4ECDC4", end_color="4ECDC4", fill_type="solid"),

        # Entity colors
        'target_fill': PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid"),
        'buyer_fill': PatternFill(start_color="DEEBF7", end_color="DEEBF7", fill_type="solid"),
    }


def _apply_header_style(ws, row, styles, num_cols):
    """Apply header styling."""
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['header_alignment']
        cell.border = styles['border']


def _apply_severity_formatting(cell, value, styles):
    """Apply severity-based formatting."""
    if not value:
        return
    val = str(value).lower()
    if val == 'critical':
        cell.fill = styles['critical_fill']
        cell.font = styles['critical_font']
    elif val == 'high':
        cell.fill = styles['high_fill']
    elif val == 'medium':
        cell.fill = styles['medium_fill']
    elif val == 'low':
        cell.fill = styles['low_fill']


def _apply_phase_formatting(cell, value, styles):
    """Apply phase-based formatting."""
    if not value:
        return
    val = str(value).lower().replace('_', '')
    if 'day1' in val:
        cell.fill = styles['day1_fill']
    elif 'day100' in val:
        cell.fill = styles['day100_fill']
    elif 'post' in val:
        cell.fill = styles['post100_fill']


def _auto_size_columns(ws, min_width=10, max_width=50):
    """Auto-size columns."""
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[column_letter].width = min(max(max_length + 2, min_width), max_width)


def _create_summary_sheet(wb, fact_store, reasoning_store, target_name, styles):
    """Create Summary worksheet."""
    ws = wb.active
    ws.title = "Summary"

    ws['A1'] = f"IT Due Diligence: {target_name}"
    ws['A1'].font = styles['title_font']
    ws.merge_cells('A1:D1')

    ws['A3'] = "Generated:"
    ws['B3'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Counts
    ws['A5'] = "Findings Summary"
    ws['A5'].font = styles['section_font']

    counts = [
        ("Facts Extracted", len(fact_store.facts)),
        ("Gaps Identified", len(fact_store.gaps)),
        ("Risks", len(reasoning_store.risks)),
        ("Strategic Considerations", len(reasoning_store.strategic_considerations)),
        ("Work Items", len(reasoning_store.work_items)),
        ("Recommendations", len(reasoning_store.recommendations)),
    ]

    for i, (label, count) in enumerate(counts, 6):
        ws.cell(row=i, column=1, value=label)
        ws.cell(row=i, column=2, value=count)

    # Risk severity breakdown
    ws['A14'] = "Risk Severity"
    ws['A14'].font = styles['section_font']

    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for risk in reasoning_store.risks:
        sev = str(risk.severity).lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    for i, (sev, count) in enumerate(severity_counts.items(), 15):
        cell = ws.cell(row=i, column=1, value=sev.title())
        ws.cell(row=i, column=2, value=count)
        _apply_severity_formatting(cell, sev, styles)

    # Work items by phase
    ws['A21'] = "Work Items by Phase"
    ws['A21'].font = styles['section_font']

    phase_counts = {'Day_1': 0, 'Day_100': 0, 'Post_100': 0}
    for wi in reasoning_store.work_items:
        if wi.phase in phase_counts:
            phase_counts[wi.phase] += 1

    for i, (phase, count) in enumerate(phase_counts.items(), 22):
        cell = ws.cell(row=i, column=1, value=phase.replace('_', ' '))
        ws.cell(row=i, column=2, value=count)
        _apply_phase_formatting(cell, phase, styles)

    _auto_size_columns(ws)


def _create_facts_sheet(wb, fact_store, styles):
    """Create Facts worksheet."""
    ws = wb.create_sheet("Facts")

    headers = ["Fact ID", "Domain", "Category", "Item", "Entity", "Status", "Details", "Evidence Quote", "Source"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    for row_num, fact in enumerate(fact_store.facts, 2):
        ws.cell(row=row_num, column=1, value=fact.fact_id)
        ws.cell(row=row_num, column=2, value=fact.domain)
        ws.cell(row=row_num, column=3, value=fact.category)
        ws.cell(row=row_num, column=4, value=fact.item)

        entity_cell = ws.cell(row=row_num, column=5, value=fact.entity)
        if fact.entity == 'target':
            entity_cell.fill = styles['target_fill']
        elif fact.entity == 'buyer':
            entity_cell.fill = styles['buyer_fill']

        ws.cell(row=row_num, column=6, value=fact.status)

        # Format details as string
        if isinstance(fact.details, dict):
            details_str = "; ".join(f"{k}: {v}" for k, v in fact.details.items())
        else:
            details_str = str(fact.details)
        ws.cell(row=row_num, column=7, value=details_str)

        ws.cell(row=row_num, column=8, value=fact.evidence.get('exact_quote', ''))
        ws.cell(row=row_num, column=9, value=fact.source_document)

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)


def _create_risks_sheet(wb, reasoning_store, styles):
    """Create Risks worksheet."""
    ws = wb.create_sheet("Risks")

    headers = ["ID", "Domain", "Title", "Description", "Category", "Severity",
               "Integration Dependent", "Mitigation", "Based On Facts", "Confidence"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    for row_num, risk in enumerate(reasoning_store.risks, 2):
        ws.cell(row=row_num, column=1, value=risk.finding_id)
        ws.cell(row=row_num, column=2, value=risk.domain)
        ws.cell(row=row_num, column=3, value=risk.title)
        ws.cell(row=row_num, column=4, value=risk.description)
        ws.cell(row=row_num, column=5, value=risk.category)

        sev_cell = ws.cell(row=row_num, column=6, value=risk.severity)
        _apply_severity_formatting(sev_cell, risk.severity, styles)

        ws.cell(row=row_num, column=7, value='Yes' if risk.integration_dependent else 'No')
        ws.cell(row=row_num, column=8, value=risk.mitigation)
        ws.cell(row=row_num, column=9, value=", ".join(risk.based_on_facts))
        ws.cell(row=row_num, column=10, value=risk.confidence)

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)


def _create_work_items_sheet(wb, reasoning_store, styles):
    """Create Work Items worksheet."""
    ws = wb.create_sheet("Work Items")

    headers = ["ID", "Domain", "Title", "Description", "Phase", "Priority",
               "Owner", "Cost Estimate", "Triggered By", "Based On Facts"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    for row_num, wi in enumerate(reasoning_store.work_items, 2):
        ws.cell(row=row_num, column=1, value=wi.finding_id)
        ws.cell(row=row_num, column=2, value=wi.domain)
        ws.cell(row=row_num, column=3, value=wi.title)
        ws.cell(row=row_num, column=4, value=wi.description)

        phase_cell = ws.cell(row=row_num, column=5, value=wi.phase)
        _apply_phase_formatting(phase_cell, wi.phase, styles)

        pri_cell = ws.cell(row=row_num, column=6, value=wi.priority)
        _apply_severity_formatting(pri_cell, wi.priority, styles)

        ws.cell(row=row_num, column=7, value=wi.owner_type)
        ws.cell(row=row_num, column=8, value=wi.cost_estimate)
        ws.cell(row=row_num, column=9, value=", ".join(wi.triggered_by))
        ws.cell(row=row_num, column=10, value=", ".join(wi.based_on_facts))

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)


def _create_recommendations_sheet(wb, reasoning_store, styles):
    """Create Recommendations worksheet."""
    ws = wb.create_sheet("Recommendations")

    headers = ["ID", "Domain", "Title", "Description", "Action Type", "Urgency",
               "Rationale", "Based On Facts"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    for row_num, rec in enumerate(reasoning_store.recommendations, 2):
        ws.cell(row=row_num, column=1, value=rec.finding_id)
        ws.cell(row=row_num, column=2, value=rec.domain)
        ws.cell(row=row_num, column=3, value=rec.title)
        ws.cell(row=row_num, column=4, value=rec.description)
        ws.cell(row=row_num, column=5, value=rec.action_type)

        urg_cell = ws.cell(row=row_num, column=6, value=rec.urgency)
        _apply_severity_formatting(urg_cell, rec.urgency, styles)

        ws.cell(row=row_num, column=7, value=rec.rationale)
        ws.cell(row=row_num, column=8, value=", ".join(rec.based_on_facts))

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)


def _create_strategic_sheet(wb, reasoning_store, styles):
    """Create Strategic Considerations worksheet."""
    ws = wb.create_sheet("Strategic")

    headers = ["ID", "Domain", "Title", "Description", "Lens", "Implication",
               "Based On Facts", "Confidence"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    for row_num, sc in enumerate(reasoning_store.strategic_considerations, 2):
        ws.cell(row=row_num, column=1, value=sc.finding_id)
        ws.cell(row=row_num, column=2, value=sc.domain)
        ws.cell(row=row_num, column=3, value=sc.title)
        ws.cell(row=row_num, column=4, value=sc.description)
        ws.cell(row=row_num, column=5, value=sc.lens)
        ws.cell(row=row_num, column=6, value=sc.implication)
        ws.cell(row=row_num, column=7, value=", ".join(sc.based_on_facts))
        ws.cell(row=row_num, column=8, value=sc.confidence)

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)


def _create_vdr_sheet(wb, vdr_pack, styles):
    """Create VDR Requests worksheet."""
    ws = wb.create_sheet("VDR Requests")

    headers = ["ID", "Domain", "Priority", "Title", "Description", "Category",
               "Source", "Suggested Documents"]

    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _apply_header_style(ws, 1, styles, len(headers))

    row_num = 2
    for req in vdr_pack.requests:
        ws.cell(row=row_num, column=1, value=req.request_id)
        ws.cell(row=row_num, column=2, value=req.domain)

        pri_cell = ws.cell(row=row_num, column=3, value=req.priority)
        _apply_severity_formatting(pri_cell, req.priority, styles)

        ws.cell(row=row_num, column=4, value=req.title)
        ws.cell(row=row_num, column=5, value=req.description)
        ws.cell(row=row_num, column=6, value=req.category)
        ws.cell(row=row_num, column=7, value=f"{req.source}: {req.source_id}" if req.source_id else req.source)
        ws.cell(row=row_num, column=8, value=", ".join(req.suggested_documents))

        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).alignment = styles['data_alignment']
            ws.cell(row=row_num, column=col).border = styles['border']

        row_num += 1

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    _auto_size_columns(ws)
