#!/usr/bin/env python3
"""
Test the cost engine with real data from the database.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from web.database import db, Fact

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


def test_cost_engine(deal_id: str):
    """Test cost engine with deal data."""
    from services.cost_engine import (
        get_effective_drivers,
        calculate_deal_costs,
        generate_deal_costs_csv,
        generate_drivers_csv,
        generate_assumptions_csv,
    )
    from stores.fact_store import FactStore

    app = create_minimal_app()

    with app.app_context():
        # Load facts from database
        facts = Fact.query.filter_by(deal_id=deal_id).all()
        print(f"\n=== Loading facts from database ===")
        print(f"Deal: {deal_id}")
        print(f"Facts loaded: {len(facts)}")

        # Create a fact store from database facts
        fact_store = FactStore(deal_id=deal_id)
        for f in facts:
            fact_store.add_fact(
                domain=f.domain,
                category=f.category or '',
                item=f.item,
                details=f.details or {},
                status=f.status or 'documented',
                evidence=f.evidence or {},
                entity=f.entity or 'target',
                source_document=f.source_document or '',
            )

        print(f"FactStore populated: {len(fact_store.facts)} facts")

        # Test driver extraction
        print(f"\n=== Testing Driver Extraction ===")
        driver_result = get_effective_drivers(deal_id, fact_store, db_session=db.session)

        drivers = driver_result.drivers
        print(f"Drivers extracted: {driver_result.drivers_extracted}")
        print(f"Drivers assumed: {driver_result.drivers_assumed}")

        print(f"\nKey drivers:")
        print(f"  - Total Users: {drivers.total_users}")
        print(f"  - Sites: {drivers.sites}")
        print(f"  - Endpoints: {drivers.endpoints}")
        print(f"  - Applications: {drivers.total_apps}")
        print(f"  - ERP: {drivers.erp_system}")
        print(f"  - Identity Provider: {drivers.identity_provider}")
        print(f"  - Data Centers: {drivers.data_centers}")
        print(f"  - Cloud Provider: {drivers.cloud_provider}")

        # Test cost calculation
        print(f"\n=== Testing Cost Calculation ===")
        summary = calculate_deal_costs(deal_id, drivers)

        print(f"\nTotal Costs (One-Time):")
        print(f"  - Upside:  ${summary.total_one_time_upside:,.0f}")
        print(f"  - Base:    ${summary.total_one_time_base:,.0f}")
        print(f"  - Stress:  ${summary.total_one_time_stress:,.0f}")
        print(f"  - Annual:  ${summary.total_annual_licenses:,.0f}/yr")

        print(f"\nCosts by Tower:")
        for tower, costs in summary.tower_costs.items():
            print(f"  {tower}: ${costs['one_time_base']:,.0f} (base)")

        print(f"\nTop Assumptions:")
        for assumption in summary.top_assumptions[:5]:
            print(f"  - {assumption}")

        # Test CSV exports
        print(f"\n=== Testing CSV Exports ===")
        costs_csv = generate_deal_costs_csv(summary)
        drivers_csv = generate_drivers_csv(driver_result)  # Pass full result, not just drivers
        assumptions_csv = generate_assumptions_csv(summary, driver_result)

        print(f"Costs CSV: {len(costs_csv.splitlines())} lines")
        print(f"Drivers CSV: {len(drivers_csv.splitlines())} lines")
        print(f"Assumptions CSV: {len(assumptions_csv.splitlines())} lines")

        print("\n=== Sample Costs CSV ===")
        for line in costs_csv.splitlines()[:10]:
            print(line)

        print("\n=== COST ENGINE TEST PASSED ===")
        return True


if __name__ == '__main__':
    deal_id = sys.argv[1] if len(sys.argv) > 1 else '20260204-142146'
    success = test_cost_engine(deal_id)
    sys.exit(0 if success else 1)
