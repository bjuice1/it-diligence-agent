#!/usr/bin/env python3
"""
Parse evidence quotes into proper details for application facts.
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.database import db, Fact
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

def parse_evidence(quote: str) -> dict:
    """Parse pipe-delimited evidence string into details dict."""
    if not quote:
        return {}

    parts = [p.strip() for p in quote.split('|')]

    # Expected format: Name | Vendor | Category | Version | Deployment | Users | Cost | Criticality
    details = {}

    if len(parts) >= 2:
        details['vendor'] = parts[1]
    if len(parts) >= 4:
        details['version'] = parts[3]
    if len(parts) >= 5:
        details['deployment'] = parts[4].lower()
        details['hosting'] = parts[4].lower()  # Alias
    if len(parts) >= 6:
        # Parse user count - remove commas
        try:
            details['user_count'] = int(parts[5].replace(',', ''))
            details['users'] = details['user_count']  # Alias
        except ValueError:
            pass
    if len(parts) >= 7:
        # Parse cost - remove $ and commas
        try:
            cost_str = parts[6].replace('$', '').replace(',', '')
            details['annual_cost'] = float(cost_str)
        except ValueError:
            pass
    if len(parts) >= 8:
        details['criticality'] = parts[7].upper()
        details['business_criticality'] = parts[7].upper()  # Alias

    return details

def enrich_apps(deal_id: str):
    app = create_app()

    with app.app_context():
        # Get all application facts with empty details
        facts = Fact.query.filter_by(
            deal_id=deal_id,
            domain='applications'
        ).all()

        updated = 0
        for fact in facts:
            # Skip if already has details
            if fact.details and fact.details.get('vendor'):
                continue

            # Try to parse from evidence
            evidence = fact.evidence or {}
            quote = evidence.get('exact_quote', '')

            if not quote or '|' not in quote:
                continue

            new_details = parse_evidence(quote)

            if new_details:
                # Merge with existing details
                merged = {**(fact.details or {}), **new_details}
                fact.details = merged
                updated += 1
                print(f"Updated: {fact.item} -> vendor={new_details.get('vendor')}, users={new_details.get('user_count')}")

        db.session.commit()
        print(f"\nEnriched {updated} application facts")

        # Verify
        print("\nSample enriched apps:")
        for fact in Fact.query.filter_by(deal_id=deal_id, domain='applications').limit(10):
            d = fact.details or {}
            print(f"  {fact.item}: vendor={d.get('vendor')}, users={d.get('user_count')}, cost={d.get('annual_cost')}")

if __name__ == '__main__':
    enrich_apps('20260204-142146')
