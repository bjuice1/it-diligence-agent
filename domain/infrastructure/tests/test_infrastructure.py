"""
Tests for Infrastructure aggregate (infrastructure.py).

Coverage target: 80%+
Critical: Tests kernel integration, observation management, vendor=None support

Created: 2026-02-12 (Worker 3 - Infrastructure Domain, Task-019)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.infrastructure.infrastructure import Infrastructure


class TestInfrastructureCreation:
    """Test infrastructure creation and validation."""

    def test_create_valid_infrastructure_with_vendor(self):
        """Test creating infrastructure with vendor (cloud)."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2 t3.large",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra.id == "INFRA-TARGET-a3f291c2"
        assert infra.name == "AWS EC2 t3.large"
        assert infra.name_normalized == "aws ec2"
        assert infra.vendor == "AWS"
        assert infra.entity == Entity.TARGET
        assert infra.deal_id == "deal-123"
        assert len(infra.observations) == 0

    def test_create_valid_infrastructure_without_vendor(self):
        """Test creating infrastructure without vendor (on-prem)."""
        infra = Infrastructure(
            id="INFRA-TARGET-b4e8f1d3",
            name="On-Prem Data Center",
            name_normalized="on-prem data center",
            vendor=None,  # On-prem has no vendor
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra.id == "INFRA-TARGET-b4e8f1d3"
        assert infra.name == "On-Prem Data Center"
        assert infra.vendor is None  # ✅ vendor=None works

    def test_infrastructure_requires_id(self):
        """Test infrastructure requires ID."""
        with pytest.raises(TypeError):
            Infrastructure(
                # Missing id
                name="AWS EC2",
                name_normalized="aws ec2",
                vendor="AWS",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_infrastructure_requires_valid_id_format(self):
        """Test infrastructure validates ID format."""
        with pytest.raises(ValueError, match="Invalid infrastructure ID format"):
            Infrastructure(
                id="INVALID-FORMAT",
                name="AWS EC2",
                name_normalized="aws ec2",
                vendor="AWS",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_infrastructure_requires_name(self):
        """Test infrastructure requires name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Infrastructure(
                id="INFRA-TARGET-a3f291c2",
                name="",  # Empty name
                name_normalized="aws ec2",
                vendor="AWS",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_infrastructure_requires_deal_id(self):
        """Test infrastructure requires deal_id for multi-tenant isolation."""
        with pytest.raises(ValueError, match="deal_id is required"):
            Infrastructure(
                id="INFRA-TARGET-a3f291c2",
                name="AWS EC2",
                name_normalized="aws ec2",
                vendor="AWS",
                entity=Entity.TARGET,
                deal_id=""  # Empty deal_id
            )

    def test_infrastructure_requires_entity_enum(self):
        """Test infrastructure validates entity is Entity enum."""
        with pytest.raises(ValueError, match="must be Entity enum"):
            Infrastructure(
                id="INFRA-TARGET-a3f291c2",
                name="AWS EC2",
                name_normalized="aws ec2",
                vendor="AWS",
                entity="target",  # String, not Entity enum
                deal_id="deal-123"
            )


class TestInfrastructureObservations:
    """Test observation management (kernel.Observation)."""

    def test_add_observation(self):
        """Test adding observation to infrastructure."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
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
            data={"cost": 50000}
        )

        infra.add_observation(obs)

        assert len(infra.observations) == 1
        assert infra.observations[0].source_type == "table"
        assert infra.observations[0].data["cost"] == 50000

    def test_add_observation_validates_entity_match(self):
        """Test observation entity must match infrastructure entity."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
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
            data={"cost": 50000}
        )

        with pytest.raises(ValueError, match="entity"):
            infra.add_observation(obs)

    def test_add_observation_validates_deal_id_match(self):
        """Test observation deal_id must match infrastructure deal_id."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
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
            data={"cost": 50000}
        )

        with pytest.raises(ValueError, match="deal_id"):
            infra.add_observation(obs)

    def test_observation_priority_merging(self):
        """Test observations are merged by priority."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Add low priority observation
        obs1 = Observation(
            source_type="llm_assumption",
            confidence=0.5,
            evidence="Doc 1",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 10000}
        )
        infra.add_observation(obs1)

        # Add high priority observation
        obs2 = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )
        infra.add_observation(obs2)

        # get_cost_from_observations should return higher priority value
        cost = infra.get_cost_from_observations()
        assert cost == 50000  # Table (priority 3) beats llm_assumption (priority 1)

    def test_get_cost_from_observations(self):
        """Test extracting cost from observations."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
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
            data={"cost": 75000}
        )
        infra.add_observation(obs)

        cost = infra.get_cost_from_observations()
        assert cost == 75000.0


class TestInfrastructureMerge:
    """Test infrastructure merging (deduplication)."""

    def test_merge_infrastructure(self):
        """Test merging two infrastructure aggregates."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2 Instance",
            name_normalized="aws ec2",
            vendor="AWS",
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
            data={"cost": 50000}
        )
        infra1.add_observation(obs1)

        obs2 = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="Doc 2",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"users": 100}
        )
        infra2.add_observation(obs2)

        # Merge infra2 into infra1
        infra1.merge(infra2)

        # Should have both observations
        assert len(infra1.observations) == 2

    def test_merge_validates_same_entity(self):
        """Test merge validates same entity."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-BUYER-b4e8f1d3",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        with pytest.raises(ValueError, match="different entities"):
            infra1.merge(infra2)

    def test_merge_validates_same_deal(self):
        """Test merge validates same deal_id."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-TARGET-b4e8f1d3",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        with pytest.raises(ValueError, match="different deals"):
            infra1.merge(infra2)


class TestInfrastructureDuplicateDetection:
    """Test duplicate detection (is_duplicate_of)."""

    def test_is_duplicate_exact_match(self):
        """Test exact duplicate detection."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",  # Same ID
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert infra1.is_duplicate_of(infra2)

    def test_is_duplicate_different_entity_not_duplicate(self):
        """Test different entity = not duplicate."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-BUYER-b4e8f1d3",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.BUYER,  # Different entity
            deal_id="deal-123"
        )

        assert not infra1.is_duplicate_of(infra2)

    def test_is_duplicate_different_deal_not_duplicate(self):
        """Test different deal_id = not duplicate."""
        infra1 = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        infra2 = Infrastructure(
            id="INFRA-TARGET-b4e8f1d3",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        assert not infra1.is_duplicate_of(infra2)


class TestInfrastructureSerialization:
    """Test to_dict and from_dict."""

    def test_to_dict(self):
        """Test serializing infrastructure to dictionary."""
        infra = Infrastructure(
            id="INFRA-TARGET-a3f291c2",
            name="AWS EC2",
            name_normalized="aws ec2",
            vendor="AWS",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        data = infra.to_dict()

        assert data["id"] == "INFRA-TARGET-a3f291c2"
        assert data["name"] == "AWS EC2"
        assert data["name_normalized"] == "aws ec2"
        assert data["vendor"] == "AWS"
        assert data["entity"] == "target"
        assert data["deal_id"] == "deal-123"

    def test_from_dict(self):
        """Test deserializing infrastructure from dictionary."""
        data = {
            "id": "INFRA-TARGET-a3f291c2",
            "name": "AWS EC2",
            "name_normalized": "aws ec2",
            "vendor": "AWS",
            "entity": "target",
            "deal_id": "deal-123",
            "observations": [],
            "created_at": "2026-02-12T12:00:00",
            "updated_at": "2026-02-12T12:00:00"
        }

        infra = Infrastructure.from_dict(data)

        assert infra.id == "INFRA-TARGET-a3f291c2"
        assert infra.name == "AWS EC2"
        assert infra.vendor == "AWS"
        assert infra.entity == Entity.TARGET
        assert infra.deal_id == "deal-123"

    def test_from_dict_with_vendor_none(self):
        """Test deserializing on-prem infrastructure (vendor=None)."""
        data = {
            "id": "INFRA-TARGET-b4e8f1d3",
            "name": "On-Prem Data Center",
            "name_normalized": "on-prem data center",
            "vendor": None,  # On-prem has no vendor
            "entity": "target",
            "deal_id": "deal-123",
            "observations": [],
            "created_at": "2026-02-12T12:00:00",
            "updated_at": "2026-02-12T12:00:00"
        }

        infra = Infrastructure.from_dict(data)

        assert infra.vendor is None  # ✅ vendor=None works
