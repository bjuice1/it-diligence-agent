"""
Function Story Template

Generates structured narrative stories for each IT function/team.
Stories provide the contextual depth that feeds executive narratives.

Each story answers:
- What do they do day-to-day? (operating reality)
- What do they likely do well? (strengths)
- Where are they constrained? (risks/bottlenecks)
- What are their dependencies? (upstream/downstream)
- What's the M&A implication? (Day-1/TSA/Separation/Synergy)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


# =============================================================================
# FUNCTION STORY DATA STRUCTURE
# =============================================================================

@dataclass
class FunctionStory:
    """A structured narrative story for an IT function/team."""
    function_name: str
    domain: str

    # Core story elements
    day_to_day: str  # 2-3 sentences on primary activities
    strengths: List[str]  # 1-3 strengths with evidence
    constraints: List[str]  # 1-3 constraints/risks with evidence

    # Dependencies
    upstream_dependencies: List[str]  # What this function depends on
    downstream_dependents: List[str]  # What depends on this function

    # M&A framing
    mna_implication: str  # 1-2 sentences on deal relevance
    mna_lens: str  # Primary lens: day_1_continuity, tsa_exposure, etc.

    # Evidence
    based_on_facts: List[str]  # Fact IDs supporting this story
    inferences: List[str]  # Labeled inferences made

    # Metadata
    confidence: str = "medium"  # high, medium, low
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_markdown(self) -> str:
        """Render the story as markdown for narrative output."""
        md = f"### {self.function_name}\n\n"
        md += f"**What they do day-to-day**: {self.day_to_day}\n\n"

        md += "**What they likely do well**:\n"
        for strength in self.strengths:
            md += f"- {strength}\n"
        md += "\n"

        md += "**Where they're likely constrained**:\n"
        for constraint in self.constraints:
            md += f"- {constraint}\n"
        md += "\n"

        md += "**Key dependencies & handoffs**:\n"
        md += f"- *Upstream*: {', '.join(self.upstream_dependencies) if self.upstream_dependencies else 'None identified'}\n"
        md += f"- *Downstream*: {', '.join(self.downstream_dependents) if self.downstream_dependents else 'None identified'}\n"
        md += "\n"

        md += f"**M&A Implication** ({self.mna_lens}): {self.mna_implication}\n"

        return md


# =============================================================================
# FUNCTION-TO-DOMAIN MAPPING
# =============================================================================

FUNCTION_DOMAIN_MAP = {
    # Organization domain - IT team structure
    "organization": [
        {
            "function": "IT Leadership",
            "description": "CIO/CTO and direct reports; strategic direction and governance",
            "typical_signals": ["CIO", "CTO", "VP IT", "IT Director", "governance", "strategy"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "Applications Team",
            "description": "Application development, support, and maintenance",
            "typical_signals": ["developers", "application support", "software engineers", "app team"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Infrastructure Team",
            "description": "Server, storage, and data center operations",
            "typical_signals": ["sysadmin", "infrastructure", "server team", "DC ops"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Security Team",
            "description": "Information security, compliance, and risk management",
            "typical_signals": ["CISO", "security analyst", "SOC", "compliance"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Service Desk",
            "description": "End-user support, incident management, request fulfillment",
            "typical_signals": ["helpdesk", "service desk", "tier 1", "end user support"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "PMO/Project Management",
            "description": "Project delivery, portfolio management, change management",
            "typical_signals": ["PMO", "project manager", "program manager", "change management"],
            "day_1_critical": False,
            "tsa_likely": False
        },
        {
            "function": "Data & Analytics",
            "description": "BI, reporting, data engineering, analytics",
            "typical_signals": ["BI", "data analyst", "reporting", "data engineer", "analytics"],
            "day_1_critical": False,
            "tsa_likely": True
        }
    ],

    # Applications domain - application portfolio
    "applications": [
        {
            "function": "ERP",
            "description": "Enterprise resource planning - finance, supply chain, operations",
            "typical_signals": ["SAP", "Oracle EBS", "NetSuite", "Dynamics", "JD Edwards", "ERP"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "CRM",
            "description": "Customer relationship management - sales, service, marketing",
            "typical_signals": ["Salesforce", "Dynamics CRM", "HubSpot", "CRM"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "HCM/Payroll",
            "description": "Human capital management - HR, payroll, benefits, time tracking",
            "typical_signals": ["Workday", "ADP", "UKG", "payroll", "HRIS", "HCM"],
            "day_1_critical": True,  # Payroll is Day 1 critical
            "tsa_likely": True
        },
        {
            "function": "BI/Analytics",
            "description": "Business intelligence - reporting, dashboards, data warehouse",
            "typical_signals": ["Tableau", "Power BI", "Looker", "data warehouse", "reporting"],
            "day_1_critical": False,
            "tsa_likely": True
        },
        {
            "function": "Custom Applications",
            "description": "Internally developed or heavily customized applications",
            "typical_signals": ["custom", "in-house", "proprietary", "legacy app"],
            "day_1_critical": True,  # Often core business logic
            "tsa_likely": False
        },
        {
            "function": "Integration/Middleware",
            "description": "Integration platforms, ESB, API management, ETL",
            "typical_signals": ["MuleSoft", "Dell Boomi", "Informatica", "ESB", "API", "integration"],
            "day_1_critical": True,
            "tsa_likely": True
        }
    ],

    # Infrastructure domain - hosting and compute
    "infrastructure": [
        {
            "function": "Data Center",
            "description": "Physical or colo facilities housing IT equipment",
            "typical_signals": ["data center", "DC", "colo", "Equinix", "facility"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Compute/Virtualization",
            "description": "Server infrastructure - physical and virtual",
            "typical_signals": ["VMware", "Hyper-V", "servers", "VMs", "ESXi"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Storage",
            "description": "Enterprise storage - SAN, NAS, object storage",
            "typical_signals": ["SAN", "NAS", "NetApp", "Pure", "EMC", "storage"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Backup/DR",
            "description": "Backup infrastructure and disaster recovery",
            "typical_signals": ["backup", "Veeam", "Commvault", "DR", "disaster recovery", "replication"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Cloud Infrastructure",
            "description": "Public cloud platforms - IaaS, PaaS",
            "typical_signals": ["AWS", "Azure", "GCP", "cloud", "IaaS"],
            "day_1_critical": True,
            "tsa_likely": False  # Usually account-based, easier to transfer
        }
    ],

    # Network domain - connectivity
    "network": [
        {
            "function": "WAN",
            "description": "Wide area network - site connectivity, MPLS, SD-WAN",
            "typical_signals": ["MPLS", "SD-WAN", "WAN", "carrier", "AT&T", "Verizon"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "LAN",
            "description": "Local area network - switches, campus network",
            "typical_signals": ["LAN", "switches", "Cisco", "campus network"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "Wireless",
            "description": "WiFi infrastructure",
            "typical_signals": ["WiFi", "wireless", "Aruba", "Meraki", "access points"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "Firewalls/Security",
            "description": "Network security - firewalls, IPS, network segmentation",
            "typical_signals": ["firewall", "Palo Alto", "Fortinet", "Cisco ASA", "IPS"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "VPN/Remote Access",
            "description": "Remote access infrastructure",
            "typical_signals": ["VPN", "remote access", "Cisco AnyConnect", "GlobalProtect"],
            "day_1_critical": True,
            "tsa_likely": True
        }
    ],

    # Cybersecurity domain - security operations
    "cybersecurity": [
        {
            "function": "Security Operations",
            "description": "SOC, monitoring, incident response",
            "typical_signals": ["SOC", "SIEM", "monitoring", "incident response", "MDR"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Vulnerability Management",
            "description": "Scanning, patching, remediation tracking",
            "typical_signals": ["vulnerability", "patching", "Qualys", "Tenable", "Rapid7"],
            "day_1_critical": False,
            "tsa_likely": True
        },
        {
            "function": "Endpoint Security",
            "description": "EDR, antivirus, endpoint protection",
            "typical_signals": ["EDR", "CrowdStrike", "Defender", "antivirus", "endpoint"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "Security Compliance",
            "description": "GRC, audit, compliance management",
            "typical_signals": ["compliance", "SOC 2", "ISO 27001", "audit", "GRC"],
            "day_1_critical": False,
            "tsa_likely": False
        }
    ],

    # Identity domain - access management
    "identity_access": [
        {
            "function": "Directory Services",
            "description": "Active Directory, Azure AD, LDAP",
            "typical_signals": ["Active Directory", "AD", "Azure AD", "LDAP", "directory"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Access Management",
            "description": "SSO, federation, access control",
            "typical_signals": ["SSO", "Okta", "SAML", "federation", "access management"],
            "day_1_critical": True,
            "tsa_likely": True
        },
        {
            "function": "Privileged Access",
            "description": "PAM, privileged account management",
            "typical_signals": ["PAM", "CyberArk", "privileged", "admin accounts"],
            "day_1_critical": True,
            "tsa_likely": False
        },
        {
            "function": "JML Process",
            "description": "Joiner/Mover/Leaver - onboarding, offboarding, access reviews",
            "typical_signals": ["onboarding", "offboarding", "JML", "access review", "provisioning"],
            "day_1_critical": True,
            "tsa_likely": True
        }
    ]
}


# =============================================================================
# SIGNAL DETECTION FOR STORIES
# =============================================================================

STRENGTH_SIGNALS = {
    "mature_tooling": {
        "signals": ["enterprise", "established", "industry-leading", "best-of-breed"],
        "inference": "Inference: Enterprise-grade tooling suggests operational maturity"
    },
    "adequate_staffing": {
        "signals": ["team of", "dedicated", "full-time", "24x7"],
        "inference": "Inference: Dedicated staffing suggests adequate capacity"
    },
    "certifications": {
        "signals": ["SOC 2", "ISO 27001", "certified", "compliant"],
        "inference": "Inference: Certifications indicate baseline process maturity"
    },
    "documented_processes": {
        "signals": ["documented", "runbooks", "procedures", "SOP"],
        "inference": "Inference: Documentation suggests knowledge capture and repeatability"
    },
    "redundancy": {
        "signals": ["redundant", "HA", "failover", "backup", "DR"],
        "inference": "Inference: Redundancy indicates resilience investment"
    },
    "modern_platform": {
        "signals": ["cloud-native", "SaaS", "current version", "recently upgraded"],
        "inference": "Inference: Modern platforms suggest ongoing investment"
    }
}

CONSTRAINT_SIGNALS = {
    "understaffing": {
        "signals": ["lean", "small team", "single person", "one admin", "part-time"],
        "inference": "Inference: Limited staffing suggests capacity constraints and key-person risk"
    },
    "technical_debt": {
        "signals": ["legacy", "EOL", "end of life", "unsupported", "outdated", "old version"],
        "inference": "Inference: Technical debt indicates deferred investment and potential security exposure"
    },
    "single_point_of_failure": {
        "signals": ["single", "no backup", "one", "only"],
        "inference": "Inference: Single points of failure create operational risk"
    },
    "skill_scarcity": {
        "signals": ["mainframe", "COBOL", "legacy skills", "retiring", "hard to find"],
        "inference": "Inference: Scarce skills create retention risk and knowledge concentration"
    },
    "manual_processes": {
        "signals": ["manual", "spreadsheet", "email-based", "no automation"],
        "inference": "Inference: Manual processes suggest efficiency gaps and error risk"
    },
    "no_documentation": {
        "signals": ["undocumented", "tribal knowledge", "in their head", "no runbooks"],
        "inference": "Inference: Lack of documentation creates knowledge transfer risk"
    },
    "outsourced_dependency": {
        "signals": ["outsourced", "MSP", "vendor-managed", "third-party"],
        "inference": "Inference: Outsourcing creates vendor dependency and potential TSA complexity"
    }
}


# =============================================================================
# DEPENDENCY MAPPING
# =============================================================================

DEPENDENCY_MAP = {
    # What each function typically depends on (upstream)
    "upstream": {
        "Applications Team": ["Infrastructure Team", "Security Team", "Network"],
        "Infrastructure Team": ["Network", "Data Center", "Vendors"],
        "Security Team": ["Infrastructure Team", "Identity", "Network"],
        "Service Desk": ["All IT Teams", "HR Systems", "Identity"],
        "PMO": ["All IT Teams", "Business Stakeholders"],
        "Data & Analytics": ["Applications Team", "Infrastructure Team", "Data Sources"],

        "ERP": ["Infrastructure", "Network", "Identity", "Integration"],
        "CRM": ["Infrastructure", "Network", "Identity", "Integration"],
        "HCM/Payroll": ["Infrastructure", "Identity", "HR Data"],
        "BI/Analytics": ["Data Sources", "ERP", "Infrastructure"],
        "Custom Applications": ["Infrastructure", "Network", "Identity"],
        "Integration/Middleware": ["Network", "Applications", "Infrastructure"],

        "Data Center": ["Power", "Cooling", "Physical Security", "Network Carriers"],
        "Compute/Virtualization": ["Storage", "Network", "Data Center"],
        "Storage": ["Data Center", "Network"],
        "Backup/DR": ["Storage", "Network", "Compute"],
        "Cloud Infrastructure": ["Network", "Identity", "Security"],

        "WAN": ["Carriers", "Network Equipment"],
        "LAN": ["Network Equipment", "Cabling"],
        "Firewalls/Security": ["Network", "Security Policies"],
        "VPN/Remote Access": ["Firewalls", "Identity", "Network"],

        "Security Operations": ["SIEM", "Network", "Endpoint Security", "Staffing"],
        "Vulnerability Management": ["Asset Inventory", "Scanning Tools"],
        "Endpoint Security": ["Identity", "Deployment Tools"],

        "Directory Services": ["Network", "Infrastructure"],
        "Access Management": ["Directory Services", "Applications"],
        "Privileged Access": ["Directory Services", "Security Policies"],
        "JML Process": ["HR Systems", "Directory Services", "Applications"]
    },

    # What typically depends on each function (downstream)
    "downstream": {
        "IT Leadership": ["All IT Functions", "Business Decisions"],
        "Applications Team": ["Business Users", "Data & Analytics"],
        "Infrastructure Team": ["All Applications", "All Users"],
        "Security Team": ["Compliance", "Risk Management", "All IT"],
        "Service Desk": ["All End Users"],
        "PMO": ["Project Delivery", "Change Success"],
        "Data & Analytics": ["Business Decisions", "Reporting"],

        "ERP": ["Finance", "Operations", "Supply Chain", "Reporting"],
        "CRM": ["Sales", "Customer Service", "Marketing"],
        "HCM/Payroll": ["All Employees", "Finance", "Compliance"],
        "BI/Analytics": ["Executive Decisions", "Operations"],
        "Custom Applications": ["Business Processes", "Users"],
        "Integration/Middleware": ["All Integrated Systems", "Data Flow"],

        "Data Center": ["All Infrastructure", "All Applications"],
        "Compute/Virtualization": ["All Applications", "All Services"],
        "Storage": ["All Data", "All Applications"],
        "Backup/DR": ["Data Protection", "Business Continuity"],
        "Cloud Infrastructure": ["Cloud Applications", "Modern Workloads"],

        "WAN": ["All Remote Sites", "Cloud Access"],
        "LAN": ["All Local Users", "All Local Systems"],
        "Firewalls/Security": ["All Network Traffic", "Security Posture"],
        "VPN/Remote Access": ["Remote Workers", "Partner Access"],

        "Security Operations": ["Threat Detection", "Incident Response"],
        "Vulnerability Management": ["Risk Reduction", "Compliance"],
        "Endpoint Security": ["All Endpoints", "User Protection"],

        "Directory Services": ["All Authentication", "All Applications"],
        "Access Management": ["All User Access", "SSO"],
        "Privileged Access": ["Admin Operations", "Security"],
        "JML Process": ["User Lifecycle", "Compliance"]
    }
}


# =============================================================================
# STORY GENERATION PROMPT
# =============================================================================

FUNCTION_STORY_PROMPT = """
## FUNCTION STORY GENERATION

For the **{function_name}** function in the **{domain}** domain, generate a structured narrative story.

### Source Evidence
{evidence}

### Required Output Structure

Generate a story with these EXACT sections:

**1. DAY-TO-DAY OPERATIONS** (2-3 sentences)
What does this function primarily do? Focus on operational reality based on evidence.
- Base ONLY on inventory evidence
- Describe typical activities and responsibilities

**2. STRENGTHS** (1-3 bullet points)
What do they likely do well? Look for:
- Enterprise/mature tooling
- Adequate staffing indicators
- Certifications or compliance
- Documented processes
- Redundancy/resilience
- Modern platforms

Format: "• [Strength]. Evidence: [fact reference]. {inference_label if applicable}"

**3. CONSTRAINTS** (1-3 bullet points)
Where are they likely bottlenecked? Look for:
- Understaffing signals (lean, single person)
- Technical debt (EOL, legacy, unsupported)
- Single points of failure
- Skill scarcity
- Manual processes
- Documentation gaps
- Heavy outsourcing

Format: "• [Constraint]. Evidence: [fact reference]. Inference: [what this implies]"

**4. DEPENDENCIES**
- Upstream (what this function depends on): List 2-4 dependencies
- Downstream (what depends on this function): List 2-4 dependents

**5. M&A IMPLICATION** (1-2 sentences)
Connect to the deal context using one of the 5 M&A lenses:
- Day-1 Continuity: Is this critical for Day 1 operations?
- TSA Exposure: Will this require transition services?
- Separation Complexity: How entangled with parent?
- Synergy Opportunity: Consolidation potential?
- Cost Driver: What drives cost?

### Evidence Discipline
- Cite specific fact IDs where possible
- Label inferences explicitly: "Inference: [reasoning]"
- If evidence is insufficient, state: "Gap: [what's missing]"

### Deal Context
{deal_context}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_functions_for_domain(domain: str) -> List[Dict]:
    """Get the list of functions to story for a domain."""
    return FUNCTION_DOMAIN_MAP.get(domain, [])


def get_all_functions() -> Dict[str, List[Dict]]:
    """Get all functions across all domains."""
    return FUNCTION_DOMAIN_MAP


def get_function_details(domain: str, function_name: str) -> Optional[Dict]:
    """Get details for a specific function."""
    functions = FUNCTION_DOMAIN_MAP.get(domain, [])
    for func in functions:
        if func["function"] == function_name:
            return func
    return None


def get_upstream_dependencies(function_name: str) -> List[str]:
    """Get upstream dependencies for a function."""
    return DEPENDENCY_MAP["upstream"].get(function_name, [])


def get_downstream_dependents(function_name: str) -> List[str]:
    """Get downstream dependents for a function."""
    return DEPENDENCY_MAP["downstream"].get(function_name, [])


def detect_strength_signals(text: str) -> List[Dict]:
    """Detect strength signals in text."""
    detected = []
    text_lower = text.lower()
    for signal_type, config in STRENGTH_SIGNALS.items():
        for signal in config["signals"]:
            if signal.lower() in text_lower:
                detected.append({
                    "type": signal_type,
                    "signal": signal,
                    "inference": config["inference"]
                })
                break  # Only detect each type once
    return detected


def detect_constraint_signals(text: str) -> List[Dict]:
    """Detect constraint signals in text."""
    detected = []
    text_lower = text.lower()
    for signal_type, config in CONSTRAINT_SIGNALS.items():
        for signal in config["signals"]:
            if signal.lower() in text_lower:
                detected.append({
                    "type": signal_type,
                    "signal": signal,
                    "inference": config["inference"]
                })
                break  # Only detect each type once
    return detected


def get_story_prompt(function_name: str, domain: str, evidence: str, deal_context: str) -> str:
    """Generate the prompt for creating a function story."""
    return FUNCTION_STORY_PROMPT.format(
        function_name=function_name,
        domain=domain,
        evidence=evidence,
        deal_context=deal_context
    )


def get_day1_critical_functions() -> List[str]:
    """Get list of all Day-1 critical functions across domains."""
    critical = []
    for domain, functions in FUNCTION_DOMAIN_MAP.items():
        for func in functions:
            if func.get("day_1_critical", False):
                critical.append(f"{domain}: {func['function']}")
    return critical


def get_tsa_likely_functions() -> List[str]:
    """Get list of functions likely to require TSA."""
    tsa_functions = []
    for domain, functions in FUNCTION_DOMAIN_MAP.items():
        for func in functions:
            if func.get("tsa_likely", False):
                tsa_functions.append(f"{domain}: {func['function']}")
    return tsa_functions


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'FunctionStory',
    'FUNCTION_DOMAIN_MAP',
    'STRENGTH_SIGNALS',
    'CONSTRAINT_SIGNALS',
    'DEPENDENCY_MAP',
    'FUNCTION_STORY_PROMPT',
    'get_functions_for_domain',
    'get_all_functions',
    'get_function_details',
    'get_upstream_dependencies',
    'get_downstream_dependents',
    'detect_strength_signals',
    'detect_constraint_signals',
    'get_story_prompt',
    'get_day1_critical_functions',
    'get_tsa_likely_functions'
]
