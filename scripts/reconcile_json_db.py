#!/usr/bin/env python3
"""
JSON/PostgreSQL Reconciliation Script

Detects drift between JSON files and PostgreSQL database.
Reports differences and optionally syncs data.

Usage:
    python scripts/reconcile_json_db.py [--fix] [--verbose]

Options:
    --fix       Attempt to fix discrepancies (sync JSON to DB)
    --verbose   Show detailed comparison output
    --json-dir  Path to JSON data directory
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / 'docker' / '.env')
load_dotenv(project_root / '.env')


@dataclass
class ReconciliationResult:
    """Results of reconciliation check."""
    entity_type: str
    json_count: int
    db_count: int
    only_in_json: List[str]
    only_in_db: List[str]
    value_mismatches: List[Dict[str, Any]]
    matched: int

    @property
    def is_synced(self) -> bool:
        return (
            len(self.only_in_json) == 0 and
            len(self.only_in_db) == 0 and
            len(self.value_mismatches) == 0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_type': self.entity_type,
            'json_count': self.json_count,
            'db_count': self.db_count,
            'only_in_json': len(self.only_in_json),
            'only_in_db': len(self.only_in_db),
            'value_mismatches': len(self.value_mismatches),
            'matched': self.matched,
            'is_synced': self.is_synced
        }


def create_app():
    """Create Flask app for database access."""
    from flask import Flask
    from web.database import db, init_db

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'reconcile-key')
    init_db(app)

    return app


def load_json_facts(output_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load all facts from JSON files."""
    facts = {}

    # Look for session directories with facts
    for session_dir in output_dir.glob('*'):
        if not session_dir.is_dir():
            continue

        # Check for facts directory
        facts_dir = session_dir / 'facts'
        if facts_dir.exists():
            for json_file in facts_dir.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for fact in data:
                                fact_id = fact.get('fact_id')
                                if fact_id:
                                    facts[fact_id] = fact
                        elif isinstance(data, dict):
                            for fact in data.get('facts', []):
                                fact_id = fact.get('fact_id')
                                if fact_id:
                                    facts[fact_id] = fact
                except Exception as e:
                    print(f"  Warning: Could not load {json_file}: {e}")

        # Also check domain-specific files
        for domain in ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']:
            domain_file = session_dir / f'{domain}_facts.json'
            if domain_file.exists():
                try:
                    with open(domain_file, 'r') as f:
                        data = json.load(f)
                        for fact in data.get('facts', []):
                            fact_id = fact.get('fact_id')
                            if fact_id:
                                facts[fact_id] = fact
                except Exception as e:
                    print(f"  Warning: Could not load {domain_file}: {e}")

    return facts


def load_json_findings(output_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load all findings from JSON files."""
    findings = {}

    for session_dir in output_dir.glob('*'):
        if not session_dir.is_dir():
            continue

        # Check for findings directory
        findings_dir = session_dir / 'findings'
        if findings_dir.exists():
            for json_file in findings_dir.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                        # Handle different structures
                        items = []
                        if isinstance(data, list):
                            items = data
                        elif 'risks' in data:
                            items.extend(data.get('risks', []))
                        elif 'work_items' in data:
                            items.extend(data.get('work_items', []))
                        elif 'findings' in data:
                            items.extend(data.get('findings', []))

                        for finding in items:
                            finding_id = (
                                finding.get('finding_id') or
                                finding.get('risk_id') or
                                finding.get('id')
                            )
                            if finding_id:
                                findings[finding_id] = finding
                except Exception as e:
                    print(f"  Warning: Could not load {json_file}: {e}")

    return findings


def compare_fact(json_fact: Dict, db_fact) -> List[str]:
    """Compare a JSON fact with a DB fact and return differences."""
    differences = []

    # Compare key fields
    comparisons = [
        ('domain', json_fact.get('domain'), db_fact.domain),
        ('category', json_fact.get('category'), db_fact.category),
        ('item', json_fact.get('item'), db_fact.item),
        ('status', json_fact.get('status'), db_fact.status),
        ('entity', json_fact.get('entity'), db_fact.entity),
        ('verified', json_fact.get('verified'), db_fact.verified),
    ]

    for field, json_val, db_val in comparisons:
        if json_val != db_val:
            differences.append(f"{field}: JSON={json_val}, DB={db_val}")

    return differences


def compare_finding(json_finding: Dict, db_finding) -> List[str]:
    """Compare a JSON finding with a DB finding and return differences."""
    differences = []

    json_title = json_finding.get('title') or json_finding.get('description', '')
    json_domain = json_finding.get('domain', '')
    json_severity = json_finding.get('severity')

    comparisons = [
        ('title', json_title[:100], (db_finding.title or '')[:100]),
        ('domain', json_domain, db_finding.domain),
        ('severity', json_severity, db_finding.severity),
    ]

    for field, json_val, db_val in comparisons:
        if json_val != db_val:
            differences.append(f"{field}: JSON={json_val}, DB={db_val}")

    return differences


def reconcile_facts(app, output_dir: Path, verbose: bool = False) -> ReconciliationResult:
    """Reconcile facts between JSON and PostgreSQL."""
    from web.database import Fact as DBFact

    print("\n--- Reconciling Facts ---")

    # Load JSON facts
    json_facts = load_json_facts(output_dir)
    print(f"  Loaded {len(json_facts)} facts from JSON")

    with app.app_context():
        # Load DB facts
        db_facts = {f.id: f for f in DBFact.query.filter(DBFact.deleted_at.is_(None)).all()}
        print(f"  Loaded {len(db_facts)} facts from PostgreSQL")

        # Compare
        json_ids = set(json_facts.keys())
        db_ids = set(db_facts.keys())

        only_in_json = list(json_ids - db_ids)
        only_in_db = list(db_ids - json_ids)
        common = json_ids & db_ids

        value_mismatches = []
        matched = 0

        for fact_id in common:
            diffs = compare_fact(json_facts[fact_id], db_facts[fact_id])
            if diffs:
                value_mismatches.append({
                    'id': fact_id,
                    'differences': diffs
                })
            else:
                matched += 1

        if verbose:
            if only_in_json:
                print(f"\n  Only in JSON ({len(only_in_json)}):")
                for fid in only_in_json[:10]:
                    print(f"    - {fid}")
                if len(only_in_json) > 10:
                    print(f"    ... and {len(only_in_json) - 10} more")

            if only_in_db:
                print(f"\n  Only in DB ({len(only_in_db)}):")
                for fid in only_in_db[:10]:
                    print(f"    - {fid}")
                if len(only_in_db) > 10:
                    print(f"    ... and {len(only_in_db) - 10} more")

            if value_mismatches:
                print(f"\n  Value mismatches ({len(value_mismatches)}):")
                for mismatch in value_mismatches[:5]:
                    print(f"    - {mismatch['id']}: {', '.join(mismatch['differences'][:2])}")
                if len(value_mismatches) > 5:
                    print(f"    ... and {len(value_mismatches) - 5} more")

        return ReconciliationResult(
            entity_type='facts',
            json_count=len(json_facts),
            db_count=len(db_facts),
            only_in_json=only_in_json,
            only_in_db=only_in_db,
            value_mismatches=value_mismatches,
            matched=matched
        )


def reconcile_findings(app, output_dir: Path, verbose: bool = False) -> ReconciliationResult:
    """Reconcile findings between JSON and PostgreSQL."""
    from web.database import Finding as DBFinding

    print("\n--- Reconciling Findings ---")

    # Load JSON findings
    json_findings = load_json_findings(output_dir)
    print(f"  Loaded {len(json_findings)} findings from JSON")

    with app.app_context():
        # Load DB findings
        db_findings = {f.id: f for f in DBFinding.query.filter(DBFinding.deleted_at.is_(None)).all()}
        print(f"  Loaded {len(db_findings)} findings from PostgreSQL")

        # Compare
        json_ids = set(json_findings.keys())
        db_ids = set(db_findings.keys())

        only_in_json = list(json_ids - db_ids)
        only_in_db = list(db_ids - json_ids)
        common = json_ids & db_ids

        value_mismatches = []
        matched = 0

        for finding_id in common:
            diffs = compare_finding(json_findings[finding_id], db_findings[finding_id])
            if diffs:
                value_mismatches.append({
                    'id': finding_id,
                    'differences': diffs
                })
            else:
                matched += 1

        if verbose:
            if only_in_json:
                print(f"\n  Only in JSON ({len(only_in_json)}):")
                for fid in only_in_json[:10]:
                    print(f"    - {fid}")

            if only_in_db:
                print(f"\n  Only in DB ({len(only_in_db)}):")
                for fid in only_in_db[:10]:
                    print(f"    - {fid}")

        return ReconciliationResult(
            entity_type='findings',
            json_count=len(json_findings),
            db_count=len(db_findings),
            only_in_json=only_in_json,
            only_in_db=only_in_db,
            value_mismatches=value_mismatches,
            matched=matched
        )


def fix_discrepancies(app, output_dir: Path, results: List[ReconciliationResult]):
    """Attempt to fix discrepancies by syncing JSON to DB."""
    from web.database import db, Fact as DBFact, Finding as DBFinding, Deal

    print("\n--- Fixing Discrepancies ---")

    with app.app_context():
        # Get or create default deal
        default_deal = Deal.query.first()
        if not default_deal:
            default_deal = Deal(
                name='Reconciliation Import',
                target_name='Imported Data',
                deal_type='acquisition',
                status='active'
            )
            db.session.add(default_deal)
            db.session.commit()

        for result in results:
            if result.entity_type == 'facts' and result.only_in_json:
                json_facts = load_json_facts(output_dir)
                created = 0

                for fact_id in result.only_in_json:
                    if fact_id not in json_facts:
                        continue

                    fact_data = json_facts[fact_id]
                    try:
                        db_fact = DBFact(
                            id=fact_id,
                            deal_id=default_deal.id,
                            domain=fact_data.get('domain', 'unknown'),
                            category=fact_data.get('category', ''),
                            item=fact_data.get('item', ''),
                            status=fact_data.get('status', 'documented'),
                            entity=fact_data.get('entity', 'target'),
                            details=fact_data.get('details', {}),
                            evidence=fact_data.get('evidence', {}),
                            source_document=fact_data.get('source_document', ''),
                            confidence_score=fact_data.get('confidence_score', 0.5),
                            verified=fact_data.get('verified', False),
                            verification_status=fact_data.get('verification_status', 'pending'),
                        )
                        db.session.add(db_fact)
                        created += 1
                    except Exception as e:
                        print(f"  Error creating fact {fact_id}: {e}")

                db.session.commit()
                print(f"  Created {created} facts in PostgreSQL")

            elif result.entity_type == 'findings' and result.only_in_json:
                json_findings = load_json_findings(output_dir)
                created = 0

                for finding_id in result.only_in_json:
                    if finding_id not in json_findings:
                        continue

                    finding_data = json_findings[finding_id]
                    try:
                        # Determine finding type from ID
                        finding_type = 'risk'
                        if finding_id.startswith('WI-'):
                            finding_type = 'work_item'
                        elif finding_id.startswith('REC-'):
                            finding_type = 'recommendation'

                        db_finding = DBFinding(
                            id=finding_id,
                            deal_id=default_deal.id,
                            finding_type=finding_type,
                            domain=finding_data.get('domain', 'unknown'),
                            title=finding_data.get('title', finding_data.get('description', '')),
                            description=finding_data.get('description', ''),
                            severity=finding_data.get('severity'),
                            phase=finding_data.get('phase'),
                            based_on_facts=finding_data.get('based_on_facts', []),
                        )
                        db.session.add(db_finding)
                        created += 1
                    except Exception as e:
                        print(f"  Error creating finding {finding_id}: {e}")

                db.session.commit()
                print(f"  Created {created} findings in PostgreSQL")


def print_summary(results: List[ReconciliationResult]):
    """Print reconciliation summary."""
    print("\n" + "=" * 60)
    print("RECONCILIATION SUMMARY")
    print("=" * 60)

    all_synced = True
    for result in results:
        status = "✓ SYNCED" if result.is_synced else "⚠ DRIFT DETECTED"
        print(f"\n{result.entity_type.upper()}: {status}")
        print(f"  JSON count:      {result.json_count}")
        print(f"  DB count:        {result.db_count}")
        print(f"  Matched:         {result.matched}")
        print(f"  Only in JSON:    {len(result.only_in_json)}")
        print(f"  Only in DB:      {len(result.only_in_db)}")
        print(f"  Value mismatch:  {len(result.value_mismatches)}")

        if not result.is_synced:
            all_synced = False

    print("\n" + "=" * 60)
    if all_synced:
        print("All data is synchronized between JSON and PostgreSQL")
    else:
        print("DRIFT DETECTED - Run with --fix to synchronize")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Reconcile JSON and PostgreSQL data')
    parser.add_argument('--fix', action='store_true', help='Fix discrepancies by syncing JSON to DB')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--json-dir', type=str, help='Path to JSON data directory')
    args = parser.parse_args()

    # Get output directory
    if args.json_dir:
        output_dir = Path(args.json_dir)
    else:
        from config_v2 import OUTPUT_DIR
        output_dir = OUTPUT_DIR

    print("=" * 60)
    print("JSON/PostgreSQL Reconciliation")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    app = create_app()
    results = []

    # Reconcile facts
    facts_result = reconcile_facts(app, output_dir, verbose=args.verbose)
    results.append(facts_result)

    # Reconcile findings
    findings_result = reconcile_findings(app, output_dir, verbose=args.verbose)
    results.append(findings_result)

    # Print summary
    print_summary(results)

    # Fix if requested
    if args.fix:
        fix_discrepancies(app, output_dir, results)

        # Re-run reconciliation to verify
        print("\n--- Verifying fix ---")
        results = []
        results.append(reconcile_facts(app, output_dir, verbose=False))
        results.append(reconcile_findings(app, output_dir, verbose=False))
        print_summary(results)


if __name__ == '__main__':
    main()
