#!/usr/bin/env python3
"""
Quick script to add pipeline-level domain model integration to main_v2.py

This adds:
1. integrate_domain_model() function
2. --use-domain-model CLI flag
3. Integration calls in 3 pipeline paths
"""

INTEGRATE_FUNCTION = '''

def integrate_domain_model(
    fact_store: FactStore,
    inventory_store: InventoryStore,
    domains: List[str] = None
) -> Dict[str, int]:
    """
    Integrate domain model adapters into pipeline (experimental).

    Converts FactStore → Domain Model → InventoryStore with deduplication.

    Args:
        fact_store: FactStore with extracted facts
        inventory_store: InventoryStore to sync aggregates to
        domains: Domains to process (default: all with facts)

    Returns:
        Dict with integration statistics
    """
    from domain.adapters.fact_store_adapter import FactStoreAdapter
    from domain.adapters.inventory_adapter import InventoryAdapter
    from domain.applications.repository import ApplicationRepository
    from domain.infrastructure.repository import InfrastructureRepository
    from domain.organization.repository import PersonRepository
    from domain.kernel.entity import Entity

    logger.info("\\n" + "="*60)
    logger.info("DOMAIN MODEL INTEGRATION (Experimental)")
    logger.info("="*60)

    stats = {
        "applications_created": 0,
        "infrastructure_created": 0,
        "people_created": 0,
        "applications_synced": 0,
        "infrastructure_synced": 0,
        "people_synced": 0,
    }

    fact_adapter = FactStoreAdapter()
    inv_adapter = InventoryAdapter()

    # Determine which domains to process
    if domains is None:
        domains_in_facts = set(f.domain for f in fact_store.facts)
        domains = []
        if "applications" in domains_in_facts:
            domains.append("applications")
        if "infrastructure" in domains_in_facts:
            domains.append("infrastructure")
        if "organization" in domains_in_facts:
            domains.append("organization")

    # Process applications
    if "applications" in domains:
        logger.info("\\n[Applications Domain]")
        app_repo = ApplicationRepository()
        target_apps = fact_adapter.load_applications(fact_store, app_repo, entity_filter=Entity.TARGET)
        buyer_apps = fact_adapter.load_applications(fact_store, app_repo, entity_filter=Entity.BUYER)
        all_apps = target_apps + buyer_apps
        stats["applications_created"] = len(all_apps)
        logger.info(f"  Created {len(target_apps)} target + {len(buyer_apps)} buyer applications")
        logger.info(f"  Total: {len(all_apps)} (after deduplication)")
        inv_adapter.sync_applications(all_apps, inventory_store)
        stats["applications_synced"] = len(all_apps)

    # Process infrastructure
    if "infrastructure" in domains:
        logger.info("\\n[Infrastructure Domain]")
        infra_repo = InfrastructureRepository()
        target_infra = fact_adapter.load_infrastructure(fact_store, infra_repo, entity_filter=Entity.TARGET)
        buyer_infra = fact_adapter.load_infrastructure(fact_store, infra_repo, entity_filter=Entity.BUYER)
        all_infra = target_infra + buyer_infra
        stats["infrastructure_created"] = len(all_infra)
        logger.info(f"  Created {len(target_infra)} target + {len(buyer_infra)} buyer infrastructure")
        logger.info(f"  Total: {len(all_infra)} (after deduplication)")
        inv_adapter.sync_infrastructure(all_infra, inventory_store)
        stats["infrastructure_synced"] = len(all_infra)

    # Process organization
    if "organization" in domains:
        logger.info("\\n[Organization Domain]")
        person_repo = PersonRepository()
        target_people = fact_adapter.load_people(fact_store, person_repo, entity_filter=Entity.TARGET)
        buyer_people = fact_adapter.load_people(fact_store, person_repo, entity_filter=Entity.BUYER)
        all_people = target_people + buyer_people
        stats["people_created"] = len(all_people)
        logger.info(f"  Created {len(target_people)} target + {len(buyer_people)} buyer people")
        logger.info(f"  Total: {len(all_people)} (after deduplication)")
        inv_adapter.sync_people(all_people, inventory_store)
        stats["people_synced"] = len(all_people)

    logger.info("\\n[Domain Model Integration Complete]")
    logger.info(f"  Aggregates created: {stats['applications_created'] + stats['infrastructure_created'] + stats['people_created']}")
    logger.info(f"  Items synced to inventory: {stats['applications_synced'] + stats['infrastructure_synced'] + stats['people_synced']}")
    logger.info("="*60 + "\\n")

    return stats

'''

def main():
    # Read main_v2.py
    with open('main_v2.py', 'r') as f:
        content = f.read()

    # Add function after detect_entity_from_document (before run_discovery)
    marker = '    return "target"\n\n\ndef run_discovery('
    if marker in content:
        content = content.replace(marker, f'    return "target"\n{INTEGRATE_FUNCTION}\n\ndef run_discovery(')
        print("✅ Added integrate_domain_model() function")
    else:
        print("❌ Could not find insertion point for function")
        return False

    # Add CLI flag
    flag_marker = '    parser.add_argument(\n        "--narrative",'
    if flag_marker in content:
        new_flag = '''    parser.add_argument(
        "--use-domain-model",
        action="store_true",
        help="Use experimental domain model with deduplication (fixes P0-3 bugs)"
    )
    parser.add_argument(
        "--narrative",'''
        content = content.replace(flag_marker, new_flag)
        print("✅ Added --use-domain-model CLI flag")
    else:
        print("❌ Could not find insertion point for CLI flag")

    # Write back
    with open('main_v2.py', 'w') as f:
        f.write(content)

    print("\n✅ main_v2.py updated successfully!")
    print("\nNext: Manually add integration calls in 3 pipeline paths")
    return True

if __name__ == "__main__":
    main()
