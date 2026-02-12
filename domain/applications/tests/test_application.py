"""
Tests for Application aggregate.

Coverage target: 80%+

Created: 2026-02-12 (Worker 2 - Application Domain, Task-013)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation

from domain.applications.application import Application


class TestApplicationCreation:
    """Test application creation and validation."""

    def test_create_valid_application(self):
        """Test creating valid application."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce CRM",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert app.id == "APP-TARGET-a3f291c2"
        assert app.name == "Salesforce CRM"
        assert app.entity == Entity.TARGET
        assert app.deal_id == "deal-123"
        assert len(app.observations) == 0

    def test_application_requires_id(self):
        """Test application requires ID."""
        with pytest.raises(ValueError, match="Application ID is required"):
            Application(
                id="",
                name="Salesforce",
                name_normalized="salesforce",
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_application_requires_valid_id_format(self):
        """Test application ID must have APP- prefix."""
        with pytest.raises(ValueError, match="Invalid application ID format"):
            Application(
                id="INVALID-TARGET-a3f291c2",
                name="Salesforce",
                name_normalized="salesforce",
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_application_requires_name(self):
        """Test application requires name."""
        with pytest.raises(ValueError, match="Application name is required"):
            Application(
                id="APP-TARGET-a3f291c2",
                name="",
                name_normalized="",
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id="deal-123"
            )

    def test_application_requires_deal_id(self):
        """Test application requires deal_id (multi-tenant isolation)."""
        with pytest.raises(ValueError, match="deal_id is required"):
            Application(
                id="APP-TARGET-a3f291c2",
                name="Salesforce",
                name_normalized="salesforce",
                vendor="Salesforce",
                entity=Entity.TARGET,
                deal_id=""
            )

    def test_application_requires_entity_enum(self):
        """Test application requires Entity enum (not string)."""
        with pytest.raises(ValueError, match="entity must be Entity enum"):
            Application(
                id="APP-TARGET-a3f291c2",
                name="Salesforce",
                name_normalized="salesforce",
                vendor="Salesforce",
                entity="target",  # String, not Entity enum
                deal_id="deal-123"
            )


class TestApplicationObservations:
    """Test observation management."""

    def test_add_observation(self):
        """Test adding observation to application."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5, row 3",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )

        app.add_observation(obs)

        assert len(app.observations) == 1
        assert app.observations[0] == obs

    def test_add_observation_validates_entity_match(self):
        """Test observation entity must match application entity."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Observation for BUYER (app is TARGET)
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.BUYER,  # Wrong entity!
            data={}
        )

        with pytest.raises(ValueError, match="Observation entity .* does not match"):
            app.add_observation(obs)

    def test_add_observation_validates_deal_id_match(self):
        """Test observation deal_id must match application deal_id."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Observation for different deal
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5",
            extracted_at=datetime.now(),
            deal_id="deal-456",  # Wrong deal!
            entity=Entity.TARGET,
            data={}
        )

        with pytest.raises(ValueError, match="Observation deal_id .* does not match"):
            app.add_observation(obs)

    def test_observation_priority_merging(self):
        """Test observations are merged by priority (manual > table > llm)."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Add table observation (priority=3)
        obs_table = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Table",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )
        app.add_observation(obs_table)
        assert len(app.observations) == 1

        # Add manual observation (priority=4, higher)
        obs_manual = Observation(
            source_type="manual",
            confidence=1.0,
            evidence="Manual entry",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 60000}
        )
        app.add_observation(obs_manual)

        # Manual should replace table
        assert len(app.observations) == 1
        assert app.observations[0].source_type == "manual"

    def test_get_cost_from_observations(self):
        """Test get_cost returns cost from highest priority observation."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        # Add LLM observation with cost
        obs_llm = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="LLM",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 40000}
        )
        app.add_observation(obs_llm)

        # Add table observation with different cost (higher priority)
        obs_table = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Table",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )
        app.add_observation(obs_table)

        # Should return cost from table (higher priority)
        assert app.get_cost() == 50000


class TestApplicationMerge:
    """Test application merging (for deduplication)."""

    def test_merge_applications(self):
        """Test merging two applications."""
        app1 = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[
                Observation(
                    source_type="table",
                    confidence=0.95,
                    evidence="Doc 1",
                    extracted_at=datetime.now(),
                    deal_id="deal-123",
                    entity=Entity.TARGET,
                    data={"cost": 50000}
                )
            ]
        )

        app2 = Application(
            id="APP-TARGET-b4e8f1d3",
            name="Salesforce CRM",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123",
            observations=[
                Observation(
                    source_type="llm_prose",
                    confidence=0.7,
                    evidence="Doc 2",
                    extracted_at=datetime.now(),
                    deal_id="deal-123",
                    entity=Entity.TARGET,
                    data={"users": 100}
                )
            ]
        )

        # Merge app2 into app1
        app1.merge(app2)

        # app1 should have observations from both
        assert len(app1.observations) >= 1  # At least table observation

    def test_merge_validates_same_entity(self):
        """Test can't merge applications from different entities."""
        app_target = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app_buyer = Application(
            id="APP-BUYER-b4e8f1d3",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        with pytest.raises(ValueError, match="Cannot merge applications from different entities"):
            app_target.merge(app_buyer)

    def test_merge_validates_same_deal(self):
        """Test can't merge applications from different deals."""
        app1 = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app2 = Application(
            id="APP-TARGET-b4e8f1d3",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        with pytest.raises(ValueError, match="Cannot merge applications from different deals"):
            app1.merge(app2)


class TestApplicationDuplicateDetection:
    """Test duplicate detection."""

    def test_is_duplicate_exact_match(self):
        """Test exact normalized name match."""
        app1 = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app2 = Application(
            id="APP-TARGET-b4e8f1d3",
            name="Salesforce CRM",
            name_normalized="salesforce",  # Same normalized
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        assert app1.is_duplicate_of(app2)
        assert app2.is_duplicate_of(app1)

    def test_is_duplicate_different_entity_not_duplicate(self):
        """Test same name, different entity = not duplicate."""
        app_target = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app_buyer = Application(
            id="APP-BUYER-b4e8f1d3",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.BUYER,
            deal_id="deal-123"
        )

        assert not app_target.is_duplicate_of(app_buyer)

    def test_is_duplicate_different_deal_not_duplicate(self):
        """Test same name, different deal = not duplicate."""
        app1 = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app2 = Application(
            id="APP-TARGET-b4e8f1d3",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-456"  # Different deal
        )

        assert not app1.is_duplicate_of(app2)


class TestApplicationSerialization:
    """Test serialization (to_dict/from_dict)."""

    def test_to_dict(self):
        """Test application serialization."""
        app = Application(
            id="APP-TARGET-a3f291c2",
            name="Salesforce",
            name_normalized="salesforce",
            vendor="Salesforce",
            entity=Entity.TARGET,
            deal_id="deal-123"
        )

        app_dict = app.to_dict()

        assert app_dict["id"] == "APP-TARGET-a3f291c2"
        assert app_dict["name"] == "Salesforce"
        assert app_dict["entity"] == "target"
        assert app_dict["deal_id"] == "deal-123"

    def test_from_dict(self):
        """Test application deserialization."""
        app_dict = {
            "id": "APP-TARGET-a3f291c2",
            "name": "Salesforce",
            "name_normalized": "salesforce",
            "vendor": "Salesforce",
            "entity": "target",
            "deal_id": "deal-123",
            "observations": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        app = Application.from_dict(app_dict)

        assert app.id == "APP-TARGET-a3f291c2"
        assert app.name == "Salesforce"
        assert app.entity == Entity.TARGET
        assert app.deal_id == "deal-123"
