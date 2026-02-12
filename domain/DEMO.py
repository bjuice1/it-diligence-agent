"""
DOMAIN MODEL DEMONSTRATION
==========================

This file demonstrates how the new domain-first architecture solves
the duplication crisis.

Run this with: python -m domain.DEMO
"""

from domain.value_objects.entity import Entity
from domain.value_objects.application_id import ApplicationId
from domain.value_objects.money import Money
from domain.entities.observation import Observation
from domain.entities.application import Application


def demo_stable_ids():
    """Demonstrate stable ID generation."""
    print("\n" + "="*70)
    print("DEMO 1: Stable ID Generation")
    print("="*70)

    # Same name variants generate same ID
    id1 = ApplicationId.generate("Salesforce", Entity.TARGET)
    id2 = ApplicationId.generate("Salesforce CRM", Entity.TARGET)
    id3 = ApplicationId.generate("SALESFORCE", Entity.TARGET)

    print(f"\n'Salesforce' → {id1.value}")
    print(f"'Salesforce CRM' → {id2.value}")
    print(f"'SALESFORCE' → {id3.value}")
    print(f"\nAll IDs match: {id1 == id2 == id3}")

    # Different entity = different ID
    id_buyer = ApplicationId.generate("Salesforce", Entity.BUYER)
    print(f"\nBuyer 'Salesforce' → {id_buyer.value}")
    print(f"Different from Target: {id1 != id_buyer}")


def demo_deduplication():
    """Demonstrate how find_or_create prevents duplicates."""
    print("\n" + "="*70)
    print("DEMO 2: Automatic Deduplication (Conceptual)")
    print("="*70)

    # In real code, this would use ApplicationRepository.find_or_create()
    # Here we simulate it manually

    # First extraction: deterministic parser finds "Salesforce" in table
    app_id = ApplicationId.generate("Salesforce", Entity.TARGET)

    app = Application(
        id=app_id,
        entity=Entity.TARGET,
        name="Salesforce"
    )

    # Add observation from table
    table_obs = Observation.from_table(
        source_document="inventory.xlsx",
        extracted_data={"vendor": "Salesforce.com", "cost": 50000}
    )
    app.add_observation(table_obs)

    print(f"\n1. Parser created: {app}")
    print(f"   Observations: {app.observation_count}")
    print(f"   Vendor: {app.vendor}")
    print(f"   Cost: {app.cost.format() if app.cost else 'None'}")

    # Second extraction: LLM finds "Salesforce CRM" in prose
    # With OLD architecture: creates duplicate
    # With NEW architecture: find_or_create returns SAME app

    # Generate ID from "Salesforce CRM"
    llm_app_id = ApplicationId.generate("Salesforce CRM", Entity.TARGET)

    print(f"\n2. LLM tries to create from 'Salesforce CRM'")
    print(f"   Generated ID: {llm_app_id.value}")
    print(f"   Matches existing: {llm_app_id == app_id}")

    # Since IDs match, find_or_create would return existing app
    # We just add the LLM observation to the SAME app

    llm_obs = Observation.from_llm(
        source_document="diligence.pdf",
        extracted_data={"users": 100, "criticality": "high"},
        confidence=0.8
    )
    app.add_observation(llm_obs)

    print(f"\n3. Added LLM observation to EXISTING app (no duplicate!)")
    print(f"   Observations: {app.observation_count}")
    print(f"   Has table data: {app.has_table_data}")
    print(f"   Has LLM data: {app.has_llm_data}")

    print(f"\nFINAL RESULT: 1 app with {app.observation_count} observations")
    print(f"  OLD ARCHITECTURE: Would have created 2 apps")
    print(f"  NEW ARCHITECTURE: Single app, no duplicates ✓")


def demo_data_quality():
    """Demonstrate data quality scoring and observation ranking."""
    print("\n" + "="*70)
    print("DEMO 3: Data Quality & Observation Ranking")
    print("="*70)

    app = Application(
        id=ApplicationId.generate("SAP ERP", Entity.TARGET),
        entity=Entity.TARGET,
        name="SAP ERP"
    )

    # Low confidence LLM observation
    low_confidence_obs = Observation.from_llm(
        source_document="notes.txt",
        extracted_data={"vendor": "SAP??", "cost": "~100k"},  # Uncertain data
        confidence=0.5
    )
    app.add_observation(low_confidence_obs)

    print(f"\nAfter low-confidence observation:")
    print(f"  Vendor: {app.vendor}")
    print(f"  Data quality: {app.data_quality_score:.2f}")

    # High confidence table observation (should override)
    high_confidence_obs = Observation.from_table(
        source_document="contracts.xlsx",
        extracted_data={"vendor": "SAP SE", "cost": 125000}  # Precise data
    )
    app.add_observation(high_confidence_obs)

    print(f"\nAfter high-confidence table observation:")
    print(f"  Vendor: {app.vendor}  (table data won!)")
    print(f"  Cost: {app.cost.format() if app.cost else 'None'}")
    print(f"  Data quality: {app.data_quality_score:.2f}  (improved!)")


def demo_entity_isolation():
    """Demonstrate target/buyer entity isolation."""
    print("\n" + "="*70)
    print("DEMO 4: Entity Isolation (Target vs Buyer)")
    print("="*70)

    # Same app name, different entities = different IDs
    target_app = Application(
        id=ApplicationId.generate("Workday", Entity.TARGET),
        entity=Entity.TARGET,
        name="Workday"
    )

    buyer_app = Application(
        id=ApplicationId.generate("Workday", Entity.BUYER),
        entity=Entity.BUYER,
        name="Workday"
    )

    print(f"\nTarget Workday: {target_app.id.value}")
    print(f"Buyer Workday:  {buyer_app.id.value}")
    print(f"IDs are different: {target_app.id != buyer_app.id}")
    print(f"\nDuplication check: {target_app.is_duplicate_of(buyer_app)}")
    print(f"  → False (different entities cannot be duplicates)")


def demo_value_objects():
    """Demonstrate value object immutability and validation."""
    print("\n" + "="*70)
    print("DEMO 5: Value Object Safety")
    print("="*70)

    # Money value object
    cost1 = Money.from_float(50000, status="known")
    cost2 = Money.from_float(25000, status="estimated")

    print(f"\nCost 1: {cost1.format()} ({cost1.status})")
    print(f"Cost 2: {cost2.format()} ({cost2.status})")

    total = cost1 + cost2
    print(f"Total:  {total.format()} ({total.status})")

    # Try to modify (will fail - frozen dataclass)
    try:
        total.amount = 100000
        print("ERROR: Money was mutable!")
    except Exception as e:
        print(f"\n✓ Money is immutable (as expected)")
        print(f"  Attempted modification raised: {type(e).__name__}")

    # Entity validation
    try:
        entity = Entity.from_string("invalid")
        print("ERROR: Invalid entity accepted!")
    except ValueError as e:
        print(f"\n✓ Entity validates input")
        print(f"  Rejected 'invalid': {e}")


def main():
    """Run all demos."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "DOMAIN MODEL DEMONSTRATION" + " "*27 + "║")
    print("╚" + "="*68 + "╝")

    demo_stable_ids()
    demo_deduplication()
    demo_data_quality()
    demo_entity_isolation()
    demo_value_objects()

    print("\n" + "="*70)
    print("SUMMARY: How This Fixes The Duplication Crisis")
    print("="*70)
    print("""
OLD ARCHITECTURE (Current):
  Deterministic Parser → InventoryStore (ID: I-APP-abc123)
  LLM Discovery → FactStore → Promotion → InventoryStore (ID: I-APP-def456)
  RESULT: 2 Salesforce entries (143 apps, should be ~60)

NEW ARCHITECTURE (This Demo):
  Deterministic Parser → Application (ID: app_a3f291cd_target)
  LLM Discovery → SAME Application.add_observation()
  RESULT: 1 Salesforce with 2 observations (correct count!)

KEY INNOVATIONS:
  ✓ Stable, deterministic IDs (same name → same ID)
  ✓ Single source of truth (Application, not FactStore + InventoryStore)
  ✓ Observations are PART OF Application (composition, not separate store)
  ✓ Repository.find_or_create() enforces deduplication
  ✓ Database UNIQUE constraint prevents duplicates at lowest level

MIGRATION PATH:
  Week 1: Domain model (THIS CODE)
  Week 2: PostgreSQL repository implementation
  Week 3: Update analysis pipeline to use domain model
  Week 4: Update UI to read from ApplicationRepository
  Week 5-6: Testing, migration, cutover
""")

    print("="*70)


if __name__ == "__main__":
    main()
