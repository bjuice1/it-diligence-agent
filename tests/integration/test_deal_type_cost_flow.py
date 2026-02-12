"""
Integration tests for deal type → cost calculation flow.

Tests the full path: Deal model → analysis_runner → cost_engine → result

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from web.database import Deal, db
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from services.cost_engine.calculator import calculate_deal_costs
from services.cost_engine.drivers import DealDrivers, OwnershipType


class TestDealTypeCostFlow:
    """Test deal type propagation through cost calculation pipeline."""

    def test_acquisition_cost_flow(self):
        """Test that acquisition deal type flows through to cost calculation."""
        # Create acquisition deal
        deal = Deal(
            name="Acquisition Test",
            target_name="Target Co",
            buyer_name="Buyer Co",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Create stores
            fact_store = FactStore(deal_id=deal.id)
            inv_store = InventoryStore(deal_id=deal.id)

            # Add sample inventory
            inv_store.add_item('applications', {
                'name': 'Test App',
                'entity': 'target',
                'category': 'CRM'
            })

            # Calculate costs with deal_type from deal
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify cost estimate reflects acquisition logic
            assert result.total_one_time_base > 0
            assert result.total_tsa_costs == 0, "Acquisition should have no TSA costs"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()

    def test_carveout_cost_flow(self):
        """Test that carve-out deal type flows through to cost calculation."""
        deal = Deal(
            name="Carve-Out Test",
            target_name="Target Co",
            buyer_name="NewCo",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            fact_store = FactStore(deal_id=deal.id)
            inv_store = InventoryStore(deal_id=deal.id)

            # Add shared services that trigger separation costs
            inv_store.add_item('applications', {
                'name': 'Shared ERP',
                'entity': 'target',
                'hosted_by_parent': True
            })
            inv_store.add_item('infrastructure', {
                'name': 'Corporate Network',
                'entity': 'target',
                'shared_with_parent': True
            })

            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50,
                identity_owned_by=OwnershipType.PARENT
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify cost estimate reflects carve-out logic
            assert result.total_one_time_base > 0, "Should have one-time costs"
            assert result.total_tsa_costs > 0, "Carve-out should have TSA costs"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()

    def test_divestiture_cost_flow(self):
        """Test that divestiture deal type flows through to cost calculation."""
        deal = Deal(
            name="Divestiture Test",
            target_name="Divested Unit",
            buyer_name="Acquirer",
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            inv_store = InventoryStore(deal_id=deal.id)

            # Add deeply integrated systems
            inv_store.add_item('applications', {
                'name': 'Integrated System',
                'entity': 'target',
                'integration_level': 'deeply_integrated'
            })

            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                applications=50
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Verify cost estimate reflects divestiture logic (higher costs)
            assert result.total_one_time_base > 0, "Should have one-time costs"

        finally:
            # Cleanup
            db.session.delete(deal)
            db.session.commit()

    def test_cost_multiplier_applied_in_pipeline(self):
        """Test that cost multipliers are applied in full pipeline."""
        # Create same work items, different deal types → different costs
        acq_deal = Deal(
            name="Acq Pipeline",
            target_name="Target",
            deal_type="acquisition"
        )
        carve_deal = Deal(
            name="Carve Pipeline",
            target_name="Target",
            deal_type="carveout"
        )

        db.session.add_all([acq_deal, carve_deal])
        db.session.commit()

        try:
            # Same drivers for both
            drivers = DealDrivers(
                entity="target",
                total_users=1000,
                sites=3,
                endpoints=1200
            )

            # Run identical analysis for both
            acq_result = calculate_deal_costs(
                deal_id=acq_deal.id,
                drivers=drivers,
                deal_type='acquisition'
            )
            carve_result = calculate_deal_costs(
                deal_id=carve_deal.id,
                drivers=drivers,
                deal_type='carveout'
            )

            # Carve-out should cost more
            assert carve_result.total_one_time_base > acq_result.total_one_time_base, \
                f"Carveout ({carve_result.total_one_time_base}) should cost more than " \
                f"acquisition ({acq_result.total_one_time_base})"

            # Ratio should be at least 1.5x
            ratio = carve_result.total_one_time_base / acq_result.total_one_time_base
            assert ratio >= 1.5, f"Carveout should be at least 1.5x acquisition, got {ratio:.2f}x"

        finally:
            # Cleanup
            db.session.delete(acq_deal)
            db.session.delete(carve_deal)
            db.session.commit()


class TestDealTypePropagation:
    """Test that deal_type propagates correctly through layers."""

    def test_deal_type_from_database(self):
        """Test reading deal_type from database."""
        deal = Deal(
            name="Propagation Test",
            target_name="Target",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Read back from database
            retrieved_deal = db.session.get(Deal, deal.id)
            assert retrieved_deal is not None
            assert retrieved_deal.deal_type == "carveout"

            # Test to_dict includes deal_type
            deal_dict = retrieved_deal.to_dict()
            assert deal_dict['deal_type'] == "carveout"

        finally:
            db.session.delete(deal)
            db.session.commit()

    def test_deal_type_persistence(self):
        """Test that deal_type persists across sessions."""
        deal = Deal(
            name="Persistence Test",
            target_name="Target",
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()
        deal_id = deal.id

        try:
            # Clear session
            db.session.expunge_all()

            # Retrieve in new session
            retrieved_deal = db.session.get(Deal, deal_id)
            assert retrieved_deal.deal_type == "divestiture"

        finally:
            if retrieved_deal:
                db.session.delete(retrieved_deal)
                db.session.commit()


class TestCostCalculationEdgeCases:
    """Test edge cases in cost calculation flow."""

    def test_missing_inventory_store(self):
        """Test cost calculation without inventory store."""
        drivers = DealDrivers(
            entity="target",
            total_users=1000
        )

        # Should not crash
        result = calculate_deal_costs(
            deal_id="test-no-inv",
            drivers=drivers,
            deal_type='acquisition'
        )

        assert result.total_one_time_base > 0

    def test_empty_inventory_store(self):
        """Test cost calculation with empty inventory."""
        inv_store = InventoryStore(deal_id="test-empty")

        drivers = DealDrivers(
            entity="target",
            total_users=1000
        )

        result = calculate_deal_costs(
            deal_id="test-empty",
            drivers=drivers,
            deal_type='carveout',
            inventory_store=inv_store
        )

        # Should still calculate costs based on drivers
        assert result.total_one_time_base > 0

    def test_carveout_tsa_calculation(self):
        """Test TSA cost calculation for carveout with various scenarios."""
        inv_store = InventoryStore(deal_id="test-tsa")

        # Scenario 1: Few shared services
        inv_store.add_item('applications', {
            'name': 'Shared App 1',
            'entity': 'target',
            'hosted_by_parent': True
        })

        drivers = DealDrivers(entity="target", total_users=500)

        result_small = calculate_deal_costs(
            deal_id="test-tsa-small",
            drivers=drivers,
            deal_type='carveout',
            inventory_store=inv_store
        )

        # Scenario 2: Many shared services
        for i in range(10):
            inv_store.add_item('applications', {
                'name': f'Shared App {i+2}',
                'entity': 'target',
                'hosted_by_parent': True
            })

        result_large = calculate_deal_costs(
            deal_id="test-tsa-large",
            drivers=drivers,
            deal_type='carveout',
            inventory_store=inv_store
        )

        # More shared services should generally mean higher TSA costs
        # (though there may be a ceiling)
        assert result_large.total_tsa_costs >= result_small.total_tsa_costs


class TestMultipleDealsIsolation:
    """Test that multiple deals with different types are properly isolated."""

    def test_concurrent_deals_different_types(self):
        """Test that multiple deals can coexist with different deal types."""
        deals = [
            Deal(name="Deal 1", target_name="T1", deal_type="acquisition"),
            Deal(name="Deal 2", target_name="T2", deal_type="carveout"),
            Deal(name="Deal 3", target_name="T3", deal_type="divestiture")
        ]

        db.session.add_all(deals)
        db.session.commit()

        try:
            # Verify each has correct type
            for deal in deals:
                retrieved = db.session.get(Deal, deal.id)
                assert retrieved.deal_type == deal.deal_type

            # Calculate costs for each
            drivers = DealDrivers(entity="target", total_users=1000)

            results = []
            for deal in deals:
                result = calculate_deal_costs(
                    deal_id=deal.id,
                    drivers=drivers,
                    deal_type=deal.deal_type
                )
                results.append((deal.deal_type, result.total_one_time_base))

            # Verify costs increase: acquisition < carveout < divestiture
            acq_cost = [r[1] for r in results if r[0] == 'acquisition'][0]
            carve_cost = [r[1] for r in results if r[0] == 'carveout'][0]
            div_cost = [r[1] for r in results if r[0] == 'divestiture'][0]

            assert carve_cost > acq_cost
            assert div_cost > carve_cost

        finally:
            # Cleanup
            for deal in deals:
                db.session.delete(deal)
            db.session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
