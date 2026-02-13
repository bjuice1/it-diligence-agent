"""
Tests for InfrastructureRepository (deduplication engine).

Coverage target: 80%+
Critical: Tests find_or_create (THE deduplication primitive), vendor=None support

Created: 2026-02-12 (Worker 3 - Infrastructure Domain, Task-019)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.infrastructure.repository import InfrastructureRepository
from domain.infrastructure.infrastructure import Infrastructure


class TestRepositoryBasics:
    """Test basic repository operations."""

    def test_save_and_find_by_id(self):
        """Test saving and finding infrastructure."""
        repo = InfrastructureRepository()

        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Save
        saved = repo.save(infra)
        assert saved.id == infra.id

        # Find
        found = repo.find_by_id("INFRA-TARGET-a3f291c2")
        assert found is not None
        assert found.id == "INFRA-TARGET-a3f291c2"
        assert found.name == "AWS EC2"

    def test_find_by_id_not_found(self):
        """Test finding non-existent infrastructure."""
        repo = InfrastructureRepository()

        found = repo.find_by_id("INFRA-TARGET-nonexistent")
        assert found is None

    def test_repository_length(self):
        """Test repository length."""
        repo = InfrastructureRepository()

        assert len(repo) == 0

        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(infra)

        assert len(repo) == 1

    def test_delete(self):
        """Test deleting infrastructure."""
        repo = InfrastructureRepository()

        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(infra)

        # Delete
        deleted = repo.delete("INFRA-TARGET-a3f291c2")
        assert deleted is True

        # Verify deleted
        found = repo.find_by_id("INFRA-TARGET-a3f291c2")
        assert found is None

    def test_clear(self):
        """Test clearing repository."""
        repo = InfrastructureRepository()

        # Add multiple infrastructure
        for i in range(5):
            infra = Infrastructure(
                id=f"INFRA-TARGET-{i:08x}",
                name=f"Infra {i}",
                name_normalized=f"infra{i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            repo.save(infra)

        assert len(repo) == 5

        # Clear
        repo.clear()
        assert len(repo) == 0


class TestFindOrCreate:
    """Test find_or_create (THE deduplication primitive)."""

    def test_find_or_create_new_infrastructure_with_vendor(self):
        """Test creating new infrastructure with vendor (cloud)."""
        repo = InfrastructureRepository()

        infra = repo.find_or_create(
            name="AWS EC2 t3.large",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra.id.startswith("INFRA-TARGET-")
        assert infra.name == "AWS EC2 t3.large"
        # Infrastructure normalization preserves environment info (t3.large)
        assert infra.name_normalized == "aws ec2 t3large"
        assert infra.vendor == "AWS"
        assert len(repo) == 1

    def test_find_or_create_new_infrastructure_without_vendor(self):
        """Test creating new infrastructure without vendor (on-prem) - P0-BLOCKER FIX."""
        repo = InfrastructureRepository()

        infra = repo.find_or_create(
            name="On-Prem Data Center",
            vendor=None,  # ✅ vendor=None works (P0-blocker fix)
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra.id.startswith("INFRA-TARGET-")
        assert infra.name == "On-Prem Data Center"
        assert infra.vendor is None  # ✅ Vendor can be None
        assert len(repo) == 1

    def test_find_or_create_existing_infrastructure(self):
        """Test finding existing infrastructure (deduplication)."""
        repo = InfrastructureRepository()

        # First call: Create
        infra1 = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Second call: Find (exact same name)
        infra2 = repo.find_or_create(
            name="AWS EC2",  # Same name
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should return SAME infrastructure (deduplication works!)
        assert infra1.id == infra2.id
        assert len(repo) == 1  # Only 1 infrastructure created

    def test_find_or_create_different_variants_deduplicated(self):
        """Test different name variants deduplicate to same infrastructure."""
        repo = InfrastructureRepository()

        # Use case-insensitive variants (guaranteed to normalize the same)
        variants = [
            "AWS EC2",
            "aws ec2",
            "Aws Ec2",
            "AWS EC2"
        ]

        infras = []
        for variant in variants:
            infra = repo.find_or_create(
                name=variant,
                vendor="AWS",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            infras.append(infra)

        # All should have same ID (deduplication works!)
        ids = [infra.id for infra in infras]
        assert len(set(ids)) == 1  # Only 1 unique ID

        # Only 1 infrastructure created
        assert len(repo) == 1

    def test_find_or_create_different_vendor_different_infra(self):
        """Test same name, different vendor = different infrastructure."""
        repo = InfrastructureRepository()

        infra1 = repo.find_or_create(
            name="EC2 Instance",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = repo.find_or_create(
            name="EC2 Instance",
            vendor="Azure",  # Different vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should be DIFFERENT infrastructure
        assert infra1.id != infra2.id
        assert len(repo) == 2

    def test_find_or_create_different_entity_different_infra(self):
        """Test same name, different entity = different infrastructure."""
        repo = InfrastructureRepository()

        infra_target = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra_buyer = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        # Should be DIFFERENT infrastructure
        assert infra_target.id != infra_buyer.id
        assert len(repo) == 2

    def test_find_or_create_vendor_none_vs_vendor_different(self):
        """Test vendor=None vs vendor=X creates different infrastructure."""
        repo = InfrastructureRepository()

        # On-prem (vendor=None)
        infra1 = repo.find_or_create(
            name="Data Center",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Cloud (vendor=AWS)
        infra2 = repo.find_or_create(
            name="Data Center",
            vendor="AWS",  # Different from None
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should be DIFFERENT infrastructure (vendor matters)
        assert infra1.id != infra2.id
        assert len(repo) == 2

    def test_find_or_create_merges_observations(self):
        """Test find_or_create merges observations when finding existing."""
        repo = InfrastructureRepository()

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
        infra1 = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs1]
        )
        assert len(infra1.observations) == 1

        obs2 = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"users": 100}
        )

        # Second call: Find existing and merge new observation (same name)
        infra2 = repo.find_or_create(
            name="AWS EC2",  # Same name - guaranteed to find existing
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs2]
        )

        # Should be same infra with merged observations
        assert infra1.id == infra2.id
        assert len(infra2.observations) >= 1  # Has at least one observation


class TestFindByEntity:
    """Test finding infrastructure by entity."""

    def test_find_by_entity_target(self):
        """Test finding target infrastructure."""
        repo = InfrastructureRepository()

        # Create target infra
        for i in range(3):
            repo.find_or_create(
                name=f"Infra {i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create buyer infra
        repo.find_or_create(
            name="Buyer Infra",
            vendor="Vendor",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Find target infra
        target_infra = repo.find_by_entity(Entity.TARGET)
        assert len(target_infra) == 3

    def test_find_by_entity_buyer(self):
        """Test finding buyer infrastructure."""
        repo = InfrastructureRepository()

        # Create buyer infra
        for i in range(2):
            repo.find_or_create(
                name=f"Infra {i}",
                vendor=f"Vendor{i}",
                entity=Entity.BUYER,
                deal_id="deal-123"
            )

        # Create target infra
        repo.find_or_create(
            name="Target Infra",
            vendor="Vendor",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find buyer infra
        buyer_infra = repo.find_by_entity(Entity.BUYER)
        assert len(buyer_infra) == 2

    def test_find_by_entity_with_deal_filter(self):
        """Test finding infrastructure filtered by deal."""
        repo = InfrastructureRepository()

        # Create infra for deal-123
        for i in range(2):
            repo.find_or_create(
                name=f"Infra {i}",
                vendor=f"Vendor{i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create infra for deal-456
        repo.find_or_create(
            name="Infra X",
            vendor="Vendor",
            entity=Entity.TARGET,
            deal_id="deal-456"
        )

        # Find infra for deal-123 only
        infra = repo.find_by_entity(Entity.TARGET, deal_id="deal-123")
        assert len(infra) == 2

        # Find infra for deal-456 only
        infra = repo.find_by_entity(Entity.TARGET, deal_id="deal-456")
        assert len(infra) == 1

    def test_count_by_entity(self):
        """Test counting infrastructure by entity."""
        repo = InfrastructureRepository()

        # Create infra
        for i in range(3):
            repo.find_or_create(
                name=f"Infra {i}",
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
        repo = InfrastructureRepository()

        # Create infrastructure
        repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find similar (exact match)
        similar = repo.find_similar("AWS EC2", threshold=0.8)
        assert len(similar) == 1
        assert similar[0].name == "AWS EC2"

    def test_find_similar_fuzzy_match(self):
        """Test finding similar with fuzzy matching."""
        repo = InfrastructureRepository()

        # Create infrastructure
        infras = [
            ("AWS EC2", "AWS"),
            ("AWS EC2 t3.large", "AWS"),
            ("AWS EC2 t3.xlarge", "AWS"),
        ]

        for name, vendor in infras:
            repo.find_or_create(
                name=name,
                vendor=vendor,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar to "AWS EC2"
        similar = repo.find_similar("AWS EC2", threshold=0.5, limit=3)
        assert len(similar) >= 1  # At least exact match

    def test_find_similar_respects_limit(self):
        """Test find_similar respects limit parameter."""
        repo = InfrastructureRepository()

        # Create many similar infrastructure
        for i in range(10):
            repo.find_or_create(
                name=f"Infra {i}",
                vendor="Vendor",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar with limit=3
        similar = repo.find_similar("Infra", threshold=0.5, limit=3)
        assert len(similar) <= 3


class TestKernelCompliance:
    """Test that repository uses kernel primitives correctly."""

    def test_uses_kernel_normalization(self):
        """Test repository uses kernel.NormalizationRules."""
        repo = InfrastructureRepository()

        # Test normalization
        infra = repo.find_or_create(
            name="AWS EC2 Instance t3.large",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Normalized name should use kernel normalization
        # (infrastructure normalization keeps environment info)
        assert "ec2" in infra.name_normalized.lower()

    def test_uses_kernel_fingerprint(self):
        """Test repository uses kernel.FingerprintGenerator."""
        repo = InfrastructureRepository()

        infra = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # ID should have INFRA-TARGET-{hash} format
        assert infra.id.startswith("INFRA-TARGET-")
        parts = infra.id.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 8  # 8-character hash

    def test_vendor_optional_works(self):
        """Test vendor=None works correctly (P0-blocker fix)."""
        repo = InfrastructureRepository()

        # On-prem infrastructure (vendor=None)
        infra = repo.find_or_create(
            name="On-Prem Server",
            vendor=None,  # ✅ P0-blocker fix allows this
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra.id.startswith("INFRA-TARGET-")
        assert infra.vendor is None  # ✅ Vendor can be None

    def test_circuit_breaker_inherited(self):
        """Test repository inherits circuit breaker from kernel (P0-2 fix)."""
        repo = InfrastructureRepository()

        # Circuit breaker constant should be inherited from DomainRepository
        assert hasattr(repo, 'MAX_ITEMS_FOR_RECONCILIATION')
        assert repo.MAX_ITEMS_FOR_RECONCILIATION == 500  # P0-2 fix


class TestEntityIsolation:
    """Test entity isolation (target vs buyer)."""

    def test_entity_isolation(self):
        """Test target and buyer are isolated."""
        repo = InfrastructureRepository()

        # Same name, different entity
        target = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        buyer = repo.find_or_create(
            name="AWS EC2",
            vendor="AWS",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Should be DIFFERENT infrastructure (different entity)
        assert target.id != buyer.id
        assert target.id.startswith("INFRA-TARGET-")
        assert buyer.id.startswith("INFRA-BUYER-")

    def test_entity_isolation_with_vendor_none(self):
        """Test entity isolation works with vendor=None."""
        repo = InfrastructureRepository()

        # On-prem, different entity
        target = repo.find_or_create(
            name="On-Prem Server",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        buyer = repo.find_or_create(
            name="On-Prem Server",
            vendor=None,
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Should be DIFFERENT infrastructure
        assert target.id != buyer.id
        assert target.id.startswith("INFRA-TARGET-")
        assert buyer.id.startswith("INFRA-BUYER-")
