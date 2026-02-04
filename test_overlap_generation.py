"""
Quick test of overlap generation pipeline stage.

This tests Point 1-2 of Milestone 1: Overlap Pipeline Stage
"""

import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.overlap_generator import OverlapGenerator


def test_overlap_generation():
    """Test overlap generation with mock facts."""

    # Mock target facts (applications domain)
    target_facts = [
        {
            "fact_id": "F-TGT-APP-001",
            "domain": "applications",
            "entity": "target",
            "category": "ERP Systems",
            "statement": "Target uses SAP S/4HANA as primary ERP platform",
            "details": {
                "vendor": "SAP",
                "product": "S/4HANA",
                "version": "2021",
                "users": "500",
                "hosting": "On-premise"
            }
        },
        {
            "fact_id": "F-TGT-APP-002",
            "domain": "applications",
            "entity": "target",
            "category": "Customization",
            "statement": "Target has 247 custom ABAP programs in SAP",
            "details": {
                "custom_programs": "247",
                "documentation": "Limited"
            }
        }
    ]

    # Mock buyer facts (applications domain)
    buyer_facts = [
        {
            "fact_id": "F-BYR-APP-001",
            "domain": "applications",
            "entity": "buyer",
            "category": "ERP Systems",
            "statement": "Buyer uses Oracle ERP Cloud as primary ERP platform",
            "details": {
                "vendor": "Oracle",
                "product": "ERP Cloud",
                "version": "23D",
                "users": "4272",
                "hosting": "Cloud"
            }
        },
        {
            "fact_id": "F-BYR-APP-002",
            "domain": "applications",
            "entity": "buyer",
            "category": "ERP Strategy",
            "statement": "Buyer has standardized on Oracle ERP Cloud across all business units",
            "details": {
                "standardized": "true",
                "implementation_date": "2020"
            }
        }
    ]

    # Test overlap generation
    print("\n" + "="*70)
    print("TESTING OVERLAP GENERATION")
    print("="*70)

    generator = OverlapGenerator()

    print(f"\nTarget facts: {len(target_facts)}")
    print(f"Buyer facts: {len(buyer_facts)}")

    overlaps = generator.generate_overlap_map_for_domain(
        domain="applications",
        target_facts=target_facts,
        buyer_facts=buyer_facts
    )

    print(f"\n✅ Generated {len(overlaps)} overlaps")

    for i, overlap in enumerate(overlaps, 1):
        print(f"\n--- Overlap {i} ---")
        print(f"ID: {overlap.overlap_id}")
        print(f"Type: {overlap.overlap_type}")
        print(f"Target: {overlap.target_summary}")
        print(f"Buyer: {overlap.buyer_summary}")
        print(f"Why it matters: {overlap.why_it_matters}")
        print(f"Confidence: {overlap.confidence}")
        print(f"Target facts cited: {overlap.target_fact_ids}")
        print(f"Buyer facts cited: {overlap.buyer_fact_ids}")

    # Validate overlaps
    print("\n" + "="*70)
    print("VALIDATION")
    print("="*70)

    for overlap in overlaps:
        errors = overlap.validate()
        if errors:
            print(f"❌ {overlap.overlap_id}: {errors}")
        else:
            print(f"✅ {overlap.overlap_id}: Valid")

    print("\n" + "="*70)
    print(f"TEST COMPLETE: {len(overlaps)} overlaps generated")
    print("="*70)

    return overlaps


if __name__ == "__main__":
    test_overlap_generation()
