#!/usr/bin/env python3
"""
Import facts from JSON file into the database for testing.
"""
import json
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from web.database import db, Deal, Fact
from flask import Flask

def create_minimal_app():
    """Create minimal Flask app for database operations."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://diligence:diligence@postgres:5432/diligence'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def import_facts(json_path: str, deal_name: str = None):
    """Import facts from JSON file."""

    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    metadata = data.get('metadata', {})
    facts_list = data.get('facts', [])

    print(f"Loaded {len(facts_list)} facts from {json_path}")
    print(f"Deal ID in file: {metadata.get('deal_id')}")

    app = create_minimal_app()

    with app.app_context():
        # Create or get deal
        deal_id = metadata.get('deal_id', 'test-deal')
        target_name = deal_name or 'National Mutual'

        existing_deal = Deal.query.filter_by(target_name=target_name).first()
        if existing_deal:
            deal = existing_deal
            print(f"Using existing deal: {deal.id} - {deal.target_name}")
        else:
            deal = Deal(
                id=deal_id.replace('session-', ''),  # Clean up ID
                target_name=target_name,
                deal_type='acquisition',
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(deal)
            db.session.commit()
            print(f"Created deal: {deal.id} - {deal.target_name}")

        # Clear existing facts for this deal
        deleted = Fact.query.filter_by(deal_id=deal.id).delete()
        if deleted:
            print(f"Cleared {deleted} existing facts")

        # Import facts
        imported = 0
        skipped = 0
        for fact_data in facts_list:
            try:
                fact = Fact(
                    id=fact_data.get('fact_id', f'F-IMP-{imported:03d}'),
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
            except Exception as e:
                print(f"Error importing fact {fact_data.get('fact_id')}: {e}")
                skipped += 1

        db.session.commit()
        print(f"\nImported {imported} facts, skipped {skipped}")
        print(f"Deal ID for testing: {deal.id}")

        # Verify
        count = Fact.query.filter_by(deal_id=deal.id).count()
        print(f"Verified: {count} facts in database for deal {deal.id}")

        return deal.id

if __name__ == '__main__':
    json_path = sys.argv[1] if len(sys.argv) > 1 else '/app/output/facts_20260204_142146.json'
    deal_name = sys.argv[2] if len(sys.argv) > 2 else 'National Mutual'

    deal_id = import_facts(json_path, deal_name)
    print(f"\nDeal ID: {deal_id}")
