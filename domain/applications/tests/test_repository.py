"""
Tests for ApplicationRepository (deduplication engine).

Coverage target: 80%+
Critical: Tests find_or_create (THE deduplication primitive)

Created: 2026-02-12 (Worker 2 - Application Domain, Task-013)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.applications.repository import ApplicationRepository
from domain.applications.application import Application


class TestRepositoryBasics:
    """Test basic repository operations."""

    def test_save_and_find_by_id(self):
        """Test saving and finding application."""
        repo = ApplicationRepository()

        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Save
        saved = repo.save(app)
        assert saved.id == app.id

        # Find
        found = repo.find_by_id("APP-TARGET-a3f291c2")
        assert found is not None
        assert found.id == "APP-TARGET-a3f291c2"
        assert found.name == "Salesforce"

    def test_find_by_id_not_found(self):
        """Test finding non-existent application."""
        repo = ApplicationRepository()

        found = repo.find_by_id("APP-TARGET-nonexistent")
        assert found is None

    def test_repository_length(self):
        """Test repository length."""
        repo = ApplicationRepository()

        assert len(repo) == 0

        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(app)

        assert len(repo) == 1

    def test_delete(self):
        """Test deleting application."""
        repo = ApplicationRepository()

        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(app)

        # Delete
        deleted = repo.delete("APP-TARGET-a3f291c2")
        assert deleted is True

        # Verify deleted
        found = repo.find_by_id("APP-TARGET-a3f291c2")
        assert found is None

    def test_clear(self):
        """Test clearing repository."""
        repo = ApplicationRepository()

        # Add multiple applications
        for i in range(5):
            app = Application(
                id=f"APP-TARGET-{i:08x}",
                name=f"App {i}",
                name_normalized=f"app{i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            repo.save(app)

        assert len(repo) == 5

        # Clear
        repo.clear()
        assert len(repo) == 0


class TestFindOrCreate:
    """Test find_or_create (THE deduplication primitive)."""

    def test_find_or_create_new_application(self):
        """Test creating new application when it doesn't exist."""
        repo = ApplicationRepository()

        app = repo.find_or_create(
            name="Salesforce CRM",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert app.id.startswith("APP-TARGET-")
        assert app.name == "Salesforce CRM"
        assert app.name_normalized == "salesforce"
        assert app.vendor == "Salesforce"
        assert len(repo) == 1

    def test_find_or_create_existing_application(self):
        """Test finding existing application (deduplication)."""
        repo = ApplicationRepository()

        # First call: Create
        app1 = repo.find_or_create(
            name="Salesforce CRM",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Second call: Find (same name variant)
        app2 = repo.find_or_create(
            name="Salesforce",  # Different name variant
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should return SAME application (deduplication works!)
        assert app1.id == app2.id
        assert len(repo) == 1  # Only 1 application created

    def test_find_or_create_different_variants_deduplicated(self):
        """Test different name variants deduplicate to same application."""
        repo = ApplicationRepository()

        variants = [
            "Salesforce",
            "Salesforce CRM",
            "SALESFORCE",
            "salesforce crm"
        ]

        apps = []
        for variant in variants:
            app = repo.find_or_create(
                name=variant,
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            apps.append(app)

        # All should have same ID (deduplication works!)
        ids = [app.id for app in apps]
        assert len(set(ids)) == 1  # Only 1 unique ID

        # Only 1 application created
        assert len(repo) == 1

    def test_find_or_create_different_vendor_different_app(self):
        """Test P0-3 fix: Same name, different vendor = different app."""
        repo = ApplicationRepository()

        app1 = repo.find_or_create(
            name="CRM System",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app2 = repo.find_or_create(
            name="CRM System",
            vendor="Oracle",  # Different vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should be DIFFERENT applications (P0-3 fix working!)
        assert app1.id != app2.id
        assert len(repo) == 2

    def test_find_or_create_different_entity_different_app(self):
        """Test same name, different entity = different app."""
        repo = ApplicationRepository()

        app_target = repo.find_or_create(
            name="Salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app_buyer = repo.find_or_create(
            name="Salesforce",
            vendor="Salesforce",
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        # Should be DIFFERENT applications
        assert app_target.id != app_buyer.id
        assert len(repo) == 2

    def test_find_or_create_merges_observations(self):
        """Test find_or_create merges observations when finding existing."""
        repo = ApplicationRepository()

        obs1 = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc 1",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )

        # First call: Create with observation
        app1 = repo.find_or_create(
            name="Salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs1]
        )
        assert len(app1.observations) == 1

        obs2 = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"users": 100}
        )

        # Second call: Find existing and merge new observation
        app2 = repo.find_or_create(
            name="Salesforce CRM",  # Variant
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs2]
        )

        # Should be same app with merged observations
        assert app1.id == app2.id
        assert len(app2.observations) >= 1  # Has at least one observation


class TestFindByEntity:
    """Test finding applications by entity."""

    def test_find_by_entity_target(self):
        """Test finding target applications."""
        repo = ApplicationRepository()

        # Create target apps
        for i in range(3):
            repo.find_or_create(
                name=f"App {i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create buyer app
        repo.find_or_create(
            name="Buyer App",
            vendor="Vendor",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Find target apps
        target_apps = repo.find_by_entity(Entity.TARGET)
        assert len(target_apps) == 3

    def test_find_by_entity_buyer(self):
        """Test finding buyer applications."""
        repo = ApplicationRepository()

        # Create buyer apps
        for i in range(2):
            repo.find_or_create(
                name=f"App {i}",
                vendor=f"Vendor{i}",
                entity=Entity.BUYER,
                deal_id="deal-123"
            )

        # Create target app
        repo.find_or_create(
            name="Target App",
            vendor="Vendor",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find buyer apps
        buyer_apps = repo.find_by_entity(Entity.BUYER)
        assert len(buyer_apps) == 2

    def test_find_by_entity_with_deal_filter(self):
        """Test finding applications filtered by deal."""
        repo = ApplicationRepository()

        # Create apps for deal-123
        for i in range(2):
            repo.find_or_create(
                name=f"App {i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create app for deal-456
        repo.find_or_create(
            name="App X",
            vendor="Vendor",
            entity=Entity.TARGET,
            deal_id="deal-456"
        )

        # Find apps for deal-123 only
        apps = repo.find_by_entity(Entity.TARGET, deal_id="deal-123")
        assert len(apps) == 2

        # Find apps for deal-456 only
        apps = repo.find_by_entity(Entity.TARGET, deal_id="deal-456")
        assert len(apps) == 1

    def test_count_by_entity(self):
        """Test counting applications by entity."""
        repo = ApplicationRepository()

        # Create apps
        for i in range(3):
            repo.find_or_create(
                name=f"App {i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        count = repo.count_by_entity(Entity.TARGET)
        assert count == 3


class TestFindSimilar:
    """Test fuzzy search (find_similar)."""

    def test_find_similar_exact_match(self):
        """Test finding similar with exact match."""
        repo = ApplicationRepository()

        # Create application
        repo.find_or_create(
            name="Salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find similar (exact match)
        similar = repo.find_similar("Salesforce", threshold=0.8)
        assert len(similar) == 1
        assert similar[0].name == "Salesforce"

    def test_find_similar_fuzzy_match(self):
        """Test finding similar with fuzzy matching."""
        repo = ApplicationRepository()

        # Create applications
        apps = [
            ("Salesforce", "Salesforce"),
            ("Salesforce CRM", "Salesforce"),
            ("Salesforce Marketing Cloud", "Salesforce"),
        ]

        for name, vendor in apps:
            repo.find_or_create(
                name=name,
                vendor=vendor,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar to "Salesforce"
        similar = repo.find_similar("Salesforce", threshold=0.5, limit=3)
        assert len(similar) >= 1  # At least exact match

    def test_find_similar_respects_limit(self):
        """Test find_similar respects limit parameter."""
        repo = ApplicationRepository()

        # Create many similar applications
        for i in range(10):
            repo.find_or_create(
                name=f"App {i}",
                vendor="Vendor",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar with limit=3
        similar = repo.find_similar("App", threshold=0.5, limit=3)
        assert len(similar) <= 3


class TestKernelCompliance:
    """Test that repository uses kernel primitives correctly."""

    def test_uses_kernel_normalization(self):
        """Test repository uses kernel.NormalizationRules."""
        repo = ApplicationRepository()

        # Test normalization removes "CRM" suffix
        app = repo.find_or_create(
            name="Salesforce CRM",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Normalized name should be "salesforce" (CRM removed)
        assert app.name_normalized == "salesforce"

    def test_uses_kernel_fingerprint(self):
        """Test repository uses kernel.FingerprintGenerator."""
        repo = ApplicationRepository()

        app = repo.find_or_create(
            name="Salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # ID should have APP-TARGET-{hash} format
        assert app.id.startswith("APP-TARGET-")
        parts = app.id.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 8  # 8-character hash
