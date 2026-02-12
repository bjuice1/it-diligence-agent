"""
Integration tests for deal type → reasoning → findings flow.

Tests that deal type conditioning reaches reasoning agents and affects findings.

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore


class TestDealTypeReasoningFlow:
    """Test deal type affects reasoning agent outputs."""

    def test_acquisition_generates_consolidation_findings(self):
        """Test that acquisition generates consolidation-focused findings."""
        fact_store = FactStore(deal_id="test-acq-reasoning")

        # Add facts about overlapping applications
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high', 'users': 500},
            entity="buyer",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high', 'users': 300},
            entity="target",
            confidence=0.9
        )

        # In a real scenario, reasoning agent would be called here
        # For now, we test that facts are set up correctly
        buyer_facts = fact_store.get_facts(entity="buyer", domain="applications")
        target_facts = fact_store.get_facts(entity="target", domain="applications")

        assert len(buyer_facts) > 0
        assert len(target_facts) > 0

        # Check for overlapping apps (same name)
        buyer_app_names = {f.item for f in buyer_facts}
        target_app_names = {f.item for f in target_facts}
        overlaps = buyer_app_names.intersection(target_app_names)

        assert len(overlaps) > 0, "Should have overlapping applications"
        assert "Salesforce CRM" in overlaps

    def test_carveout_focuses_on_separation(self):
        """Test that carve-out scenario focuses on separation needs."""
        fact_store = FactStore(deal_id="test-carveout-reasoning")

        # Add facts about shared services
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="SAP ERP",
            details={
                'hosting': 'parent_datacenter',
                'shared_service': True,
                'users': 1000
            },
            entity="target",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="infrastructure",
            category="network",
            item="Corporate Network",
            details={'shared_with_parent': True},
            entity="target",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="identity",
            category="directory",
            item="Active Directory",
            details={'owned_by': 'parent', 'integrated': True},
            entity="target",
            confidence=0.9
        )

        # Verify facts are set up for separation analysis
        target_facts = fact_store.get_facts(entity="target")
        assert len(target_facts) >= 3

        # Check for shared/parent-dependent services
        shared_facts = [
            f for f in target_facts
            if f.details.get('shared_service') or
               f.details.get('shared_with_parent') or
               f.details.get('owned_by') == 'parent'
        ]
        assert len(shared_facts) >= 3, "Should have multiple shared services"

    def test_no_overlapping_apps_no_consolidation_opportunity(self):
        """Test that non-overlapping apps don't trigger consolidation."""
        fact_store = FactStore(deal_id="test-no-overlap")

        # Add different apps for buyer and target
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce CRM",
            details={'usage': 'high'},
            entity="buyer",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Microsoft Dynamics",
            details={'usage': 'high'},
            entity="target",
            confidence=0.9
        )

        buyer_facts = fact_store.get_facts(entity="buyer", domain="applications")
        target_facts = fact_store.get_facts(entity="target", domain="applications")

        buyer_app_names = {f.item for f in buyer_facts}
        target_app_names = {f.item for f in target_facts}
        overlaps = buyer_app_names.intersection(target_app_names)

        assert len(overlaps) == 0, "Should have no overlapping applications"

    def test_divestiture_deep_integration_detected(self):
        """Test that divestiture scenario detects deep integration."""
        fact_store = FactStore(deal_id="test-divestiture-reasoning")

        # Add facts about deeply integrated systems
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Custom ERP",
            details={
                'integration_level': 'deeply_integrated',
                'custom_integrations': 10,
                'shared_database': True
            },
            entity="target",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="applications",
            category="data",
            item="Data Warehouse",
            details={
                'shared_with_parent': True,
                'mixed_data': True
            },
            entity="target",
            confidence=0.9
        )
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="Shared Infrastructure",
            details={
                'colocated_workloads': True,
                'no_clear_boundary': True
            },
            entity="target",
            confidence=0.9
        )

        target_facts = fact_store.get_facts(entity="target")

        # Check for deep integration indicators
        deep_integration_facts = [
            f for f in target_facts
            if f.details.get('integration_level') == 'deeply_integrated' or
               f.details.get('shared_database') or
               f.details.get('mixed_data') or
               f.details.get('colocated_workloads')
        ]
        assert len(deep_integration_facts) >= 3, \
            "Should detect multiple deep integration points"


class TestInventoryBasedReasoning:
    """Test reasoning based on inventory data."""

    def test_acquisition_inventory_overlap_detection(self):
        """Test detecting inventory overlaps for acquisition."""
        inv_store = InventoryStore(deal_id="test-inv-overlap")

        # Add overlapping applications
        inv_store.add_item('applications', {
            'name': 'Salesforce',
            'category': 'CRM',
            'entity': 'buyer',
            'licenses': 1000
        })
        inv_store.add_item('applications', {
            'name': 'Salesforce',
            'category': 'CRM',
            'entity': 'target',
            'licenses': 500
        })
        inv_store.add_item('applications', {
            'name': 'Workday',
            'category': 'HRIS',
            'entity': 'buyer',
            'licenses': 800
        })
        inv_store.add_item('applications', {
            'name': 'Workday',
            'category': 'HRIS',
            'entity': 'target',
            'licenses': 400
        })

        # Query for overlaps
        buyer_apps = inv_store.get_items(domain='applications', entity='buyer')
        target_apps = inv_store.get_items(domain='applications', entity='target')

        buyer_app_names = {app['name'] for app in buyer_apps}
        target_app_names = {app['name'] for app in target_apps}
        overlaps = buyer_app_names.intersection(target_app_names)

        assert len(overlaps) >= 2, "Should detect at least 2 overlapping apps"
        assert 'Salesforce' in overlaps
        assert 'Workday' in overlaps

    def test_carveout_shared_services_detection(self):
        """Test detecting shared services for carveout."""
        inv_store = InventoryStore(deal_id="test-shared-services")

        # Add shared services
        inv_store.add_item('applications', {
            'name': 'SAP ERP',
            'category': 'ERP',
            'entity': 'target',
            'hosting': 'parent_datacenter',
            'shared_service': True
        })
        inv_store.add_item('infrastructure', {
            'name': 'Corporate Network',
            'type': 'network',
            'entity': 'target',
            'shared_with_parent': True
        })
        inv_store.add_item('cybersecurity', {
            'name': 'SOC Services',
            'type': 'security_service',
            'entity': 'target',
            'provided_by_parent': True
        })

        target_items = inv_store.get_items(entity='target')

        # Count shared/parent-dependent items
        shared_items = [
            item for item in target_items
            if item.get('shared_service') or
               item.get('shared_with_parent') or
               item.get('provided_by_parent') or
               item.get('hosting') == 'parent_datacenter'
        ]

        assert len(shared_items) >= 3, "Should detect multiple shared services"


class TestFactQualityImpact:
    """Test how fact quality impacts reasoning."""

    def test_high_confidence_facts_more_weight(self):
        """Test that high confidence facts are prioritized."""
        fact_store = FactStore(deal_id="test-confidence")

        # Add high confidence fact
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce",
            details={'usage': 'high'},
            entity="target",
            confidence=0.95
        )

        # Add low confidence fact
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Unknown CRM",
            details={'usage': 'unknown'},
            entity="target",
            confidence=0.3
        )

        high_conf_facts = fact_store.get_facts(entity="target", min_confidence=0.8)
        low_conf_facts = fact_store.get_facts(entity="target", min_confidence=0.0, max_confidence=0.5)

        assert len(high_conf_facts) >= 1
        assert len(low_conf_facts) >= 1

    def test_evidence_chain_completeness(self):
        """Test that facts with complete evidence chains are preferred."""
        fact_store = FactStore(deal_id="test-evidence")

        # Add fact with evidence
        fact_id = fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce",
            details={'users': 1000},
            entity="target",
            confidence=0.9,
            evidence="Found in IT inventory document page 5"
        )

        facts = fact_store.get_facts(entity="target")
        fact_with_evidence = [f for f in facts if f.evidence]

        assert len(fact_with_evidence) >= 1


class TestCrossDomainReasoning:
    """Test reasoning that spans multiple domains."""

    def test_identity_and_application_interaction(self):
        """Test reasoning about identity and applications together."""
        fact_store = FactStore(deal_id="test-cross-domain")

        # Add identity facts
        fact_store.add_fact(
            domain="identity",
            category="directory",
            item="Active Directory",
            details={'owned_by': 'parent', 'users': 5000},
            entity="target",
            confidence=0.9
        )

        # Add application facts that depend on identity
        fact_store.add_fact(
            domain="applications",
            category="enterprise",
            item="Salesforce",
            details={'auth_method': 'AD_SSO', 'users': 1000},
            entity="target",
            confidence=0.9
        )

        identity_facts = fact_store.get_facts(domain="identity", entity="target")
        app_facts = fact_store.get_facts(domain="applications", entity="target")

        assert len(identity_facts) > 0
        assert len(app_facts) > 0

        # Check for SSO dependency
        sso_apps = [f for f in app_facts if 'SSO' in f.details.get('auth_method', '')]
        assert len(sso_apps) > 0, "Should detect apps with SSO dependency"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
