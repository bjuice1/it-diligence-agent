"""
Category Checkpoints - Defines validation rules for each category.

Each checkpoint specifies:
- Expected item counts (min/max)
- Required fields that must be present
- Validation prompts for LLM verification
- Importance level for prioritization

These checkpoints are used by the CategoryValidator to ensure
complete extraction before proceeding.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CategoryCheckpoint:
    """
    Defines validation rules for a single category.

    Attributes:
        category: Category name (must match extraction categories)
        min_expected_items: Minimum items expected (0 = optional category)
        max_expected_items: Maximum reasonable items (for sanity check)
        required_fields: Fields that must be present in each item
        optional_fields: Fields that are nice to have but not required
        validation_prompt: Prompt template for LLM validation
        importance: Priority level - "critical", "high", "medium", "low"
        description: Human-readable description of what this category covers
    """
    category: str
    min_expected_items: int
    max_expected_items: int
    required_fields: List[str]
    validation_prompt: str
    importance: str = "high"
    description: str = ""
    optional_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "min_expected_items": self.min_expected_items,
            "max_expected_items": self.max_expected_items,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "importance": self.importance,
            "description": self.description
        }


# =============================================================================
# ORGANIZATION DOMAIN CHECKPOINTS
# =============================================================================

ORGANIZATION_CHECKPOINTS: Dict[str, CategoryCheckpoint] = {

    "central_it": CategoryCheckpoint(
        category="central_it",
        min_expected_items=5,
        max_expected_items=15,
        required_fields=["item", "headcount"],
        optional_fields=["personnel_cost", "leader", "description"],
        importance="critical",
        description="IT teams/departments with headcount breakdown",
        validation_prompt="""
You are validating the extraction of Central IT teams from an IT due diligence document.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if ALL teams mentioned in the document are captured
2. Verify headcount numbers match what's stated in the document
3. Look for any teams that were missed or partially extracted
4. Check if team names are accurate

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Team Name", "evidence": "Quote from document mentioning this team"}}
    ],
    "incorrect_items": [
        {{"fact_id": "...", "issue": "Description of the problem", "correct_value": "..."}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "leadership": CategoryCheckpoint(
        category="leadership",
        min_expected_items=1,
        max_expected_items=10,
        required_fields=["item", "role"],
        optional_fields=["reports_to", "tenure", "background"],
        importance="high",
        description="IT leadership roles (CIO, VPs, Directors)",
        validation_prompt="""
You are validating the extraction of IT Leadership from an IT due diligence document.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if key leadership roles (CIO, VP, Directors) are captured
2. Verify reporting structures if mentioned
3. Look for any leadership positions that were missed

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Role/Person", "evidence": "Quote from document"}}
    ],
    "incorrect_items": [
        {{"fact_id": "...", "issue": "Description of the problem"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "outsourcing": CategoryCheckpoint(
        category="outsourcing",
        min_expected_items=0,  # Optional - not all companies outsource
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["vendor", "headcount", "cost", "scope"],
        importance="high",
        description="Outsourced IT functions and vendors",
        validation_prompt="""
You are validating the extraction of IT Outsourcing arrangements.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Identify all outsourcing relationships mentioned
2. Check if vendor names are captured
3. Verify scope and headcount if mentioned
4. Note if document explicitly states "no outsourcing"

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Vendor/Function", "evidence": "Quote from document"}}
    ],
    "no_outsourcing_stated": true/false,
    "notes": "Any additional observations"
}}
"""
    ),

    "roles": CategoryCheckpoint(
        category="roles",
        min_expected_items=0,
        max_expected_items=50,
        required_fields=["item"],
        optional_fields=["count", "team", "level"],
        importance="medium",
        description="Specific IT roles and positions",
        validation_prompt="""
You are validating the extraction of IT Roles/Positions.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if key roles mentioned are captured
2. Verify role counts if stated
3. Note any roles that seem to be missing

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Role", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "contractors": CategoryCheckpoint(
        category="contractors",
        min_expected_items=0,
        max_expected_items=30,
        required_fields=["item"],
        optional_fields=["count", "vendor", "cost", "function"],
        importance="medium",
        description="Contract staff and temporary resources",
        validation_prompt="""
You are validating the extraction of IT Contractors/Contingent workers.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if contractor arrangements are captured
2. Verify headcounts and costs if stated
3. Note if document explicitly states "no contractors"

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Contractor type/vendor", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "governance": CategoryCheckpoint(
        category="governance",
        min_expected_items=0,
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["description", "frequency", "participants"],
        importance="medium",
        description="IT governance structures, committees, processes",
        validation_prompt="""
You are validating the extraction of IT Governance structures.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if governance committees are captured
2. Verify processes and frameworks mentioned
3. Note reporting structures

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Committee/Process", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),
}


# =============================================================================
# INFRASTRUCTURE DOMAIN CHECKPOINTS
# =============================================================================

INFRASTRUCTURE_CHECKPOINTS: Dict[str, CategoryCheckpoint] = {

    "hosting": CategoryCheckpoint(
        category="hosting",
        min_expected_items=1,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["location", "provider", "type", "count"],
        importance="critical",
        description="Data centers, hosting locations, colocation",
        validation_prompt="""
You are validating the extraction of Hosting/Data Center information.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if all data centers/hosting locations are captured
2. Verify location details (city, provider)
3. Note hosting type (on-prem, colo, cloud)

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Data center/Location", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "compute": CategoryCheckpoint(
        category="compute",
        min_expected_items=1,
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["count", "type", "vendor", "specs"],
        importance="critical",
        description="Servers, virtual machines, compute resources",
        validation_prompt="""
You are validating the extraction of Compute resources.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if server counts are captured
2. Verify VM/physical breakdown if stated
3. Note any compute platforms mentioned

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Compute resource", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "storage": CategoryCheckpoint(
        category="storage",
        min_expected_items=1,
        max_expected_items=15,
        required_fields=["item"],
        optional_fields=["capacity", "vendor", "type"],
        importance="high",
        description="Storage systems, SAN, NAS, capacity",
        validation_prompt="""
You are validating the extraction of Storage infrastructure.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if storage systems are captured
2. Verify capacity figures if stated
3. Note storage vendors/types

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Storage system", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "backup_dr": CategoryCheckpoint(
        category="backup_dr",
        min_expected_items=1,
        max_expected_items=15,
        required_fields=["item"],
        optional_fields=["rpo", "rto", "vendor", "location"],
        importance="critical",
        description="Backup systems, disaster recovery, business continuity",
        validation_prompt="""
You are validating the extraction of Backup/DR information.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if backup solutions are captured
2. Verify DR site/approach if mentioned
3. Note RPO/RTO targets if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Backup/DR component", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "cloud": CategoryCheckpoint(
        category="cloud",
        min_expected_items=0,  # Optional - not all companies use cloud
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["provider", "services", "spend", "workloads"],
        importance="high",
        description="Cloud platforms, IaaS, PaaS usage",
        validation_prompt="""
You are validating the extraction of Cloud infrastructure.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if cloud providers are captured (AWS, Azure, GCP)
2. Verify cloud services/workloads mentioned
3. Note cloud spend if stated
4. Note if document states "no cloud usage"

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Cloud service/provider", "evidence": "Quote from document"}}
    ],
    "no_cloud_stated": true/false,
    "notes": "Any additional observations"
}}
"""
    ),

    "virtualization": CategoryCheckpoint(
        category="virtualization",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "version", "vm_count"],
        importance="medium",
        description="Virtualization platforms (VMware, Hyper-V)",
        validation_prompt="""
You are validating the extraction of Virtualization platforms.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if virtualization platform is captured
2. Verify version/VM counts if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Virtualization platform", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "endpoints": CategoryCheckpoint(
        category="endpoints",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["count", "type", "os"],
        importance="medium",
        description="Desktops, laptops, workstations",
        validation_prompt="""
You are validating the extraction of Endpoint devices.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if endpoint counts are captured
2. Verify device types (desktop, laptop, tablet)
3. Note OS breakdown if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Endpoint type", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),
}


# =============================================================================
# APPLICATIONS DOMAIN CHECKPOINTS
# =============================================================================

APPLICATIONS_CHECKPOINTS: Dict[str, CategoryCheckpoint] = {

    "erp": CategoryCheckpoint(
        category="erp",
        min_expected_items=0,
        max_expected_items=5,
        required_fields=["item"],
        optional_fields=["vendor", "version", "modules", "users"],
        importance="critical",
        description="ERP systems (SAP, Oracle, etc.)",
        validation_prompt="""
You are validating the extraction of ERP systems.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if ERP system(s) are captured
2. Verify vendor, version, modules if stated
3. Note user counts or license info

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "ERP system", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "crm": CategoryCheckpoint(
        category="crm",
        min_expected_items=0,
        max_expected_items=5,
        required_fields=["item"],
        optional_fields=["vendor", "users", "integrations"],
        importance="high",
        description="CRM systems (Salesforce, Dynamics, etc.)",
        validation_prompt="""
You are validating the extraction of CRM systems.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if CRM system(s) are captured
2. Verify vendor and user counts if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "CRM system", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "saas": CategoryCheckpoint(
        category="saas",
        min_expected_items=0,
        max_expected_items=100,
        required_fields=["item"],
        optional_fields=["vendor", "purpose", "users", "cost"],
        importance="medium",
        description="SaaS applications",
        validation_prompt="""
You are validating the extraction of SaaS applications.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if major SaaS applications are captured
2. Note if there's a stated total count of SaaS apps
3. Verify key applications are listed

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "SaaS application", "evidence": "Quote from document"}}
    ],
    "stated_total": null or number,
    "notes": "Any additional observations"
}}
"""
    ),

    "custom": CategoryCheckpoint(
        category="custom",
        min_expected_items=0,
        max_expected_items=50,
        required_fields=["item"],
        optional_fields=["technology", "purpose", "age", "support"],
        importance="high",
        description="Custom/in-house developed applications",
        validation_prompt="""
You are validating the extraction of Custom applications.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if custom applications are captured
2. Note technology stack if mentioned
3. Verify application purposes

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Custom application", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "integration": CategoryCheckpoint(
        category="integration",
        min_expected_items=0,
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["type", "vendor", "connections"],
        importance="medium",
        description="Integration platforms, middleware, APIs",
        validation_prompt="""
You are validating the extraction of Integration/Middleware.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if integration platforms are captured
2. Note middleware/ESB if mentioned
3. Verify API platforms

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Integration platform", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "database": CategoryCheckpoint(
        category="database",
        min_expected_items=0,
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["vendor", "version", "count", "size"],
        importance="high",
        description="Database platforms and instances",
        validation_prompt="""
You are validating the extraction of Database systems.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if database platforms are captured
2. Verify vendor/version if stated
3. Note instance counts if mentioned

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Database platform", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),
}


# =============================================================================
# NETWORK DOMAIN CHECKPOINTS
# =============================================================================

NETWORK_CHECKPOINTS: Dict[str, CategoryCheckpoint] = {

    "wan": CategoryCheckpoint(
        category="wan",
        min_expected_items=1,
        max_expected_items=15,
        required_fields=["item"],
        optional_fields=["provider", "bandwidth", "type", "locations"],
        importance="critical",
        description="WAN connectivity, MPLS, internet links",
        validation_prompt="""
You are validating the extraction of WAN/Connectivity.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if WAN connections are captured
2. Verify providers and bandwidth if stated
3. Note connection types (MPLS, internet, etc.)

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "WAN connection", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "lan": CategoryCheckpoint(
        category="lan",
        min_expected_items=0,
        max_expected_items=20,
        required_fields=["item"],
        optional_fields=["vendor", "type", "ports"],
        importance="medium",
        description="LAN infrastructure, switches, wireless",
        validation_prompt="""
You are validating the extraction of LAN infrastructure.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if LAN equipment is captured
2. Note vendor/types if stated
3. Verify wireless infrastructure

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "LAN component", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "remote_access": CategoryCheckpoint(
        category="remote_access",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "type", "users"],
        importance="high",
        description="VPN, remote access solutions",
        validation_prompt="""
You are validating the extraction of Remote Access solutions.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if VPN/remote access is captured
2. Verify vendor and type
3. Note user counts if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Remote access solution", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "dns_dhcp": CategoryCheckpoint(
        category="dns_dhcp",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["provider", "type"],
        importance="low",
        description="DNS, DHCP, core network services",
        validation_prompt="""
You are validating the extraction of DNS/DHCP services.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if DNS/DHCP is mentioned and captured
2. Note providers if stated

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Network service", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),
}


# =============================================================================
# SECURITY DOMAIN CHECKPOINTS
# =============================================================================

SECURITY_CHECKPOINTS: Dict[str, CategoryCheckpoint] = {

    "endpoint_security": CategoryCheckpoint(
        category="endpoint_security",
        min_expected_items=1,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "coverage", "features"],
        importance="critical",
        description="Endpoint protection, antivirus, EDR",
        validation_prompt="""
You are validating the extraction of Endpoint Security.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if endpoint security solution is captured
2. Verify vendor name
3. Note EDR/XDR capabilities if mentioned

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Endpoint security tool", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "perimeter": CategoryCheckpoint(
        category="perimeter",
        min_expected_items=1,
        max_expected_items=15,
        required_fields=["item"],
        optional_fields=["vendor", "type", "location"],
        importance="critical",
        description="Firewalls, IPS/IDS, perimeter security",
        validation_prompt="""
You are validating the extraction of Perimeter Security.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if firewalls are captured
2. Verify vendor names
3. Note IPS/IDS if mentioned

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Perimeter security", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "identity": CategoryCheckpoint(
        category="identity",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "type", "users"],
        importance="high",
        description="Identity management, SSO, MFA",
        validation_prompt="""
You are validating the extraction of Identity Management.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if identity solutions are captured
2. Verify SSO/MFA if mentioned
3. Note Active Directory or other directory services

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Identity solution", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "siem": CategoryCheckpoint(
        category="siem",
        min_expected_items=0,
        max_expected_items=5,
        required_fields=["item"],
        optional_fields=["vendor", "coverage"],
        importance="high",
        description="SIEM, security monitoring, SOC",
        validation_prompt="""
You are validating the extraction of SIEM/Security Monitoring.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if SIEM solution is captured
2. Note SOC operations if mentioned
3. Verify vendor name

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "SIEM/Monitoring", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "vulnerability": CategoryCheckpoint(
        category="vulnerability",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "frequency", "scope"],
        importance="medium",
        description="Vulnerability management, scanning, patching",
        validation_prompt="""
You are validating the extraction of Vulnerability Management.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if vulnerability scanning is captured
2. Note patch management if mentioned
3. Verify vendor/tool names

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Vulnerability tool", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),

    "email_security": CategoryCheckpoint(
        category="email_security",
        min_expected_items=0,
        max_expected_items=10,
        required_fields=["item"],
        optional_fields=["vendor", "features"],
        importance="medium",
        description="Email security, anti-spam, DLP",
        validation_prompt="""
You are validating the extraction of Email Security.

DOCUMENT EXCERPT:
{document_excerpt}

EXTRACTED ITEMS:
{extracted_items}

VALIDATION TASKS:
1. Check if email security is captured
2. Note anti-spam, DLP if mentioned
3. Verify vendor names

Respond in JSON format:
{{
    "is_complete": true/false,
    "confidence": 0.0-1.0,
    "missing_items": [
        {{"item": "Email security", "evidence": "Quote from document"}}
    ],
    "notes": "Any additional observations"
}}
"""
    ),
}


# =============================================================================
# DOMAIN CHECKPOINT MAPPING
# =============================================================================

DOMAIN_CHECKPOINTS: Dict[str, Dict[str, CategoryCheckpoint]] = {
    "organization": ORGANIZATION_CHECKPOINTS,
    "infrastructure": INFRASTRUCTURE_CHECKPOINTS,
    "applications": APPLICATIONS_CHECKPOINTS,
    "network": NETWORK_CHECKPOINTS,
    "security": SECURITY_CHECKPOINTS,
}


def get_checkpoints_for_domain(domain: str) -> Dict[str, CategoryCheckpoint]:
    """Get all checkpoints for a specific domain."""
    return DOMAIN_CHECKPOINTS.get(domain, {})


def get_checkpoint(domain: str, category: str) -> Optional[CategoryCheckpoint]:
    """Get a specific checkpoint by domain and category."""
    domain_checkpoints = DOMAIN_CHECKPOINTS.get(domain, {})
    return domain_checkpoints.get(category)


def get_critical_checkpoints(domain: str) -> Dict[str, CategoryCheckpoint]:
    """Get only critical importance checkpoints for a domain."""
    all_checkpoints = get_checkpoints_for_domain(domain)
    return {
        cat: cp for cat, cp in all_checkpoints.items()
        if cp.importance == "critical"
    }


def get_required_categories(domain: str) -> List[str]:
    """Get list of categories with min_expected_items > 0."""
    all_checkpoints = get_checkpoints_for_domain(domain)
    return [
        cat for cat, cp in all_checkpoints.items()
        if cp.min_expected_items > 0
    ]
