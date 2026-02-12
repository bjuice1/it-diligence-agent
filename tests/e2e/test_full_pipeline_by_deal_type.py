"""
End-to-end tests for full pipeline by deal type.

Tests the complete flow:
Document upload → Discovery → Reasoning → Cost → Narrative
for all 3 deal types.

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from web.database import Deal, db
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from services.cost_engine.calculator import calculate_deal_costs
from services.cost_engine.drivers import DealDrivers


class TestFullPipelineByDealType:
    """E2E tests for full pipeline with different deal types."""

    @pytest.mark.slow
    def test_acquisition_full_pipeline(self):
        """Test full pipeline for acquisition deal."""
        deal = Deal(
            name="Acquisition E2E",
            target_name="Target Co",
            buyer_name="Buyer Co",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Phase 1: Discovery - Create facts
            fact_store = FactStore(deal_id=deal.id)

            # Add buyer facts
            fact_store.add_fact(
                domain="applications",
                category="enterprise",
                item="Salesforce CRM",
                details={'users': 500, 'licenses': 600},
                entity="buyer",
                confidence=0.9
            )

            # Add target facts (overlapping)
            fact_store.add_fact(
                domain="applications",
                category="enterprise",
                item="Salesforce CRM",
                details={'users': 300, 'licenses': 350},
                entity="target",
                confidence=0.9
            )

            # Phase 2: Create inventory
            inv_store = InventoryStore(deal_id=deal.id)

            inv_store.add_item('applications', {
                'name': 'Salesforce CRM',
                'category': 'CRM',
                'entity': 'buyer',
                'users': 500
            })
            inv_store.add_item('applications', {
                'name': 'Salesforce CRM',
                'category': 'CRM',
                'entity': 'target',
                'users': 300
            })

            # Phase 3: Cost calculation
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50
            )

            cost_result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify acquisition-specific outputs
            assert cost_result.total_one_time_base > 0, "Should have costs"
            assert cost_result.total_tsa_costs == 0, "Acquisition should have no TSA costs"

            # Verify facts were created
            all_facts = fact_store.get_facts()
            assert len(all_facts) >= 2, "Should have facts from discovery"

            # Verify inventory was created
            all_items = inv_store.get_items()
            assert len(all_items) >= 2, "Should have inventory items"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()

    @pytest.mark.slow
    def test_carveout_full_pipeline(self):
        """Test full pipeline for carve-out deal."""
        deal = Deal(
            name="Carve-Out E2E",
            target_name="Target Co",
            buyer_name="NewCo",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Phase 1: Discovery - Create facts about shared services
            fact_store = FactStore(deal_id=deal.id)

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
                details={'owned_by': 'parent'},
                entity="target",
                confidence=0.9
            )

            # Phase 2: Create inventory
            inv_store = InventoryStore(deal_id=deal.id)

            inv_store.add_item('applications', {
                'name': 'SAP ERP',
                'category': 'ERP',
                'entity': 'target',
                'hosted_by_parent': True,
                'shared_service': True
            })
            inv_store.add_item('infrastructure', {
                'name': 'Corporate Network',
                'type': 'network',
                'entity': 'target',
                'shared_with_parent': True
            })
            inv_store.add_item('identity', {
                'name': 'Active Directory',
                'type': 'directory',
                'entity': 'target',
                'owned_by_parent': True
            })

            # Phase 3: Cost calculation
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50
            )

            cost_result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify carve-out-specific outputs
            assert cost_result.total_one_time_base > 0, "Should have one-time costs"
            assert cost_result.total_tsa_costs > 0, "Carve-out should have TSA costs"

            # Verify separation-focused facts
            shared_facts = [
                f for f in fact_store.get_facts()
                if f.details.get('shared_service') or
                   f.details.get('shared_with_parent') or
                   f.details.get('owned_by') == 'parent'
            ]
            assert len(shared_facts) >= 3, "Should have multiple shared service facts"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()

    @pytest.mark.slow
    def test_divestiture_full_pipeline(self):
        """Test full pipeline for divestiture deal."""
        deal = Deal(
            name="Divestiture E2E",
            target_name="Divested Unit",
            buyer_name="Acquirer",
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Phase 1: Discovery - Create facts about deep integration
            fact_store = FactStore(deal_id=deal.id)

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
                details={'shared_with_parent': True, 'mixed_data': True},
                entity="target",
                confidence=0.9
            )
            fact_store.add_fact(
                domain="infrastructure",
                category="compute",
                item="Shared Infrastructure",
                details={'colocated_workloads': True},
                entity="target",
                confidence=0.9
            )

            # Phase 2: Create inventory
            inv_store = InventoryStore(deal_id=deal.id)

            inv_store.add_item('applications', {
                'name': 'Custom ERP',
                'category': 'ERP',
                'entity': 'target',
                'integration_level': 'deeply_integrated'
            })
            inv_store.add_item('applications', {
                'name': 'Data Warehouse',
                'category': 'Data',
                'entity': 'target',
                'shared_with_parent': True
            })

            # Phase 3: Cost calculation
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50
            )

            cost_result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify divestiture-specific outputs (highest costs)
            assert cost_result.total_one_time_base > 0, "Should have one-time costs"

            # Verify deep integration facts
            integrated_facts = [
                f for f in fact_store.get_facts()
                if f.details.get('integration_level') == 'deeply_integrated' or
                   f.details.get('shared_database') or
                   f.details.get('mixed_data')
            ]
            assert len(integrated_facts) >= 2, "Should detect deep integration"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()


class TestPipelineComparison:
    """Test comparative behavior across deal types."""

    @pytest.mark.slow
    def test_costs_increase_by_deal_type(self):
        """Test that costs increase: acquisition < carveout < divestiture."""
        deals = [
            Deal(name="Acq Compare", target_name="T", deal_type="acquisition"),
            Deal(name="Carve Compare", target_name="T", deal_type="carveout"),
            Deal(name="Div Compare", target_name="T", deal_type="divestiture")
        ]

        db.session.add_all(deals)
        db.session.commit()

        try:
            # Same drivers for all
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50,
                sites=3
            )

            # Calculate costs
            results = {}
            for deal in deals:
                inv_store = InventoryStore(deal_id=deal.id)

                # Add some shared services for carveout/divestiture
                if deal.deal_type in ['carveout', 'divestiture']:
                    inv_store.add_item('applications', {
                        'name': 'Shared App',
                        'entity': 'target',
                        'hosted_by_parent': True
                    })

                cost_result = calculate_deal_costs(
                    deal_id=deal.id,
                    drivers=drivers,
                    deal_type=deal.deal_type,
                    inventory_store=inv_store
                )

                results[deal.deal_type] = cost_result.total_one_time_base

            # Verify increasing costs
            assert results['carveout'] > results['acquisition'], \
                f"Carveout ({results['carveout']}) should cost more than acquisition ({results['acquisition']})"
            assert results['divestiture'] > results['carveout'], \
                f"Divestiture ({results['divestiture']}) should cost more than carveout ({results['carveout']})"

        finally:
            # Cleanup
            for deal in deals:
                db.session.delete(deal)
            db.session.commit()


class TestPipelineErrorHandling:
    """Test error handling in full pipeline."""

    def test_invalid_deal_type_graceful_failure(self):
        """Test that invalid deal type is caught early."""
        with pytest.raises(Exception):
            deal = Deal(
                name="Invalid Type",
                target_name="Target",
                deal_type="merger"  # Invalid
            )
            db.session.add(deal)
            db.session.commit()

    def test_missing_required_fields(self):
        """Test that missing required fields are caught."""
        with pytest.raises(Exception):
            deal = Deal(
                name="Missing Target",
                deal_type="acquisition"
                # target_name missing
            )
            db.session.add(deal)
            db.session.commit()

    def test_empty_pipeline_still_produces_costs(self):
        """Test that pipeline produces costs even with minimal data."""
        deal = Deal(
            name="Minimal Data",
            target_name="Target",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Minimal drivers
            drivers = DealDrivers(
                entity="target",
                total_users=100
            )

            # Should still produce costs
            cost_result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type
            )

            assert cost_result.total_one_time_base > 0

        finally:
            db.session.delete(deal)
            db.session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--slow"])
