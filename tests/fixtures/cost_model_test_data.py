"""
Test data factory for entity-aware cost model integration tests.

Provides realistic test data scenarios for buyer vs target cost analysis,
including drivers, facts, inventory items, and expected outcomes.
"""

from typing import Dict, List, Any
from unittest.mock import Mock
from services.cost_engine.drivers import DealDrivers
from web.blueprints.costs import CostCategory, RunRateCosts, OneTimeCosts


class CostModelTestData:
    """Factory for creating entity-aware cost test data."""

    @staticmethod
    def create_target_drivers() -> DealDrivers:
        """Create realistic drivers for target company."""
        return DealDrivers(
            total_users=500,
            sites=3,
            endpoints=500,
            servers=25,
            vms=40,
            total_apps=30,
            entity="target"
        )

    @staticmethod
    def create_buyer_drivers() -> DealDrivers:
        """Create realistic drivers for buyer company (larger scale)."""
        return DealDrivers(
            total_users=2000,
            sites=10,
            endpoints=2000,
            servers=100,
            vms=200,
            total_apps=80,
            entity="buyer"
        )

    @staticmethod
    def create_combined_drivers() -> DealDrivers:
        """Create combined drivers for both entities."""
        return DealDrivers(
            total_users=2500,
            sites=13,
            endpoints=2500,
            servers=125,
            vms=240,
            total_apps=110,
            entity="all"
        )

    @staticmethod
    def create_org_facts(entity: str = "target") -> List[Mock]:
        """Create mock organization facts for headcount costs."""
        facts = []

        if entity in ["target", "all"]:
            # Target engineering team
            eng_fact = Mock()
            eng_fact.entity = "target"
            eng_fact.category = "engineering"
            eng_fact.details = {
                "headcount": 25,
                "total_personnel_cost": 2_500_000,
                "avg_salary": 100_000
            }
            facts.append(eng_fact)

            # Target operations team
            ops_fact = Mock()
            ops_fact.entity = "target"
            ops_fact.category = "operations"
            ops_fact.details = {
                "headcount": 15,
                "total_personnel_cost": 1_200_000,
                "avg_salary": 80_000
            }
            facts.append(ops_fact)

        if entity in ["buyer", "all"]:
            # Buyer engineering team (larger)
            buyer_eng = Mock()
            buyer_eng.entity = "buyer"
            buyer_eng.category = "engineering"
            buyer_eng.details = {
                "headcount": 100,
                "total_personnel_cost": 12_000_000,
                "avg_salary": 120_000
            }
            facts.append(buyer_eng)

            # Buyer operations team
            buyer_ops = Mock()
            buyer_ops.entity = "buyer"
            buyer_ops.category = "operations"
            buyer_ops.details = {
                "headcount": 50,
                "total_personnel_cost": 4_500_000,
                "avg_salary": 90_000
            }
            facts.append(buyer_ops)

        return facts

    @staticmethod
    def create_work_items(entity: str = "target") -> List[Mock]:
        """Create mock work items for one-time costs."""
        items = []

        if entity in ["target", "all"]:
            # Target identity separation
            target_wi = Mock()
            target_wi.entity = "target"
            target_wi.cost_estimate = "500k_to_1m"
            target_wi.phase = "Day_1"
            target_wi.domain = "identity"
            items.append(target_wi)

            # Target email migration
            email_wi = Mock()
            email_wi.entity = "target"
            email_wi.cost_estimate = "100k_to_500k"
            email_wi.phase = "Day_1"
            email_wi.domain = "applications"
            items.append(email_wi)

        if entity in ["buyer", "all"]:
            # Buyer network integration
            buyer_wi = Mock()
            buyer_wi.entity = "buyer"
            buyer_wi.cost_estimate = "over_1m"
            buyer_wi.phase = "Day_100"
            buyer_wi.domain = "network"
            items.append(buyer_wi)

        return items

    @staticmethod
    def create_application_inventory(entity: str = "target") -> List[Mock]:
        """Create mock application inventory items."""
        apps = []

        if entity in ["target", "all"]:
            # Target Salesforce CRM
            target_crm = Mock()
            target_crm.name = "Salesforce (Target)"
            target_crm.data = {"category": "crm"}
            target_crm.cost = 300_000
            target_crm.entity = "target"
            target_crm.status = "active"
            apps.append(target_crm)

            # Target ERP
            target_erp = Mock()
            target_erp.name = "NetSuite"
            target_erp.data = {"category": "erp"}
            target_erp.cost = 400_000
            target_erp.entity = "target"
            target_erp.status = "active"
            apps.append(target_erp)

            # Target collaboration tool
            target_collab = Mock()
            target_collab.name = "Slack"
            target_collab.data = {"category": "collaboration"}
            target_collab.cost = 50_000
            target_collab.entity = "target"
            target_collab.status = "active"
            apps.append(target_collab)

        if entity in ["buyer", "all"]:
            # Buyer Salesforce CRM (larger contract)
            buyer_crm = Mock()
            buyer_crm.name = "Salesforce (Buyer)"
            buyer_crm.data = {"category": "crm"}
            buyer_crm.cost = 800_000
            buyer_crm.entity = "buyer"
            buyer_crm.status = "active"
            apps.append(buyer_crm)

            # Buyer ERP (different system)
            buyer_erp = Mock()
            buyer_erp.name = "SAP"
            buyer_erp.data = {"category": "erp"}
            buyer_erp.cost = 1_200_000
            buyer_erp.entity = "buyer"
            buyer_erp.status = "active"
            apps.append(buyer_erp)

            # Buyer collaboration tool (same category, potential synergy)
            buyer_collab = Mock()
            buyer_collab.name = "Microsoft Teams"
            buyer_collab.data = {"category": "collaboration"}
            buyer_collab.cost = 100_000
            buyer_collab.entity = "buyer"
            buyer_collab.status = "active"
            apps.append(buyer_collab)

        return apps

    @staticmethod
    def create_run_rate_costs(entity: str = "target") -> RunRateCosts:
        """Create RunRateCosts object with realistic data."""
        headcount = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        apps = CostCategory(name="applications", display_name="Applications", icon="📱")
        infra = CostCategory(name="infrastructure", display_name="Infrastructure", icon="🖥️")
        vendors = CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")

        if entity == "target":
            headcount.total = 3_700_000  # Engineering + ops
            headcount.items = [Mock()] * 40  # 40 people

            apps.total = 750_000  # Salesforce + NetSuite + Slack
            apps.items = [Mock()] * 3

            infra.total = 500_000
            infra.items = [Mock()] * 15

            vendors.total = 200_000
            vendors.items = [Mock()] * 5

        elif entity == "buyer":
            headcount.total = 16_500_000  # Larger org
            headcount.items = [Mock()] * 150

            apps.total = 2_100_000  # Salesforce + SAP + Teams
            apps.items = [Mock()] * 6

            infra.total = 2_000_000
            infra.items = [Mock()] * 50

            vendors.total = 800_000
            vendors.items = [Mock()] * 12

        elif entity == "all":
            headcount.total = 20_200_000  # Combined
            headcount.items = [Mock()] * 190

            apps.total = 2_850_000
            apps.items = [Mock()] * 9

            infra.total = 2_500_000
            infra.items = [Mock()] * 65

            vendors.total = 1_000_000
            vendors.items = [Mock()] * 17

        return RunRateCosts(
            headcount=headcount,
            applications=apps,
            infrastructure=infra,
            vendors_msp=vendors
        )

    @staticmethod
    def create_one_time_costs(entity: str = "target") -> OneTimeCosts:
        """Create OneTimeCosts object with realistic estimates."""
        one_time = OneTimeCosts()

        if entity == "target":
            # Identity + email migration
            one_time.total_low = 600_000
            one_time.total_mid = 900_000
            one_time.total_high = 1_500_000

        elif entity == "buyer":
            # Larger network integration
            one_time.total_low = 1_200_000
            one_time.total_mid = 1_800_000
            one_time.total_high = 2_500_000

        elif entity == "all":
            # Combined
            one_time.total_low = 1_800_000
            one_time.total_mid = 2_700_000
            one_time.total_high = 4_000_000

        return one_time

    @staticmethod
    def create_expected_synergies() -> List[Dict[str, Any]]:
        """Create expected synergy opportunities from buyer vs target overlap."""
        return [
            {
                "name": "CRM Consolidation",
                "category": "consolidation",
                "annual_savings_low": 300_000 + (800_000 * 0.10),  # $380K
                "annual_savings_high": 300_000 + (800_000 * 0.30),  # $540K
                "cost_to_achieve_low": 300_000 * 0.5,  # $150K
                "cost_to_achieve_high": 300_000 * 2.0,  # $600K
                "timeframe": "12-18 months",
                "confidence": "medium"
            },
            {
                "name": "ERP Consolidation",
                "category": "consolidation",
                "annual_savings_low": 400_000 + (1_200_000 * 0.10),  # $520K
                "annual_savings_high": 400_000 + (1_200_000 * 0.30),  # $760K
                "cost_to_achieve_low": 400_000 * 0.5,  # $200K
                "cost_to_achieve_high": 400_000 * 2.0,  # $800K
                "timeframe": "12-18 months",
                "confidence": "medium"
            },
            {
                "name": "Collaboration Consolidation",
                "category": "consolidation",
                "annual_savings_low": 50_000 + (100_000 * 0.10),  # $60K
                "annual_savings_high": 50_000 + (100_000 * 0.30),  # $80K
                "cost_to_achieve_low": 50_000 * 0.5,  # $25K
                "cost_to_achieve_high": 50_000 * 2.0,  # $100K
                "timeframe": "6-12 months",
                "confidence": "high"
            }
        ]

    @staticmethod
    def create_expected_quality_scores(entity: str = "target") -> Dict[str, Dict[str, str]]:
        """Create expected data quality scores for entity."""
        if entity == "target":
            return {
                "headcount": {"overall": "very_high"},  # $3.7M (above 1M)
                "applications": {"overall": "high"},  # $750K (between 500K-2M)
                "infrastructure": {"overall": "very_high"},  # $500K (exactly at 500K threshold, >= check means "very_high")
                "one_time": {"overall": "high"}  # $900K (between 500K-2M, so "high")
            }
        elif entity == "buyer":
            return {
                "headcount": {"overall": "very_high"},  # $16.5M
                "applications": {"overall": "very_high"},  # $2.1M
                "infrastructure": {"overall": "very_high"},  # $2M
                "one_time": {"overall": "medium"}  # $1.8M
            }
        else:  # all
            return {
                "headcount": {"overall": "very_high"},  # $20.2M
                "applications": {"overall": "very_high"},  # $2.85M
                "infrastructure": {"overall": "very_high"},  # $2.5M
                "one_time": {"overall": "very_high"}  # $2.7M (above 2M threshold)
            }
