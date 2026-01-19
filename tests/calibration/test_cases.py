"""
Calibration Test Cases for Executive Narrative Generation

Defines test cases with varying deal types, complexity levels, and expected outputs.
Each test case includes mock inventory data that simulates real-world scenarios.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class DealType(Enum):
    ACQUISITION = "acquisition"
    CARVEOUT = "carveout"
    DIVESTITURE = "divestiture"


class Complexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    HIGH = "high"


@dataclass
class TestCase:
    """Definition of a calibration test case."""
    id: str
    name: str
    description: str
    deal_type: DealType
    complexity: Complexity

    # Deal context
    target_name: str
    buyer_name: Optional[str] = None

    # Mock inventory data
    inventory: Dict[str, Any] = field(default_factory=dict)

    # Expected output characteristics
    expected_characteristics: Dict[str, Any] = field(default_factory=dict)

    # Minimum scores by dimension (0-5 scale)
    minimum_scores: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# TEST CASE 1: Simple Acquisition
# =============================================================================

TC_01_SIMPLE_ACQUISITION = TestCase(
    id="TC-01",
    name="Simple Acquisition",
    description="Clean synergy-focused narrative for straightforward bolt-on acquisition",
    deal_type=DealType.ACQUISITION,
    complexity=Complexity.SIMPLE,
    target_name="TechCo Solutions",
    buyer_name="Enterprise Corp",
    inventory={
        "organization": {
            "it_headcount": 12,
            "structure": {
                "cio": {"name": "John Smith", "reports_to": "CFO", "tenure": "3 years"},
                "teams": [
                    {"name": "Infrastructure", "headcount": 4, "outsourced_pct": 25},
                    {"name": "Applications", "headcount": 3, "outsourced_pct": 0},
                    {"name": "Service Desk", "headcount": 3, "outsourced_pct": 100},
                    {"name": "Security", "headcount": 2, "outsourced_pct": 0}
                ]
            },
            "key_person_dependencies": ["CIO - sole architect of current systems"]
        },
        "applications": {
            "erp": {"name": "NetSuite", "users": 150, "modules": ["Finance", "Inventory"]},
            "crm": {"name": "Salesforce", "users": 80},
            "custom_apps": 3,
            "integration_platform": "MuleSoft"
        },
        "infrastructure": {
            "data_centers": 0,
            "cloud_primary": "AWS",
            "cloud_spend": 180000,
            "servers": {"physical": 0, "virtual": 45}
        },
        "cybersecurity": {
            "mfa_coverage": 85,
            "endpoint_protection": "CrowdStrike",
            "siem": "None",
            "last_pentest": "2025-06"
        },
        "network": {
            "wan_provider": "AT&T",
            "sd_wan": True,
            "locations": 3
        }
    },
    expected_characteristics={
        "narrative_focus": "synergy_opportunity",
        "tsa_emphasis": "low",
        "key_synergies": ["license consolidation", "service desk consolidation", "cloud optimization"],
        "key_risks": ["key person dependency", "no SIEM"],
        "exec_summary_bullets": (5, 7)
    },
    minimum_scores={
        "mna_framing": 4.0,
        "evidence_discipline": 4.0,
        "actionability": 3.5,
        "narrative_flow": 3.5,
        "completeness": 4.0,
        "tone": 3.5
    }
)


# =============================================================================
# TEST CASE 2: Complex Carveout
# =============================================================================

TC_02_COMPLEX_CARVEOUT = TestCase(
    id="TC-02",
    name="Complex Carveout",
    description="Detailed TSA/separation analysis for carveout from large parent",
    deal_type=DealType.CARVEOUT,
    complexity=Complexity.COMPLEX,
    target_name="Industrial Division",
    buyer_name=None,  # PE acquisition
    inventory={
        "organization": {
            "it_headcount": 8,  # Dedicated to division
            "shared_services_dependency": "High",
            "structure": {
                "it_lead": {"name": "Maria Garcia", "reports_to": "Parent CIO (dotted)", "tenure": "5 years"},
                "teams": [
                    {"name": "Applications", "headcount": 4, "outsourced_pct": 0, "shared_with_parent": True},
                    {"name": "Local IT Support", "headcount": 4, "outsourced_pct": 0, "shared_with_parent": False}
                ]
            },
            "parent_shared_services": [
                "Infrastructure (100%)",
                "Security Operations (100%)",
                "Network (100%)",
                "Service Desk (100%)",
                "ERP Support (80%)"
            ]
        },
        "applications": {
            "erp": {"name": "SAP S/4HANA", "shared_instance": True, "separation_complexity": "High"},
            "mes": {"name": "Custom MES", "dedicated": True},
            "crm": {"name": "Parent Salesforce", "shared_instance": True},
            "custom_apps": 12,
            "parent_integrations": 45
        },
        "infrastructure": {
            "data_centers": "Parent DC (co-located)",
            "cloud_primary": "Parent Azure tenant",
            "dedicated_servers": 0,
            "shared_servers": 120
        },
        "cybersecurity": {
            "mfa_coverage": "Parent managed",
            "endpoint_protection": "Parent managed - Symantec",
            "siem": "Parent SOC",
            "identity": "Parent AD forest"
        },
        "network": {
            "wan_provider": "Parent MPLS",
            "dedicated_circuits": 0,
            "locations": 5,
            "firewall": "Parent managed"
        }
    },
    expected_characteristics={
        "narrative_focus": "separation_complexity",
        "tsa_emphasis": "high",
        "tsa_services_count": (8, 12),
        "separation_considerations": (5, 10),
        "standalone_readiness": "low",
        "key_risks": ["SAP separation", "no dedicated infrastructure", "parent AD dependency"],
        "exec_summary_bullets": (5, 7)
    },
    minimum_scores={
        "mna_framing": 4.5,
        "evidence_discipline": 4.0,
        "actionability": 4.0,
        "narrative_flow": 3.5,
        "completeness": 4.5,
        "tone": 3.5
    }
)


# =============================================================================
# TEST CASE 3: Medium Divestiture
# =============================================================================

TC_03_MEDIUM_DIVESTITURE = TestCase(
    id="TC-03",
    name="Medium Divestiture",
    description="Clean separation focus for business unit sale",
    deal_type=DealType.DIVESTITURE,
    complexity=Complexity.MEDIUM,
    target_name="Consumer Products BU",
    buyer_name="Strategic Buyer Inc",
    inventory={
        "organization": {
            "it_headcount": 15,
            "structure": {
                "it_director": {"name": "Robert Chen", "reports_to": "BU President"},
                "teams": [
                    {"name": "Applications", "headcount": 5, "dedicated": True},
                    {"name": "Infrastructure", "headcount": 4, "dedicated": False},
                    {"name": "Support", "headcount": 4, "dedicated": True},
                    {"name": "Security", "headcount": 2, "dedicated": False}
                ]
            },
            "remainco_impact": "Infrastructure and Security teams support multiple BUs"
        },
        "applications": {
            "erp": {"name": "Oracle EBS", "instance": "Dedicated", "data_separation": "Required"},
            "ecommerce": {"name": "Shopify Plus", "dedicated": True},
            "warehouse": {"name": "Manhattan WMS", "shared": False},
            "custom_apps": 8,
            "shared_data_feeds": 15
        },
        "infrastructure": {
            "data_centers": "Shared corporate DC",
            "cloud": {"aws_account": "Dedicated", "azure": "Shared tenant"},
            "servers_dedicated": 25,
            "servers_shared": 40
        },
        "cybersecurity": {
            "dedicated_tools": ["Endpoint protection"],
            "shared_tools": ["SIEM", "PAM", "Vuln scanning"],
            "compliance": "SOC 2 Type II (shared report)"
        },
        "network": {
            "wan": "Shared MPLS with dedicated VRF",
            "locations": 8,
            "internet_egress": "Shared"
        }
    },
    expected_characteristics={
        "narrative_focus": "clean_separation",
        "remainco_impact_addressed": True,
        "data_separation_items": (3, 8),
        "contract_assignment_items": (2, 5),
        "key_risks": ["shared infrastructure", "data separation", "RemainCo support gap"],
        "exec_summary_bullets": (5, 7)
    },
    minimum_scores={
        "mna_framing": 4.0,
        "evidence_discipline": 4.0,
        "actionability": 4.0,
        "narrative_flow": 3.5,
        "completeness": 4.0,
        "tone": 3.5
    }
)


# =============================================================================
# TEST CASE 4: Complex Acquisition (Dual ERP)
# =============================================================================

TC_04_COMPLEX_ACQUISITION = TestCase(
    id="TC-04",
    name="Complex Acquisition - Dual ERP",
    description="Extended application story for target with multiple ERPs",
    deal_type=DealType.ACQUISITION,
    complexity=Complexity.COMPLEX,
    target_name="Manufacturing Global Inc",
    buyer_name="Industrial Holdings",
    inventory={
        "organization": {
            "it_headcount": 45,
            "structure": {
                "cio": {"name": "Sarah Williams", "reports_to": "CEO", "tenure": "7 years"},
                "teams": [
                    {"name": "ERP Team (SAP)", "headcount": 8},
                    {"name": "ERP Team (Oracle)", "headcount": 6},
                    {"name": "Integration/Middleware", "headcount": 5},
                    {"name": "Infrastructure", "headcount": 10, "outsourced_pct": 40},
                    {"name": "Cybersecurity", "headcount": 6},
                    {"name": "Service Desk", "headcount": 5, "outsourced_pct": 80},
                    {"name": "PMO", "headcount": 3},
                    {"name": "Data/Analytics", "headcount": 2}
                ]
            },
            "geographic_spread": ["US", "Germany", "China", "Mexico"]
        },
        "applications": {
            "erp_systems": [
                {"name": "SAP ECC", "users": 800, "regions": ["US", "Mexico"], "version": "ECC 6.0"},
                {"name": "Oracle EBS", "users": 400, "regions": ["Germany", "China"], "version": "R12"}
            ],
            "erp_strategy": "Dual ERP from prior acquisition, never consolidated",
            "crm": {"name": "Salesforce", "users": 250},
            "plm": {"name": "Siemens Teamcenter", "users": 150},
            "mes": [
                {"name": "Rockwell FactoryTalk", "plants": 3},
                {"name": "Custom MES", "plants": 2}
            ],
            "integration_platform": "IBM MQ + custom ETL",
            "custom_apps": 35,
            "technical_debt": "High - multiple unsupported versions"
        },
        "infrastructure": {
            "data_centers": 2,
            "cloud_adoption": "Early stage - 15%",
            "servers": {"physical": 85, "virtual": 320},
            "storage": "EMC VMAX (aging)"
        },
        "cybersecurity": {
            "mfa_coverage": 72,
            "endpoint_protection": "Mixed (McAfee + Symantec)",
            "siem": "Splunk",
            "pam": "None",
            "compliance": ["SOX", "GDPR"],
            "security_debt": "PAM project stalled, multiple tools need consolidation"
        },
        "network": {
            "wan_provider": "Multiple (regional)",
            "sd_wan": False,
            "mpls_circuits": 12,
            "locations": 18
        }
    },
    expected_characteristics={
        "narrative_focus": "integration_complexity",
        "erp_consolidation_addressed": True,
        "synergy_quantification": True,
        "key_synergies": ["ERP consolidation", "DC consolidation", "security tool rationalization", "WAN optimization"],
        "key_risks": ["dual ERP complexity", "technical debt", "no PAM", "aging infrastructure"],
        "exec_summary_bullets": (5, 7)
    },
    minimum_scores={
        "mna_framing": 4.5,
        "evidence_discipline": 4.0,
        "actionability": 4.0,
        "narrative_flow": 4.0,
        "completeness": 4.5,
        "tone": 4.0
    }
)


# =============================================================================
# TEST CASE 5: High Complexity Carveout (No Dedicated IT)
# =============================================================================

TC_05_HIGH_CARVEOUT_NO_IT = TestCase(
    id="TC-05",
    name="High Complexity Carveout - No Dedicated IT",
    description="Heavy TSA, build-from-scratch scenario",
    deal_type=DealType.CARVEOUT,
    complexity=Complexity.HIGH,
    target_name="Healthcare Services Division",
    buyer_name=None,  # PE sponsor
    inventory={
        "organization": {
            "dedicated_it_headcount": 0,
            "shared_it_support": "100% from parent",
            "structure": {
                "it_liaison": {"name": "Jennifer Park", "role": "Business Analyst", "it_knowledge": "Limited"},
                "parent_it_contacts": [
                    "Infrastructure Director (parent)",
                    "Applications Manager (parent)",
                    "Security Team (parent)"
                ]
            },
            "tsa_criticality": "Existential - no Day 1 IT capability without TSA"
        },
        "applications": {
            "erp": {"name": "Parent Workday", "module": "Financials only", "dedicated_instance": False},
            "emr": {"name": "Epic", "hosted_by": "Parent", "data_separation": "Complex"},
            "scheduling": {"name": "Parent custom app"},
            "billing": {"name": "Parent billing system"},
            "custom_apps": 0,
            "all_applications_parent_owned": True
        },
        "infrastructure": {
            "dedicated_infrastructure": "None",
            "parent_dc_dependency": "100%",
            "cloud": "Parent Azure tenant",
            "end_user_devices": 450,
            "device_management": "Parent Intune"
        },
        "cybersecurity": {
            "security_posture": "Unknown - managed by parent",
            "mfa": "Parent Azure AD",
            "endpoint": "Parent managed",
            "compliance": ["HIPAA - covered under parent BAA"],
            "standalone_compliance_gap": "No dedicated HIPAA compliance capability"
        },
        "network": {
            "wan": "Parent network",
            "locations": 12,
            "dedicated_circuits": 0,
            "internet": "Parent egress"
        }
    },
    expected_characteristics={
        "narrative_focus": "tsa_critical",
        "tsa_emphasis": "critical",
        "standalone_build_required": True,
        "tsa_services_count": (10, 15),
        "day_1_risks": (5, 10),
        "key_risks": ["no IT capability", "HIPAA compliance gap", "Epic separation", "complete dependency"],
        "cost_to_standalone": "significant",
        "exec_summary_bullets": (5, 7)
    },
    minimum_scores={
        "mna_framing": 5.0,  # Must be excellent given complexity
        "evidence_discipline": 4.0,
        "actionability": 4.5,
        "narrative_flow": 4.0,
        "completeness": 5.0,
        "tone": 4.0
    }
)


# =============================================================================
# TEST CASE REGISTRY
# =============================================================================

TEST_CASES = {
    "TC-01": TC_01_SIMPLE_ACQUISITION,
    "TC-02": TC_02_COMPLEX_CARVEOUT,
    "TC-03": TC_03_MEDIUM_DIVESTITURE,
    "TC-04": TC_04_COMPLEX_ACQUISITION,
    "TC-05": TC_05_HIGH_CARVEOUT_NO_IT,
}


def get_test_case(case_id: str) -> Optional[TestCase]:
    """Get a test case by ID."""
    return TEST_CASES.get(case_id)


def get_all_test_cases() -> List[TestCase]:
    """Get all test cases."""
    return list(TEST_CASES.values())


def get_test_cases_by_deal_type(deal_type: DealType) -> List[TestCase]:
    """Get test cases filtered by deal type."""
    return [tc for tc in TEST_CASES.values() if tc.deal_type == deal_type]


def get_test_cases_by_complexity(complexity: Complexity) -> List[TestCase]:
    """Get test cases filtered by complexity."""
    return [tc for tc in TEST_CASES.values() if tc.complexity == complexity]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'TestCase',
    'DealType',
    'Complexity',
    'TEST_CASES',
    'get_test_case',
    'get_all_test_cases',
    'get_test_cases_by_deal_type',
    'get_test_cases_by_complexity',
    'TC_01_SIMPLE_ACQUISITION',
    'TC_02_COMPLEX_CARVEOUT',
    'TC_03_MEDIUM_DIVESTITURE',
    'TC_04_COMPLEX_ACQUISITION',
    'TC_05_HIGH_CARVEOUT_NO_IT',
]
