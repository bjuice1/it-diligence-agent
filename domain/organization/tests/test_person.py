"""
Tests for Person aggregate (person.py).

Coverage target: 80%+
Critical: Tests kernel integration, observation management, vendor=None enforcement

Created: 2026-02-12 (Worker 4 - Organization Domain, Task-024)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.organization.person import Person


class TestPersonCreation:
    """Test person creation and validation."""

    def test_create_valid_person(self):
        """Test creating person (vendor must be None)."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith - CTO",
            name_normalized="john smith",
            vendor=None,  # Must be None for people
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert person.id == "ORG-TARGET-f3b8c9d2"
        assert person.name == "John Smith - CTO"
        assert person.name_normalized == "john smith"
        assert person.vendor is None  # ✅ Vendor is None
        assert person.entity == Entity.TARGET
        assert person.deal_id == "deal-123"
        assert len(person.observations) == 0

    def test_create_team_department(self):
        """Test creating team/department."""
        team = Person(
            id="ORG-TARGET-a1b2c3d4",
            name="IT Department",
            name_normalized="it department",
            vendor=None,  # Departments have no vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert team.id == "ORG-TARGET-a1b2c3d4"
        assert team.name == "IT Department"
        assert team.vendor is None  # ✅ Vendor is None

    def test_person_vendor_must_be_none(self):
        """Test person validates vendor is None."""
        with pytest.raises(ValueError, match="vendor must be None"):
            Person(
                id="ORG-TARGET-f3b8c9d2",
                name="John Smith",
                name_normalized="john smith",
                vendor="Some Vendor",  # ❌ Invalid - people have no vendor
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_person_requires_id(self):
        """Test person requires ID."""
        with pytest.raises(TypeError):
            Person(
                # Missing id
                name="John Smith",
                name_normalized="john smith",
                vendor=None,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_person_requires_valid_id_format(self):
        """Test person validates ID format."""
        with pytest.raises(ValueError, match="Invalid person ID format"):
            Person(
                id="INVALID-FORMAT",
                name="John Smith",
                name_normalized="john smith",
                vendor=None,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_person_requires_name(self):
        """Test person requires name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Person(
                id="ORG-TARGET-f3b8c9d2",
                name="",  # Empty name
                name_normalized="john smith",
                vendor=None,
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_person_requires_deal_id(self):
        """Test person requires deal_id for multi-tenant isolation."""
        with pytest.raises(ValueError, match="deal_id is required"):
            Person(
                id="ORG-TARGET-f3b8c9d2",
                name="John Smith",
                name_normalized="john smith",
                vendor=None,
                entity=Entity.TARGET,
                deal_id=""  # Empty deal_id
            )

    def test_person_requires_entity_enum(self):
        """Test person validates entity is Entity enum."""
        with pytest.raises(ValueError, match="must be Entity enum"):
            Person(
                id="ORG-TARGET-f3b8c9d2",
                name="John Smith",
                name_normalized="john smith",
                vendor=None,
                entity="target",  # String, not Entity enum
                deal_id="deal-123"
            )


class TestPersonObservations:
    """Test observation management (kernel.Observation)."""

    def test_add_observation(self):
        """Test adding observation to person."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc page 5",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"role": "CTO", "department": "IT"}
        )

        person.add_observation(obs)

        assert len(person.observations) == 1
        assert person.observations[0].source_type == "table"
        assert person.observations[0].data["role"] == "CTO"

    def test_add_observation_validates_entity_match(self):
        """Test observation entity must match person entity."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.BUYER,  # Different entity!
            data={"role": "CTO"}
        )

        with pytest.raises(ValueError, match="entity"):
            person.add_observation(obs)

    def test_add_observation_validates_deal_id_match(self):
        """Test observation deal_id must match person deal_id."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc",
            extracted_at=datetime.now(),
            deal_id="deal-456",  # Different deal!
            entity=Entity.TARGET,
            data={"role": "CTO"}
        )

        with pytest.raises(ValueError, match="deal_id"):
            person.add_observation(obs)

    def test_get_role_from_observations(self):
        """Test extracting role from observations."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"role": "Chief Technology Officer"}
        )
        person.add_observation(obs)

        role = person.get_role_from_observations()
        assert role == "Chief Technology Officer"


class TestPersonMerge:
    """Test person merging (deduplication)."""

    def test_merge_person(self):
        """Test merging two person aggregates."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith - CTO",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs1 = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc 1",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"role": "CTO"}
        )
        person1.add_observation(obs1)

        obs2 = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"department": "IT"}
        )
        person2.add_observation(obs2)

        # Merge person2 into person1
        person1.merge(person2)

        # Should have both observations
        assert len(person1.observations) == 2

    def test_merge_validates_same_entity(self):
        """Test merge validates same entity."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-BUYER-a1b2c3d4",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        with pytest.raises(ValueError, match="different entities"):
            person1.merge(person2)

    def test_merge_validates_same_deal(self):
        """Test merge validates same deal_id."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-TARGET-a1b2c3d4",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        with pytest.raises(ValueError, match="different deals"):
            person1.merge(person2)


class TestPersonDuplicateDetection:
    """Test duplicate detection (is_duplicate_of)."""

    def test_is_duplicate_exact_match(self):
        """Test exact duplicate detection."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-TARGET-f3b8c9d2",  # Same ID
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert person1.is_duplicate_of(person2)

    def test_is_duplicate_different_entity_not_duplicate(self):
        """Test different entity = not duplicate."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-BUYER-a1b2c3d4",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        assert not person1.is_duplicate_of(person2)

    def test_is_duplicate_different_deal_not_duplicate(self):
        """Test different deal_id = not duplicate."""
        person1 = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        person2 = Person(
            id="ORG-TARGET-a1b2c3d4",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        assert not person1.is_duplicate_of(person2)


class TestPersonSerialization:
    """Test to_dict and from_dict."""

    def test_to_dict(self):
        """Test serializing person to dictionary."""
        person = Person(
            id="ORG-TARGET-f3b8c9d2",
            name="John Smith",
            name_normalized="john smith",
            vendor=None,
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        data = person.to_dict()

        assert data["id"] == "ORG-TARGET-f3b8c9d2"
        assert data["name"] == "John Smith"
        assert data["name_normalized"] == "john smith"
        assert data["vendor"] is None  # ✅ Vendor is None
        assert data["entity"] == "target"
        assert data["deal_id"] == "deal-123"

    def test_from_dict(self):
        """Test deserializing person from dictionary."""
        data = {
            "id": "ORG-TARGET-f3b8c9d2",
            "name": "John Smith",
            "name_normalized": "john smith",
            "vendor": None,  # Vendor is None for people
            "entity": "target",
            "deal_id": "deal-123",
            "observations": [],
            "created_at": "2026-02-12T12:00:00",
            "updated_at": "2026-02-12T12:00:00"
        }

        person = Person.from_dict(data)

        assert person.id == "ORG-TARGET-f3b8c9d2"
        assert person.name == "John Smith"
        assert person.vendor is None  # ✅ Vendor is None
        assert person.entity == Entity.TARGET
        assert person.deal_id == "deal-123"
