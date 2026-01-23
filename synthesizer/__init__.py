"""
IT DD Synthesizer

A lean tool to transform Tolt/Harvey outputs into structured reports.

Usage:
    from synthesizer import ITDDSynthesizer, generate_html_report, export_to_excel

    # Create synthesizer
    synth = ITDDSynthesizer(target_company="Acme Corp")

    # Parse Tolt outputs
    synth.parse_applications_csv(apps_csv_content)
    synth.parse_risks_csv(risks_csv_content)

    # Run synthesis (adds EOL risks, calculates costs)
    result = synth.synthesize()

    # Generate outputs
    html = generate_html_report(result)
    export_to_excel(result, "report.xlsx")

CLI Usage:
    python -m synthesizer.cli --apps apps.csv --risks risks.csv --company "Acme" --output report
"""

from .models import (
    Application,
    Risk,
    FollowUpQuestion,
    CostItem,
    DomainSummary,
    SynthesisResult,
)

from .synthesizer import ITDDSynthesizer

from .html_report import generate_html_report

from .excel_export import export_to_excel, OPENPYXL_AVAILABLE

from .eol_data import (
    EOL_DATABASE,
    lookup_eol,
    get_eol_status,
    get_eol_date,
    is_eol_risk,
)

from .cost_engine import (
    COST_RANGES,
    estimate_cost_for_risk,
    calculate_costs,
    format_currency,
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "Application",
    "Risk",
    "FollowUpQuestion",
    "CostItem",
    "DomainSummary",
    "SynthesisResult",
    # Synthesizer
    "ITDDSynthesizer",
    # Reports
    "generate_html_report",
    "export_to_excel",
    "OPENPYXL_AVAILABLE",
    # EOL
    "EOL_DATABASE",
    "lookup_eol",
    "get_eol_status",
    "get_eol_date",
    "is_eol_risk",
    # Costs
    "COST_RANGES",
    "estimate_cost_for_risk",
    "calculate_costs",
    "format_currency",
]
