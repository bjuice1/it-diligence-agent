"""
Comprehensive tests for domain kernel.

CRITICAL: Must achieve 90%+ coverage.
Tests P0-3 fix (normalization collisions), P0-2 fix (reconciliation circuit breaker).

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-008)
"""

import pytest
from datetime import datetime

from domain.kernel.entity import Entity
from domain.kernel.observation import Observation
from domain.kernel.normalization import NormalizationRules
from domain.kernel.entity_inference import EntityInference
from domain.kernel.fingerprint import FingerprintGenerator
from domain.kernel.extraction import ExtractionCoordinator


class TestEntity:
    """Test Entity value object."""

    def test_entity_values(self):
        """Test entity enum values."""
        assert Entity.TARGET.value == "target"
        assert Entity.BUYER.value == "buyer"

    def test_entity_string_conversion(self):
        """Test string conversion."""
        assert str(Entity.TARGET) == "target"
        assert str(Entity.BUYER) == "buyer"

    def test_entity_from_string(self):
        """Test from_string() method."""
        assert Entity.from_string("target") == Entity.TARGET
        assert Entity.from_string("TARGET") == Entity.TARGET
        assert Entity.from_string("buyer") == Entity.BUYER
        assert Entity.from_string("BUYER") == Entity.BUYER

    def test_entity_from_string_invalid(self):
        """Test from_string() with invalid value."""
        with pytest.raises(ValueError, match="Invalid entity value"):
            Entity.from_string("invalid")

    def test_entity_comparison(self):
        """Test entity comparison."""
        assert Entity.TARGET == Entity.TARGET
        assert Entity.BUYER == Entity.BUYER
        assert Entity.TARGET != Entity.BUYER


class TestObservation:
    """Test Observation schema."""

    def test_observation_creation(self):
        """Test basic observation creation."""
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5, row 3",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )
        assert obs.confidence == 0.95
        assert obs.deal_id == "deal-123"
        assert obs.entity == Entity.TARGET

    def test_observation_confidence_validation(self):
        """Test confidence range validation."""
        # Valid confidence
        obs = Observation(
            source_type="table",
            confidence=0.5,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )
        assert obs.confidence == 0.5

        # Invalid - too high
        with pytest.raises(ValueError, match="Confidence must be between"):
            Observation(
                source_type="table",
                confidence=1.5,
                evidence="test",
                extracted_at=datetime.now(),
                deal_id="d1",
                entity=Entity.TARGET,
                data={}
            )

        # Invalid - too low
        with pytest.raises(ValueError, match="Confidence must be between"):
            Observation(
                source_type="table",
                confidence=-0.1,
                evidence="test",
                extracted_at=datetime.now(),
                deal_id="d1",
                entity=Entity.TARGET,
                data={}
            )

    def test_observation_deal_id_required(self):
        """Test deal_id is required."""
        with pytest.raises(ValueError, match="deal_id is required"):
            Observation(
                source_type="table",
                confidence=0.9,
                evidence="test",
                extracted_at=datetime.now(),
                deal_id="",  # Empty
                entity=Entity.TARGET,
                data={}
            )

    def test_observation_priority_scoring(self):
        """Test priority scoring for observation merging."""
        obs_manual = Observation(
            source_type="manual",
            confidence=1.0,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )
        obs_table = Observation(
            source_type="table",
            confidence=0.9,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )
        obs_llm_prose = Observation(
            source_type="llm_prose",
            confidence=0.7,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )
        obs_llm_assumption = Observation(
            source_type="llm_assumption",
            confidence=0.5,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )

        # Test priority order
        assert obs_manual.get_priority_score() == 4
        assert obs_table.get_priority_score() == 3
        assert obs_llm_prose.get_priority_score() == 2
        assert obs_llm_assumption.get_priority_score() == 1

        # Test should_replace
        assert obs_manual.should_replace(obs_table)
        assert obs_table.should_replace(obs_llm_prose)
        assert obs_llm_prose.should_replace(obs_llm_assumption)
        assert not obs_llm_assumption.should_replace(obs_table)

    def test_observation_serialization(self):
        """Test to_dict() and from_dict()."""
        obs = Observation(
            source_type="table",
            confidence=0.95,
            evidence="Page 5",
            extracted_at=datetime.now(),
            deal_id="deal-123",
            entity=Entity.TARGET,
            data={"cost": 50000}
        )

        # Serialize
        obs_dict = obs.to_dict()
        assert obs_dict["source_type"] == "table"
        assert obs_dict["confidence"] == 0.95
        assert obs_dict["entity"] == "target"

        # Deserialize
        obs_restored = Observation.from_dict(obs_dict)
        assert obs_restored.source_type == obs.source_type
        assert obs_restored.confidence == obs.confidence
        assert obs_restored.entity == obs.entity
        assert obs_restored.data == obs.data


class TestNormalization:
    """Test normalization rules (P0-3 fix)."""

    def test_application_normalization_basic(self):
        """Test basic application normalization."""
        assert NormalizationRules.normalize_name("Salesforce CRM", "application") == "salesforce"
        assert NormalizationRules.normalize_name("Microsoft Dynamics 365", "application") == "microsoft dynamics 365"
        assert NormalizationRules.normalize_name("SAP ERP", "application") == "sap"

    def test_application_normalization_no_collision(self):
        """Test P0-3 fix: SAP ERP vs SAP SuccessFactors don't collide."""
        # This is the critical P0-3 fix test
        sap_erp = NormalizationRules.normalize_name("SAP ERP", "application")
        sap_successfactors = NormalizationRules.normalize_name("SAP SuccessFactors", "application")

        # They should be DIFFERENT (not both "sap")
        assert sap_erp == "sap"  # Trailing "ERP" removed
        assert sap_successfactors == "sap successfactors"  # No suffix to remove
        assert sap_erp != sap_successfactors  # ✅ P0-3 FIX VALIDATED

    def test_application_normalization_case_insensitive(self):
        """Test case-insensitive normalization."""
        assert NormalizationRules.normalize_name("SALESFORCE", "application") == "salesforce"
        assert NormalizationRules.normalize_name("SalesForce", "application") == "salesforce"
        assert NormalizationRules.normalize_name("salesforce", "application") == "salesforce"

    def test_infrastructure_normalization_keeps_environment(self):
        """Test infrastructure normalization keeps environment indicators."""
        assert NormalizationRules.normalize_name("AWS EC2 Production", "infrastructure") == "aws ec2 production"
        assert NormalizationRules.normalize_name("AWS EC2 Development", "infrastructure") == "aws ec2 development"
        # Different environments should stay different
        assert NormalizationRules.normalize_name("AWS EC2 Production", "infrastructure") != \
               NormalizationRules.normalize_name("AWS EC2 Development", "infrastructure")

    def test_organization_normalization(self):
        """Test organization normalization."""
        assert NormalizationRules.normalize_name("John Smith - IT Director", "organization") == "john smith - it director"
        assert NormalizationRules.normalize_name("Jane Doe - VP of Technology", "organization") == "jane doe - vp of technology"

    def test_should_merge_priority(self):
        """Test observation merging priority."""
        obs_manual = Observation(
            source_type="manual",
            confidence=1.0,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )
        obs_table = Observation(
            source_type="table",
            confidence=0.9,
            evidence="test",
            extracted_at=datetime.now(),
            deal_id="d1",
            entity=Entity.TARGET,
            data={}
        )

        # Manual should replace table
        assert NormalizationRules.should_merge(obs_manual, obs_table)
        # Table should not replace manual
        assert not NormalizationRules.should_merge(obs_table, obs_manual)


class TestEntityInference:
    """Test entity inference."""

    def test_infer_target(self):
        """Test target entity inference."""
        assert EntityInference.infer_entity("Target Company - IT Landscape") == Entity.TARGET
        assert EntityInference.infer_entity("Acquisition Target Systems") == Entity.TARGET
        assert EntityInference.infer_entity("Their Applications") == Entity.TARGET

    def test_infer_buyer(self):
        """Test buyer entity inference."""
        assert EntityInference.infer_entity("Our Current Infrastructure") == Entity.BUYER
        assert EntityInference.infer_entity("Acquirer Systems Overview") == Entity.BUYER
        assert EntityInference.infer_entity("Existing Applications") == Entity.BUYER

    def test_infer_default(self):
        """Test default when no indicators present."""
        # No indicators → uses default (TARGET)
        assert EntityInference.infer_entity("IT Systems Overview") == Entity.TARGET
        assert EntityInference.infer_entity("Applications Inventory") == Entity.TARGET

    def test_infer_with_confidence(self):
        """Test inference with confidence scores."""
        # Strong target indicator (matches "target" AND "target company" = 2 indicators)
        entity, confidence = EntityInference.infer_with_confidence("Target Company IT")
        assert entity == Entity.TARGET
        assert confidence == 1.0  # 2 indicators = very confident

        # No indicators
        entity, confidence = EntityInference.infer_with_confidence("Systems Overview")
        assert entity == Entity.TARGET  # Default
        assert confidence == 0.5  # Uncertain


class TestFingerprint:
    """Test fingerprint generation (P0-3 fix)."""

    def test_generate_with_vendor(self):
        """Test fingerprint includes vendor."""
        fp1 = FingerprintGenerator.generate("salesforce", "Salesforce", Entity.TARGET, "APP")
        assert fp1.startswith("APP-TARGET-")
        assert len(fp1) == len("APP-TARGET-a3f291c2")  # Correct length

    def test_generate_different_vendors_different_ids(self):
        """Test P0-3 fix: Same name, different vendors → different IDs."""
        # SAP ERP (vendor: SAP)
        fp_sap_erp = FingerprintGenerator.generate("sap", "SAP", Entity.TARGET, "APP")

        # SAP SuccessFactors (vendor: SAP, but different normalized name)
        fp_sap_sf = FingerprintGenerator.generate("sap successfactors", "SAP", Entity.TARGET, "APP")

        # Should be different (P0-3 fix validated)
        assert fp_sap_erp != fp_sap_sf

    def test_generate_same_entity_same_id(self):
        """Test same name + vendor + entity → same ID (stability)."""
        fp1 = FingerprintGenerator.generate("salesforce", "Salesforce", Entity.TARGET, "APP")
        fp2 = FingerprintGenerator.generate("salesforce", "Salesforce", Entity.TARGET, "APP")
        assert fp1 == fp2  # Stable IDs

    def test_generate_different_entity_different_id(self):
        """Test same name, different entity → different ID."""
        fp_target = FingerprintGenerator.generate("salesforce", "Salesforce", Entity.TARGET, "APP")
        fp_buyer = FingerprintGenerator.generate("salesforce", "Salesforce", Entity.BUYER, "APP")
        assert fp_target != fp_buyer

    def test_parse_domain_id(self):
        """Test parsing domain ID."""
        parsed = FingerprintGenerator.parse_domain_id("APP-TARGET-a3f291c2")
        assert parsed["domain_prefix"] == "APP"
        assert parsed["entity"] == "TARGET"
        assert parsed["hash"] == "a3f291c2"

    def test_parse_domain_id_invalid(self):
        """Test parsing invalid domain ID."""
        with pytest.raises(ValueError, match="Invalid domain ID format"):
            FingerprintGenerator.parse_domain_id("invalid")

        with pytest.raises(ValueError, match="Invalid entity"):
            FingerprintGenerator.parse_domain_id("APP-INVALID-a3f291c2")

    def test_extract_entity_from_id(self):
        """Test extracting entity from domain ID."""
        assert FingerprintGenerator.extract_entity_from_id("APP-TARGET-a3f291c2") == Entity.TARGET
        assert FingerprintGenerator.extract_entity_from_id("INFRA-BUYER-b4e8f1d3") == Entity.BUYER

    def test_is_valid_domain_id(self):
        """Test domain ID validation."""
        assert FingerprintGenerator.is_valid_domain_id("APP-TARGET-a3f291c2")
        assert FingerprintGenerator.is_valid_domain_id("INFRA-BUYER-b4e8f1d3")
        assert not FingerprintGenerator.is_valid_domain_id("invalid")
        assert not FingerprintGenerator.is_valid_domain_id("APP-TARGET")  # Missing hash


class TestExtractionCoordinator:
    """Test extraction coordinator (prevents double-counting)."""

    def test_mark_and_check_extracted(self):
        """Test marking and checking extraction."""
        coordinator = ExtractionCoordinator()

        # Mark extracted
        coordinator.mark_extracted("doc-123", "Salesforce", "application")

        # Check
        assert coordinator.already_extracted("doc-123", "Salesforce", "application")
        assert not coordinator.already_extracted("doc-123", "Salesforce", "infrastructure")

    def test_already_extracted_by_any_domain(self):
        """Test cross-domain extraction check."""
        coordinator = ExtractionCoordinator()

        # Application domain extracts Salesforce
        coordinator.mark_extracted("doc-123", "Salesforce", "application")

        # Infrastructure domain checks (should see it's already extracted)
        assert coordinator.already_extracted_by_any_domain("doc-123", "Salesforce")
        assert not coordinator.already_extracted_by_any_domain("doc-123", "AWS")

    def test_get_extracting_domain(self):
        """Test getting which domain extracted an entity."""
        coordinator = ExtractionCoordinator()

        coordinator.mark_extracted("doc-123", "Salesforce", "application")
        domain = coordinator.get_extracting_domain("doc-123", "Salesforce")
        assert domain == "application"

    def test_case_insensitive_matching(self):
        """Test case-insensitive entity matching."""
        coordinator = ExtractionCoordinator()

        coordinator.mark_extracted("doc-123", "Salesforce CRM", "application")

        # Should match regardless of case
        assert coordinator.already_extracted("doc-123", "salesforce crm", "application")
        assert coordinator.already_extracted("doc-123", "SALESFORCE CRM", "application")

    def test_get_extracted_count(self):
        """Test extraction count."""
        coordinator = ExtractionCoordinator()

        coordinator.mark_extracted("doc-123", "Salesforce", "application")
        coordinator.mark_extracted("doc-123", "SAP", "application")

        count = coordinator.get_extracted_count("doc-123", "application")
        assert count == 2

    def test_clear_document(self):
        """Test clearing document extraction records."""
        coordinator = ExtractionCoordinator()

        coordinator.mark_extracted("doc-123", "Salesforce", "application")
        assert coordinator.already_extracted("doc-123", "Salesforce", "application")

        coordinator.clear_document("doc-123")
        assert not coordinator.already_extracted("doc-123", "Salesforce", "application")


# P0-2 Fix Validation Test (Circuit Breaker)
class TestRepositoryCircuitBreaker:
    """Test repository circuit breaker (P0-2 fix)."""

    def test_circuit_breaker_constant(self):
        """Test circuit breaker constant is set correctly."""
        from domain.kernel.repository import DomainRepository
        assert DomainRepository.MAX_ITEMS_FOR_RECONCILIATION == 500

    # Note: Full reconcile_duplicates() test requires concrete repository implementation
    # This will be tested in application/infrastructure/organization repository tests
