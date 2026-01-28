"""
Data Migration Script for Phase 3

Migrates data from JSON files to PostgreSQL/SQLite database.
Supports:
- One-time full migration
- Incremental sync (dual-write validation)
- Rollback to JSON if needed
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_v2 import OUTPUT_DIR, DATA_DIR


def migrate_users(app, db):
    """Migrate users from JSON file to database."""
    from web.database import User

    users_file = DATA_DIR / "users.json"
    if not users_file.exists():
        print("No users.json file found, skipping user migration")
        return 0

    with open(users_file, 'r') as f:
        data = json.load(f)

    migrated = 0
    for user_data in data.get('users', []):
        # Check if user already exists
        existing = User.query.filter_by(email=user_data['email']).first()
        if existing:
            print(f"  User {user_data['email']} already exists, skipping")
            continue

        user = User(
            id=user_data['id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            name=user_data.get('name', ''),
            roles=user_data.get('roles', ['analyst']),
            active=user_data.get('active', True),
            created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow(),
            last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None,
        )
        db.session.add(user)
        migrated += 1

    db.session.commit()
    print(f"  Migrated {migrated} users")
    return migrated


def migrate_facts_from_file(app, db, facts_file: Path, deal_id: str):
    """Migrate facts from a JSON file to database."""
    from web.database import Fact

    if not facts_file.exists():
        return 0

    with open(facts_file, 'r') as f:
        data = json.load(f)

    facts_data = data.get('facts', [])
    if not facts_data:
        return 0

    migrated = 0
    for fact_data in facts_data:
        fact_id = fact_data.get('fact_id')
        if not fact_id:
            continue

        # Check if fact already exists
        existing = Fact.query.filter_by(id=fact_id, deal_id=deal_id).first()
        if existing:
            continue

        fact = Fact(
            id=fact_id,
            deal_id=deal_id,
            domain=fact_data.get('domain', 'general'),
            category=fact_data.get('category', ''),
            entity=fact_data.get('entity', 'target'),
            item=fact_data.get('item', ''),
            status=fact_data.get('status', 'documented'),
            details=fact_data.get('details', {}),
            evidence=fact_data.get('evidence', {}),
            source_document=fact_data.get('source_document', ''),
            confidence_score=fact_data.get('confidence_score', 0.5),
            verified=fact_data.get('verified', False),
            verified_by=fact_data.get('verified_by'),
            verified_at=datetime.fromisoformat(fact_data['verified_at']) if fact_data.get('verified_at') else None,
            verification_status=fact_data.get('verification_status', 'pending'),
            verification_note=fact_data.get('verification_note', ''),
            needs_review=fact_data.get('needs_review', False),
            needs_review_reason=fact_data.get('needs_review_reason', ''),
            analysis_phase=fact_data.get('analysis_phase', 'target_extraction'),
            is_integration_insight=fact_data.get('is_integration_insight', False),
            related_domains=fact_data.get('related_domains', []),
            created_at=datetime.fromisoformat(fact_data['created_at']) if fact_data.get('created_at') else datetime.utcnow(),
        )
        db.session.add(fact)
        migrated += 1

    db.session.commit()
    return migrated


def migrate_findings_from_file(app, db, findings_file: Path, deal_id: str):
    """Migrate findings (risks, work items, etc.) from JSON file to database."""
    from web.database import Finding

    if not findings_file.exists():
        return 0

    with open(findings_file, 'r') as f:
        data = json.load(f)

    migrated = 0

    # Migrate risks
    for risk_data in data.get('risks', []):
        finding_id = risk_data.get('finding_id')
        if not finding_id:
            continue

        existing = Finding.query.filter_by(id=finding_id, deal_id=deal_id).first()
        if existing:
            continue

        finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            finding_type='risk',
            domain=risk_data.get('domain', 'general'),
            title=risk_data.get('title', ''),
            description=risk_data.get('description', ''),
            reasoning=risk_data.get('reasoning', ''),
            confidence=risk_data.get('confidence', 'medium'),
            mna_lens=risk_data.get('mna_lens', ''),
            mna_implication=risk_data.get('mna_implication', ''),
            based_on_facts=risk_data.get('based_on_facts', []),
            severity=risk_data.get('severity'),
            category=risk_data.get('category', ''),
            mitigation=risk_data.get('mitigation', ''),
            integration_dependent=risk_data.get('integration_dependent', False),
            timeline=risk_data.get('timeline'),
            created_at=datetime.fromisoformat(risk_data['created_at']) if risk_data.get('created_at') else datetime.utcnow(),
        )
        db.session.add(finding)
        migrated += 1

    # Migrate work items
    for wi_data in data.get('work_items', []):
        finding_id = wi_data.get('finding_id')
        if not finding_id:
            continue

        existing = Finding.query.filter_by(id=finding_id, deal_id=deal_id).first()
        if existing:
            continue

        finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            finding_type='work_item',
            domain=wi_data.get('domain', 'general'),
            title=wi_data.get('title', ''),
            description=wi_data.get('description', ''),
            reasoning=wi_data.get('reasoning', ''),
            confidence=wi_data.get('confidence', 'medium'),
            mna_lens=wi_data.get('mna_lens', ''),
            mna_implication=wi_data.get('mna_implication', ''),
            based_on_facts=wi_data.get('based_on_facts', []),
            phase=wi_data.get('phase'),
            priority=wi_data.get('priority'),
            owner_type=wi_data.get('owner_type'),
            cost_estimate=wi_data.get('cost_estimate'),
            triggered_by_risks=wi_data.get('triggered_by_risks', []),
            dependencies=wi_data.get('dependencies', []),
            created_at=datetime.fromisoformat(wi_data['created_at']) if wi_data.get('created_at') else datetime.utcnow(),
        )
        db.session.add(finding)
        migrated += 1

    # Migrate recommendations
    for rec_data in data.get('recommendations', []):
        finding_id = rec_data.get('finding_id')
        if not finding_id:
            continue

        existing = Finding.query.filter_by(id=finding_id, deal_id=deal_id).first()
        if existing:
            continue

        finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            finding_type='recommendation',
            domain=rec_data.get('domain', 'general'),
            title=rec_data.get('title', ''),
            description=rec_data.get('description', ''),
            reasoning=rec_data.get('reasoning', ''),
            confidence=rec_data.get('confidence', 'medium'),
            mna_lens=rec_data.get('mna_lens', ''),
            mna_implication=rec_data.get('mna_implication', ''),
            based_on_facts=rec_data.get('based_on_facts', []),
            action_type=rec_data.get('action_type'),
            urgency=rec_data.get('urgency'),
            rationale=rec_data.get('rationale', ''),
            created_at=datetime.fromisoformat(rec_data['created_at']) if rec_data.get('created_at') else datetime.utcnow(),
        )
        db.session.add(finding)
        migrated += 1

    # Migrate strategic considerations
    for sc_data in data.get('strategic_considerations', []):
        finding_id = sc_data.get('finding_id')
        if not finding_id:
            continue

        existing = Finding.query.filter_by(id=finding_id, deal_id=deal_id).first()
        if existing:
            continue

        finding = Finding(
            id=finding_id,
            deal_id=deal_id,
            finding_type='strategic_consideration',
            domain=sc_data.get('domain', 'general'),
            title=sc_data.get('title', ''),
            description=sc_data.get('description', ''),
            reasoning=sc_data.get('reasoning', ''),
            confidence=sc_data.get('confidence', 'medium'),
            mna_lens=sc_data.get('mna_lens', ''),
            mna_implication=sc_data.get('mna_implication', ''),
            based_on_facts=sc_data.get('based_on_facts', []),
            lens=sc_data.get('lens'),
            implication=sc_data.get('implication', ''),
            created_at=datetime.fromisoformat(sc_data['created_at']) if sc_data.get('created_at') else datetime.utcnow(),
        )
        db.session.add(finding)
        migrated += 1

    db.session.commit()
    return migrated


def find_latest_analysis_files() -> Dict[str, Path]:
    """Find the latest facts and findings files in the output directory."""
    files = {}

    # Find latest facts file
    facts_files = list(OUTPUT_DIR.glob("facts_*.json"))
    if facts_files:
        files['facts'] = max(facts_files, key=lambda p: p.stat().st_mtime)

    # Find latest findings file
    findings_files = list(OUTPUT_DIR.glob("findings_*.json"))
    if findings_files:
        files['findings'] = max(findings_files, key=lambda p: p.stat().st_mtime)

    # Find latest deal context
    context_files = list(OUTPUT_DIR.glob("deal_context_*.json"))
    if context_files:
        files['context'] = max(context_files, key=lambda p: p.stat().st_mtime)

    return files


def run_migration(app=None):
    """Run the full data migration."""
    if app is None:
        # Create app context
        from web.app import app

    from web.database import db, Deal

    print("=" * 60)
    print("IT Due Diligence - Data Migration to Database")
    print("=" * 60)

    with app.app_context():
        # 1. Migrate users
        print("\n1. Migrating users...")
        migrate_users(app, db)

        # 2. Find latest analysis files
        print("\n2. Finding analysis files...")
        files = find_latest_analysis_files()

        if not files:
            print("  No analysis files found in output directory")
            return

        for name, path in files.items():
            print(f"  Found {name}: {path.name}")

        # 3. Create or get deal
        print("\n3. Creating deal record...")

        # Load deal context if available
        deal_context = {}
        if 'context' in files:
            with open(files['context'], 'r') as f:
                deal_context = json.load(f)

        # Check if deal already exists
        target_name = deal_context.get('target_name', 'Default Target')
        existing_deal = Deal.query.filter_by(target_name=target_name).first()

        if existing_deal:
            deal = existing_deal
            print(f"  Using existing deal: {deal.target_name} (ID: {deal.id})")
        else:
            deal = Deal(
                target_name=target_name,
                buyer_name=deal_context.get('buyer_name', ''),
                deal_type=deal_context.get('deal_type', 'acquisition'),
                industry=deal_context.get('industry', ''),
                context=deal_context,
            )
            db.session.add(deal)
            db.session.commit()
            print(f"  Created deal: {deal.target_name} (ID: {deal.id})")

        # 4. Migrate facts
        if 'facts' in files:
            print("\n4. Migrating facts...")
            facts_count = migrate_facts_from_file(app, db, files['facts'], deal.id)
            print(f"  Migrated {facts_count} facts")

        # 5. Migrate findings
        if 'findings' in files:
            print("\n5. Migrating findings...")
            findings_count = migrate_findings_from_file(app, db, files['findings'], deal.id)
            print(f"  Migrated {findings_count} findings")

        print("\n" + "=" * 60)
        print("Migration complete!")
        print("=" * 60)

        # Summary
        from web.database import Fact, Finding
        print(f"\nDatabase summary:")
        print(f"  Deals: {Deal.query.count()}")
        print(f"  Facts: {Fact.query.count()}")
        print(f"  Findings: {Finding.query.count()}")


def verify_migration(app=None):
    """Verify that migration was successful by comparing counts."""
    if app is None:
        from web.app import app

    from web.database import db, Fact, Finding

    print("\nVerifying migration...")

    with app.app_context():
        # Count database records
        db_facts = Fact.query.count()
        db_findings = Finding.query.count()

        # Count JSON records
        files = find_latest_analysis_files()

        json_facts = 0
        if 'facts' in files:
            with open(files['facts'], 'r') as f:
                data = json.load(f)
                json_facts = len(data.get('facts', []))

        json_findings = 0
        if 'findings' in files:
            with open(files['findings'], 'r') as f:
                data = json.load(f)
                json_findings = (
                    len(data.get('risks', [])) +
                    len(data.get('work_items', [])) +
                    len(data.get('recommendations', [])) +
                    len(data.get('strategic_considerations', []))
                )

        print(f"  Facts: JSON={json_facts}, DB={db_facts}, Match={json_facts == db_facts}")
        print(f"  Findings: JSON={json_findings}, DB={db_findings}, Match={json_findings == db_findings}")

        return json_facts == db_facts and json_findings == db_findings


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate data to database')
    parser.add_argument('--verify', action='store_true', help='Verify migration')
    args = parser.parse_args()

    # Need to enable database for migration
    os.environ['USE_DATABASE'] = 'true'

    from web.app import app

    if args.verify:
        verify_migration(app)
    else:
        run_migration(app)
