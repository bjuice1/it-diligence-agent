"""
IT Due Diligence Reasoning Engine

The core intelligence that:
1. Takes facts (from documents) + context (deal type, buyer, meeting notes)
2. Applies deal framework logic to understand what matters
3. Derives required activities from workstream model
4. Generates narrative explanation of reasoning
5. Produces cost estimates with full traceability

The engine EXPLAINS its reasoning - it doesn't just produce numbers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import json
import hashlib
import re


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class Fact:
    """A fact extracted from documents or provided by user."""
    fact_id: str
    content: str
    source: str  # "document", "meeting_notes", "user_input"
    confidence: float = 1.0
    category: Optional[str] = None  # Which workstream it relates to


@dataclass
class Consideration:
    """A consideration derived from facts + framework."""
    consideration_id: str
    workstream: str
    finding: str  # What we found
    implication: str  # What it means for the deal
    reasoning: str  # Why this matters
    supporting_facts: List[str]  # Fact IDs
    deal_relevance: str  # How this relates to deal type
    milestone_impact: Dict[str, str]  # Impact at each milestone
    criticality: str  # "critical", "important", "informational"


@dataclass
class DerivedActivity:
    """An activity derived from considerations."""
    activity_id: str
    workstream: str
    name: str
    description: str
    why_needed: str  # The reasoning behind this activity
    triggered_by: List[str]  # Consideration IDs
    cost_range: Tuple[float, float]
    timeline_months: Tuple[int, int]
    requires_tsa: bool
    tsa_duration_months: Optional[Tuple[int, int]]
    dependencies: List[str]  # Other activity IDs


@dataclass
class TSARequirement:
    """A TSA service requirement."""
    service: str
    workstream: str
    why_needed: str
    duration_months: Tuple[int, int]
    criticality: str
    exit_activities: List[str]  # Activity IDs needed to exit this TSA
    supporting_facts: List[str]


@dataclass
class ReasoningOutput:
    """Complete output from the reasoning engine."""
    deal_type: str
    user_count: int
    facts_analyzed: int

    # The reasoning chain
    considerations: List[Consideration]
    derived_activities: List[DerivedActivity]
    tsa_requirements: List[TSARequirement]

    # Cost summary
    workstream_costs: Dict[str, Tuple[float, float]]
    total_one_time_cost: Tuple[float, float]
    tsa_exit_cost: Tuple[float, float]
    contingency: Tuple[float, float]
    grand_total: Tuple[float, float]

    # Timeline
    critical_path_months: Tuple[int, int]

    # Narrative
    executive_summary: str
    detailed_narrative: str

    # Traceability
    input_hash: str


# =============================================================================
# PATTERN LIBRARIES
# =============================================================================

# Patterns that indicate parent dependencies (trigger separation activities)
PARENT_DEPENDENCY_PATTERNS = {
    "identity": {
        "patterns": [
            r"parent\s*(azure\s*)?ad",
            r"corporate\s*(azure\s*)?ad",
            r"parent\s*okta",
            r"corporate\s*directory",
            r"federated\s*identity",
            r"parent\s*sso",
            r"corporate\s*sso",
            r"shared\s*identity",
        ],
        "finding_template": "Identity services are provided by parent",
        "implication_template": "Post-separation, target will need standalone identity platform",
        "why_critical": "Without identity services, users cannot authenticate to ANY system. Business stops.",
    },
    "email": {
        "patterns": [
            r"parent\s*(microsoft\s*)?365",
            r"parent\s*m365",
            r"corporate\s*email",
            r"parent\s*tenant",
            r"parent\s*exchange",
            r"shared\s*email",
            r"corporate\s*outlook",
        ],
        "finding_template": "Email/collaboration provided through parent tenant",
        "implication_template": "Post-separation, target needs standalone email platform",
        "why_critical": "Email is primary business communication. Cannot operate without it.",
    },
    "infrastructure": {
        "patterns": [
            r"parent\s*data\s*center",
            r"corporate\s*infrastructure",
            r"parent[\s\-]*hosted",
            r"shared\s*servers",
            r"parent\s*aws",
            r"parent\s*azure",
            r"corporate\s*cloud",
        ],
        "finding_template": "Infrastructure hosted by parent",
        "implication_template": "Post-separation, target needs standalone hosting",
        "why_critical": "Applications run on infrastructure. No infrastructure = no applications.",
    },
    "network": {
        "patterns": [
            r"parent\s*wan",
            r"corporate\s*network",
            r"shared\s*mpls",
            r"parent\s*vpn",
            r"corporate\s*firewall",
            r"parent\s*network",
        ],
        "finding_template": "Network connectivity provided by parent",
        "implication_template": "Post-separation, target needs standalone network",
        "why_critical": "Network connects everything. No network = isolated sites, no remote access.",
    },
    "security": {
        "patterns": [
            r"parent\s*soc",
            r"corporate\s*security",
            r"shared\s*siem",
            r"parent[\s\-]*managed\s*security",
            r"corporate\s*soc",
        ],
        "finding_template": "Security monitoring provided by parent",
        "implication_template": "Post-separation, target needs standalone security operations",
        "why_critical": "Security monitoring detects threats. Gap in coverage = undetected breaches.",
    },
    "service_desk": {
        "patterns": [
            r"parent\s*service\s*desk",
            r"corporate\s*helpdesk",
            r"parent\s*support",
            r"shared\s*itsm",
            r"corporate\s*it\s*support",
        ],
        "finding_template": "IT support provided by parent service desk",
        "implication_template": "Post-separation, target needs standalone IT support",
        "why_critical": "Users need support. No helpdesk = unresolved issues, productivity loss.",
    },
    "applications": {
        "patterns": [
            r"parent\s*sap",
            r"shared\s*erp",
            r"corporate\s*oracle",
            r"parent\s*netsuite",
            r"shared\s*instance",
            r"parent[\s\-]*managed\s*erp",
        ],
        "finding_template": "ERP/core applications shared with or provided by parent",
        "implication_template": "Post-separation, target needs standalone ERP instance",
        "why_critical": "ERP runs finance, operations, HR. Critical for business operations.",
    },
}

# Patterns that indicate technology choices (for acquisition integration)
TECHNOLOGY_PATTERNS = {
    "email_google": {
        "patterns": [r"gmail", r"google\s*workspace", r"g\s*suite"],
        "technology": "Google Workspace",
        "category": "email",
    },
    "email_microsoft": {
        "patterns": [r"microsoft\s*365", r"m365", r"outlook", r"exchange\s*online", r"office\s*365"],
        "technology": "Microsoft 365",
        "category": "email",
    },
    "cloud_aws": {
        "patterns": [r"\baws\b", r"amazon\s*web\s*services", r"ec2", r"s3\s*bucket"],
        "technology": "AWS",
        "category": "cloud",
    },
    "cloud_azure": {
        "patterns": [r"\bazure\b", r"microsoft\s*cloud"],
        "technology": "Azure",
        "category": "cloud",
    },
    "cloud_gcp": {
        "patterns": [r"\bgcp\b", r"google\s*cloud"],
        "technology": "GCP",
        "category": "cloud",
    },
    "identity_okta": {
        "patterns": [r"\bokta\b"],
        "technology": "Okta",
        "category": "identity",
    },
    "identity_azure_ad": {
        "patterns": [r"azure\s*ad", r"entra\s*id", r"azure\s*active\s*directory"],
        "technology": "Azure AD",
        "category": "identity",
    },
    "erp_sap": {
        "patterns": [r"\bsap\b", r"s/4\s*hana", r"ecc"],
        "technology": "SAP",
        "category": "erp",
    },
    "erp_oracle": {
        "patterns": [r"oracle\s*erp", r"oracle\s*ebs", r"oracle\s*cloud"],
        "technology": "Oracle",
        "category": "erp",
    },
    "erp_netsuite": {
        "patterns": [r"netsuite"],
        "technology": "NetSuite",
        "category": "erp",
    },
    "security_crowdstrike": {
        "patterns": [r"crowdstrike"],
        "technology": "CrowdStrike",
        "category": "security",
    },
    "security_splunk": {
        "patterns": [r"splunk"],
        "technology": "Splunk",
        "category": "security",
    },
}

# Patterns that indicate gaps or risks
GAP_PATTERNS = {
    "no_mfa": {
        "patterns": [r"no\s*mfa", r"mfa\s*not\s*deployed", r"without\s*mfa"],
        "finding": "MFA not fully deployed",
        "implication": "Security gap - requires remediation",
        "criticality": "high",
    },
    "no_edr": {
        "patterns": [r"no\s*edr", r"no\s*endpoint", r"antivirus\s*only"],
        "finding": "No EDR/advanced endpoint protection",
        "implication": "Security gap - modern endpoint protection needed",
        "criticality": "high",
    },
    "no_siem": {
        "patterns": [r"no\s*siem", r"no\s*security\s*monitoring", r"no\s*logging"],
        "finding": "No SIEM/security monitoring",
        "implication": "Security gap - cannot detect threats",
        "criticality": "high",
    },
    "technical_debt": {
        "patterns": [r"technical\s*debt", r"legacy\s*code", r"unsupported", r"end\s*of\s*life"],
        "finding": "Technical debt or legacy systems identified",
        "implication": "Increases project risk and potential for cost overruns",
        "criticality": "medium",
    },
    "key_person": {
        "patterns": [r"key\s*person", r"single\s*point", r"one\s*person\s*knows", r"tribal\s*knowledge"],
        "finding": "Key person dependency identified",
        "implication": "Risk if key personnel leave during transition",
        "criticality": "high",
    },
}

# Quantitative patterns for extracting numbers
QUANTITATIVE_PATTERNS = {
    "user_count": [
        r"(\d{1,3}(?:,\d{3})*)\s*(?:employees|users|staff|people)",
        r"(?:employees|users|staff|headcount).*?(\d{1,3}(?:,\d{3})*)",
    ],
    "site_count": [
        r"(\d+)\s*(?:sites|locations|offices|facilities)",
        r"(?:sites|locations|offices).*?(\d+)",
    ],
    "app_count": [
        r"(\d+)\s*(?:applications|apps|systems)",
        r"(?:applications|apps).*?(\d+)",
    ],
    "server_count": [
        r"(\d+)\s*(?:servers|vms|virtual\s*machines)",
    ],
}


# =============================================================================
# COST ANCHORS (from cost_model.py, simplified)
# =============================================================================

ACTIVITY_COSTS = {
    # Identity
    "identity_separation_design": (50000, 120000),
    "identity_platform_provision": (75000, 200000),
    "identity_user_migration_per_user": (15, 40),
    "identity_sso_reconfig_per_app": (2000, 8000),
    "identity_mfa_reenroll_per_user": (5, 15),
    "identity_cutover": (25000, 75000),

    # Email
    "email_tenant_provision": (25000, 60000),
    "email_migration_per_user": (15, 40),
    "email_domain_cutover": (10000, 30000),
    "email_training_per_user": (10, 25),
    "email_platform_migration_per_user": (25, 60),  # Gmail to M365 or vice versa

    # Infrastructure
    "infra_assessment": (50000, 120000),
    "infra_architecture_design": (75000, 200000),
    "infra_cloud_provision": (100000, 300000),
    "infra_server_migration_per_server": (3000, 10000),
    "infra_data_migration_per_tb": (500, 2000),
    "infra_cutover": (50000, 150000),

    # Network
    "network_assessment": (30000, 80000),
    "network_design": (50000, 150000),
    "network_procurement": (25000, 75000),
    "network_site_deploy_per_site": (5000, 20000),
    "network_cutover": (30000, 80000),

    # Security
    "security_assessment": (50000, 120000),
    "security_edr_deploy_per_endpoint": (30, 80),
    "security_siem_deploy": (75000, 200000),
    "security_mdr_establish": (100000, 300000),
    "security_policy_development": (40000, 100000),
    "security_gap_remediation": (100000, 500000),

    # Service Desk
    "service_desk_design": (25000, 75000),
    "service_desk_itsm_deploy": (50000, 150000),
    "service_desk_msp_contract": (30000, 80000),
    "service_desk_knowledge_transfer": (40000, 100000),

    # Applications/ERP
    "erp_separation_assessment": (100000, 250000),
    "erp_instance_provision": (200000, 600000),
    "erp_data_extraction": (150000, 400000),
    "erp_customization_rebuild": (200000, 800000),
    "erp_integration_rebuild_per_integration": (10000, 40000),
    "erp_uat": (75000, 200000),
    "erp_cutover": (50000, 150000),
}


# =============================================================================
# REASONING ENGINE
# =============================================================================

class ReasoningEngine:
    """
    The core reasoning engine that connects facts → framework → activities → costs.

    Key principle: Every output is EXPLAINED with reasoning, not just stated.
    """

    def __init__(self):
        self.parent_patterns = PARENT_DEPENDENCY_PATTERNS
        self.tech_patterns = TECHNOLOGY_PATTERNS
        self.gap_patterns = GAP_PATTERNS
        self.quant_patterns = QUANTITATIVE_PATTERNS
        self.activity_costs = ACTIVITY_COSTS

    def _match_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Match regex patterns against text."""
        matches = []
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches.append(pattern)
        return matches

    def _extract_number(self, text: str, patterns: List[str]) -> Optional[int]:
        """Extract a number from text using patterns."""
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                num_str = match.group(1).replace(",", "")
                return int(num_str)
        return None

    def extract_quantitative_context(self, facts: List[Dict]) -> Dict[str, int]:
        """Extract quantitative context (user count, sites, etc.) from facts."""
        context = {
            "user_count": 1000,  # Default
            "site_count": 5,
            "app_count": 20,
            "server_count": 50,
        }

        for fact in facts:
            content = fact.get("content", "")

            for key, patterns in self.quant_patterns.items():
                extracted = self._extract_number(content, patterns)
                if extracted:
                    context[key] = extracted

        return context

    def identify_parent_dependencies(
        self,
        facts: List[Dict]
    ) -> List[Consideration]:
        """Identify parent dependencies from facts."""
        considerations = []
        consideration_id = 1

        for workstream, config in self.parent_patterns.items():
            matching_facts = []

            for fact in facts:
                content = fact.get("content", "")
                if self._match_patterns(content, config["patterns"]):
                    matching_facts.append(fact)

            if matching_facts:
                considerations.append(Consideration(
                    consideration_id=f"C{consideration_id:03d}",
                    workstream=workstream,
                    finding=config["finding_template"],
                    implication=config["implication_template"],
                    reasoning=config["why_critical"],
                    supporting_facts=[f.get("fact_id", "unknown") for f in matching_facts],
                    deal_relevance="Requires separation activities in carveout; may need TSA",
                    milestone_impact={
                        "day_1": "TSA required to maintain operations",
                        "day_100": "Standalone capability should be established",
                    },
                    criticality="critical",
                ))
                consideration_id += 1

        return considerations

    def identify_technology_stack(
        self,
        facts: List[Dict]
    ) -> Dict[str, List[str]]:
        """Identify target's technology stack."""
        stack = {}

        for tech_key, config in self.tech_patterns.items():
            for fact in facts:
                content = fact.get("content", "")
                if self._match_patterns(content, config["patterns"]):
                    category = config["category"]
                    if category not in stack:
                        stack[category] = []
                    if config["technology"] not in stack[category]:
                        stack[category].append(config["technology"])

        return stack

    def identify_gaps_and_risks(
        self,
        facts: List[Dict]
    ) -> List[Consideration]:
        """Identify security gaps and risks."""
        considerations = []
        consideration_id = 100  # Start at 100 for gaps

        for gap_key, config in self.gap_patterns.items():
            matching_facts = []

            for fact in facts:
                content = fact.get("content", "")
                if self._match_patterns(content, config["patterns"]):
                    matching_facts.append(fact)

            if matching_facts:
                considerations.append(Consideration(
                    consideration_id=f"C{consideration_id:03d}",
                    workstream="security" if "mfa" in gap_key or "edr" in gap_key or "siem" in gap_key else "general",
                    finding=config["finding"],
                    implication=config["implication"],
                    reasoning=f"This gap must be addressed to ensure secure operations post-transaction",
                    supporting_facts=[f.get("fact_id", "unknown") for f in matching_facts],
                    deal_relevance="Requires remediation regardless of deal type",
                    milestone_impact={
                        "day_1": "Gap may exist at close",
                        "day_100": "Should be remediated",
                    },
                    criticality=config["criticality"],
                ))
                consideration_id += 1

        return considerations

    def derive_activities_for_carveout(
        self,
        considerations: List[Consideration],
        quant_context: Dict[str, int]
    ) -> List[DerivedActivity]:
        """Derive required activities for a carveout based on considerations."""
        activities = []
        activity_id = 1

        user_count = quant_context.get("user_count", 1000)
        site_count = quant_context.get("site_count", 5)
        app_count = quant_context.get("app_count", 20)
        server_count = quant_context.get("server_count", 50)

        for consideration in considerations:
            if consideration.criticality not in ["critical", "important"]:
                continue

            ws = consideration.workstream

            # Identity separation activities
            if ws == "identity":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="identity",
                        name="Design standalone identity architecture",
                        description="Design new AD/Azure AD/Okta tenant structure for standalone operations",
                        why_needed=f"Because: {consideration.finding}. {consideration.reasoning}",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["identity_separation_design"],
                        timeline_months=(1, 2),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="identity",
                        name="Provision standalone identity platform",
                        description="Build new directory services (Azure AD, Okta, etc.)",
                        why_needed="Required before users can be migrated off parent identity",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["identity_platform_provision"],
                        timeline_months=(1, 2),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 2:03d}",
                        workstream="identity",
                        name=f"Migrate {user_count:,} user accounts",
                        description="Export/import user accounts, groups, and attributes",
                        why_needed="Users must exist in new directory before cutover",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["identity_user_migration_per_user"][0] * user_count,
                            self.activity_costs["identity_user_migration_per_user"][1] * user_count,
                        ),
                        timeline_months=(1, 2),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id + 1:03d}"],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 3:03d}",
                        workstream="identity",
                        name=f"Reconfigure SSO for {app_count} applications",
                        description="Update SAML/OIDC configurations for all integrated applications",
                        why_needed="Applications must point to new identity provider",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["identity_sso_reconfig_per_app"][0] * app_count,
                            self.activity_costs["identity_sso_reconfig_per_app"][1] * app_count,
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id + 1:03d}"],
                    ),
                ])
                activity_id += 4

            # Email separation activities
            elif ws == "email":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="email",
                        name="Provision standalone email tenant",
                        description="Set up new M365 or Google Workspace tenant",
                        why_needed=f"Because: {consideration.finding}. Target needs own email platform.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["email_tenant_provision"],
                        timeline_months=(0.5, 1),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="email",
                        name=f"Migrate {user_count:,} mailboxes",
                        description="Cross-tenant mailbox migration including email, calendar, contacts",
                        why_needed="Users need their email history in new environment",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["email_migration_per_user"][0] * user_count,
                            self.activity_costs["email_migration_per_user"][1] * user_count,
                        ),
                        timeline_months=(1, 3),
                        requires_tsa=True,
                        tsa_duration_months=(2, 4),
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

            # Infrastructure separation activities
            elif ws == "infrastructure":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="infrastructure",
                        name="Infrastructure assessment and inventory",
                        description="Document all servers, storage, dependencies in parent environment",
                        why_needed=f"Because: {consideration.finding}. Must understand what needs to move.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["infra_assessment"],
                        timeline_months=(0.5, 1),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="infrastructure",
                        name="Design target state architecture",
                        description="Design cloud/colo architecture for standalone operations",
                        why_needed="Need to know where workloads are going before migration",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["infra_architecture_design"],
                        timeline_months=(1, 2),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 2:03d}",
                        workstream="infrastructure",
                        name="Provision standalone cloud environment",
                        description="Build out AWS/Azure/GCP environment for target",
                        why_needed="Destination must exist before migration can begin",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["infra_cloud_provision"],
                        timeline_months=(1, 2),
                        requires_tsa=True,
                        tsa_duration_months=(6, 12),
                        dependencies=[f"A{activity_id + 1:03d}"],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 3:03d}",
                        workstream="infrastructure",
                        name=f"Migrate {server_count} servers/workloads",
                        description="Lift-and-shift or replatform workloads to standalone environment",
                        why_needed="Applications must run somewhere - move from parent to standalone",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["infra_server_migration_per_server"][0] * server_count,
                            self.activity_costs["infra_server_migration_per_server"][1] * server_count,
                        ),
                        timeline_months=(3, 6),
                        requires_tsa=True,
                        tsa_duration_months=(6, 12),
                        dependencies=[f"A{activity_id + 2:03d}"],
                    ),
                ])
                activity_id += 4

            # Network separation activities
            elif ws == "network":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="network",
                        name="Network assessment and design",
                        description="Document current network, design standalone WAN/SDWAN architecture",
                        why_needed=f"Because: {consideration.finding}. Must plan network independence.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["network_assessment"][0] + self.activity_costs["network_design"][0],
                            self.activity_costs["network_assessment"][1] + self.activity_costs["network_design"][1],
                        ),
                        timeline_months=(1, 2),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="network",
                        name=f"Deploy network connectivity to {site_count} sites",
                        description="Install circuits, configure routers/firewalls at each location",
                        why_needed="Each site needs independent connectivity",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["network_site_deploy_per_site"][0] * site_count + self.activity_costs["network_procurement"][0],
                            self.activity_costs["network_site_deploy_per_site"][1] * site_count + self.activity_costs["network_procurement"][1],
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

            # Security activities
            elif ws == "security":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="security",
                        name="Security assessment and gap analysis",
                        description="Assess current security posture, identify gaps for standalone",
                        why_needed=f"Because: {consideration.finding}. Must understand security requirements.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["security_assessment"],
                        timeline_months=(0.5, 1),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="security",
                        name="Deploy security tooling (SIEM, EDR, etc.)",
                        description="Implement security monitoring, endpoint protection, threat detection",
                        why_needed="Cannot operate without security controls - compliance and risk",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["security_siem_deploy"][0] + self.activity_costs["security_edr_deploy_per_endpoint"][0] * int(user_count * 1.2),
                            self.activity_costs["security_siem_deploy"][1] + self.activity_costs["security_edr_deploy_per_endpoint"][1] * int(user_count * 1.2),
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 2:03d}",
                        workstream="security",
                        name="Establish SOC/MDR capability",
                        description="Contract MDR provider or build internal security operations",
                        why_needed="Need 24/7 monitoring and incident response capability",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["security_mdr_establish"],
                        timeline_months=(1, 3),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[f"A{activity_id + 1:03d}"],
                    ),
                ])
                activity_id += 3

            # Service desk activities
            elif ws == "service_desk":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="service_desk",
                        name="Establish standalone IT support",
                        description="Contract MSP or hire staff, deploy ITSM tool, transfer knowledge",
                        why_needed=f"Because: {consideration.finding}. Users need support from Day 1.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["service_desk_design"][0] + self.activity_costs["service_desk_itsm_deploy"][0] + self.activity_costs["service_desk_msp_contract"][0],
                            self.activity_costs["service_desk_design"][1] + self.activity_costs["service_desk_itsm_deploy"][1] + self.activity_costs["service_desk_msp_contract"][1],
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=True,
                        tsa_duration_months=(3, 6),
                        dependencies=[],
                    ),
                ])
                activity_id += 1

            # ERP/Applications activities
            elif ws == "applications":
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="applications",
                        name="ERP separation assessment",
                        description="Analyze data, customizations, integrations requiring separation",
                        why_needed=f"Because: {consideration.finding}. Must understand ERP separation scope.",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs["erp_separation_assessment"],
                        timeline_months=(1, 2),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="applications",
                        name="ERP separation/migration",
                        description="Full ERP instance separation including data, customizations, integrations",
                        why_needed="Cannot operate long-term on shared ERP instance",
                        triggered_by=[consideration.consideration_id],
                        cost_range=(
                            self.activity_costs["erp_instance_provision"][0] + self.activity_costs["erp_data_extraction"][0] + self.activity_costs["erp_customization_rebuild"][0],
                            self.activity_costs["erp_instance_provision"][1] + self.activity_costs["erp_data_extraction"][1] + self.activity_costs["erp_customization_rebuild"][1],
                        ),
                        timeline_months=(9, 18),
                        requires_tsa=True,
                        tsa_duration_months=(12, 18),
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

        return activities

    def identify_technology_mismatches(
        self,
        target_stack: Dict[str, List[str]],
        buyer_context: Dict[str, Any]
    ) -> List[Dict]:
        """Identify technology mismatches between target and buyer."""
        mismatches = []

        # Email mismatch
        target_email = target_stack.get("email", [])
        buyer_email = buyer_context.get("email", "")

        if target_email and buyer_email:
            target_is_google = any("Google" in t or "Gmail" in t for t in target_email)
            target_is_microsoft = any("Microsoft" in t or "365" in t for t in target_email)
            buyer_is_google = "google" in buyer_email.lower() or "gmail" in buyer_email.lower()
            buyer_is_microsoft = "microsoft" in buyer_email.lower() or "365" in buyer_email.lower() or "outlook" in buyer_email.lower()

            if target_is_google and buyer_is_microsoft:
                mismatches.append({
                    "category": "email",
                    "target": "Google Workspace",
                    "buyer": "Microsoft 365",
                    "action": "Migrate target from Gmail to Microsoft 365",
                    "complexity": "moderate",
                })
            elif target_is_microsoft and buyer_is_google:
                mismatches.append({
                    "category": "email",
                    "target": "Microsoft 365",
                    "buyer": "Google Workspace",
                    "action": "Migrate target from Microsoft 365 to Google Workspace",
                    "complexity": "moderate",
                })

        # Cloud mismatch
        target_cloud = target_stack.get("cloud", [])
        buyer_cloud = buyer_context.get("cloud", "")

        if target_cloud and buyer_cloud:
            target_clouds = set(t.lower() for t in target_cloud)
            buyer_cloud_lower = buyer_cloud.lower()

            if "aws" in target_clouds and "azure" in buyer_cloud_lower:
                mismatches.append({
                    "category": "cloud",
                    "target": "AWS",
                    "buyer": "Azure",
                    "action": "Migrate target workloads from AWS to Azure or establish multi-cloud",
                    "complexity": "high",
                })
            elif "azure" in target_clouds and "aws" in buyer_cloud_lower:
                mismatches.append({
                    "category": "cloud",
                    "target": "Azure",
                    "buyer": "AWS",
                    "action": "Migrate target workloads from Azure to AWS or establish multi-cloud",
                    "complexity": "high",
                })
            elif "gcp" in target_clouds and ("aws" in buyer_cloud_lower or "azure" in buyer_cloud_lower):
                mismatches.append({
                    "category": "cloud",
                    "target": "GCP",
                    "buyer": buyer_cloud,
                    "action": f"Migrate target workloads from GCP to {buyer_cloud}",
                    "complexity": "high",
                })

        # Identity mismatch
        target_identity = target_stack.get("identity", [])
        buyer_identity = buyer_context.get("identity", "")

        if target_identity and buyer_identity:
            target_has_okta = any("okta" in t.lower() for t in target_identity)
            target_has_azure = any("azure" in t.lower() for t in target_identity)
            buyer_has_okta = "okta" in buyer_identity.lower()
            buyer_has_azure = "azure" in buyer_identity.lower()

            if target_has_okta and buyer_has_azure:
                mismatches.append({
                    "category": "identity",
                    "target": "Okta",
                    "buyer": "Azure AD",
                    "action": "Migrate target users from Okta to Azure AD",
                    "complexity": "moderate",
                })
            elif target_has_azure and buyer_has_okta:
                mismatches.append({
                    "category": "identity",
                    "target": "Azure AD",
                    "buyer": "Okta",
                    "action": "Migrate target users from Azure AD to Okta",
                    "complexity": "moderate",
                })

        # ERP differences
        target_erp = target_stack.get("erp", [])
        buyer_erp = buyer_context.get("erp", "")

        if target_erp and buyer_erp:
            target_erps = [t.lower() for t in target_erp]
            buyer_erp_lower = buyer_erp.lower()

            if any("sap" in t for t in target_erps) and "netsuite" in buyer_erp_lower:
                mismatches.append({
                    "category": "erp",
                    "target": "SAP",
                    "buyer": "NetSuite",
                    "action": "ERP consolidation required - significant effort",
                    "complexity": "very_high",
                })
            elif any("netsuite" in t for t in target_erps) and "sap" in buyer_erp_lower:
                mismatches.append({
                    "category": "erp",
                    "target": "NetSuite",
                    "buyer": "SAP",
                    "action": "Migrate target to buyer's SAP",
                    "complexity": "very_high",
                })

        return mismatches

    def derive_activities_for_acquisition(
        self,
        considerations: List[Consideration],
        tech_mismatches: List[Dict],
        quant_context: Dict[str, int],
        buyer_context: Dict[str, Any]
    ) -> List[DerivedActivity]:
        """Derive required activities for an acquisition based on integration needs."""
        activities = []
        activity_id = 1

        user_count = quant_context.get("user_count", 1000)
        site_count = quant_context.get("site_count", 5)
        app_count = quant_context.get("app_count", 20)
        server_count = quant_context.get("server_count", 50)

        # Process technology mismatches first - these drive integration activities
        for mismatch in tech_mismatches:
            category = mismatch["category"]

            if category == "email":
                # Email platform migration
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="email",
                        name=f"Email migration: {mismatch['target']} → {mismatch['buyer']}",
                        description=f"Migrate target users from {mismatch['target']} to buyer's {mismatch['buyer']} platform",
                        why_needed=f"Target uses {mismatch['target']}, buyer uses {mismatch['buyer']}. Consolidation required for unified collaboration.",
                        triggered_by=[],
                        cost_range=(
                            self.activity_costs["email_platform_migration_per_user"][0] * user_count,
                            self.activity_costs["email_platform_migration_per_user"][1] * user_count,
                        ),
                        timeline_months=(1, 3),
                        requires_tsa=True,  # Need to maintain old platform during migration
                        tsa_duration_months=(2, 4),
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="email",
                        name="User training on new collaboration platform",
                        description=f"Train {user_count:,} users on {mismatch['buyer']} tools and workflows",
                        why_needed="Users need to learn new email/collaboration platform for productivity",
                        triggered_by=[],
                        cost_range=(
                            self.activity_costs["email_training_per_user"][0] * user_count,
                            self.activity_costs["email_training_per_user"][1] * user_count,
                        ),
                        timeline_months=(0.5, 1),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

            elif category == "identity":
                # Identity integration
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="identity",
                        name=f"Identity integration: {mismatch['target']} → {mismatch['buyer']}",
                        description=f"Migrate target users into buyer's {mismatch['buyer']} directory",
                        why_needed=f"Target uses {mismatch['target']}, buyer uses {mismatch['buyer']}. Single identity platform needed.",
                        triggered_by=[],
                        cost_range=(
                            self.activity_costs["identity_user_migration_per_user"][0] * user_count + 50000,
                            self.activity_costs["identity_user_migration_per_user"][1] * user_count + 150000,
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=False,  # Buyer provides destination
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="identity",
                        name="Reconfigure target applications for buyer SSO",
                        description=f"Update {app_count} applications to use buyer's identity provider",
                        why_needed="Applications must authenticate against buyer's directory",
                        triggered_by=[],
                        cost_range=(
                            self.activity_costs["identity_sso_reconfig_per_app"][0] * app_count * 0.7,  # Slightly less than separation
                            self.activity_costs["identity_sso_reconfig_per_app"][1] * app_count * 0.7,
                        ),
                        timeline_months=(2, 4),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

            elif category == "cloud":
                # Cloud consolidation
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="infrastructure",
                        name=f"Cloud strategy assessment: {mismatch['target']} vs {mismatch['buyer']}",
                        description="Evaluate consolidation to single cloud vs multi-cloud approach",
                        why_needed=f"Target on {mismatch['target']}, buyer on {mismatch['buyer']}. Need unified strategy.",
                        triggered_by=[],
                        cost_range=(50000, 120000),
                        timeline_months=(0.5, 1),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="infrastructure",
                        name=f"Cloud workload migration: {mismatch['target']} → {mismatch['buyer']}",
                        description=f"Migrate {server_count} workloads to buyer's cloud platform",
                        why_needed="Consolidation to single cloud platform for operational efficiency",
                        triggered_by=[],
                        cost_range=(
                            self.activity_costs["infra_server_migration_per_server"][0] * server_count * 1.3,  # Cross-cloud is harder
                            self.activity_costs["infra_server_migration_per_server"][1] * server_count * 1.3,
                        ),
                        timeline_months=(4, 9),
                        requires_tsa=False,  # Can run in parallel
                        tsa_duration_months=None,
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

            elif category == "erp":
                # ERP consolidation (major undertaking)
                activities.extend([
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="applications",
                        name="ERP consolidation assessment",
                        description=f"Assess path to consolidate {mismatch['target']} into buyer's {mismatch['buyer']}",
                        why_needed=f"Two ERP systems is expensive and complex. Consolidation yields synergies.",
                        triggered_by=[],
                        cost_range=(100000, 300000),
                        timeline_months=(1, 3),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    ),
                    DerivedActivity(
                        activity_id=f"A{activity_id + 1:03d}",
                        workstream="applications",
                        name=f"ERP consolidation: {mismatch['target']} → {mismatch['buyer']}",
                        description="Full ERP migration including data, processes, integrations",
                        why_needed="Single ERP platform reduces cost and complexity",
                        triggered_by=[],
                        cost_range=(1000000, 5000000),  # ERP consolidation is expensive
                        timeline_months=(12, 24),
                        requires_tsa=False,  # Not TSA - just long project
                        tsa_duration_months=None,
                        dependencies=[f"A{activity_id:03d}"],
                    ),
                ])
                activity_id += 2

        # Day-1 connectivity - always needed for acquisition
        activities.append(
            DerivedActivity(
                activity_id=f"A{activity_id:03d}",
                workstream="network",
                name="Day-1 network connectivity",
                description="Establish VPN/connectivity between target and buyer environments",
                why_needed="Target and buyer need to communicate from Day 1 for collaboration",
                triggered_by=[],
                cost_range=(30000, 100000),
                timeline_months=(0.5, 1),
                requires_tsa=False,
                tsa_duration_months=None,
                dependencies=[],
            )
        )
        activity_id += 1

        # Security integration - always needed
        activities.extend([
            DerivedActivity(
                activity_id=f"A{activity_id:03d}",
                workstream="security",
                name="Security assessment of target",
                description="Assess target's security posture, identify gaps vs buyer standards",
                why_needed="Must understand target's security before integration",
                triggered_by=[],
                cost_range=(40000, 100000),
                timeline_months=(0.5, 1),
                requires_tsa=False,
                tsa_duration_months=None,
                dependencies=[],
            ),
            DerivedActivity(
                activity_id=f"A{activity_id + 1:03d}",
                workstream="security",
                name="Deploy buyer security tools to target",
                description=f"Roll out buyer's security stack (EDR, monitoring) to {user_count:,} target users",
                why_needed="Unified security posture across combined organization",
                triggered_by=[],
                cost_range=(
                    self.activity_costs["security_edr_deploy_per_endpoint"][0] * int(user_count * 1.2) + 30000,
                    self.activity_costs["security_edr_deploy_per_endpoint"][1] * int(user_count * 1.2) + 80000,
                ),
                timeline_months=(1, 3),
                requires_tsa=False,
                tsa_duration_months=None,
                dependencies=[f"A{activity_id:03d}"],
            ),
        ])
        activity_id += 2

        # Check for gaps/risks from considerations
        for consideration in considerations:
            if consideration.criticality == "high" and "gap" in consideration.finding.lower():
                activities.append(
                    DerivedActivity(
                        activity_id=f"A{activity_id:03d}",
                        workstream="security",
                        name=f"Remediate: {consideration.finding}",
                        description=consideration.implication,
                        why_needed=f"Security gap identified: {consideration.finding}",
                        triggered_by=[consideration.consideration_id],
                        cost_range=self.activity_costs.get("security_gap_remediation", (100000, 500000)),
                        timeline_months=(2, 6),
                        requires_tsa=False,
                        tsa_duration_months=None,
                        dependencies=[],
                    )
                )
                activity_id += 1

        return activities

    def derive_synergy_opportunities(
        self,
        tech_mismatches: List[Dict],
        quant_context: Dict[str, int]
    ) -> List[Dict]:
        """Identify synergy opportunities from consolidation."""
        synergies = []
        user_count = quant_context.get("user_count", 1000)

        for mismatch in tech_mismatches:
            if mismatch["category"] == "email":
                # Email consolidation synergy
                synergies.append({
                    "category": "License Consolidation",
                    "description": f"Consolidate to single email platform ({mismatch['buyer']})",
                    "annual_savings_range": (user_count * 50, user_count * 150),  # $50-150/user/year
                    "realization_timeline": "Year 1",
                    "confidence": "high",
                })

            elif mismatch["category"] == "erp":
                # ERP consolidation synergy (longer term)
                synergies.append({
                    "category": "ERP Consolidation",
                    "description": f"Consolidate to single ERP platform ({mismatch['buyer']})",
                    "annual_savings_range": (200000, 1000000),  # Highly variable
                    "realization_timeline": "Year 2-3",
                    "confidence": "medium",
                })

            elif mismatch["category"] == "cloud":
                # Cloud consolidation synergy
                synergies.append({
                    "category": "Infrastructure Consolidation",
                    "description": f"Consolidate to single cloud platform ({mismatch['buyer']})",
                    "annual_savings_range": (100000, 500000),
                    "realization_timeline": "Year 1-2",
                    "confidence": "medium",
                })

        # Security tool consolidation (often a quick win)
        synergies.append({
            "category": "Security Tool Consolidation",
            "description": "Consolidate security tools to buyer's standard stack",
            "annual_savings_range": (user_count * 20, user_count * 60),
            "realization_timeline": "Year 1",
            "confidence": "high",
        })

        return synergies

    def derive_tsa_requirements(
        self,
        activities: List[DerivedActivity]
    ) -> List[TSARequirement]:
        """Derive TSA requirements from activities."""
        tsa_by_workstream = {}

        for activity in activities:
            if activity.requires_tsa:
                ws = activity.workstream
                if ws not in tsa_by_workstream:
                    tsa_by_workstream[ws] = {
                        "activities": [],
                        "max_duration": (0, 0),
                    }
                tsa_by_workstream[ws]["activities"].append(activity.activity_id)
                if activity.tsa_duration_months:
                    current_max = tsa_by_workstream[ws]["max_duration"]
                    tsa_by_workstream[ws]["max_duration"] = (
                        max(current_max[0], activity.tsa_duration_months[0]),
                        max(current_max[1], activity.tsa_duration_months[1]),
                    )

        workstream_names = {
            "identity": "Identity & Authentication Services",
            "email": "Email & Collaboration Services",
            "infrastructure": "Infrastructure & Hosting Services",
            "network": "Network Services",
            "security": "Security Monitoring Services",
            "service_desk": "IT Support / Service Desk",
            "applications": "ERP & Application Services",
        }

        criticality_map = {
            "identity": "Day-1 Critical",
            "email": "Day-1 Critical",
            "infrastructure": "Day-1 Critical",
            "network": "Day-1 Critical",
            "security": "Day-1 Critical",
            "service_desk": "Day-1 Important",
            "applications": "Day-1 Important",
        }

        requirements = []
        for ws, data in tsa_by_workstream.items():
            requirements.append(TSARequirement(
                service=workstream_names.get(ws, ws),
                workstream=ws,
                why_needed=f"Parent currently provides {ws} services; TSA bridges until standalone capability established",
                duration_months=data["max_duration"],
                criticality=criticality_map.get(ws, "Important"),
                exit_activities=data["activities"],
                supporting_facts=[],  # Would be populated from considerations
            ))

        return requirements

    def calculate_costs(
        self,
        activities: List[DerivedActivity]
    ) -> Dict[str, Any]:
        """Calculate costs from activities."""
        workstream_costs = {}

        for activity in activities:
            ws = activity.workstream
            if ws not in workstream_costs:
                workstream_costs[ws] = [0, 0]
            workstream_costs[ws][0] += activity.cost_range[0]
            workstream_costs[ws][1] += activity.cost_range[1]

        # Convert to tuples
        workstream_costs = {k: tuple(v) for k, v in workstream_costs.items()}

        subtotal_low = sum(v[0] for v in workstream_costs.values())
        subtotal_high = sum(v[1] for v in workstream_costs.values())

        # PMO (10-15%)
        pmo_low = subtotal_low * 0.10
        pmo_high = subtotal_high * 0.15

        # Contingency (15-20%)
        contingency_low = (subtotal_low + pmo_low) * 0.15
        contingency_high = (subtotal_high + pmo_high) * 0.20

        grand_total_low = subtotal_low + pmo_low + contingency_low
        grand_total_high = subtotal_high + pmo_high + contingency_high

        return {
            "workstream_costs": workstream_costs,
            "subtotal": (subtotal_low, subtotal_high),
            "pmo": (pmo_low, pmo_high),
            "contingency": (contingency_low, contingency_high),
            "grand_total": (grand_total_low, grand_total_high),
        }

    def generate_narrative(
        self,
        deal_type: str,
        considerations: List[Consideration],
        activities: List[DerivedActivity],
        tsa_requirements: List[TSARequirement],
        costs: Dict,
        quant_context: Dict
    ) -> Tuple[str, str]:
        """Generate executive summary and detailed narrative."""

        user_count = quant_context.get("user_count", 1000)

        # Executive Summary
        if deal_type.lower() in ["carveout", "divestiture"]:
            intro = f"This {deal_type} involves separating a {user_count:,}-user organization from parent company IT services."
        else:
            intro = f"This {deal_type} involves integrating a {user_count:,}-user organization into the buyer's IT environment."

        exec_lines = [
            f"## Executive Summary",
            "",
            intro,
            "",
            f"**Key Findings:**",
        ]

        critical_considerations = [c for c in considerations if c.criticality == "critical"]
        for c in critical_considerations[:5]:
            exec_lines.append(f"- {c.finding} → {c.implication}")

        exec_lines.extend([
            "",
            f"**Cost Estimate:** ${costs['grand_total'][0]:,.0f} - ${costs['grand_total'][1]:,.0f}",
            f"**TSA Services Required:** {len(tsa_requirements)}",
            "",
        ])

        if tsa_requirements:
            exec_lines.append("**TSA Summary:**")
            for tsa in tsa_requirements:
                exec_lines.append(f"- {tsa.service}: {tsa.duration_months[0]}-{tsa.duration_months[1]} months ({tsa.criticality})")

        executive_summary = "\n".join(exec_lines)

        # Detailed Narrative
        detail_lines = [
            "## Detailed Analysis",
            "",
            "### Why These Activities Are Required",
            "",
        ]

        # Group activities by workstream
        by_workstream = {}
        for activity in activities:
            ws = activity.workstream
            if ws not in by_workstream:
                by_workstream[ws] = []
            by_workstream[ws].append(activity)

        workstream_names = {
            "identity": "Identity & Access Management",
            "email": "Email & Collaboration",
            "infrastructure": "Infrastructure & Hosting",
            "network": "Network & Connectivity",
            "security": "Security & Compliance",
            "service_desk": "IT Support",
            "applications": "Business Applications",
        }

        for ws, ws_activities in by_workstream.items():
            ws_cost = costs["workstream_costs"].get(ws, (0, 0))
            detail_lines.append(f"#### {workstream_names.get(ws, ws)}")
            detail_lines.append(f"**Estimated Cost:** ${ws_cost[0]:,.0f} - ${ws_cost[1]:,.0f}")
            detail_lines.append("")

            for activity in ws_activities:
                detail_lines.append(f"**{activity.name}**")
                detail_lines.append(f"- {activity.description}")
                detail_lines.append(f"- *Why needed:* {activity.why_needed}")
                detail_lines.append(f"- Cost: ${activity.cost_range[0]:,.0f} - ${activity.cost_range[1]:,.0f}")
                if activity.requires_tsa:
                    detail_lines.append(f"- TSA bridge required: {activity.tsa_duration_months[0]}-{activity.tsa_duration_months[1]} months")
                detail_lines.append("")

        detailed_narrative = "\n".join(detail_lines)

        return executive_summary, detailed_narrative

    def reason(
        self,
        facts: List[Dict],
        deal_type: str,
        buyer_context: Optional[Dict] = None,
        meeting_notes: Optional[str] = None
    ) -> ReasoningOutput:
        """
        Main reasoning method.

        Takes facts, deal context, and optional meeting notes.
        Returns complete reasoning output with explanations.
        """
        # Convert meeting notes to facts if provided
        all_facts = list(facts)
        if meeting_notes:
            # Split meeting notes into fact-like chunks
            note_lines = [line.strip() for line in meeting_notes.split("\n") if line.strip()]
            for i, line in enumerate(note_lines):
                all_facts.append({
                    "fact_id": f"MN{i+1:03d}",
                    "content": line,
                    "source": "meeting_notes",
                })

        # Extract quantitative context
        quant_context = self.extract_quantitative_context(all_facts)

        # Identify considerations
        parent_deps = self.identify_parent_dependencies(all_facts)
        gaps_risks = self.identify_gaps_and_risks(all_facts)
        all_considerations = parent_deps + gaps_risks

        # Identify technology stack
        tech_stack = self.identify_technology_stack(all_facts)

        # Derive activities based on deal type
        synergies = []
        if deal_type.lower() == "carveout" or deal_type.lower() == "divestiture":
            activities = self.derive_activities_for_carveout(all_considerations, quant_context)
        elif deal_type.lower() == "acquisition" or deal_type.lower() == "platform_addon":
            # For acquisitions, identify technology mismatches
            if buyer_context:
                tech_mismatches = self.identify_technology_mismatches(tech_stack, buyer_context)
            else:
                tech_mismatches = []

            activities = self.derive_activities_for_acquisition(
                all_considerations, tech_mismatches, quant_context, buyer_context or {}
            )
            synergies = self.derive_synergy_opportunities(tech_mismatches, quant_context)
        else:
            # Default to carveout logic
            activities = self.derive_activities_for_carveout(all_considerations, quant_context)

        # Derive TSA requirements
        tsa_requirements = self.derive_tsa_requirements(activities)

        # Calculate costs
        costs = self.calculate_costs(activities)

        # Calculate critical path (longest TSA duration)
        if tsa_requirements:
            critical_path = (
                max(t.duration_months[0] for t in tsa_requirements),
                max(t.duration_months[1] for t in tsa_requirements),
            )
        else:
            critical_path = (3, 6)

        # Generate narratives
        exec_summary, detailed_narrative = self.generate_narrative(
            deal_type, all_considerations, activities, tsa_requirements, costs, quant_context
        )

        # Generate input hash for reproducibility
        input_hash = hashlib.sha256(
            json.dumps({
                "facts": [f.get("content", "")[:50] for f in all_facts],
                "deal_type": deal_type,
                "quant_context": quant_context,
            }, sort_keys=True).encode()
        ).hexdigest()[:12]

        return ReasoningOutput(
            deal_type=deal_type,
            user_count=quant_context.get("user_count", 1000),
            facts_analyzed=len(all_facts),
            considerations=all_considerations,
            derived_activities=activities,
            tsa_requirements=tsa_requirements,
            workstream_costs=costs["workstream_costs"],
            total_one_time_cost=costs["subtotal"],
            tsa_exit_cost=(0, 0),  # Calculated separately
            contingency=costs["contingency"],
            grand_total=costs["grand_total"],
            critical_path_months=critical_path,
            executive_summary=exec_summary,
            detailed_narrative=detailed_narrative,
            input_hash=input_hash,
        )

    def format_output(self, output: ReasoningOutput) -> str:
        """Format reasoning output for display."""
        lines = [
            "=" * 80,
            "IT DUE DILIGENCE - REASONING-BASED COST ESTIMATE",
            "=" * 80,
            f"Deal Type: {output.deal_type.upper()}",
            f"Users: {output.user_count:,}",
            f"Facts Analyzed: {output.facts_analyzed}",
            "",
            output.executive_summary,
            "",
            "-" * 80,
            "COST BREAKDOWN BY WORKSTREAM",
            "-" * 80,
        ]

        workstream_names = {
            "identity": "Identity & Access",
            "email": "Email & Collaboration",
            "infrastructure": "Infrastructure",
            "network": "Network",
            "security": "Security",
            "service_desk": "IT Support",
            "applications": "Applications/ERP",
        }

        for ws, cost in output.workstream_costs.items():
            name = workstream_names.get(ws, ws)
            lines.append(f"  {name}: ${cost[0]:,.0f} - ${cost[1]:,.0f}")

        lines.extend([
            "",
            f"  Subtotal: ${output.total_one_time_cost[0]:,.0f} - ${output.total_one_time_cost[1]:,.0f}",
            f"  PMO + Contingency: ${output.contingency[0]:,.0f} - ${output.contingency[1]:,.0f}",
            "",
            f"  GRAND TOTAL: ${output.grand_total[0]:,.0f} - ${output.grand_total[1]:,.0f}",
            "",
            "-" * 80,
            "TSA REQUIREMENTS",
            "-" * 80,
        ])

        for tsa in output.tsa_requirements:
            lines.append(f"  • {tsa.service}")
            lines.append(f"    Duration: {tsa.duration_months[0]}-{tsa.duration_months[1]} months")
            lines.append(f"    Criticality: {tsa.criticality}")
            lines.append(f"    Why: {tsa.why_needed}")
            lines.append("")

        lines.extend([
            "-" * 80,
            "TIMELINE",
            "-" * 80,
            f"  Critical Path: {output.critical_path_months[0]}-{output.critical_path_months[1]} months",
            "",
            "-" * 80,
            f"Input Hash: {output.input_hash}",
            "=" * 80,
        ])

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'Fact',
    'Consideration',
    'DerivedActivity',
    'TSARequirement',
    'ReasoningOutput',
    'ReasoningEngine',
]
