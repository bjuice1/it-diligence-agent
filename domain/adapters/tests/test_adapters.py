"""
Integration Tests for Domain Adapters.

Tests the complete data flow:
    FactStore → FactStoreAdapter → Domain Model → InventoryAdapter → InventoryStore

Validates:
- Data integrity (no loss)
- Entity separation (target vs buyer)
- Deduplication working
- Round-trip consistency

Created: 2026-02-12 (Integration Layer)
"""

import pytest
from datetime import datetime

from stores.fact_store import FactStore, Fact
from stores.inventory_store import InventoryStore
from domain.kernel.entity import Entity
from domain.applications.repository import ApplicationRepository
from domain.infrastructure.repository import InfrastructureRepository
from domain.adapters.fact_store_adapter import FactStoreAdapter
from domain.adapters.inventory_adapter import InventoryAdapter
from domain.adapters.comparison import ComparisonTool


class TestFactStoreAdapter:
    """Test FactStore → Domain Model conversion."""

    def test_load_applications_basic(self):
        """Test loading applications from FactStore."""
        # Create FactStore with application facts
        fact_store = FactStore(deal_id="test-deal")

        # Add application facts
        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce",
            details={"vendor": "Salesforce", "cost": 50000},
            status="documented",
            evidence={"exact_quote": "Page 5: Salesforce CRM"},
            entity="target",
            deal_id="test-deal"
        )

        # Create adapter and repository
        adapter = FactStoreAdapter()
        repo = ApplicationRepository()

        # Load applications
        applications = adapter.load_applications(fact_store, repo)

        # Assertions
        assert len(applications) == 1
        assert applications[0].name == "Salesforce"
        assert applications[0].vendor == "Salesforce"
        assert applications[0].entity == Entity.TARGET
        assert applications[0].deal_id == "test-deal"
        assert len(applications[0].observations) == 1

    def test_load_applications_deduplication(self):
        """Test deduplication when loading applications."""
        fact_store = FactStore(deal_id="test-deal")

        # Add duplicate facts (different variants of same app)
        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce",
            details={"vendor": "Salesforce"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce CRM",  # Variant
            details={"vendor": "Salesforce"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="SALESFORCE",  # Another variant
            details={"vendor": "Salesforce"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = ApplicationRepository()

        applications = adapter.load_applications(fact_store, repo)

        # Should deduplicate to 1 application with 3 observations
        assert len(applications) == 1
        assert len(applications[0].observations) == 3

    def test_load_applications_entity_separation(self):
        """Test target vs buyer separation."""
        fact_store = FactStore(deal_id="test-deal")

        # Add same app for target and buyer
        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce",
            details={"vendor": "Salesforce"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce",
            details={"vendor": "Salesforce"},
            status="documented",
            evidence={},
            entity="buyer",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = ApplicationRepository()

        applications = adapter.load_applications(fact_store, repo)

        # Should create 2 separate applications (different entities)
        assert len(applications) == 2

        target_apps = [app for app in applications if app.entity == Entity.TARGET]
        buyer_apps = [app for app in applications if app.entity == Entity.BUYER]

        assert len(target_apps) == 1
        assert len(buyer_apps) == 1

        # Different IDs
        assert target_apps[0].id != buyer_apps[0].id

    def test_load_infrastructure_vendor_none(self):
        """Test loading infrastructure with vendor=None (on-prem)."""
        fact_store = FactStore(deal_id="test-deal")

        # Add on-prem infrastructure fact (no vendor)
        fact_store.add_fact(
            domain="infrastructure",
            category="hosting",
            item="On-Prem Data Center",
            details={},  # No vendor
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = InfrastructureRepository()

        infrastructures = adapter.load_infrastructure(fact_store, repo)

        assert len(infrastructures) == 1
        assert infrastructures[0].vendor is None  # Vendor=None supported

    def test_adapter_stats(self):
        """Test adapter statistics tracking."""
        fact_store = FactStore(deal_id="test-deal")

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="App1",
            details={"vendor": "Vendor1"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = ApplicationRepository()

        adapter.load_applications(fact_store, repo)

        stats = adapter.get_stats()
        assert stats["facts_processed"] == 1
        assert stats["applications_created"] == 1
        assert stats["observations_converted"] == 1

    def test_load_people_basic(self):
        """Test loading people from FactStore."""
        from domain.organization.repository import PersonRepository

        fact_store = FactStore(deal_id="test-deal")

        # Add person fact
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="John Smith - CTO",
            details={},  # No vendor for people
            status="documented",
            evidence={"exact_quote": "John Smith serves as CTO"},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = PersonRepository()

        people = adapter.load_people(fact_store, repo)

        assert len(people) == 1
        assert people[0].name == "John Smith - CTO"
        assert people[0].vendor is None  # Vendor ALWAYS None for people
        assert people[0].entity == Entity.TARGET
        assert people[0].deal_id == "test-deal"
        assert len(people[0].observations) == 1

    def test_load_people_deduplication(self):
        """Test deduplication when loading people."""
        from domain.organization.repository import PersonRepository

        fact_store = FactStore(deal_id="test-deal")

        # Add duplicate facts (case-insensitive variants that normalize the same)
        # Note: Organization normalization preserves role info, so "John Smith" and
        # "John Smith - CTO" are DIFFERENT people. Use case variants instead.
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="John Smith",
            details={},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="john smith",  # Case variant (normalizes same)
            details={},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="JOHN SMITH",  # Case variant (normalizes same)
            details={},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = PersonRepository()

        people = adapter.load_people(fact_store, repo)

        # Should deduplicate to 1 person with 3 observations
        assert len(people) == 1
        assert len(people[0].observations) == 3

    def test_load_people_entity_separation(self):
        """Test target vs buyer separation for people."""
        from domain.organization.repository import PersonRepository

        fact_store = FactStore(deal_id="test-deal")

        # Add same person for target and buyer
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="John Smith",
            details={},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="John Smith",
            details={},
            status="documented",
            evidence={},
            entity="buyer",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = PersonRepository()

        people = adapter.load_people(fact_store, repo)

        # Should create 2 separate people (different entities)
        assert len(people) == 2

        target_people = [p for p in people if p.entity == Entity.TARGET]
        buyer_people = [p for p in people if p.entity == Entity.BUYER]

        assert len(target_people) == 1
        assert len(buyer_people) == 1

        # Different IDs
        assert target_people[0].id != buyer_people[0].id

        # Both have vendor=None
        assert target_people[0].vendor is None
        assert buyer_people[0].vendor is None

    def test_load_people_vendor_always_none(self):
        """Test that people always have vendor=None."""
        from domain.organization.repository import PersonRepository

        fact_store = FactStore(deal_id="test-deal")

        # Add person fact (vendor should be ignored even if in details)
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="Jane Doe",
            details={"vendor": "SomeCompany"},  # Should be ignored
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        adapter = FactStoreAdapter()
        repo = PersonRepository()

        people = adapter.load_people(fact_store, repo)

        assert len(people) == 1
        assert people[0].vendor is None  # Vendor ALWAYS None for people


class TestInventoryAdapter:
    """Test Domain Model → InventoryStore conversion."""

    def test_sync_applications_basic(self):
        """Test syncing applications to InventoryStore."""
        # Create domain model application
        from domain.applications.application import Application
        from domain.kernel.observation import Observation

        obs = Observation(
            source_type="table",
            confidence=0.9,
            evidence="Test evidence",
            extracted_at=datetime.now(),
            deal_id="test-deal",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )

        app = Application(
            id="APP-TARGET-test123",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="test-deal",
            observations=[obs]
        )

        # Sync to inventory
        adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        item_ids = adapter.sync_applications([app], inventory)

        # Assertions
        assert len(item_ids) == 1

        items = inventory.get_items(status="all")
        assert len(items) == 1
        assert items[0].data["name"] == "Salesforce"
        assert items[0].data["vendor"] == "Salesforce"
        assert items[0].data["domain_id"] == "APP-TARGET-test123"
        assert items[0].entity == "target"

    def test_sync_preserves_observations(self):
        """Test that observation data is preserved in sync."""
        from domain.applications.application import Application
        from domain.kernel.observation import Observation

        obs1 = Observation(
            source_type="table",
            confidence=0.9,
            evidence="Evidence 1",
            extracted_at=datetime.now(),
            deal_id="test-deal",
            entity=Entity.TARGET,
            data={"cost": 50000, "users": 100}
        )

        obs2 = Observation(
            source_type="manual",  # Higher priority
            confidence=1.0,
            evidence="Evidence 2",
            extracted_at=datetime.now(),
            deal_id="test-deal",
            entity=Entity.TARGET,
            data={"cost": 60000}  # Different cost
        )

        app = Application(
            id="APP-TARGET-test456",
            name="Test App",
            name_normalized="test",
            vendor="Test Vendor",
            entity=Entity.TARGET,
            deal_id="test-deal",
            observations=[obs1, obs2]
        )

        adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        adapter.sync_applications([app], inventory)

        items = inventory.get_items(status="all")
        assert len(items) == 1

        # Manual observation (higher priority) should win for cost
        assert items[0].data["cost"] == 60000  # From manual observation

    def test_adapter_stats(self):
        """Test inventory adapter statistics."""
        from domain.applications.application import Application

        app = Application(
            id="APP-TARGET-stat123",
            name="Stat App",
            name_normalized="stat",
            vendor="Vendor",
            entity=Entity.TARGET,
            deal_id="test-deal",
            observations=[]
        )

        adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        adapter.sync_applications([app], inventory)

        stats = adapter.get_stats()
        assert stats["applications_synced"] == 1
        assert stats["items_added"] == 1


class TestRoundTrip:
    """Test complete round-trip: FactStore → Domain Model → InventoryStore."""

    def test_application_round_trip(self):
        """Test full application flow."""
        # Step 1: Create FactStore with facts
        fact_store = FactStore(deal_id="test-deal")

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Salesforce",
            details={"vendor": "Salesforce", "cost": 50000, "users": 100},
            status="documented",
            evidence={"exact_quote": "Page 5: Salesforce"},
            entity="target",
            deal_id="test-deal"
        )

        # Step 2: Load into domain model
        fact_adapter = FactStoreAdapter()
        app_repo = ApplicationRepository()

        applications = fact_adapter.load_applications(fact_store, app_repo)

        # Step 3: Sync to inventory
        inv_adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        inv_adapter.sync_applications(applications, inventory)

        # Step 4: Validate
        items = inventory.get_items(status="all")
        assert len(items) == 1
        assert items[0].data["name"] == "Salesforce"
        assert items[0].data["vendor"] == "Salesforce"
        assert items[0].data["cost"] == 50000
        assert items[0].data["users"] == 100
        assert items[0].entity == "target"
        assert items[0].deal_id == "test-deal"

    def test_infrastructure_round_trip(self):
        """Test full infrastructure flow."""
        fact_store = FactStore(deal_id="test-deal")

        fact_store.add_fact(
            domain="infrastructure",
            category="hosting",
            item="AWS EC2",
            details={"vendor": "AWS", "type": "compute"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_adapter = FactStoreAdapter()
        infra_repo = InfrastructureRepository()

        infrastructures = fact_adapter.load_infrastructure(fact_store, infra_repo)

        inv_adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        inv_adapter.sync_infrastructure(infrastructures, inventory)

        items = inventory.get_items(status="all")
        assert len(items) == 1
        assert items[0].data["name"] == "AWS EC2"
        assert items[0].data["vendor"] == "AWS"
        assert items[0].entity == "target"


class TestComparisonTool:
    """Test comparison tool validates old vs new system."""

    def test_comparison_same_counts(self):
        """Test comparison passes when counts match."""
        # Create FactStore
        fact_store = FactStore(deal_id="test-deal")

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="App1",
            details={"vendor": "Vendor1"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        # Create old inventory (baseline)
        old_inventory = InventoryStore(deal_id="test-deal")
        old_inventory.add_item(
            "application",
            {"name": "App1", "vendor": "Vendor1"},
            entity="target",
            deal_id="test-deal"
        )

        # Run comparison
        tool = ComparisonTool()
        result = tool.compare(fact_store, old_inventory, "test-deal")

        # Should pass (same counts)
        assert result.passed
        assert result.old_counts.get("application_target", 0) == 1
        assert result.new_counts.get("application_target", 0) == 1

    def test_quick_check(self):
        """Test quick count check."""
        fact_store = FactStore(deal_id="test-deal")

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="App1",
            details={"vendor": "Vendor1"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        tool = ComparisonTool()
        counts = tool.quick_check(fact_store, "test-deal")

        assert "application_target" in counts
        assert counts["application_target"] >= 1


class TestEntitySeparation:
    """Test that entity separation is maintained through adapters."""

    def test_entity_not_contaminated(self):
        """Test target and buyer facts stay separated."""
        fact_store = FactStore(deal_id="test-deal")

        # Add same app for both entities
        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Common App",
            details={"vendor": "Vendor"},
            status="documented",
            evidence={},
            entity="target",
            deal_id="test-deal"
        )

        fact_store.add_fact(
            domain="applications",
            category="saas",
            item="Common App",
            details={"vendor": "Vendor"},
            status="documented",
            evidence={},
            entity="buyer",
            deal_id="test-deal"
        )

        # Load through adapters
        fact_adapter = FactStoreAdapter()
        app_repo = ApplicationRepository()

        applications = fact_adapter.load_applications(fact_store, app_repo)

        # Should create 2 separate applications
        assert len(applications) == 2

        target_app = [app for app in applications if app.entity == Entity.TARGET][0]
        buyer_app = [app for app in applications if app.entity == Entity.BUYER][0]

        # Different IDs (entity in fingerprint)
        assert target_app.id != buyer_app.id
        assert "TARGET" in target_app.id
        assert "BUYER" in buyer_app.id

        # Sync to inventory
        inv_adapter = InventoryAdapter()
        inventory = InventoryStore(deal_id="test-deal")

        inv_adapter.sync_applications(applications, inventory)

        # Check inventory has both
        items = inventory.get_items(status="all")
        assert len(items) == 2

        target_items = [item for item in items if item.entity == "target"]
        buyer_items = [item for item in items if item.entity == "buyer"]

        assert len(target_items) == 1
        assert len(buyer_items) == 1
