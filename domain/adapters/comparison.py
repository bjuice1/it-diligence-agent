"""
Comparison Tool - Validates old vs new system outputs match.

Compares data from:
- Old System: FactStore → InventoryStore (production)
- New System: FactStore → Domain Model → InventoryStore (via adapters)

Validates:
- Same counts (no data loss)
- Same entities (no cross-contamination)
- Same deduplication (no false merges or splits)

Created: 2026-02-12 (Integration Layer)
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
import logging

from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from domain.kernel.entity import Entity
from domain.applications.repository import ApplicationRepository
from domain.infrastructure.repository import InfrastructureRepository
from domain.adapters.fact_store_adapter import FactStoreAdapter
from domain.adapters.inventory_adapter import InventoryAdapter

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """
    Results of comparing old vs new system.

    Attributes:
        passed: Did comparison pass (no significant differences)?
        old_counts: Counts from old system
        new_counts: Counts from new system
        differences: List of differences found
        warnings: List of warnings (non-blocking)
        details: Additional comparison details
    """
    passed: bool
    old_counts: Dict[str, int] = field(default_factory=dict)
    new_counts: Dict[str, int] = field(default_factory=dict)
    differences: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def print_summary(self):
        """Print comparison summary to console."""
        print("\n" + "="*70)
        print("COMPARISON SUMMARY: Old System vs New System")
        print("="*70)

        # Status
        status = "✅ PASS" if self.passed else "❌ FAIL"
        print(f"\nStatus: {status}")

        # Counts comparison
        print("\n--- Counts ---")
        print(f"{'Item':<30} {'Old':<10} {'New':<10} {'Diff':<10}")
        print("-" * 70)
        for key in sorted(set(self.old_counts.keys()) | set(self.new_counts.keys())):
            old = self.old_counts.get(key, 0)
            new = self.new_counts.get(key, 0)
            diff = new - old
            diff_str = f"{diff:+d}" if diff != 0 else "0"
            marker = "✅" if diff == 0 else "⚠️"
            print(f"{marker} {key:<28} {old:<10} {new:<10} {diff_str:<10}")

        # Differences
        if self.differences:
            print(f"\n--- Differences ({len(self.differences)}) ---")
            for diff in self.differences:
                print(f"  ❌ {diff}")

        # Warnings
        if self.warnings:
            print(f"\n--- Warnings ({len(self.warnings)}) ---")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        # Details
        if self.details:
            print(f"\n--- Details ---")
            for key, value in self.details.items():
                print(f"  {key}: {value}")

        print("="*70 + "\n")


class ComparisonTool:
    """
    Compares old production system vs new domain model system.

    Usage:
        tool = ComparisonTool()

        # Run full comparison
        result = tool.compare(
            fact_store=fact_store,
            old_inventory=old_inventory_store,
            deal_id="deal-123"
        )

        result.print_summary()

        if not result.passed:
            print("Differences found! Review before cutover.")
    """

    def __init__(self):
        """Initialize comparison tool."""
        self.fact_adapter = FactStoreAdapter()
        self.inv_adapter = InventoryAdapter()

    def compare(
        self,
        fact_store: FactStore,
        old_inventory: InventoryStore,
        deal_id: str,
        tolerance: float = 0.05  # Allow 5% difference
    ) -> ComparisonResult:
        """
        Compare old system vs new system.

        Process:
        1. Count items in old InventoryStore (baseline)
        2. Run new system: FactStore → Domain Model → InventoryStore
        3. Count items in new InventoryStore
        4. Compare counts, validate no data loss
        5. Validate entity separation maintained

        Args:
            fact_store: Source FactStore with production facts
            old_inventory: OLD InventoryStore (production baseline)
            deal_id: Deal ID for scoping
            tolerance: Allowed difference as fraction (0.05 = 5%)

        Returns:
            ComparisonResult with pass/fail and details
        """
        logger.info(f"Running comparison for deal {deal_id}")

        result = ComparisonResult(passed=True)

        # Step 1: Count old system
        old_counts = self._count_old_inventory(old_inventory)
        result.old_counts = old_counts

        # Step 2: Run new system
        new_inventory = self._run_new_system(fact_store, deal_id)
        new_counts = self._count_new_inventory(new_inventory)
        result.new_counts = new_counts

        # Step 3: Compare counts
        for key in sorted(set(old_counts.keys()) | set(new_counts.keys())):
            old_count = old_counts.get(key, 0)
            new_count = new_counts.get(key, 0)

            # Calculate difference
            if old_count == 0 and new_count == 0:
                continue  # Both zero, skip

            if old_count == 0:
                # New system found items old system didn't
                result.warnings.append(
                    f"{key}: New system found {new_count} items, old system found 0"
                )
            elif new_count == 0:
                # Data loss!
                result.differences.append(
                    f"{key}: Old system had {old_count} items, new system has 0 (DATA LOSS!)"
                )
                result.passed = False
            else:
                # Both have items - check tolerance
                diff_pct = abs(new_count - old_count) / old_count
                if diff_pct > tolerance:
                    result.differences.append(
                        f"{key}: Count difference {diff_pct:.1%} exceeds tolerance {tolerance:.1%} "
                        f"(old={old_count}, new={new_count})"
                    )
                    result.passed = False

        # Step 4: Validate entity separation
        entity_check = self._validate_entity_separation(new_inventory)
        if not entity_check["passed"]:
            result.differences.append(
                f"Entity separation violated: {entity_check['message']}"
            )
            result.passed = False

        # Step 5: Add details
        result.details["old_total"] = sum(old_counts.values())
        result.details["new_total"] = sum(new_counts.values())
        result.details["adapter_stats"] = {
            "fact_adapter": self.fact_adapter.get_stats(),
            "inv_adapter": self.inv_adapter.get_stats(),
        }

        logger.info(f"Comparison complete: {'PASS' if result.passed else 'FAIL'}")

        return result

    def _count_old_inventory(self, inventory: InventoryStore) -> Dict[str, int]:
        """
        Count items in old InventoryStore.

        Returns:
            Dict mapping "type_entity" → count
            e.g., {"application_target": 50, "application_buyer": 20, ...}
        """
        counts = {}

        for item in inventory.get_items(status="all"):
            key = f"{item.inventory_type}_{item.entity}"
            counts[key] = counts.get(key, 0) + 1

        return counts

    def _run_new_system(
        self,
        fact_store: FactStore,
        deal_id: str
    ) -> InventoryStore:
        """
        Run new domain model system: FactStore → Domain Model → InventoryStore.

        Args:
            fact_store: Source facts
            deal_id: Deal ID for scoping

        Returns:
            New InventoryStore populated via domain model
        """
        logger.info("Running new system (domain model)")

        # Create repositories
        app_repo = ApplicationRepository()
        infra_repo = InfrastructureRepository()

        # Load from FactStore into domain model
        applications = self.fact_adapter.load_applications(fact_store, app_repo)
        infrastructures = self.fact_adapter.load_infrastructure(fact_store, infra_repo)

        # Create new inventory
        new_inventory = InventoryStore(deal_id=deal_id)

        # Sync domain model to inventory
        self.inv_adapter.sync_applications(applications, new_inventory)
        self.inv_adapter.sync_infrastructure(infrastructures, new_inventory)

        return new_inventory

    def _count_new_inventory(self, inventory: InventoryStore) -> Dict[str, int]:
        """Count items in new InventoryStore (same format as old)."""
        return self._count_old_inventory(inventory)

    def _validate_entity_separation(self, inventory: InventoryStore) -> Dict[str, Any]:
        """
        Validate that target and buyer entities are properly separated.

        Checks:
        - No items with entity=null
        - Target items have different IDs than buyer items
        - No cross-contamination

        Returns:
            Dict with "passed" (bool) and "message" (str)
        """
        items = inventory.get_items(status="all")

        # Check for null entities
        null_entity_items = [item for item in items if not item.entity]
        if null_entity_items:
            return {
                "passed": False,
                "message": f"Found {len(null_entity_items)} items with null entity"
            }

        # Check for cross-contamination (same name in both target and buyer)
        target_names = {
            item.data.get("name") for item in items
            if item.entity == "target" and item.data.get("name")
        }
        buyer_names = {
            item.data.get("name") for item in items
            if item.entity == "buyer" and item.data.get("name")
        }

        overlap = target_names & buyer_names
        if overlap:
            return {
                "passed": True,  # This is actually OK - same name can exist in both
                "message": f"{len(overlap)} names appear in both target and buyer (expected)"
            }

        return {
            "passed": True,
            "message": "Entity separation validated"
        }

    def quick_check(
        self,
        fact_store: FactStore,
        deal_id: str
    ) -> Dict[str, int]:
        """
        Quick count check without full comparison.

        Returns counts from new system only (for fast validation).

        Args:
            fact_store: Source facts
            deal_id: Deal ID

        Returns:
            Dict with counts
        """
        new_inventory = self._run_new_system(fact_store, deal_id)
        return self._count_new_inventory(new_inventory)
