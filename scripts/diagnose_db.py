#!/usr/bin/env python3
"""
Database Diagnostic Script for IT Diligence Agent

Run this to diagnose why deals appear empty or data isn't persisting.

Usage:
    python scripts/diagnose_db.py                    # Check all deals
    python scripts/diagnose_db.py --deal-id <id>    # Check specific deal
    python scripts/diagnose_db.py --verbose         # Show sample data
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from collections import defaultdict


def create_app():
    """Create Flask app for database access."""
    from flask import Flask
    from web.database import db, init_db

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'diagnostic-script'
    init_db(app)

    return app, db


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def print_section(text):
    print(f"\n--- {text} ---")


def print_ok(text):
    print(f"  ✓ {text}")


def print_warn(text):
    print(f"  ⚠ {text}")


def print_error(text):
    print(f"  ✗ {text}")


def print_info(text):
    print(f"  • {text}")


def diagnose_all_deals(db, verbose=False):
    """Check overall database health."""
    from web.database import Deal, Fact, Finding, Gap, AnalysisRun, Document

    print_header("DATABASE OVERVIEW")

    # Count all records
    deals = Deal.query.filter(Deal.deleted_at.is_(None)).all()
    total_facts = Fact.query.filter(Fact.deleted_at.is_(None)).count()
    total_findings = Finding.query.filter(Finding.deleted_at.is_(None)).count()
    total_gaps = Gap.query.filter(Gap.deleted_at.is_(None)).count()
    total_runs = AnalysisRun.query.count()
    total_docs = Document.query.filter(Document.deleted_at.is_(None)).count()

    print_info(f"Deals: {len(deals)}")
    print_info(f"Documents: {total_docs}")
    print_info(f"Facts: {total_facts}")
    print_info(f"Findings: {total_findings}")
    print_info(f"Gaps: {total_gaps}")
    print_info(f"Analysis Runs: {total_runs}")

    if not deals:
        print_warn("No deals found in database")
        return

    print_header("DEAL SUMMARY")

    for deal in deals:
        print_section(f"Deal: {deal.name or deal.target_name} ({deal.id[:8]}...)")
        diagnose_deal(db, deal.id, verbose=verbose, brief=True)

    # Check for orphaned data
    print_header("ORPHANED DATA CHECK")

    orphaned_facts = Fact.query.filter(
        Fact.deleted_at.is_(None),
        ~Fact.deal_id.in_([d.id for d in deals])
    ).count()

    orphaned_findings = Finding.query.filter(
        Finding.deleted_at.is_(None),
        ~Finding.deal_id.in_([d.id for d in deals])
    ).count()

    if orphaned_facts:
        print_warn(f"Orphaned facts (no valid deal): {orphaned_facts}")
    else:
        print_ok("No orphaned facts")

    if orphaned_findings:
        print_warn(f"Orphaned findings (no valid deal): {orphaned_findings}")
    else:
        print_ok("No orphaned findings")


def diagnose_deal(db, deal_id, verbose=False, brief=False):
    """Diagnose a specific deal."""
    from web.database import Deal, Fact, Finding, Gap, AnalysisRun, Document

    deal = Deal.query.get(deal_id)

    if not deal:
        print_error(f"Deal not found: {deal_id}")
        return

    if not brief:
        print_header(f"DIAGNOSING DEAL: {deal.name or deal.target_name}")
        print_info(f"Deal ID: {deal.id}")
        print_info(f"Status: {deal.status}")
        print_info(f"Created: {deal.created_at}")

    # === 1. CHECK ANALYSIS RUNS ===
    if not brief:
        print_section("Analysis Runs")

    runs = AnalysisRun.query.filter_by(deal_id=deal_id).order_by(AnalysisRun.created_at.desc()).all()

    if not runs:
        print_error("NO ANALYSIS RUNS FOUND - Analysis was never run or Phase 1 isn't working")
    else:
        if not brief:
            print_ok(f"Found {len(runs)} analysis run(s)")

        for run in runs:
            status_icon = "✓" if run.status == 'completed' else "⚠" if run.status == 'running' else "✗"
            if brief:
                print_info(f"Run #{run.run_number}: {run.status} | Facts: {run.facts_created} | Findings: {run.findings_created}")
            else:
                print_info(f"[{status_icon}] Run #{run.run_number} ({run.id[:8]}...)")
                print(f"      Status: {run.status}")
                print(f"      Progress: {run.progress}%")
                print(f"      Current step: {run.current_step or 'N/A'}")
                print(f"      Facts created: {run.facts_created}")
                print(f"      Findings created: {run.findings_created}")
                print(f"      Started: {run.started_at}")
                print(f"      Completed: {run.completed_at}")
                if run.error_message:
                    print(f"      ERROR: {run.error_message}")

    # Check for completed runs
    completed_runs = [r for r in runs if r.status == 'completed']
    if runs and not completed_runs:
        print_warn("NO COMPLETED RUNS - All runs are incomplete/failed")
        print_warn("Phase 2 UI will show empty because it filters by 'completed' status")

    # === 2. CHECK DOCUMENTS ===
    if not brief:
        print_section("Documents")

    docs = Document.query.filter_by(deal_id=deal_id).filter(Document.deleted_at.is_(None)).all()
    if not docs:
        print_warn("No documents uploaded")
    else:
        if not brief:
            print_ok(f"Found {len(docs)} document(s)")
            for doc in docs[:5]:  # Show first 5
                print_info(f"{doc.filename} ({doc.status}) - {doc.entity}")

    # === 3. CHECK FACTS ===
    if not brief:
        print_section("Facts")

    facts = Fact.query.filter_by(deal_id=deal_id).filter(Fact.deleted_at.is_(None)).all()

    if not facts:
        print_error("NO FACTS FOUND - Either analysis didn't run or Phase 1 writes failed")
    else:
        print_ok(f"Found {len(facts)} fact(s)")

        # Check domain distribution
        domains = defaultdict(int)
        for f in facts:
            domains[f.domain] += 1

        if not brief:
            print_info("Facts by domain:")
            for domain, count in sorted(domains.items()):
                print(f"      {domain}: {count}")

        # Check analysis_run_id linkage
        facts_with_run = sum(1 for f in facts if f.analysis_run_id)
        facts_without_run = len(facts) - facts_with_run

        if facts_without_run > 0:
            print_warn(f"{facts_without_run} facts have NO analysis_run_id (orphaned from runs)")
            print_warn("These facts may not show in Phase 2 UI which filters by run")
        else:
            print_ok("All facts linked to an analysis run")

        if verbose and facts:
            print_info("Sample facts:")
            for f in facts[:3]:
                print(f"      [{f.domain}] {f.item[:60]}...")

    # === 4. CHECK FINDINGS ===
    if not brief:
        print_section("Findings")

    findings = Finding.query.filter_by(deal_id=deal_id).filter(Finding.deleted_at.is_(None)).all()

    if not findings:
        print_warn("No findings found")
    else:
        print_ok(f"Found {len(findings)} finding(s)")

        # Check type distribution
        types = defaultdict(int)
        for f in findings:
            types[f.finding_type] += 1

        if not brief:
            print_info("Findings by type:")
            for ftype, count in sorted(types.items()):
                print(f"      {ftype}: {count}")

        # Check analysis_run_id linkage
        findings_with_run = sum(1 for f in findings if f.analysis_run_id)
        findings_without_run = len(findings) - findings_with_run

        if findings_without_run > 0:
            print_warn(f"{findings_without_run} findings have NO analysis_run_id")

        if verbose and findings:
            print_info("Sample findings:")
            for f in findings[:3]:
                print(f"      [{f.finding_type}] {f.title[:60]}...")

    # === 5. CHECK GAPS ===
    if not brief:
        print_section("Gaps")

    gaps = Gap.query.filter_by(deal_id=deal_id).filter(Gap.deleted_at.is_(None)).all()

    if not gaps:
        if not brief:
            print_info("No gaps found (may be normal)")
    else:
        print_ok(f"Found {len(gaps)} gap(s)")

    # === 6. DIAGNOSIS SUMMARY ===
    if not brief:
        print_header("DIAGNOSIS SUMMARY")

        issues = []

        if not runs:
            issues.append("CRITICAL: No analysis runs - Phase 1 may not be integrated")
        elif not completed_runs:
            issues.append("CRITICAL: No completed runs - UI will show empty")

        if not facts:
            issues.append("CRITICAL: No facts in database - nothing to display")
        elif facts_without_run > 0:
            issues.append(f"WARNING: {facts_without_run} facts missing analysis_run_id")

        if not docs:
            issues.append("WARNING: No documents uploaded")

        if issues:
            print_error("Issues found:")
            for issue in issues:
                print(f"    • {issue}")
        else:
            print_ok("No critical issues found")
            print_info("If UI still shows empty, check that routes are reading from DB (Phase 2)")


def diagnose_run_scoping(db):
    """Check how Phase 2's run scoping will affect data visibility."""
    from web.database import Deal, Fact, Finding, AnalysisRun

    print_header("RUN SCOPING ANALYSIS")
    print_info("Phase 2 will show data from 'latest completed run' by default")
    print_info("This shows what data will/won't be visible:\n")

    deals = Deal.query.filter(Deal.deleted_at.is_(None)).all()

    for deal in deals:
        print_section(f"Deal: {deal.name or deal.target_name}")

        # Get latest completed run
        latest_completed = AnalysisRun.query.filter_by(
            deal_id=deal.id,
            status='completed'
        ).order_by(AnalysisRun.created_at.desc()).first()

        # Get all facts/findings
        all_facts = Fact.query.filter_by(deal_id=deal.id).filter(Fact.deleted_at.is_(None)).count()
        all_findings = Finding.query.filter_by(deal_id=deal.id).filter(Finding.deleted_at.is_(None)).count()

        if latest_completed:
            print_ok(f"Latest completed run: #{latest_completed.run_number} ({latest_completed.id[:8]}...)")

            # Facts/findings for this run
            run_facts = Fact.query.filter_by(
                deal_id=deal.id,
                analysis_run_id=latest_completed.id
            ).filter(Fact.deleted_at.is_(None)).count()

            run_findings = Finding.query.filter_by(
                deal_id=deal.id,
                analysis_run_id=latest_completed.id
            ).filter(Finding.deleted_at.is_(None)).count()

            print_info(f"Facts visible in Phase 2 UI: {run_facts} / {all_facts} total")
            print_info(f"Findings visible in Phase 2 UI: {run_findings} / {all_findings} total")

            hidden_facts = all_facts - run_facts
            hidden_findings = all_findings - run_findings

            if hidden_facts > 0 or hidden_findings > 0:
                print_warn(f"Hidden data (from other runs): {hidden_facts} facts, {hidden_findings} findings")
        else:
            print_error("NO COMPLETED RUNS")
            print_error(f"ALL data will be hidden: {all_facts} facts, {all_findings} findings")

            # Check what runs exist
            all_runs = AnalysisRun.query.filter_by(deal_id=deal.id).all()
            if all_runs:
                print_info("Existing runs:")
                for run in all_runs:
                    print(f"      Run #{run.run_number}: status={run.status}")


def main():
    parser = argparse.ArgumentParser(description='Diagnose database issues')
    parser.add_argument('--deal-id', '-d', help='Specific deal ID to diagnose')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show sample data')
    parser.add_argument('--run-scoping', '-r', action='store_true', help='Analyze run scoping impact')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  IT DILIGENCE DATABASE DIAGNOSTIC")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    app, db = create_app()

    with app.app_context():
        if args.run_scoping:
            diagnose_run_scoping(db)
        elif args.deal_id:
            diagnose_deal(db, args.deal_id, verbose=args.verbose)
        else:
            diagnose_all_deals(db, verbose=args.verbose)

    print("\n" + "="*60)
    print("  DIAGNOSTIC COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
