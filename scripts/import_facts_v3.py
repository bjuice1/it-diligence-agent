#!/usr/bin/env python3
"""
Import facts - v3 with single-record commits and proper ID handling.
"""
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from web.database import db, Deal, Fact
from flask import Flask

def create_app():
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

    facts_list = data.get('facts', [])
    print(f"Loaded {len(facts_list)} facts")

    app = create_app()

    with app.app_context():
        # Delete ALL facts for this deal first
        deal_id = '20260204-142146'
        Fact.query.filter_by(deal_id=deal_id).delete()
        db.session.commit()
        print("Cleared all existing facts")

        imported = 0
        for i, fact_data in enumerate(facts_list):
            # Generate unique ID using index
            fact_id = f"F-{i:04d}-{uuid.uuid4().hex[:8]}"

            try:
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
                    analysis_phase=fact_data.get('analysis_phase', 'target_extraction'),
                    is_integration_insight=fact_data.get('is_integration_insight', False),
                    related_domains=fact_data.get('related_domains', []),
                    verified=False,
                    verification_status='pending',
                    created_at=datetime.utcnow()
                )
                db.session.add(fact)
                db.session.commit()
                imported += 1
            except Exception as e:
                db.session.rollback()
                print(f"Error on fact {i}: {e}")

        print(f"\nImported {imported} of {len(facts_list)} facts")

        # Summary by domain
        from sqlalchemy import func
        print("\nBy domain:")
        for domain, count in db.session.query(Fact.domain, func.count()).filter_by(deal_id=deal_id).group_by(Fact.domain).all():
            print(f"  {domain}: {count}")

        print("\nBy category (applications):")
        for cat, count in db.session.query(Fact.category, func.count()).filter_by(deal_id=deal_id, domain='applications').group_by(Fact.category).all():
            print(f"  {cat}: {count}")

if __name__ == '__main__':
    import_facts(sys.argv[1] if len(sys.argv) > 1 else '/app/facts_import.json')
