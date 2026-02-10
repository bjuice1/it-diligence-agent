#!/usr/bin/env python3
"""
Import facts from JSON file into the database - v2 with better error handling.
"""
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from web.database import db, Deal, Fact
from flask import Flask

def create_minimal_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://diligence:diligence@postgres:5432/diligence'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def import_facts(json_path: str, deal_name: str = None):
    with open(json_path, 'r') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    facts_list = data.get('facts', [])

    print(f"Loaded {len(facts_list)} facts from {json_path}")

    app = create_minimal_app()

    with app.app_context():
        deal_id = metadata.get('deal_id', 'test-deal').replace('session-', '')
        target_name = deal_name or 'National Mutual'

        # Get or create deal
        deal = Deal.query.filter_by(id=deal_id).first()
        if not deal:
            deal = Deal.query.filter_by(target_name=target_name).first()
        if not deal:
            deal = Deal(
                id=deal_id,
                target_name=target_name,
                deal_type='acquisition',
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(deal)
            db.session.commit()
            print(f"Created deal: {deal.id}")
        else:
            print(f"Using deal: {deal.id}")

        # Clear ALL existing facts for this deal
        deleted = Fact.query.filter_by(deal_id=deal.id).delete()
        db.session.commit()
        print(f"Cleared {deleted} existing facts")

        # Track used IDs to avoid duplicates
        used_ids = set()
        imported = 0
        errors = []

        for i, fact_data in enumerate(facts_list):
            try:
                # Generate unique ID if duplicate
                fact_id = fact_data.get('fact_id', f'F-IMP-{i:03d}')
                if fact_id in used_ids:
                    fact_id = f"{fact_id}-{uuid.uuid4().hex[:6]}"
                used_ids.add(fact_id)

                fact = Fact(
                    id=fact_id,
                    deal_id=deal.id,
                    domain=fact_data.get('domain', 'general'),
                    category=fact_data.get('category', ''),
                    entity=fact_data.get('entity', 'target'),
                    item=fact_data.get('item', ''),
                    status=fact_data.get('status', 'documented'),
                    details=fact_data.get('details', {}),
                    evidence=fact_data.get('evidence', {}),
                    source_document=fact_data.get('source_document', ''),
                    confidence_score=fact_data.get('confidence_score', 0.5),
                    analysis_phase=fact_data.get('analysis_phase', 'target_extraction'),
                    is_integration_insight=fact_data.get('is_integration_insight', False),
                    related_domains=fact_data.get('related_domains', []),
                    verified=fact_data.get('verified', False),
                    verification_status=fact_data.get('verification_status', 'pending'),
                    created_at=datetime.utcnow()
                )
                db.session.add(fact)
                imported += 1

                # Commit every 20 facts to catch errors early
                if imported % 20 == 0:
                    db.session.commit()
                    print(f"  ... imported {imported}")

            except Exception as e:
                errors.append(f"{fact_data.get('fact_id')}: {e}")
                db.session.rollback()

        # Final commit
        db.session.commit()

        print(f"\nImported {imported} facts")
        if errors:
            print(f"Errors ({len(errors)}):")
            for err in errors[:10]:
                print(f"  {err}")

        # Verify by domain
        print("\nFacts by domain:")
        from sqlalchemy import func
        results = db.session.query(
            Fact.domain, func.count(Fact.id)
        ).filter_by(deal_id=deal.id).group_by(Fact.domain).all()
        for domain, count in results:
            print(f"  {domain}: {count}")

        return deal.id

if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else '/app/facts_import.json'
    deal_name = sys.argv[2] if len(sys.argv) > 2 else 'National Mutual'
    import_facts(json_path, deal_name)
