"""
Workstream-Based Cost Model

A smarter cost estimation approach that:
1. Reasons through target state + buyer state + deal type
2. Derives required activities (not just pattern matching)
3. Costs the activities specifically
4. Identifies TSA bridge requirements
5. Provides integrated timeline

Each workstream is self-contained:
- Current state assessment
- Target state definition
- Gap/activity identification
- Cost estimation
- TSA requirements
- Timeline
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import hashlib


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class DealType(Enum):
    CARVEOUT = "carveout"
    ACQUISITION = "acquisition"
    DIVESTITURE = "divestiture"
    MERGER = "merger"


class WorkstreamStatus(Enum):
    NOT_APPLICABLE = "not_applicable"
    NO_CHANGE = "no_change"
    MINOR_CHANGE = "minor_change"
    MAJOR_CHANGE = "major_change"
    FULL_BUILD = "full_build"


@dataclass
class Activity:
    """A specific activity required to bridge a gap."""
    activity_id: str
    name: str
    description: str
    effort_days: Tuple[int, int]  # (low, high) estimate
    cost_per_unit: Tuple[float, float]  # If unit-based
    unit: Optional[str]  # "per_user", "per_app", "fixed", etc.
    requires_tsa: bool
    tsa_duration_months: Optional[Tuple[int, int]]
    prerequisites: List[str]  # Other activity IDs that must complete first


@dataclass
class WorkstreamAssessment:
    """Assessment of a single workstream."""
    workstream: str
    current_state: Dict[str, Any]
    target_state: Dict[str, Any]
    status: WorkstreamStatus
    activities: List[Dict]
    one_time_cost: Tuple[float, float]
    tsa_required: bool
    tsa_services: List[str]
    tsa_duration_months: Tuple[int, int]
    tsa_exit_cost: Tuple[float, float]
    timeline_months: Tuple[int, int]
    risks: List[str]
    dependencies: List[str]


# =============================================================================
# WORKSTREAM DEFINITIONS
# =============================================================================

WORKSTREAMS = {
    "identity": {
        "name": "Identity & Access Management",
        "description": "Directory services, SSO, MFA, access governance",
        "day1_critical": True,
        "typical_timeline_months": (3, 6),
    },
    "email": {
        "name": "Email & Collaboration",
        "description": "Email, calendar, file sharing, messaging",
        "day1_critical": True,
        "typical_timeline_months": (2, 4),
    },
    "applications": {
        "name": "Business Applications",
        "description": "ERP, CRM, HR systems, custom apps",
        "day1_critical": False,  # Can often run on TSA
        "typical_timeline_months": (6, 18),
    },
    "infrastructure": {
        "name": "Infrastructure & Hosting",
        "description": "Servers, storage, cloud platforms, data centers",
        "day1_critical": True,
        "typical_timeline_months": (6, 12),
    },
    "network": {
        "name": "Network & Connectivity",
        "description": "WAN, LAN, VPN, firewalls, internet",
        "day1_critical": True,
        "typical_timeline_months": (3, 6),
    },
    "security": {
        "name": "Security & Compliance",
        "description": "Security tools, monitoring, compliance, policies",
        "day1_critical": True,
        "typical_timeline_months": (3, 9),
    },
    "data": {
        "name": "Data & Analytics",
        "description": "Databases, data warehouse, BI, reporting",
        "day1_critical": False,
        "typical_timeline_months": (6, 12),
    },
    "service_desk": {
        "name": "IT Support & Service Desk",
        "description": "Helpdesk, desktop support, ITSM",
        "day1_critical": True,
        "typical_timeline_months": (3, 6),
    },
}


# =============================================================================
# ACTIVITY TEMPLATES - What activities are needed for each scenario?
# =============================================================================

ACTIVITY_TEMPLATES = {
    # =========================================================================
    # IDENTITY WORKSTREAM
    # =========================================================================
    "identity": {
        "separation_from_parent": {
            "triggers": ["parent ad", "parent azure ad", "corporate okta", "federated identity", "parent sso"],
            "activities": [
                {
                    "id": "ID-001",
                    "name": "Design standalone identity architecture",
                    "description": "Design new AD/Azure AD/Okta tenant structure",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 120000),
                    "requires_tsa": False,
                },
                {
                    "id": "ID-002",
                    "name": "Provision new identity platform",
                    "description": "Stand up new directory services (Azure AD, Okta, etc.)",
                    "effort_days": (15, 30),
                    "cost_fixed": (75000, 200000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "ID-003",
                    "name": "Migrate user accounts",
                    "description": "Export/import user accounts, groups, attributes",
                    "effort_days": (10, 25),
                    "cost_per_user": (15, 40),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "ID-004",
                    "name": "Reconfigure application SSO",
                    "description": "Update SAML/OIDC configs for all integrated apps",
                    "effort_days": (20, 40),
                    "cost_per_app": (2000, 8000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "ID-005",
                    "name": "MFA re-enrollment",
                    "description": "Re-enroll users in MFA on new platform",
                    "effort_days": (5, 15),
                    "cost_per_user": (5, 15),
                    "requires_tsa": True,
                    "tsa_months": (1, 2),
                },
                {
                    "id": "ID-006",
                    "name": "Credential reset and cutover",
                    "description": "Reset passwords, execute cutover weekend",
                    "effort_days": (5, 10),
                    "cost_fixed": (25000, 75000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Identity & Authentication Services",
            "tsa_criticality": "Day-1 Critical",
        },
        "integration_to_buyer": {
            "triggers": ["acquisition", "buyer directory", "buyer azure ad"],
            "activities": [
                {
                    "id": "ID-101",
                    "name": "Design identity integration",
                    "description": "Plan integration of target users into buyer directory",
                    "effort_days": (5, 15),
                    "cost_fixed": (30000, 80000),
                    "requires_tsa": False,
                },
                {
                    "id": "ID-102",
                    "name": "Provision target users in buyer directory",
                    "description": "Create accounts in buyer's AD/Azure AD",
                    "effort_days": (10, 20),
                    "cost_per_user": (10, 25),
                    "requires_tsa": False,
                },
                {
                    "id": "ID-103",
                    "name": "Establish trust/federation",
                    "description": "Set up trust between directories during transition",
                    "effort_days": (5, 10),
                    "cost_fixed": (20000, 50000),
                    "requires_tsa": False,
                },
                {
                    "id": "ID-104",
                    "name": "Migrate to buyer SSO",
                    "description": "Reconfigure target apps for buyer SSO",
                    "effort_days": (15, 30),
                    "cost_per_app": (1500, 5000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
    },

    # =========================================================================
    # EMAIL WORKSTREAM
    # =========================================================================
    "email": {
        "gmail_to_microsoft": {
            "triggers": ["gmail", "google workspace", "g suite"],
            "buyer_has": ["microsoft", "outlook", "m365", "office 365"],
            "activities": [
                {
                    "id": "EM-001",
                    "name": "Email migration planning",
                    "description": "Plan migration waves, test migrations, comms plan",
                    "effort_days": (5, 10),
                    "cost_fixed": (20000, 50000),
                    "requires_tsa": False,
                },
                {
                    "id": "EM-002",
                    "name": "Provision M365 licenses",
                    "description": "Procure and assign M365 licenses for target users",
                    "effort_days": (2, 5),
                    "cost_per_user": (0, 0),  # License cost is run-rate
                    "requires_tsa": False,
                },
                {
                    "id": "EM-003",
                    "name": "Migrate mailboxes",
                    "description": "Export Gmail mailboxes, import to Exchange Online",
                    "effort_days": (10, 25),
                    "cost_per_user": (10, 30),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "EM-004",
                    "name": "Migrate Drive to OneDrive/SharePoint",
                    "description": "Move Google Drive files to OneDrive/SharePoint",
                    "effort_days": (10, 20),
                    "cost_per_user": (8, 20),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "EM-005",
                    "name": "Reconfigure integrations",
                    "description": "Update apps that integrated with Gmail/Drive",
                    "effort_days": (5, 15),
                    "cost_per_app": (2000, 6000),
                    "requires_tsa": False,
                },
                {
                    "id": "EM-006",
                    "name": "User training",
                    "description": "Train users on Outlook/Teams/SharePoint",
                    "effort_days": (5, 10),
                    "cost_per_user": (10, 25),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Email & Collaboration (Gmail)",
            "tsa_criticality": "Day-1 Critical",
        },
        "microsoft_to_gmail": {
            "triggers": ["microsoft", "outlook", "m365", "office 365", "exchange"],
            "buyer_has": ["gmail", "google workspace"],
            "activities": [
                {
                    "id": "EM-101",
                    "name": "Google Workspace provisioning",
                    "description": "Set up Google Workspace tenant, configure domain",
                    "effort_days": (3, 8),
                    "cost_fixed": (15000, 40000),
                    "requires_tsa": False,
                },
                {
                    "id": "EM-102",
                    "name": "Migrate Exchange to Gmail",
                    "description": "Migrate mailboxes from Exchange to Gmail",
                    "effort_days": (10, 25),
                    "cost_per_user": (12, 35),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "EM-103",
                    "name": "Migrate OneDrive/SharePoint to Drive",
                    "description": "Move files to Google Drive",
                    "effort_days": (10, 20),
                    "cost_per_user": (8, 20),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "EM-104",
                    "name": "User training on Google Workspace",
                    "description": "Train users on Gmail/Drive/Meet",
                    "effort_days": (5, 10),
                    "cost_per_user": (10, 25),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Email & Collaboration (Microsoft 365)",
            "tsa_criticality": "Day-1 Critical",
        },
        "separation_from_parent": {
            "triggers": ["parent email", "parent m365", "parent tenant", "corporate email"],
            "activities": [
                {
                    "id": "EM-201",
                    "name": "Provision standalone email tenant",
                    "description": "Set up new M365/Google tenant for target",
                    "effort_days": (5, 10),
                    "cost_fixed": (25000, 60000),
                    "requires_tsa": False,
                },
                {
                    "id": "EM-202",
                    "name": "Migrate mailboxes to new tenant",
                    "description": "Cross-tenant mailbox migration",
                    "effort_days": (10, 25),
                    "cost_per_user": (15, 40),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "EM-203",
                    "name": "Domain cutover",
                    "description": "Transfer email domain to new tenant",
                    "effort_days": (2, 5),
                    "cost_fixed": (10000, 30000),
                    "requires_tsa": True,
                    "tsa_months": (1, 2),
                },
            ],
            "tsa_service": "Email & Collaboration",
            "tsa_criticality": "Day-1 Critical",
        },
    },

    # =========================================================================
    # APPLICATIONS WORKSTREAM
    # =========================================================================
    "applications": {
        "erp_separation": {
            "triggers": ["shared erp", "parent sap", "parent oracle", "shared instance", "parent netsuite"],
            "activities": [
                {
                    "id": "APP-001",
                    "name": "ERP separation assessment",
                    "description": "Analyze data, customizations, integrations to separate",
                    "effort_days": (20, 40),
                    "cost_fixed": (100000, 250000),
                    "requires_tsa": False,
                },
                {
                    "id": "APP-002",
                    "name": "Provision standalone ERP instance",
                    "description": "Set up new ERP tenant/instance for target",
                    "effort_days": (30, 60),
                    "cost_fixed": (200000, 600000),
                    "requires_tsa": True,
                    "tsa_months": (9, 18),
                },
                {
                    "id": "APP-003",
                    "name": "Data extraction and cleansing",
                    "description": "Extract target data, cleanse, transform",
                    "effort_days": (30, 60),
                    "cost_fixed": (150000, 400000),
                    "requires_tsa": True,
                    "tsa_months": (6, 12),
                },
                {
                    "id": "APP-004",
                    "name": "Rebuild customizations",
                    "description": "Recreate custom reports, workflows, objects",
                    "effort_days": (40, 100),
                    "cost_fixed": (200000, 800000),
                    "requires_tsa": True,
                    "tsa_months": (6, 12),
                },
                {
                    "id": "APP-005",
                    "name": "Rebuild integrations",
                    "description": "Reconnect integrations to new ERP instance",
                    "effort_days": (20, 50),
                    "cost_per_integration": (10000, 40000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "APP-006",
                    "name": "User acceptance testing",
                    "description": "UAT cycles with business users",
                    "effort_days": (20, 40),
                    "cost_fixed": (75000, 200000),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
                {
                    "id": "APP-007",
                    "name": "Cutover and hypercare",
                    "description": "Go-live execution and stabilization",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 150000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "ERP Services",
            "tsa_criticality": "Day-1 Important",
        },
        "erp_consolidation": {
            "triggers": ["dual erp", "multiple erp", "two erp systems"],
            "activities": [
                {
                    "id": "APP-101",
                    "name": "ERP consolidation assessment",
                    "description": "Determine target platform, migration scope",
                    "effort_days": (20, 40),
                    "cost_fixed": (100000, 250000),
                    "requires_tsa": False,
                },
                {
                    "id": "APP-102",
                    "name": "Data mapping and transformation",
                    "description": "Map data between ERPs, define transformations",
                    "effort_days": (40, 80),
                    "cost_fixed": (200000, 500000),
                    "requires_tsa": False,
                },
                {
                    "id": "APP-103",
                    "name": "Migrate to target ERP",
                    "description": "Full migration to consolidated platform",
                    "effort_days": (60, 120),
                    "cost_fixed": (500000, 2000000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
        "saas_rationalization": {
            "triggers": ["overlapping tools", "duplicate systems", "redundant apps"],
            "activities": [
                {
                    "id": "APP-201",
                    "name": "Application portfolio assessment",
                    "description": "Inventory apps, identify overlaps, recommend consolidation",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 120000),
                    "requires_tsa": False,
                },
                {
                    "id": "APP-202",
                    "name": "Retire redundant applications",
                    "description": "Migrate data, decommission apps",
                    "effort_days": (5, 15),
                    "cost_per_app": (15000, 50000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
    },

    # =========================================================================
    # INFRASTRUCTURE WORKSTREAM
    # =========================================================================
    "infrastructure": {
        "separation_from_parent_dc": {
            "triggers": ["parent data center", "parent hosted", "shared infrastructure", "parent servers"],
            "activities": [
                {
                    "id": "INF-001",
                    "name": "Infrastructure assessment",
                    "description": "Inventory servers, storage, dependencies",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 120000),
                    "requires_tsa": False,
                },
                {
                    "id": "INF-002",
                    "name": "Design target state architecture",
                    "description": "Design cloud/colo architecture for standalone",
                    "effort_days": (15, 30),
                    "cost_fixed": (75000, 200000),
                    "requires_tsa": False,
                },
                {
                    "id": "INF-003",
                    "name": "Provision cloud infrastructure",
                    "description": "Build out AWS/Azure/GCP environment",
                    "effort_days": (20, 40),
                    "cost_fixed": (100000, 300000),
                    "requires_tsa": True,
                    "tsa_months": (6, 12),
                },
                {
                    "id": "INF-004",
                    "name": "Migrate servers/workloads",
                    "description": "Lift-and-shift or replatform workloads",
                    "effort_days": (30, 60),
                    "cost_per_server": (3000, 10000),
                    "requires_tsa": True,
                    "tsa_months": (6, 12),
                },
                {
                    "id": "INF-005",
                    "name": "Data migration",
                    "description": "Migrate databases, file shares, storage",
                    "effort_days": (15, 30),
                    "cost_per_tb": (500, 2000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "INF-006",
                    "name": "Cutover and validation",
                    "description": "Execute cutover, validate all systems",
                    "effort_days": (5, 10),
                    "cost_fixed": (50000, 150000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Infrastructure & Hosting",
            "tsa_criticality": "Day-1 Critical",
        },
        "cloud_consolidation": {
            "triggers": ["different cloud", "aws and azure", "multi-cloud"],
            "buyer_has": ["aws", "azure", "gcp"],
            "activities": [
                {
                    "id": "INF-101",
                    "name": "Cloud consolidation assessment",
                    "description": "Evaluate consolidation vs multi-cloud strategy",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 120000),
                    "requires_tsa": False,
                },
                {
                    "id": "INF-102",
                    "name": "Cloud-to-cloud migration",
                    "description": "Migrate workloads to buyer's cloud platform",
                    "effort_days": (30, 60),
                    "cost_per_server": (5000, 15000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
    },

    # =========================================================================
    # NETWORK WORKSTREAM
    # =========================================================================
    "network": {
        "separation_from_parent": {
            "triggers": ["parent wan", "parent network", "shared mpls", "corporate network", "parent vpn"],
            "activities": [
                {
                    "id": "NET-001",
                    "name": "Network assessment",
                    "description": "Document current network, dependencies, traffic flows",
                    "effort_days": (5, 15),
                    "cost_fixed": (30000, 80000),
                    "requires_tsa": False,
                },
                {
                    "id": "NET-002",
                    "name": "Design standalone network",
                    "description": "Design WAN, SDWAN, internet, firewall architecture",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 150000),
                    "requires_tsa": False,
                },
                {
                    "id": "NET-003",
                    "name": "Procure network services",
                    "description": "Contract with ISP, SDWAN provider, etc.",
                    "effort_days": (10, 20),
                    "cost_fixed": (25000, 75000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "NET-004",
                    "name": "Deploy site connectivity",
                    "description": "Install circuits, configure routers/firewalls per site",
                    "effort_days": (3, 8),
                    "cost_per_site": (5000, 20000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "NET-005",
                    "name": "Network cutover",
                    "description": "Execute cutover from parent to standalone",
                    "effort_days": (5, 10),
                    "cost_fixed": (30000, 80000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Network Services",
            "tsa_criticality": "Day-1 Critical",
        },
        "integration_to_buyer": {
            "triggers": ["acquisition", "buyer network"],
            "activities": [
                {
                    "id": "NET-101",
                    "name": "Network integration design",
                    "description": "Plan connectivity between target and buyer networks",
                    "effort_days": (5, 10),
                    "cost_fixed": (25000, 60000),
                    "requires_tsa": False,
                },
                {
                    "id": "NET-102",
                    "name": "Establish site-to-site connectivity",
                    "description": "VPN or direct connect between environments",
                    "effort_days": (5, 15),
                    "cost_per_site": (3000, 10000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
    },

    # =========================================================================
    # SECURITY WORKSTREAM
    # =========================================================================
    "security": {
        "establish_standalone": {
            "triggers": ["parent soc", "parent security", "shared siem", "corporate security"],
            "activities": [
                {
                    "id": "SEC-001",
                    "name": "Security assessment",
                    "description": "Assess current security posture, identify gaps",
                    "effort_days": (10, 20),
                    "cost_fixed": (50000, 120000),
                    "requires_tsa": False,
                },
                {
                    "id": "SEC-002",
                    "name": "Deploy EDR/endpoint protection",
                    "description": "Roll out endpoint security to all devices",
                    "effort_days": (10, 20),
                    "cost_per_endpoint": (30, 80),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "SEC-003",
                    "name": "Deploy SIEM/logging",
                    "description": "Implement security monitoring and logging",
                    "effort_days": (15, 30),
                    "cost_fixed": (75000, 200000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "SEC-004",
                    "name": "Establish SOC/MDR capability",
                    "description": "Contract MDR provider or build SOC",
                    "effort_days": (10, 20),
                    "cost_fixed": (100000, 300000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "SEC-005",
                    "name": "Security policy development",
                    "description": "Create standalone security policies and procedures",
                    "effort_days": (10, 20),
                    "cost_fixed": (40000, 100000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": "Security Services",
            "tsa_criticality": "Day-1 Critical",
        },
        "integration_to_buyer": {
            "triggers": ["acquisition", "buyer security"],
            "activities": [
                {
                    "id": "SEC-101",
                    "name": "Security stack integration",
                    "description": "Deploy buyer's security tools to target environment",
                    "effort_days": (10, 25),
                    "cost_per_user": (15, 40),
                    "requires_tsa": False,
                },
                {
                    "id": "SEC-102",
                    "name": "Integrate into buyer SOC",
                    "description": "Connect target telemetry to buyer's security operations",
                    "effort_days": (5, 15),
                    "cost_fixed": (30000, 80000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
        "gap_remediation": {
            "triggers": ["no mfa", "no edr", "no siem", "security gaps", "audit findings"],
            "activities": [
                {
                    "id": "SEC-201",
                    "name": "Security gap remediation",
                    "description": "Address identified security gaps",
                    "effort_days": (20, 60),
                    "cost_fixed": (100000, 500000),
                    "requires_tsa": False,
                },
            ],
            "tsa_service": None,
            "tsa_criticality": None,
        },
    },

    # =========================================================================
    # SERVICE DESK WORKSTREAM
    # =========================================================================
    "service_desk": {
        "establish_standalone": {
            "triggers": ["parent service desk", "corporate helpdesk", "parent support", "shared itsm"],
            "activities": [
                {
                    "id": "SD-001",
                    "name": "Service desk design",
                    "description": "Design support model, SLAs, processes",
                    "effort_days": (5, 15),
                    "cost_fixed": (25000, 75000),
                    "requires_tsa": False,
                },
                {
                    "id": "SD-002",
                    "name": "ITSM tool implementation",
                    "description": "Deploy ticketing system (ServiceNow, Jira, etc.)",
                    "effort_days": (15, 30),
                    "cost_fixed": (50000, 150000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "SD-003",
                    "name": "Contract MSP or hire staff",
                    "description": "Establish support capability via MSP or internal team",
                    "effort_days": (10, 20),
                    "cost_fixed": (30000, 80000),
                    "requires_tsa": True,
                    "tsa_months": (3, 6),
                },
                {
                    "id": "SD-004",
                    "name": "Knowledge transfer from parent",
                    "description": "Document environment, transfer runbooks",
                    "effort_days": (10, 25),
                    "cost_fixed": (40000, 100000),
                    "requires_tsa": True,
                    "tsa_months": (2, 4),
                },
            ],
            "tsa_service": "IT Support / Service Desk",
            "tsa_criticality": "Day-1 Important",
        },
    },
}


# =============================================================================
# WORKSTREAM MODEL CLASS
# =============================================================================

class WorkstreamModel:
    """
    Workstream-based cost model that reasons through:
    1. Current state (from facts)
    2. Target state (from deal type + buyer context)
    3. Required activities (derived from gap)
    4. Costs (from activity templates)
    5. TSA requirements
    """

    def __init__(self):
        self.workstreams = WORKSTREAMS
        self.activity_templates = ACTIVITY_TEMPLATES

    def _extract_current_state(self, workstream: str, facts: List[Dict]) -> Dict[str, Any]:
        """Extract current state for a workstream from facts."""
        state = {
            "technologies": [],
            "providers": [],
            "parent_dependencies": [],
            "gaps_identified": [],
        }

        templates = self.activity_templates.get(workstream, {})

        for fact in facts:
            content = fact.get("content", "").lower()
            fact_id = fact.get("fact_id", "unknown")

            # Check each scenario's triggers
            for scenario_key, scenario in templates.items():
                for trigger in scenario.get("triggers", []):
                    if trigger.lower() in content:
                        if "parent" in trigger or "corporate" in trigger or "shared" in trigger:
                            state["parent_dependencies"].append({
                                "trigger": trigger,
                                "fact_id": fact_id,
                                "scenario": scenario_key
                            })
                        else:
                            state["technologies"].append({
                                "trigger": trigger,
                                "fact_id": fact_id,
                                "scenario": scenario_key
                            })

        return state

    def _determine_scenario(
        self,
        workstream: str,
        current_state: Dict,
        deal_type: DealType,
        buyer_context: Optional[Dict] = None
    ) -> Optional[str]:
        """Determine which activity scenario applies."""
        templates = self.activity_templates.get(workstream, {})

        # For carveouts, check if parent dependencies exist
        if deal_type in [DealType.CARVEOUT, DealType.DIVESTITURE]:
            if current_state["parent_dependencies"]:
                # Find the separation scenario
                for scenario_key in templates:
                    if "separation" in scenario_key:
                        return scenario_key

        # For acquisitions, check for integration scenarios
        if deal_type == DealType.ACQUISITION:
            # Check if buyer context indicates need for migration
            if buyer_context:
                buyer_tech = buyer_context.get(workstream, {})
                for scenario_key, scenario in templates.items():
                    buyer_has = scenario.get("buyer_has", [])
                    if buyer_has:
                        for tech in buyer_has:
                            if tech.lower() in str(buyer_tech).lower():
                                return scenario_key

            # Default to integration scenario if exists
            for scenario_key in templates:
                if "integration" in scenario_key:
                    return scenario_key

        # Check for consolidation/rationalization scenarios
        for tech in current_state.get("technologies", []):
            scenario = tech.get("scenario")
            if scenario and ("consolidation" in scenario or "rationalization" in scenario):
                return scenario

        # Check for gap remediation
        for gap in current_state.get("gaps_identified", []):
            scenario = gap.get("scenario")
            if scenario:
                return scenario

        return None

    def _calculate_activity_cost(
        self,
        activity: Dict,
        user_count: int,
        app_count: int = 20,
        site_count: int = 5,
        server_count: int = 50,
        endpoint_count: int = None,
        integration_count: int = 10,
        tb_count: int = 10
    ) -> Tuple[float, float]:
        """Calculate cost for a single activity."""
        if endpoint_count is None:
            endpoint_count = int(user_count * 1.2)  # Assume 1.2 devices per user

        if "cost_fixed" in activity:
            return activity["cost_fixed"]

        elif "cost_per_user" in activity:
            per_user = activity["cost_per_user"]
            return (per_user[0] * user_count, per_user[1] * user_count)

        elif "cost_per_app" in activity:
            per_app = activity["cost_per_app"]
            return (per_app[0] * app_count, per_app[1] * app_count)

        elif "cost_per_site" in activity:
            per_site = activity["cost_per_site"]
            return (per_site[0] * site_count, per_site[1] * site_count)

        elif "cost_per_server" in activity:
            per_server = activity["cost_per_server"]
            return (per_server[0] * server_count, per_server[1] * server_count)

        elif "cost_per_endpoint" in activity:
            per_endpoint = activity["cost_per_endpoint"]
            return (per_endpoint[0] * endpoint_count, per_endpoint[1] * endpoint_count)

        elif "cost_per_integration" in activity:
            per_int = activity["cost_per_integration"]
            return (per_int[0] * integration_count, per_int[1] * integration_count)

        elif "cost_per_tb" in activity:
            per_tb = activity["cost_per_tb"]
            return (per_tb[0] * tb_count, per_tb[1] * tb_count)

        return (0, 0)

    def assess_workstream(
        self,
        workstream: str,
        facts: List[Dict],
        deal_type: DealType,
        user_count: int,
        buyer_context: Optional[Dict] = None,
        app_count: int = 20,
        site_count: int = 5,
        server_count: int = 50
    ) -> WorkstreamAssessment:
        """Assess a single workstream."""
        ws_config = self.workstreams.get(workstream, {})

        # Extract current state
        current_state = self._extract_current_state(workstream, facts)

        # Determine applicable scenario
        scenario_key = self._determine_scenario(workstream, current_state, deal_type, buyer_context)

        if not scenario_key:
            return WorkstreamAssessment(
                workstream=workstream,
                current_state=current_state,
                target_state={},
                status=WorkstreamStatus.NO_CHANGE,
                activities=[],
                one_time_cost=(0, 0),
                tsa_required=False,
                tsa_services=[],
                tsa_duration_months=(0, 0),
                tsa_exit_cost=(0, 0),
                timeline_months=(0, 0),
                risks=[],
                dependencies=[]
            )

        # Get activities for this scenario
        scenario = self.activity_templates[workstream][scenario_key]
        activities = scenario.get("activities", [])

        # Calculate costs for each activity
        activity_details = []
        total_cost_low = 0
        total_cost_high = 0
        max_tsa_low = 0
        max_tsa_high = 0
        requires_tsa = False
        tsa_services = []

        for activity in activities:
            cost_range = self._calculate_activity_cost(
                activity, user_count, app_count, site_count, server_count
            )
            total_cost_low += cost_range[0]
            total_cost_high += cost_range[1]

            activity_detail = {
                "id": activity["id"],
                "name": activity["name"],
                "description": activity["description"],
                "cost_range": cost_range,
                "requires_tsa": activity.get("requires_tsa", False),
            }

            if activity.get("requires_tsa"):
                requires_tsa = True
                tsa_months = activity.get("tsa_months", (3, 6))
                activity_detail["tsa_months"] = tsa_months
                max_tsa_low = max(max_tsa_low, tsa_months[0])
                max_tsa_high = max(max_tsa_high, tsa_months[1])

            activity_details.append(activity_detail)

        if scenario.get("tsa_service"):
            tsa_services.append(scenario["tsa_service"])

        # Determine status based on activities
        if total_cost_high > 500000:
            status = WorkstreamStatus.MAJOR_CHANGE
        elif total_cost_high > 100000:
            status = WorkstreamStatus.MINOR_CHANGE
        else:
            status = WorkstreamStatus.NO_CHANGE

        # Get timeline from workstream config
        timeline = ws_config.get("typical_timeline_months", (3, 6))

        return WorkstreamAssessment(
            workstream=workstream,
            current_state=current_state,
            target_state={"scenario": scenario_key},
            status=status,
            activities=activity_details,
            one_time_cost=(round(total_cost_low, -3), round(total_cost_high, -3)),
            tsa_required=requires_tsa,
            tsa_services=tsa_services,
            tsa_duration_months=(max_tsa_low, max_tsa_high) if requires_tsa else (0, 0),
            tsa_exit_cost=(0, 0),  # Calculated separately if needed
            timeline_months=timeline,
            risks=[],
            dependencies=[]
        )

    def assess_all_workstreams(
        self,
        facts: List[Dict],
        deal_type: DealType,
        user_count: int,
        buyer_context: Optional[Dict] = None,
        app_count: int = 20,
        site_count: int = 5,
        server_count: int = 50
    ) -> Dict[str, Any]:
        """Assess all workstreams and produce comprehensive estimate."""
        assessments = {}
        total_one_time_low = 0
        total_one_time_high = 0
        all_tsa_services = []
        max_timeline_low = 0
        max_timeline_high = 0
        critical_path_items = []

        for ws_key in self.workstreams:
            assessment = self.assess_workstream(
                ws_key, facts, deal_type, user_count, buyer_context,
                app_count, site_count, server_count
            )
            assessments[ws_key] = assessment

            if assessment.status != WorkstreamStatus.NO_CHANGE:
                total_one_time_low += assessment.one_time_cost[0]
                total_one_time_high += assessment.one_time_cost[1]

                if assessment.tsa_services:
                    all_tsa_services.extend(assessment.tsa_services)

                ws_config = self.workstreams[ws_key]
                if ws_config.get("day1_critical"):
                    critical_path_items.append({
                        "workstream": ws_key,
                        "timeline": assessment.timeline_months
                    })
                    max_timeline_low = max(max_timeline_low, assessment.timeline_months[0])
                    max_timeline_high = max(max_timeline_high, assessment.timeline_months[1])

        # PMO overhead (10-15%)
        pmo_low = total_one_time_low * 0.10
        pmo_high = total_one_time_high * 0.15

        # Contingency (15-20%)
        contingency_low = (total_one_time_low + pmo_low) * 0.15
        contingency_high = (total_one_time_high + pmo_high) * 0.20

        grand_total_low = total_one_time_low + pmo_low + contingency_low
        grand_total_high = total_one_time_high + pmo_high + contingency_high

        return {
            "deal_type": deal_type.value,
            "user_count": user_count,
            "workstream_assessments": {k: self._assessment_to_dict(v) for k, v in assessments.items()},
            "summary": {
                "workstream_subtotal": (round(total_one_time_low, -3), round(total_one_time_high, -3)),
                "pmo_overhead": (round(pmo_low, -3), round(pmo_high, -3)),
                "contingency": (round(contingency_low, -3), round(contingency_high, -3)),
                "grand_total": (round(grand_total_low, -3), round(grand_total_high, -3)),
                "midpoint": round((grand_total_low + grand_total_high) / 2, -3),
            },
            "tsa_summary": {
                "services_required": list(set(all_tsa_services)),
                "count": len(set(all_tsa_services)),
            },
            "timeline_summary": {
                "critical_path_months": (max_timeline_low, max_timeline_high),
                "critical_path_items": critical_path_items,
                "overall_program_months": (max_timeline_low + 1, max_timeline_high + 3),
            },
            "methodology": "workstream_model_v1",
            "input_hash": hashlib.sha256(
                json.dumps({
                    "user_count": user_count,
                    "deal_type": deal_type.value,
                    "facts": [f.get("content", "")[:50] for f in facts]
                }, sort_keys=True).encode()
            ).hexdigest()[:12]
        }

    def _assessment_to_dict(self, assessment: WorkstreamAssessment) -> Dict:
        """Convert WorkstreamAssessment to dict for JSON serialization."""
        return {
            "workstream": assessment.workstream,
            "status": assessment.status.value,
            "activities": assessment.activities,
            "one_time_cost": assessment.one_time_cost,
            "tsa_required": assessment.tsa_required,
            "tsa_services": assessment.tsa_services,
            "tsa_duration_months": assessment.tsa_duration_months,
            "timeline_months": assessment.timeline_months,
        }

    def format_for_display(self, result: Dict) -> str:
        """Format result for display."""
        lines = [
            "=" * 80,
            "IT DUE DILIGENCE - WORKSTREAM COST ESTIMATE",
            "=" * 80,
            f"Deal Type: {result['deal_type'].upper()}",
            f"Users: {result['user_count']:,}",
            "",
        ]

        # Workstream breakdown
        lines.append("-" * 80)
        lines.append("WORKSTREAM BREAKDOWN")
        lines.append("-" * 80)

        for ws_key, ws_data in result["workstream_assessments"].items():
            if ws_data["status"] != "no_change":
                ws_name = self.workstreams[ws_key]["name"]
                cost = ws_data["one_time_cost"]
                lines.append(f"\n{ws_name}")
                lines.append(f"  Status: {ws_data['status'].replace('_', ' ').title()}")
                lines.append(f"  One-Time Cost: ${cost[0]:,.0f} - ${cost[1]:,.0f}")
                lines.append(f"  Timeline: {ws_data['timeline_months'][0]}-{ws_data['timeline_months'][1]} months")

                if ws_data["tsa_required"]:
                    lines.append(f"  TSA Required: Yes ({ws_data['tsa_duration_months'][0]}-{ws_data['tsa_duration_months'][1]} months)")
                    lines.append(f"    Services: {', '.join(ws_data['tsa_services'])}")

                lines.append("  Activities:")
                for act in ws_data["activities"][:5]:  # Show first 5
                    act_cost = act["cost_range"]
                    lines.append(f"    • {act['name']}: ${act_cost[0]:,.0f} - ${act_cost[1]:,.0f}")

        # Summary
        summary = result["summary"]
        lines.extend([
            "",
            "-" * 80,
            "COST SUMMARY",
            "-" * 80,
            f"  Workstream Subtotal: ${summary['workstream_subtotal'][0]:,.0f} - ${summary['workstream_subtotal'][1]:,.0f}",
            f"  PMO Overhead (10-15%): ${summary['pmo_overhead'][0]:,.0f} - ${summary['pmo_overhead'][1]:,.0f}",
            f"  Contingency (15-20%): ${summary['contingency'][0]:,.0f} - ${summary['contingency'][1]:,.0f}",
            "",
            f"  GRAND TOTAL: ${summary['grand_total'][0]:,.0f} - ${summary['grand_total'][1]:,.0f}",
            f"  Midpoint: ${summary['midpoint']:,.0f}",
        ])

        # TSA Summary
        tsa = result["tsa_summary"]
        if tsa["count"] > 0:
            lines.extend([
                "",
                "-" * 80,
                "TSA REQUIREMENTS",
                "-" * 80,
                f"  Services requiring TSA: {tsa['count']}",
            ])
            for svc in tsa["services_required"]:
                lines.append(f"    • {svc}")

        # Timeline
        timeline = result["timeline_summary"]
        lines.extend([
            "",
            "-" * 80,
            "TIMELINE",
            "-" * 80,
            f"  Critical Path: {timeline['critical_path_months'][0]}-{timeline['critical_path_months'][1]} months",
            f"  Overall Program: {timeline['overall_program_months'][0]}-{timeline['overall_program_months'][1]} months",
        ])

        lines.extend([
            "",
            "-" * 80,
            f"Methodology: {result['methodology']}",
            f"Input Hash: {result['input_hash']}",
            "=" * 80,
        ])

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DealType',
    'WorkstreamStatus',
    'Activity',
    'WorkstreamAssessment',
    'WORKSTREAMS',
    'ACTIVITY_TEMPLATES',
    'WorkstreamModel',
]
