"""
Coverage Checklists and Quality Scoring

Defines expected items per domain/category and functions to calculate
coverage quality based on FactStore contents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from tools_v2.fact_store import FactStore

# Import caching
try:
    from tools_v2.cache import cached_coverage
except ImportError:
    # Fallback if cache not available
    def cached_coverage(func):
        return func

# =============================================================================
# COVERAGE CHECKLISTS - What we expect to find in each domain
# =============================================================================

# Importance levels:
# - critical: Must have for any meaningful diligence
# - important: Should have for complete picture
# - nice_to_have: Helpful but not essential

COVERAGE_CHECKLISTS: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "infrastructure": {
        "hosting": [
            {"name": "primary_data_center", "importance": "critical", "description": "Primary DC location and provider"},
            {"name": "dr_site", "importance": "important", "description": "Disaster recovery site details"},
            {"name": "colocation_details", "importance": "important", "description": "Colo contracts and terms"},
        ],
        "compute": [
            {"name": "hypervisor_platform", "importance": "critical", "description": "VMware/Hyper-V/etc with version"},
            {"name": "vm_inventory", "importance": "critical", "description": "VM count and breakdown"},
            {"name": "physical_servers", "importance": "important", "description": "Physical server inventory"},
            {"name": "container_platform", "importance": "nice_to_have", "description": "Kubernetes/Docker environment"},
        ],
        "storage": [
            {"name": "primary_san", "importance": "critical", "description": "Primary SAN vendor and model"},
            {"name": "storage_capacity", "importance": "important", "description": "Total/used capacity"},
            {"name": "nas_systems", "importance": "nice_to_have", "description": "NAS systems and usage"},
        ],
        "backup_dr": [
            {"name": "backup_solution", "importance": "critical", "description": "Backup software and approach"},
            {"name": "rpo_rto", "importance": "critical", "description": "Recovery objectives"},
            {"name": "dr_testing", "importance": "important", "description": "DR test frequency and results"},
            {"name": "retention_policy", "importance": "important", "description": "Backup retention periods"},
        ],
        "cloud": [
            {"name": "cloud_provider", "importance": "critical", "description": "AWS/Azure/GCP usage"},
            {"name": "cloud_spend", "importance": "important", "description": "Monthly/annual cloud spend"},
            {"name": "cloud_services", "importance": "important", "description": "Services used (IaaS/PaaS/SaaS)"},
        ],
        "legacy": [
            {"name": "mainframe", "importance": "important", "description": "Mainframe systems if present"},
            {"name": "eol_systems", "importance": "critical", "description": "End-of-life systems"},
        ],
        "tooling": [
            {"name": "monitoring", "importance": "important", "description": "Infrastructure monitoring tools"},
            {"name": "automation", "importance": "nice_to_have", "description": "Automation/IaC tools"},
        ],
    },

    "network": {
        "wan": [
            {"name": "primary_isp", "importance": "critical", "description": "Primary ISP and bandwidth"},
            {"name": "mpls_sdwan", "importance": "important", "description": "MPLS or SD-WAN details"},
            {"name": "circuit_redundancy", "importance": "important", "description": "Redundant circuits"},
        ],
        "lan": [
            {"name": "core_switches", "importance": "critical", "description": "Core network equipment"},
            {"name": "network_vendor", "importance": "important", "description": "Primary network vendor"},
            {"name": "vlan_architecture", "importance": "nice_to_have", "description": "VLAN segmentation"},
        ],
        "remote_access": [
            {"name": "vpn_solution", "importance": "critical", "description": "VPN platform and capacity"},
            {"name": "remote_desktop", "importance": "important", "description": "RDS/VDI solution"},
        ],
        "dns_dhcp": [
            {"name": "internal_dns", "importance": "important", "description": "Internal DNS servers"},
            {"name": "external_dns", "importance": "important", "description": "External DNS provider"},
        ],
        "load_balancing": [
            {"name": "load_balancer", "importance": "important", "description": "LB platform"},
        ],
        "network_security": [
            {"name": "firewall_platform", "importance": "critical", "description": "Firewall vendor and model"},
            {"name": "segmentation", "importance": "important", "description": "Network segmentation approach"},
        ],
        "monitoring": [
            {"name": "network_monitoring", "importance": "important", "description": "Network monitoring tool"},
        ],
    },

    "cybersecurity": {
        "endpoint": [
            {"name": "edr_platform", "importance": "critical", "description": "EDR/AV solution"},
            {"name": "endpoint_coverage", "importance": "important", "description": "Deployment coverage %"},
        ],
        "perimeter": [
            {"name": "next_gen_firewall", "importance": "critical", "description": "NGFW capability"},
            {"name": "waf", "importance": "important", "description": "Web application firewall"},
            {"name": "email_security", "importance": "critical", "description": "Email security gateway"},
        ],
        "detection": [
            {"name": "siem", "importance": "critical", "description": "SIEM platform"},
            {"name": "soc_model", "importance": "important", "description": "SOC (internal/MSSP)"},
            {"name": "log_retention", "importance": "important", "description": "Log retention period"},
        ],
        "vulnerability": [
            {"name": "vuln_scanner", "importance": "critical", "description": "Vulnerability scanning tool"},
            {"name": "patch_management", "importance": "critical", "description": "Patch management process"},
            {"name": "pentest_frequency", "importance": "important", "description": "Penetration testing cadence"},
        ],
        "compliance": [
            {"name": "certifications", "importance": "critical", "description": "SOC2, ISO27001, etc."},
            {"name": "compliance_gaps", "importance": "important", "description": "Known compliance gaps"},
        ],
        "incident_response": [
            {"name": "ir_plan", "importance": "critical", "description": "IR plan existence"},
            {"name": "ir_testing", "importance": "important", "description": "IR testing frequency"},
        ],
        "governance": [
            {"name": "security_policies", "importance": "important", "description": "Security policy framework"},
            {"name": "security_training", "importance": "important", "description": "Security awareness program"},
        ],
    },

    "applications": {
        "erp": [
            {"name": "erp_platform", "importance": "critical", "description": "ERP system and version"},
            {"name": "erp_customizations", "importance": "important", "description": "Level of customization"},
            {"name": "erp_support", "importance": "important", "description": "Support model"},
        ],
        "crm": [
            {"name": "crm_platform", "importance": "critical", "description": "CRM system"},
            {"name": "crm_integrations", "importance": "important", "description": "CRM integrations"},
        ],
        "custom": [
            {"name": "custom_app_inventory", "importance": "critical", "description": "Custom applications list"},
            {"name": "custom_app_languages", "importance": "important", "description": "Development languages"},
            {"name": "technical_debt", "importance": "important", "description": "Technical debt assessment"},
        ],
        "saas": [
            {"name": "saas_inventory", "importance": "critical", "description": "SaaS applications list"},
            {"name": "saas_spend", "importance": "important", "description": "SaaS spending"},
            {"name": "shadow_it", "importance": "nice_to_have", "description": "Shadow IT assessment"},
        ],
        "integration": [
            {"name": "integration_platform", "importance": "important", "description": "Integration/middleware"},
            {"name": "api_strategy", "importance": "nice_to_have", "description": "API management"},
        ],
        "development": [
            {"name": "dev_methodology", "importance": "important", "description": "Agile/waterfall/etc"},
            {"name": "cicd_pipeline", "importance": "important", "description": "CI/CD tools"},
            {"name": "source_control", "importance": "important", "description": "Source control system"},
        ],
        "database": [
            {"name": "database_platforms", "importance": "critical", "description": "Database systems used"},
            {"name": "database_sizes", "importance": "important", "description": "Database sizes"},
        ],
    },

    "identity_access": {
        "directory": [
            {"name": "ad_environment", "importance": "critical", "description": "Active Directory setup"},
            {"name": "azure_ad", "importance": "important", "description": "Azure AD/Entra ID"},
            {"name": "ldap_systems", "importance": "nice_to_have", "description": "Other directory services"},
        ],
        "authentication": [
            {"name": "auth_methods", "importance": "critical", "description": "Authentication methods"},
            {"name": "password_policy", "importance": "important", "description": "Password requirements"},
        ],
        "privileged_access": [
            {"name": "pam_solution", "importance": "critical", "description": "PAM tool"},
            {"name": "admin_account_mgmt", "importance": "important", "description": "Admin account management"},
        ],
        "provisioning": [
            {"name": "provisioning_process", "importance": "important", "description": "User provisioning process"},
            {"name": "deprovisioning", "importance": "important", "description": "Offboarding/deprovisioning"},
        ],
        "sso": [
            {"name": "sso_platform", "importance": "important", "description": "SSO solution"},
            {"name": "sso_coverage", "importance": "important", "description": "SSO app coverage"},
        ],
        "mfa": [
            {"name": "mfa_solution", "importance": "critical", "description": "MFA platform"},
            {"name": "mfa_coverage", "importance": "critical", "description": "MFA rollout percentage"},
        ],
        "governance": [
            {"name": "access_reviews", "importance": "important", "description": "Access review process"},
            {"name": "rbac", "importance": "important", "description": "Role-based access control"},
        ],
    },

    "organization": {
        "structure": [
            {"name": "it_reporting", "importance": "critical", "description": "IT reporting structure"},
            {"name": "it_leadership", "importance": "important", "description": "IT leadership roles"},
        ],
        "staffing": [
            {"name": "headcount", "importance": "critical", "description": "IT headcount"},
            {"name": "roles_breakdown", "importance": "important", "description": "Roles distribution"},
            {"name": "turnover", "importance": "nice_to_have", "description": "IT turnover rate"},
        ],
        "vendors": [
            {"name": "key_vendors", "importance": "critical", "description": "Key IT vendors"},
            {"name": "vendor_contracts", "importance": "important", "description": "Contract terms"},
            {"name": "vendor_concentration", "importance": "important", "description": "Single vendor risks"},
        ],
        "skills": [
            {"name": "core_competencies", "importance": "important", "description": "Team capabilities"},
            {"name": "skill_gaps", "importance": "important", "description": "Identified skill gaps"},
        ],
        "processes": [
            {"name": "itil_adoption", "importance": "nice_to_have", "description": "ITIL/process maturity"},
            {"name": "change_management", "importance": "important", "description": "Change management"},
        ],
        "budget": [
            {"name": "annual_budget", "importance": "critical", "description": "Annual IT budget"},
            {"name": "capex_opex_split", "importance": "important", "description": "CapEx vs OpEx"},
        ],
        "roadmap": [
            {"name": "strategic_initiatives", "importance": "important", "description": "Planned initiatives"},
            {"name": "tech_debt_plan", "importance": "important", "description": "Tech debt remediation"},
        ],
    },
}


# =============================================================================
# COVERAGE RESULT DATACLASSES
# =============================================================================

@dataclass
class ChecklistItem:
    """A single checklist item with match status."""
    name: str
    importance: str
    description: str
    found: bool = False
    matched_fact_id: Optional[str] = None
    matched_fact_item: Optional[str] = None


@dataclass
class CategoryCoverage:
    """Coverage results for a single category."""
    category: str
    items: List[ChecklistItem]
    facts_found: int = 0
    gaps_found: int = 0

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def found_count(self) -> int:
        return sum(1 for item in self.items if item.found)

    @property
    def critical_total(self) -> int:
        return sum(1 for item in self.items if item.importance == "critical")

    @property
    def critical_found(self) -> int:
        return sum(1 for item in self.items if item.importance == "critical" and item.found)

    @property
    def coverage_percent(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.found_count / self.total_items) * 100

    @property
    def critical_coverage_percent(self) -> float:
        if self.critical_total == 0:
            return 100.0  # No critical items = fully covered
        return (self.critical_found / self.critical_total) * 100


@dataclass
class DomainCoverage:
    """Coverage results for an entire domain."""
    domain: str
    categories: Dict[str, CategoryCoverage]
    total_facts: int = 0
    total_gaps: int = 0

    @property
    def total_checklist_items(self) -> int:
        return sum(cat.total_items for cat in self.categories.values())

    @property
    def total_found(self) -> int:
        return sum(cat.found_count for cat in self.categories.values())

    @property
    def total_critical(self) -> int:
        return sum(cat.critical_total for cat in self.categories.values())

    @property
    def critical_found(self) -> int:
        return sum(cat.critical_found for cat in self.categories.values())

    @property
    def coverage_percent(self) -> float:
        if self.total_checklist_items == 0:
            return 0.0
        return (self.total_found / self.total_checklist_items) * 100

    @property
    def critical_coverage_percent(self) -> float:
        if self.total_critical == 0:
            return 100.0
        return (self.critical_found / self.total_critical) * 100

    def get_missing_critical(self) -> List[Dict[str, str]]:
        """Get list of missing critical items."""
        missing = []
        for cat_name, cat in self.categories.items():
            for item in cat.items:
                if item.importance == "critical" and not item.found:
                    missing.append({
                        "category": cat_name,
                        "item": item.name,
                        "description": item.description
                    })
        return missing


# =============================================================================
# COVERAGE ANALYZER
# =============================================================================

class CoverageAnalyzer:
    """
    Analyzes FactStore contents against coverage checklists.

    Usage:
        analyzer = CoverageAnalyzer(fact_store)
        domain_coverage = analyzer.calculate_domain_coverage("infrastructure")
        overall = analyzer.calculate_overall_coverage()
    """

    def __init__(self, fact_store: FactStore):
        self.fact_store = fact_store

    def _match_fact_to_checklist(
        self,
        fact_item: str,
        checklist_item_name: str
    ) -> bool:
        """
        Determine if a fact matches a checklist item.
        Uses fuzzy matching on item names.
        """
        # Normalize strings
        fact_lower = fact_item.lower().replace("_", " ").replace("-", " ")
        check_lower = checklist_item_name.lower().replace("_", " ").replace("-", " ")

        # Direct contains
        if check_lower in fact_lower or fact_lower in check_lower:
            return True

        # Word overlap
        fact_words = set(fact_lower.split())
        check_words = set(check_lower.split())

        # Remove common words
        common_words = {"the", "a", "an", "and", "or", "of", "for", "to", "in"}
        fact_words -= common_words
        check_words -= common_words

        # Check for significant word overlap
        if len(fact_words) > 0 and len(check_words) > 0:
            overlap = fact_words & check_words
            if len(overlap) >= min(len(fact_words), len(check_words)) * 0.5:
                return True

        # Keyword mappings for common variations
        keyword_mappings = {
            "hypervisor": ["vmware", "hyper-v", "hyperv", "esxi", "vsphere"],
            "vm": ["virtual machine", "vms", "virtualization"],
            "san": ["storage area network", "netapp", "dell emc", "pure"],
            "edr": ["endpoint detection", "crowdstrike", "sentinelone", "defender"],
            "siem": ["splunk", "sentinel", "qradar", "log management"],
            "erp": ["sap", "oracle", "netsuite", "dynamics"],
            "crm": ["salesforce", "hubspot", "dynamics crm"],
            "pam": ["privileged access", "cyberark", "beyondtrust"],
            "mfa": ["multi-factor", "two-factor", "2fa", "authenticator"],
            "sso": ["single sign-on", "okta", "ping", "azure ad"],
            "ad": ["active directory", "domain controller"],
            "vpn": ["remote access", "globalprotect", "anyconnect"],
            "firewall": ["palo alto", "fortinet", "checkpoint", "cisco asa"],
        }

        for key, variations in keyword_mappings.items():
            if key in check_lower:
                for var in variations:
                    if var in fact_lower:
                        return True

        return False

    def calculate_category_coverage(
        self,
        domain: str,
        category: str
    ) -> CategoryCoverage:
        """Calculate coverage for a single category."""
        checklist = COVERAGE_CHECKLISTS.get(domain, {}).get(category, [])

        # Get facts for this domain/category
        domain_facts = [f for f in self.fact_store.facts if f.domain == domain]
        category_facts = [f for f in domain_facts if f.category == category]
        category_gaps = [g for g in self.fact_store.gaps
                        if g.domain == domain and g.category == category]

        items = []
        for check_item in checklist:
            item = ChecklistItem(
                name=check_item["name"],
                importance=check_item["importance"],
                description=check_item["description"]
            )

            # Try to match against facts
            for fact in category_facts:
                if self._match_fact_to_checklist(fact.item, check_item["name"]):
                    item.found = True
                    item.matched_fact_id = fact.fact_id
                    item.matched_fact_item = fact.item
                    break

            items.append(item)

        return CategoryCoverage(
            category=category,
            items=items,
            facts_found=len(category_facts),
            gaps_found=len(category_gaps)
        )

    @cached_coverage
    def calculate_domain_coverage(self, domain: str) -> DomainCoverage:
        """Calculate coverage for an entire domain."""
        domain_checklist = COVERAGE_CHECKLISTS.get(domain, {})

        categories = {}
        for category in domain_checklist.keys():
            categories[category] = self.calculate_category_coverage(domain, category)

        # Get total facts and gaps for domain
        domain_facts = [f for f in self.fact_store.facts if f.domain == domain]
        domain_gaps = [g for g in self.fact_store.gaps if g.domain == domain]

        return DomainCoverage(
            domain=domain,
            categories=categories,
            total_facts=len(domain_facts),
            total_gaps=len(domain_gaps)
        )

    @cached_coverage
    def calculate_overall_coverage(self) -> Dict[str, Any]:
        """Calculate coverage across all domains."""
        results = {
            "domains": {},
            "summary": {
                "total_checklist_items": 0,
                "total_found": 0,
                "total_critical": 0,
                "critical_found": 0,
                "overall_coverage_percent": 0.0,
                "critical_coverage_percent": 0.0,
            },
            "missing_critical": [],
        }

        for domain in COVERAGE_CHECKLISTS.keys():
            domain_cov = self.calculate_domain_coverage(domain)
            results["domains"][domain] = {
                "coverage_percent": domain_cov.coverage_percent,
                "critical_coverage_percent": domain_cov.critical_coverage_percent,
                "total_items": domain_cov.total_checklist_items,
                "found": domain_cov.total_found,
                "critical_total": domain_cov.total_critical,
                "critical_found": domain_cov.critical_found,
                "facts": domain_cov.total_facts,
                "gaps": domain_cov.total_gaps,
                "missing_critical": domain_cov.get_missing_critical(),
            }

            results["summary"]["total_checklist_items"] += domain_cov.total_checklist_items
            results["summary"]["total_found"] += domain_cov.total_found
            results["summary"]["total_critical"] += domain_cov.total_critical
            results["summary"]["critical_found"] += domain_cov.critical_found

            results["missing_critical"].extend([
                {"domain": domain, **item}
                for item in domain_cov.get_missing_critical()
            ])

        # Calculate overall percentages
        total = results["summary"]["total_checklist_items"]
        found = results["summary"]["total_found"]
        crit_total = results["summary"]["total_critical"]
        crit_found = results["summary"]["critical_found"]

        results["summary"]["overall_coverage_percent"] = (
            (found / total * 100) if total > 0 else 0.0
        )
        results["summary"]["critical_coverage_percent"] = (
            (crit_found / crit_total * 100) if crit_total > 0 else 100.0
        )

        return results

    def get_coverage_grade(self) -> str:
        """Get a letter grade for overall coverage."""
        coverage = self.calculate_overall_coverage()
        crit_pct = coverage["summary"]["critical_coverage_percent"]

        if crit_pct >= 90:
            return "A"
        elif crit_pct >= 75:
            return "B"
        elif crit_pct >= 60:
            return "C"
        elif crit_pct >= 40:
            return "D"
        else:
            return "F"

    def get_coverage_summary_text(self) -> str:
        """Get human-readable coverage summary."""
        coverage = self.calculate_overall_coverage()
        summary = coverage["summary"]
        grade = self.get_coverage_grade()

        lines = [
            f"Coverage Grade: {grade}",
            f"Overall Coverage: {summary['overall_coverage_percent']:.1f}%",
            f"Critical Coverage: {summary['critical_coverage_percent']:.1f}%",
            f"Items Found: {summary['total_found']}/{summary['total_checklist_items']}",
            f"Critical Items: {summary['critical_found']}/{summary['total_critical']}",
            "",
            "Domain Breakdown:",
        ]

        for domain, data in coverage["domains"].items():
            lines.append(
                f"  {domain}: {data['coverage_percent']:.1f}% "
                f"(critical: {data['critical_coverage_percent']:.1f}%)"
            )

        if coverage["missing_critical"]:
            lines.append("")
            lines.append(f"Missing Critical Items ({len(coverage['missing_critical'])}):")
            for item in coverage["missing_critical"][:10]:  # Show first 10
                lines.append(f"  - [{item['domain']}] {item['category']}: {item['description']}")
            if len(coverage["missing_critical"]) > 10:
                lines.append(f"  ... and {len(coverage['missing_critical']) - 10} more")

        return "\n".join(lines)
