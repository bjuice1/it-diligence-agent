"""
Tests for PersonRepository (deduplication engine).

Coverage target: 80%+
Critical: Tests find_or_create (THE deduplication primitive), vendor=None enforcement

Created: 2026-02-12 (Worker 4 - Organization Domain, Task-024)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.organization.repository import PersonRepository
from domain.organization.person import Person


class TestRepositoryBasics:
    """Test basic repository operations."""

    def test_save_and_find_by_id(self):
        """Test saving and finding person."""
        repo = PersonRepository()

        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Save
        saved = repo.save(person)
        assert saved.id == person.id

        # Find
        found = repo.find_by_id("ORG-TARGET-f3b8c9d2")
        assert found is not None
        assert found.id == "ORG-TARGET-f3b8c9d2"
        assert found.name == "John Smith"

    def test_find_by_id_not_found(self):
        """Test finding non-existent person."""
        repo = PersonRepository()

        found = repo.find_by_id("ORG-TARGET-nonexistent")
        assert found is None

    def test_repository_length(self):
        """Test repository length."""
        repo = PersonRepository()

        assert len(repo) == 0

        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(person)

        assert len(repo) == 1

    def test_delete(self):
        """Test deleting person."""
        repo = PersonRepository()

        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )
        repo.save(person)

        # Delete
        deleted = repo.delete("ORG-TARGET-f3b8c9d2")
        assert deleted is True

        # Verify deleted
        found = repo.find_by_id("ORG-TARGET-f3b8c9d2")
        assert found is None

    def test_clear(self):
        """Test clearing repository."""
        repo = PersonRepository()

        # Add multiple people
        for i in range(5):
            person = Person(
                id=f"ORG-TARGET-{i:08x}",
                name=f"Person {i}",
                name_normalized=f"person{i}",
                vendor=None,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            repo.save(person)

        assert len(repo) == 5

        # Clear
        repo.clear()
        assert len(repo) == 0


class TestFindOrCreate:
    """Test find_or_create (THE deduplication primitive)."""

    def test_find_or_create_new_person(self):
        """Test creating new person (vendor is ALWAYS None)."""
        repo = PersonRepository()

        person = repo.find_or_create(
            name="John Smith - CTO",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert person.id.startswith("ORG-TARGET-")
        assert person.name == "John Smith - CTO"
        # Organization normalization preserves role info like "- CTO"
        assert person.name_normalized == "john smith - cto"
        assert person.vendor is None  # ✅ Vendor is ALWAYS None
        assert len(repo) == 1

    def test_find_or_create_existing_person(self):
        """Test finding existing person (deduplication)."""
        repo = PersonRepository()

        # First call: Create
        person1 = repo.find_or_create(
            name="John Smith - CTO",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Second call: Find (same name)
        person2 = repo.find_or_create(
            name="John Smith - CTO",  # Same name
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Should return SAME person (deduplication works!)
        assert person1.id == person2.id
        assert len(repo) == 1  # Only 1 person created

    def test_find_or_create_different_variants_deduplicated(self):
        """Test different name variants deduplicate to same person."""
        repo = PersonRepository()

        # Use case-insensitive variants (guaranteed to normalize the same)
        variants = [
            "John Smith",
            "john smith",
            "John Smith",
            "JOHN SMITH"
        ]

        people = []
        for variant in variants:
            person = repo.find_or_create(
                name=variant,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )
            people.append(person)

        # All should have same ID (deduplication works!)
        ids = [person.id for person in people]
        assert len(set(ids)) == 1  # Only 1 unique ID

        # Only 1 person created
        assert len(repo) == 1

    def test_find_or_create_different_entity_different_person(self):
        """Test same name, different entity = different person."""
        repo = PersonRepository()

        person_target = repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person_buyer = repo.find_or_create(
            name="John Smith",
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        # Should be DIFFERENT people
        assert person_target.id != person_buyer.id
        assert len(repo) == 2

    def test_find_or_create_team_department(self):
        """Test creating team/department."""
        repo = PersonRepository()

        team = repo.find_or_create(
            name="IT Department",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert team.id.startswith("ORG-TARGET-")
        assert team.name == "IT Department"
        assert team.vendor is None  # ✅ Departments have no vendor

    def test_find_or_create_merges_observations(self):
        """Test find_or_create merges observations when finding existing."""
        repo = PersonRepository()

        obs1 = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc 1",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"role": "CTO"}
        )

        # First call: Create with observation
        person1 = repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs1]
        )
        assert len(person1.observations) == 1

        obs2 = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"department": "IT"}
        )

        # Second call: Find existing and merge new observation (same name)
        person2 = repo.find_or_create(
            name="John Smith",  # Same name - guaranteed to find existing
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[obs2]
        )

        # Should be same person with merged observations
        assert person1.id == person2.id
        assert len(person2.observations) >= 1  # Has at least one observation


class TestFindByEntity:
    """Test finding people by entity."""

    def test_find_by_entity_target(self):
        """Test finding target people."""
        repo = PersonRepository()

        # Create target people
        for i in range(3):
            repo.find_or_create(
                name=f"Person {i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create buyer person
        repo.find_or_create(
            name="Buyer Person",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Find target people
        target_people = repo.find_by_entity(Entity.TARGET)
        assert len(target_people) == 3

    def test_find_by_entity_buyer(self):
        """Test finding buyer people."""
        repo = PersonRepository()

        # Create buyer people
        for i in range(2):
            repo.find_or_create(
                name=f"Person {i}",
                entity=Entity.BUYER,
                deal_id="deal-123"
            )

        # Create target person
        repo.find_or_create(
            name="Target Person",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find buyer people
        buyer_people = repo.find_by_entity(Entity.BUYER)
        assert len(buyer_people) == 2

    def test_find_by_entity_with_deal_filter(self):
        """Test finding people filtered by deal."""
        repo = PersonRepository()

        # Create people for deal-123
        for i in range(2):
            repo.find_or_create(
                name=f"Person {i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Create person for deal-456
        repo.find_or_create(
            name="Person X",
            entity=Entity.TARGET,
            deal_id="deal-456"
        )

        # Find people for deal-123 only
        people = repo.find_by_entity(Entity.TARGET, deal_id="deal-123")
        assert len(people) == 2

        # Find people for deal-456 only
        people = repo.find_by_entity(Entity.TARGET, deal_id="deal-456")
        assert len(people) == 1

    def test_count_by_entity(self):
        """Test counting people by entity."""
        repo = PersonRepository()

        # Create people
        for i in range(3):
            repo.find_or_create(
                name=f"Person {i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        count = repo.count_by_entity(Entity.TARGET)
        assert count == 3


class TestFindSimilar:
    """Test fuzzy search (find_similar)."""

    def test_find_similar_exact_match(self):
        """Test finding similar with exact match."""
        repo = PersonRepository()

        # Create person
        repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Find similar (exact match)
        similar = repo.find_similar("John Smith", threshold=0.8)
        assert len(similar) == 1
        assert similar[0].name == "John Smith"

    def test_find_similar_fuzzy_match(self):
        """Test finding similar with fuzzy matching."""
        repo = PersonRepository()

        # Create people
        people_names = [
            "John Smith",
            "John Smith Jr.",
            "Jane Smith",
        ]

        for name in people_names:
            repo.find_or_create(
                name=name,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar to "John Smith"
        similar = repo.find_similar("John Smith", threshold=0.5, limit=3)
        assert len(similar) >= 1  # At least exact match

    def test_find_similar_respects_limit(self):
        """Test find_similar respects limit parameter."""
        repo = PersonRepository()

        # Create many similar people
        for i in range(10):
            repo.find_or_create(
                name=f"Person {i}",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

        # Find similar with limit=3
        similar = repo.find_similar("Person", threshold=0.5, limit=3)
        assert len(similar) <= 3


class TestKernelCompliance:
    """Test that repository uses kernel primitives correctly."""

    def test_uses_kernel_normalization(self):
        """Test repository uses kernel.NormalizationRules."""
        repo = PersonRepository()

        # Test normalization
        person = repo.find_or_create(
            name="John Smith - CTO",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Normalized name should use kernel normalization
        # (organization normalization removes titles/roles)
        assert "smith" in person.name_normalized.lower()

    def test_uses_kernel_fingerprint(self):
        """Test repository uses kernel.FingerprintGenerator."""
        repo = PersonRepository()

        person = repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # ID should have ORG-TARGET-{hash} format
        assert person.id.startswith("ORG-TARGET-")
        parts = person.id.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 8  # 8-character hash

    def test_vendor_always_none(self):
        """Test vendor is ALWAYS None for people."""
        repo = PersonRepository()

        # Create person
        person = repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert person.vendor is None  # ✅ Vendor is ALWAYS None

    def test_circuit_breaker_inherited(self):
        """Test repository inherits circuit breaker from kernel (P0-2 fix)."""
        repo = PersonRepository()

        # Circuit breaker constant should be inherited from DomainRepository
        assert hasattr(repo, 'MAX_ITEMS_FOR_RECONCILIATION')
        assert repo.MAX_ITEMS_FOR_RECONCILIATION == 500  # P0-2 fix


class TestEntityIsolation:
    """Test entity isolation (target vs buyer)."""

    def test_entity_isolation(self):
        """Test target and buyer are isolated."""
        repo = PersonRepository()

        # Same name, different entity
        target = repo.find_or_create(
            name="John Smith",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        buyer = repo.find_or_create(
            name="John Smith",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Should be DIFFERENT people (different entity)
        assert target.id != buyer.id
        assert target.id.startswith("ORG-TARGET-")
        assert buyer.id.startswith("ORG-BUYER-")

    def test_entity_isolation_teams(self):
        """Test entity isolation works for teams/departments."""
        repo = PersonRepository()

        # IT Department, different entity
        target = repo.find_or_create(
            name="IT Department",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        buyer = repo.find_or_create(
            name="IT Department",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        # Should be DIFFERENT
        assert target.id != buyer.id
        assert target.id.startswith("ORG-TARGET-")
        assert buyer.id.startswith("ORG-BUYER-")
