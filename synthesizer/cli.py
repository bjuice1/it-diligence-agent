#!/usr/bin/env python3
"""
CLI for IT DD Synthesizer.

Usage:
    python -m synthesizer.cli --apps apps.csv --risks risks.csv --company "Acme Corp" --output report

    Or interactively:
    python -m synthesizer.cli --interactive
"""
import argparse
import sys
from pathlib import Path

from .synthesizer import ITDDSynthesizer
from .html_report import generate_html_report
from .excel_export import export_to_excel, OPENPYXL_AVAILABLE


def main():
    parser = argparse.ArgumentParser(
        description="IT DD Synthesizer - Transform Tolt outputs into reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # From CSV files:
    python -m synthesizer.cli --apps applications.csv --risks risks.csv --company "Acme Corp" --output acme_report

    # Interactive mode (paste data):
    python -m synthesizer.cli --interactive --company "Acme Corp"

    # Just applications with EOL check:
    python -m synthesizer.cli --apps apps.csv --company "TechCo" --output techco_eol_check
        """
    )

    parser.add_argument("--apps", "-a", help="Path to applications CSV from Tolt")
    parser.add_argument("--risks", "-r", help="Path to risks CSV from Tolt")
    parser.add_argument("--questions", "-q", help="Path to questions CSV from Tolt")
    parser.add_argument("--company", "-c", default="Target Company", help="Target company name")
    parser.add_argument("--output", "-o", default="it_dd_report", help="Output filename (without extension)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode - paste data")
    parser.add_argument("--html-only", action="store_true", help="Only generate HTML (skip Excel)")
    parser.add_argument("--excel-only", action="store_true", help="Only generate Excel (skip HTML)")

    args = parser.parse_args()

    # Initialize synthesizer
    synth = ITDDSynthesizer(target_company=args.company)

    if args.interactive:
        run_interactive(synth, args)
    else:
        run_batch(synth, args)


def run_batch(synth: ITDDSynthesizer, args):
    """Run in batch mode with CSV files."""
    # Parse inputs
    if args.apps:
        apps_path = Path(args.apps)
        if not apps_path.exists():
            print(f"Error: Applications file not found: {args.apps}")
            sys.exit(1)
        print(f"Parsing applications from {args.apps}...")
        apps = synth.parse_applications_csv(apps_path.read_text())
        print(f"  Found {len(apps)} applications")

    if args.risks:
        risks_path = Path(args.risks)
        if not risks_path.exists():
            print(f"Error: Risks file not found: {args.risks}")
            sys.exit(1)
        print(f"Parsing risks from {args.risks}...")
        risks = synth.parse_risks_csv(risks_path.read_text())
        print(f"  Found {len(risks)} risks")

    if args.questions:
        questions_path = Path(args.questions)
        if questions_path.exists():
            print(f"Parsing questions from {args.questions}...")
            questions = synth.parse_questions_csv(questions_path.read_text())
            print(f"  Found {len(questions)} questions")

    # Run synthesis
    print("\nRunning synthesis...")
    result = synth.synthesize()

    # Generate outputs
    generate_outputs(result, args)


def run_interactive(synth: ITDDSynthesizer, args):
    """Run in interactive mode - paste data."""
    print("=" * 60)
    print("IT DD Synthesizer - Interactive Mode")
    print("=" * 60)
    print(f"\nTarget Company: {args.company}")
    print("\nPaste your data when prompted. Enter a blank line when done.\n")

    # Applications
    print("-" * 40)
    print("APPLICATIONS (paste CSV or markdown table, blank line to finish):")
    print("-" * 40)
    apps_input = read_multiline_input()
    if apps_input.strip():
        if "|" in apps_input:
            apps = synth.parse_applications_text(apps_input)
        else:
            apps = synth.parse_applications_csv(apps_input)
        print(f"  Parsed {len(apps)} applications")

    # Risks
    print("-" * 40)
    print("RISKS (paste CSV, blank line to skip):")
    print("-" * 40)
    risks_input = read_multiline_input()
    if risks_input.strip():
        risks = synth.parse_risks_csv(risks_input)
        print(f"  Parsed {len(risks)} risks")

    # Questions
    print("-" * 40)
    print("QUESTIONS (paste CSV, blank line to skip):")
    print("-" * 40)
    questions_input = read_multiline_input()
    if questions_input.strip():
        questions = synth.parse_questions_csv(questions_input)
        print(f"  Parsed {len(questions)} questions")

    # Run synthesis
    print("\nRunning synthesis...")
    result = synth.synthesize()

    # Generate outputs
    generate_outputs(result, args)


def read_multiline_input() -> str:
    """Read multiple lines until blank line."""
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)


def generate_outputs(result, args):
    """Generate HTML and/or Excel outputs."""
    print("\n" + "=" * 60)
    print("SYNTHESIS RESULTS")
    print("=" * 60)

    # Print summary
    print(f"\nOverall Assessment: {result.overall_assessment}")
    print(f"Applications: {len(result.applications)}")
    print(f"Risks: {len(result.risks)} ({len([r for r in result.risks if r.severity == 'Critical'])} critical)")
    print(f"Cost Estimate: ${result.total_one_time_low:,} - ${result.total_one_time_high:,}")

    # EOL risks
    eol_risks = [a for a in result.applications if a.eol_status in ["Past_EOL", "Approaching_EOL"]]
    if eol_risks:
        print(f"\nEOL Risks Identified: {len(eol_risks)}")
        for app in eol_risks[:5]:
            print(f"  - {app.name} ({app.version}): {app.eol_status} - EOL {app.eol_date}")

    # Generate files
    output_base = args.output

    if not args.excel_only:
        html_path = f"{output_base}.html"
        print(f"\nGenerating HTML report: {html_path}")
        html_content = generate_html_report(result)
        Path(html_path).write_text(html_content)
        print(f"  Created: {html_path}")

    if not args.html_only:
        if OPENPYXL_AVAILABLE:
            excel_path = f"{output_base}.xlsx"
            print(f"\nGenerating Excel workbook: {excel_path}")
            excel_result = export_to_excel(result, excel_path)
            print(f"  Created: {excel_path}")
            print(f"  Sheets: {', '.join(excel_result['sheets'])}")
        else:
            print("\nSkipping Excel (openpyxl not installed)")
            print("  Install with: pip install openpyxl")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
