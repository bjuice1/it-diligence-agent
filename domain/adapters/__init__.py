"""
Domain Adapters - Integration layer between domain model and production systems.

This package provides adapters that bridge the new domain model (Workers 1-3)
with the existing production FactStore and InventoryStore.

Components:
- FactStoreAdapter: Reads production facts → Domain model
- InventoryAdapter: Writes domain model → Production inventory
- ComparisonTool: Validates old vs new system outputs match

Example Usage:
    from domain.adapters import FactStoreAdapter, InventoryAdapter, ComparisonTool
    from stores.fact_store import FactStore
    from stores.inventory_store import InventoryStore
    from domain.applications.repository import ApplicationRepository

    # Load facts from production
    fact_store = FactStore(deal_id="deal-123")

    # Convert to domain model
    fact_adapter = FactStoreAdapter()
    app_repo = ApplicationRepository()
    applications = fact_adapter.load_applications(fact_store, app_repo)

    # Sync back to inventory for UI
    inv_adapter = InventoryAdapter()
    inventory = InventoryStore(deal_id="deal-123")
    inv_adapter.sync_applications(applications, inventory)

    # Validate results match old system
    comparison = ComparisonTool()
    result = comparison.compare(fact_store, old_inventory, "deal-123")
    result.print_summary()

Created: 2026-02-12 (Integration Layer)
"""

from domain.adapters.fact_store_adapter import FactStoreAdapter
from domain.adapters.inventory_adapter import InventoryAdapter
from domain.adapters.comparison import ComparisonTool, ComparisonResult

__all__ = [
    "FactStoreAdapter",
    "InventoryAdapter",
    "ComparisonTool",
    "ComparisonResult",
]
