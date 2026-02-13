#!/usr/bin/env python3
"""
Demo: P0-3 Deduplication Fix

Shows that domain model correctly deduplicates variant names:
- "Salesforce" and "salesforce" → 1 application (not 2)
- "SAP ERP" and "SAP SuccessFactors" → 2 applications (not colliding)

This demonstrates the fix for P0-3 normalization collision bug.
"""

from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from main_v2 import integrate_domain_model


def demo_p0_3_deduplication_fix():
    """Demo showing P0-3 fix: proper deduplication without collisions."""

    print("\n" + "="*70)
    print("DEMO: P0-3 Deduplication Fix (Domain Model Integration)")
    print("="*70)

    # Create stores
    fact_store = FactStore(deal_id="demo-p0-3")
    inventory_store = InventoryStore(deal_id="demo-p0-3")

    print("\n[SETUP] Adding facts with variant names...\n")

    # Scenario 1: Case variants (should deduplicate to 1 app)
    print("Scenario 1: Case Variants")
    print("  Adding: 'Salesforce' (vendor: Salesforce)")
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="Salesforce",
        details={"vendor": "Salesforce", "cost": 50000},
        status="documented",
        evidence={"exact_quote": "Page 1: Salesforce CRM"},
        entity="target",
        deal_id="demo-p0-3"
    )

    print("  Adding: 'salesforce' (vendor: Salesforce) ← case variant")
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="salesforce",
        details={"vendor": "Salesforce", "users": 1200},
        status="documented",
        evidence={"exact_quote": "Page 2: salesforce deployment"},
        entity="target",
        deal_id="demo-p0-3"
    )

    print("  Adding: 'SALESFORCE' (vendor: Salesforce) ← case variant")
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="SALESFORCE",
        details={"vendor": "Salesforce", "version": "Enterprise"},
        status="documented",
        evidence={"exact_quote": "Page 3: SALESFORCE configuration"},
        entity="target",
        deal_id="demo-p0-3"
    )

    # Scenario 2: Different SAP products (should NOT deduplicate - different apps)
    print("\nScenario 2: Different Products (Same Vendor)")
    print("  Adding: 'SAP ERP' (vendor: SAP)")
    fact_store.add_fact(
        domain="applications",
        category="erp",
        item="SAP ERP",
        details={"vendor": "SAP", "cost": 200000},
        status="documented",
        evidence={"exact_quote": "SAP ERP system"},
        entity="target",
        deal_id="demo-p0-3"
    )

    print("  Adding: 'SAP SuccessFactors' (vendor: SAP) ← different product")
    fact_store.add_fact(
        domain="applications",
        category="hcm",
        item="SAP SuccessFactors",
        details={"vendor": "SAP", "cost": 150000},
        status="documented",
        evidence={"exact_quote": "SAP SuccessFactors HR"},
        entity="target",
        deal_id="demo-p0-3"
    )

    # Scenario 3: Same app, different entities (should NOT deduplicate - buyer vs target)
    print("\nScenario 3: Same App, Different Entities")
    print("  Adding: 'Microsoft Office' (vendor: Microsoft, entity: buyer)")
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="Microsoft Office",
        details={"vendor": "Microsoft", "cost": 30000},
        status="documented",
        evidence={"exact_quote": "Buyer uses Microsoft Office"},
        entity="buyer",
        deal_id="demo-p0-3"
    )

    print("  Adding: 'Microsoft Office' (vendor: Microsoft, entity: target)")
    fact_store.add_fact(
        domain="applications",
        category="saas",
        item="Microsoft Office",
        details={"vendor": "Microsoft", "cost": 25000},
        status="documented",
        evidence={"exact_quote": "Target uses Microsoft Office"},
        entity="target",
        deal_id="demo-p0-3"
    )

    print(f"\nTotal facts added: {len(fact_store.facts)}")
    print(f"  - Target entity: {len([f for f in fact_store.facts if f.entity == 'target'])}")
    print(f"  - Buyer entity: {len([f for f in fact_store.facts if f.entity == 'buyer'])}")

    # Run domain model integration
    print("\n[DOMAIN MODEL] Running deduplication...")
    stats = integrate_domain_model(
        fact_store=fact_store,
        inventory_store=inventory_store,
        domains=["applications"]
    )

    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    target_apps = inventory_store.get_items(inventory_type="application", entity="target")
    buyer_apps = inventory_store.get_items(inventory_type="application", entity="buyer")

    print(f"\n✅ Domain Model created {stats['applications_created']} unique applications")
    print(f"   - Target: {len(target_apps)} applications")
    print(f"   - Buyer: {len(buyer_apps)} applications")

    print("\n[TARGET APPLICATIONS]")
    for item in sorted(target_apps, key=lambda x: x.data.get("name", "")):
        name = item.data.get("name", "Unknown")
        vendor = item.data.get("vendor", "Unknown")
        obs_count = item.data.get("observation_count", 0)
        print(f"  • {name:30s} (vendor: {vendor:15s}, observations: {obs_count})")

    print("\n[BUYER APPLICATIONS]")
    for item in sorted(buyer_apps, key=lambda x: x.data.get("name", "")):
        name = item.data.get("name", "Unknown")
        vendor = item.data.get("vendor", "Unknown")
        obs_count = item.data.get("observation_count", 0)
        print(f"  • {name:30s} (vendor: {vendor:15s}, observations: {obs_count})")

    # Validate deduplication worked correctly
    print("\n" + "="*70)
    print("VALIDATION")
    print("="*70)

    # Check Scenario 1: 3 Salesforce facts → 1 application
    salesforce_items = [i for i in target_apps if "salesforce" in i.data.get("name", "").lower()]
    assert len(salesforce_items) == 1, f"Expected 1 Salesforce app, got {len(salesforce_items)}"
    assert salesforce_items[0].data.get("observation_count") == 3, "Should have 3 observations merged"
    print("✅ Scenario 1: Case variants deduplicated (3 facts → 1 app with 3 observations)")

    # Check Scenario 2: SAP ERP ≠ SAP SuccessFactors
    sap_items = [i for i in target_apps if i.data.get("vendor") == "SAP"]
    assert len(sap_items) == 2, f"Expected 2 SAP apps, got {len(sap_items)}"
    print("✅ Scenario 2: Different SAP products NOT colliding (2 distinct apps)")

    # Check Scenario 3: Same app, different entities
    target_office = [i for i in target_apps if "microsoft office" in i.data.get("name", "").lower()]
    buyer_office = [i for i in buyer_apps if "microsoft office" in i.data.get("name", "").lower()]
    assert len(target_office) == 1, "Should have 1 Microsoft Office in target"
    assert len(buyer_office) == 1, "Should have 1 Microsoft Office in buyer"
    print("✅ Scenario 3: Entity separation maintained (buyer ≠ target)")

    print("\n" + "="*70)
    print("P0-3 DEDUPLICATION FIX: VERIFIED ✅")
    print("="*70)
    print(f"\nOld system would have: {len(fact_store.facts)} items (no deduplication)")
    print(f"New system produces:   {stats['applications_created']} items (deduplicated)")
    print(f"Reduction: {len(fact_store.facts) - stats['applications_created']} duplicates eliminated")
    print("\nThis is the fix for P0-3 normalization collision bug! 🎉\n")


if __name__ == "__main__":
    demo_p0_3_deduplication_fix()
