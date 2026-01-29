#!/usr/bin/env python3
"""
JSON to PostgreSQL Migration Script

Migrates existing JSON-based data to the PostgreSQL database.
Includes progress tracking and verification.

Usage:
    python scripts/migrate_json_to_db.py [--dry-run] [--verify-only]

Options:
    --dry-run       Show what would be migrated without actually doing it
    --verify-only   Only run verification on existing data
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / 'docker' / '.env')
load_dotenv(project_root / '.env')


def create_app():
    """Create Flask app for migration."""
    from flask import Flask
    from web.database import db, init_db

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'migration-key')
    init_db(app)

    return app


class MigrationProgress:
    """Track migration progress."""

    def __init__(self):
        self.started_at = datetime.utcnow()
        self.stats = {
            'users': {'found': 0, 'migrated': 0, 'errors': 0},
            'deals': {'found': 0, 'migrated': 0, 'errors': 0},
            'documents': {'found': 0, 'migrated': 0, 'errors': 0},
            'facts': {'found': 0, 'migrated': 0, 'errors': 0},
            'findings': {'found': 0, 'migrated': 0, 'errors': 0},
        }
        self.errors: List[str] = []

    def record(self, entity_type: str, status: str):
        if entity_type in self.stats:
            self.stats[entity_type][status] += 1

    def add_error(self, message: str):
        self.errors.append(message)

    def print_summary(self):
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)

        for entity, counts in self.stats.items():
            print(f"\n{entity.upper()}:")
            print(f"  Found:    {counts['found']}")
            print(f"  Migrated: {counts['migrated']}")
            print(f"  Errors:   {counts['errors']}")

        if self.errors:
            print(f"\n{len(self.errors)} ERRORS:")
            for err in self.errors[:10]:
                print(f"  - {err}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        duration = (datetime.utcnow() - self.started_at).total_seconds()
        print(f"\nTotal time: {duration:.2f} seconds")


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def find_json_data_files(output_dir: Path) -> Dict[str, List[Path]]:
    """Find all JSON data files to migrate."""
    files = {
        'users': [],
        'facts': [],
        'findings': [],
        'documents': [],
    }

    # Users file
    users_file = output_dir.parent / 'data' / 'users.json'
    if users_file.exists():
        files['users'].append(users_file)

    # Look for session-based output directories
    for session_dir in output_dir.glob('*'):
        if not session_dir.is_dir():
            continue

        # Facts directory
        facts_dir = session_dir / 'facts'
        if facts_dir.exists():
            files['facts'].extend(facts_dir.glob('*.json'))

        # Findings directory
        findings_dir = session_dir / 'findings'
        if findings_dir.exists():
            files['findings'].extend(findings_dir.glob('*.json'))

        # Check for domain-specific files
        for domain in ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']:
            domain_facts = session_dir / f'{domain}_facts.json'
            if domain_facts.exists():
                files['facts'].append(domain_facts)

            domain_findings = session_dir / f'{domain}_findings.json'
            if domain_findings.exists():
                files['findings'].append(domain_findings)

    return files


def migrate_users(app, progress: MigrationProgress, dry_run: bool = False):
    """Migrate users from JSON to database."""
    from web.database import db, User, Tenant
    from web.models.user import UserStore

    print("\n--- Migrating Users ---")

    with app.app_context():
        # Try to load from UserStore
        try:
            user_store = UserStore()
            json_users = user_store.list_users()
        except Exception as e:
            print(f"  Could not load users from UserStore: {e}")
            json_users = []

        progress.stats['users']['found'] = len(json_users)

        for json_user in json_users:
            try:
                # Check if user already exists in DB
                existing = User.query.filter_by(email=json_user.email).first()
                if existing:
                    print(f"  User {json_user.email} already exists, skipping")
                    continue

                if dry_run:
                    print(f"  [DRY RUN] Would migrate user: {json_user.email}")
                    progress.record('users', 'migrated')
                    continue

                # Get or create default tenant
                tenant = Tenant.query.filter_by(slug='default').first()
                if not tenant:
                    tenant = Tenant(name='Default', slug='default', plan='professional')
                    db.session.add(tenant)
                    db.session.flush()

                # Create user in database
                db_user = User(
                    id=json_user.id,
                    email=json_user.email,
                    password_hash=json_user.password_hash,
                    name=json_user.name,
                    roles=json_user.roles,
                    active=json_user.active,
                    tenant_id=tenant.id,
                    created_at=datetime.fromisoformat(json_user.created_at) if json_user.created_at else datetime.utcnow(),
                )
                db.session.add(db_user)
                db.session.commit()

                print(f"  Migrated user: {json_user.email}")
                progress.record('users', 'migrated')

            except Exception as e:
                progress.record('users', 'errors')
                progress.add_error(f"User {json_user.email}: {e}")
                db.session.rollback()


def migrate_facts(app, progress: MigrationProgress, files: List[Path], dry_run: bool = False):
    """Migrate facts from JSON files to database."""
    from web.database import db, Fact, Deal

    print("\n--- Migrating Facts ---")

    with app.app_context():
        # Get or create a default deal for orphaned facts
        default_deal = Deal.query.first()
        if not default_deal and not dry_run:
            default_deal = Deal(
                name='Migrated Data',
                target_name='Migration Import',
                deal_type='acquisition',
                status='active'
            )
            db.session.add(default_deal)
            db.session.commit()

        for file_path in files:
            try:
                data = load_json_file(file_path)
                facts_list = data if isinstance(data, list) else data.get('facts', [])

                for fact_data in facts_list:
                    progress.stats['facts']['found'] += 1

                    fact_id = fact_data.get('fact_id') or fact_data.get('id')
                    if not fact_id:
                        continue

                    # Check if already exists
                    existing = Fact.query.get(fact_id)
                    if existing:
                        continue

                    if dry_run:
                        print(f"  [DRY RUN] Would migrate fact: {fact_id}")
                        progress.record('facts', 'migrated')
                        continue

                    # Map JSON fields to database model
                    db_fact = Fact(
                        id=fact_id,
                        deal_id=default_deal.id if default_deal else None,
                        domain=fact_data.get('domain', 'unknown'),
                        category=fact_data.get('category', ''),
                        entity=fact_data.get('entity', 'target'),
                        item=fact_data.get('item', ''),
                        status=fact_data.get('status', 'documented'),
                        details=fact_data.get('details', {}),
                        evidence=fact_data.get('evidence', {}),
                        source_document=fact_data.get('source_document', ''),
                        confidence_score=fact_data.get('confidence_score', 0.5),
                        verified=fact_data.get('verified', False),
                        verification_status=fact_data.get('verification_status', 'pending'),
                    )
                    db.session.add(db_fact)
                    progress.record('facts', 'migrated')

                db.session.commit()
                print(f"  Processed: {file_path.name}")

            except Exception as e:
                progress.record('facts', 'errors')
                progress.add_error(f"Facts file {file_path}: {e}")
                db.session.rollback()


def migrate_findings(app, progress: MigrationProgress, files: List[Path], dry_run: bool = False):
    """Migrate findings from JSON files to database."""
    from web.database import db, Finding, Deal

    print("\n--- Migrating Findings ---")

    with app.app_context():
        default_deal = Deal.query.first()

        for file_path in files:
            try:
                data = load_json_file(file_path)

                # Handle different file structures
                findings_list = []
                if isinstance(data, list):
                    findings_list = data
                elif 'risks' in data:
                    findings_list.extend(data.get('risks', []))
                elif 'work_items' in data:
                    findings_list.extend(data.get('work_items', []))
                elif 'findings' in data:
                    findings_list.extend(data.get('findings', []))

                for finding_data in findings_list:
                    progress.stats['findings']['found'] += 1

                    finding_id = finding_data.get('finding_id') or finding_data.get('id') or finding_data.get('risk_id')
                    if not finding_id:
                        continue

                    existing = Finding.query.get(finding_id)
                    if existing:
                        continue

                    if dry_run:
                        print(f"  [DRY RUN] Would migrate finding: {finding_id}")
                        progress.record('findings', 'migrated')
                        continue

                    # Determine finding type from ID prefix or data
                    finding_type = finding_data.get('finding_type', 'risk')
                    if finding_id.startswith('R-'):
                        finding_type = 'risk'
                    elif finding_id.startswith('WI-'):
                        finding_type = 'work_item'
                    elif finding_id.startswith('REC-'):
                        finding_type = 'recommendation'

                    db_finding = Finding(
                        id=finding_id,
                        deal_id=default_deal.id if default_deal else None,
                        finding_type=finding_type,
                        domain=finding_data.get('domain', 'unknown'),
                        title=finding_data.get('title', finding_data.get('description', '')),
                        description=finding_data.get('description', ''),
                        severity=finding_data.get('severity'),
                        phase=finding_data.get('phase'),
                        based_on_facts=finding_data.get('based_on_facts', []),
                    )
                    db.session.add(db_finding)
                    progress.record('findings', 'migrated')

                db.session.commit()
                print(f"  Processed: {file_path.name}")

            except Exception as e:
                progress.record('findings', 'errors')
                progress.add_error(f"Findings file {file_path}: {e}")
                db.session.rollback()


def verify_migration(app, progress: MigrationProgress):
    """Verify migrated data matches source."""
    from web.database import db, User, Deal, Fact, Finding

    print("\n--- Verifying Migration ---")

    with app.app_context():
        db_counts = {
            'users': User.query.count(),
            'deals': Deal.query.count(),
            'facts': Fact.query.filter(Fact.deleted_at.is_(None)).count(),
            'findings': Finding.query.filter(Finding.deleted_at.is_(None)).count(),
        }

        print("\nDatabase Counts:")
        for entity, count in db_counts.items():
            json_count = progress.stats.get(entity, {}).get('found', 0)
            migrated = progress.stats.get(entity, {}).get('migrated', 0)
            status = "✓" if count >= migrated else "⚠"
            print(f"  {status} {entity}: {count} in DB (migrated {migrated} of {json_count} found)")


def main():
    parser = argparse.ArgumentParser(description='Migrate JSON data to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing data')
    args = parser.parse_args()

    from config_v2 import OUTPUT_DIR

    print("=" * 60)
    print("JSON to PostgreSQL Migration")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    if args.dry_run:
        print("MODE: Dry run (no changes will be made)")

    app = create_app()
    progress = MigrationProgress()

    # Find data files
    files = find_json_data_files(OUTPUT_DIR)
    print(f"\nFiles found:")
    for entity, file_list in files.items():
        print(f"  {entity}: {len(file_list)} files")

    if not args.verify_only:
        # Run migrations
        migrate_users(app, progress, dry_run=args.dry_run)
        migrate_facts(app, progress, files['facts'], dry_run=args.dry_run)
        migrate_findings(app, progress, files['findings'], dry_run=args.dry_run)

    # Verify
    verify_migration(app, progress)

    # Print summary
    progress.print_summary()


if __name__ == '__main__':
    main()
