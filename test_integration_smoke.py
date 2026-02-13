#!/usr/bin/env python3
"""
Quick smoke test for domain model integration.

Verifies that the integration function works with minimal data.
"""

from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from main_v2 import integrate_domain_model


def test_integration_smoke():
    """Smoke test: Integration function runs without errors."""

    # Create minimal stores
    fact_store = FactStore(deal_id="test-integration")
    inventory_store = InventoryStore(deal_id="test-integration")

    # Add one application fact
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="Salesforce",
        details={"vendor": "Salesforce", "cost": 50000},
        status="documented",
        evidence={"exact_quote": "Salesforce CRM"},
        entity="target",
        deal_id="test-integration"
    )

    # Run integration
    stats = integrate_domain_model(
        fact_store=fact_store,
        inventory_store=inventory_store,
        domains=["applications"]
    )

    # Verify stats
    assert stats["applications_created"] > 0, "Should create at least one application"
    assert stats["applications_synced"] > 0, "Should sync at least one application"

    # Verify inventory was populated
    items = inventory_store.get_items(inventory_type="application", entity="target")
    assert len(items) > 0, "InventoryStore should have application items"

    print("✅ Integration smoke test PASSED")
    print(f"   Applications created: {stats['applications_created']}")
    print(f"   Applications synced: {stats['applications_synced']}")
    print(f"   Inventory items: {len(items)}")
    return stats


if __name__ == "__main__":
    test_integration_smoke()
