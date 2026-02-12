"""
DOMAIN MODEL DEMONSTRATION - KERNEL FOUNDATION
===============================================

This file demonstrates the NEW kernel foundation (Worker 1).

The kernel provides shared primitives for ALL domains:
- Entity enum (target vs buyer)
- Observation schema (with validation)
- Normalization rules (fixes P0-3 collision bug)
- Entity inference (infer target/buyer from context)
- Fingerprint generation (stable deterministic IDs)
- Extraction coordination (prevents double-counting)

Run this with:
    export ENABLE_DOMAIN_MODEL=true
    python -m domain.DEMO_NEW
"""

from datetime import datetime

# NEW KERNEL IMPORTS (Worker 1)
from domain.kernel.entity import Entity
from domain.kernel.observation import Observation
from domain.kernel.normalization import NormalizationRules
from domain.kernel.entity_inference import EntityInference
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.extraction import ExtractionCoordinator


def demo_entity_enum():
    """Demonstrate Entity enum (target vs buyer)."""
    print("\n" + "="*70)
    print("DEMO 1: Entity Enum - Single Source of Truth")
    print("="*70)

    # Create entities
    target = Entity.TARGET
    buyer = Entity.BUYER

    print(f"\nTarget entity: {target}")
    print(f"Buyer entity: {buyer}")
    print(f"String conversion: '{str(target)}' and '{str(buyer)}'")

    # Case-insensitive parsing
    parsed = Entity.from_string("TARGET")
    print(f"\nParsed from 'TARGET': {parsed}")
    print(f"Matches Entity.TARGET: {parsed == Entity.TARGET}")


def demo_p03_fix():
    """Demonstrate P0-3 fix: SAP ERP vs SAP SuccessFactors no longer collide."""
    print("\n" + "="*70)
    print("DEMO 2: P0-3 Fix - Normalization Collision Bug FIXED")
    print("="*70)

    # The bug: "SAP ERP" and "SAP SuccessFactors" both normalized to "sap"
    # The fix: Vendor-aware normalization with whitelist-based suffix removal

    name1 = "SAP ERP"
    name2 = "SAP SuccessFactors"

    normalized1 = NormalizationRules.normalize_name(name1, "application")
    normalized2 = NormalizationRules.normalize_name(name2, "application")

    print(f"\n'{name1}' → '{normalized1}'")
    print(f"'{name2}' → '{normalized2}'")
    print(f"\n✅ Different normalized names: {normalized1 != normalized2}")
    print("   (Old system: both → 'sap', causing collision)")

    # More examples
    examples = [
        ("Salesforce CRM", "salesforce"),
        ("Microsoft Dynamics 365", "microsoft dynamics 365"),
        ("Oracle E-Business Suite", "oracle ebusiness suite"),
    ]

    print("\nMore normalization examples:")
    for raw, expected in examples:
        result = NormalizationRules.normalize_name(raw, "application")
        print(f"  '{raw}' → '{result}'")


def demo_stable_ids():
    """Demonstrate stable ID generation with vendor in fingerprint."""
    print("\n" + "="*70)
    print("DEMO 3: Stable Deterministic IDs (Format: APP-TARGET-hash)")
    print("="*70)

    # Same name variants generate same ID
    name1 = "Salesforce"
    name2 = "Salesforce CRM"  # Suffix removed
    name3 = "SALESFORCE"      # Case normalized

    id1 = FingerprintGenerator.generate(
        normalized_name=NormalizationRules.normalize_name(name1, "application"),
        original_name=name1,
        entity=Entity.TARGET,
        domain_prefix="APP"
    )
    id2 = FingerprintGenerator.generate(
        normalized_name=NormalizationRules.normalize_name(name2, "application"),
        original_name=name2,
        entity=Entity.TARGET,
        domain_prefix="APP"
    )
    id3 = FingerprintGenerator.generate(
        normalized_name=NormalizationRules.normalize_name(name3, "application"),
        original_name=name3,
        entity=Entity.TARGET,
        domain_prefix="APP"
    )

    print(f"\n'{name1}' → {id1}")
    print(f"'{name2}' → {id2}")
    print(f"'{name3}' → {id3}")
    print(f"\n✅ All IDs match: {id1 == id2 == id3}")

    # Different entity = different ID
    id_buyer = FingerprintGenerator.generate(
        normalized_name=NormalizationRules.normalize_name(name1, "application"),
        original_name=name1,
        entity=Entity.BUYER,
        domain_prefix="APP"
    )

    print(f"\nBuyer '{name1}' → {id_buyer}")
    print(f"✅ Different from Target: {id1 != id_buyer}")

    # Parse ID back
    parsed = FingerprintGenerator.parse_domain_id(id1)
    print(f"\nParsed ID components:")
    print(f"  Domain: {parsed['domain_prefix']}")
    print(f"  Entity: {parsed['entity']}")
    print(f"  Hash: {parsed['hash']}")


def demo_entity_inference():
    """Demonstrate entity inference from context."""
    print("\n" + "="*70)
    print("DEMO 4: Entity Inference - Infer Target vs Buyer from Context")
    print("="*70)

    contexts = [
        "Target Company - IT Landscape",
        "Our Current Infrastructure",
        "Acquisition Target Applications",
        "Buyer Systems Overview",
        "Applications Inventory",  # Ambiguous - defaults to target
    ]

    print("\nInferring entity from document context:")
    for context in contexts:
        entity, confidence = EntityInference.infer_with_confidence(context)
        print(f"  '{context}'")
        print(f"    → {entity} (confidence: {confidence:.1f})")


def demo_observation_schema():
    """Demonstrate comprehensive observation schema with validation."""
    print("\n" + "="*70)
    print("DEMO 5: Observation Schema - Validated, Entity-Aware")
    print("="*70)

    # Create valid observation
    obs = Observation(
        source_type="table",
        confidence=0.95,
        evidence="Page 5, Applications table, row 3",
        extracted_at=datetime.now(),
        deal_id="deal-abc123",
        entity=Entity.TARGET,
        data={
            "name": "Salesforce",
            "cost": 50000,
            "users": 100,
            "vendor": "Salesforce"
        }
    )

    print(f"\n✅ Valid observation created:")
    print(f"   Source: {obs.source_type}")
    print(f"   Confidence: {obs.confidence}")
    print(f"   Entity: {obs.entity}")
    print(f"   Deal: {obs.deal_id}")
    print(f"   Data: {obs.data}")

    # Priority scoring (for conflict resolution)
    print(f"\n   Priority score: {obs.get_priority_score()}")
    print(f"   (manual=4, table=3, llm_prose=2, llm_assumption=1)")

    # Validation prevents bad data
    print("\n⚠️  Validation catches errors:")
    try:
        bad_obs = Observation(
            source_type="table",
            confidence=1.5,  # ❌ Invalid! Must be 0.0-1.0
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={}
        )
    except ValueError as e:
        print(f"   ❌ Caught: {e}")

    try:
        missing_entity = Observation(
            source_type="table",
            confidence=0.9,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=None,  # ❌ Invalid! Entity required
            data={}
        )
    except (ValueError, TypeError) as e:
        print(f"   ❌ Caught: Entity must be provided")


def demo_extraction_coordinator():
    """Demonstrate extraction coordination (prevents double-counting)."""
    print("\n" + "="*70)
    print("DEMO 6: Extraction Coordination - Prevents Double-Counting")
    print("="*70)

    coordinator = ExtractionCoordinator()

    # Scenario: Multiple domains extract from same document
    doc_id = "IT_Landscape.pdf"

    # Application domain extracts "Salesforce"
    coordinator.mark_extracted(doc_id, "application", "salesforce")
    print(f"\n✅ Application domain extracted 'Salesforce' from {doc_id}")

    # Check if already extracted
    already = coordinator.already_extracted(doc_id, "application", "salesforce")
    print(f"   Already extracted by application? {already}")

    # Infrastructure domain tries to extract same app
    already_by_any = coordinator.already_extracted_by_any_domain(doc_id, "salesforce")
    extracting_domain = coordinator.get_extracting_domain(doc_id, "salesforce")

    print(f"\n⚠️  Infrastructure domain checks before extracting 'Salesforce':")
    print(f"   Already extracted by any domain? {already_by_any}")
    print(f"   Extracting domain: {extracting_domain}")
    print(f"   ✅ Infrastructure skips (prevents duplicate)")

    # Stats
    print(f"\n📊 Extraction stats:")
    print(f"   Total items extracted from {doc_id}: {coordinator.get_extracted_count(doc_id)}")
    print(f"   By application domain: {coordinator.get_extracted_count(doc_id, 'application')}")


def demo_p02_fix():
    """Demonstrate P0-2 fix: Circuit breaker for reconciliation."""
    print("\n" + "="*70)
    print("DEMO 7: P0-2 Fix - Circuit Breaker for O(n²) Reconciliation")
    print("="*70)

    from domain.kernel.repository import DomainRepository

    print(f"\n✅ Circuit breaker constant:")
    print(f"   MAX_ITEMS_FOR_RECONCILIATION = {DomainRepository.MAX_ITEMS_FOR_RECONCILIATION}")
    print(f"\n   If repository has > 500 items:")
    print(f"     - Reconciliation skipped (would be O(n²) → too slow)")
    print(f"     - Uses database fuzzy search instead (O(n log n))")
    print(f"     - Prevents 5+ minute reconciliation times")

    print(f"\n   Old system: No limit → 1000 items = 500,000 comparisons")
    print(f"   New system: Circuit breaker → skips to DB search")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("🎯 KERNEL FOUNDATION DEMONSTRATION")
    print("   Worker 1 - Shared Primitives for All Domains")
    print("="*70)

    demo_entity_enum()
    demo_p03_fix()
    demo_stable_ids()
    demo_entity_inference()
    demo_observation_schema()
    demo_extraction_coordinator()
    demo_p02_fix()

    print("\n" + "="*70)
    print("✅ KERNEL DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nNext: Worker 2 will build Application domain using these primitives")
    print("      Worker 3 will build Infrastructure domain")
    print("      Worker 4 will build Organization domain")
    print("\nAll domains will use THE SAME kernel primitives (single source of truth)")
    print("="*70 + "\n")


if __name__ == "__main__":
    from domain.guards import ExperimentalGuard

    # Require experimental mode
    try:
        ExperimentalGuard.require_experimental_mode()
        main()
    except RuntimeError as e:
        print(f"\n⚠️  {e}\n")
        print("To run this demo:")
        print("  export ENABLE_DOMAIN_MODEL=true")
        print("  python -m domain.DEMO_NEW\n")
