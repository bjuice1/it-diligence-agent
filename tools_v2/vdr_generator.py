"""
VDR Request Generator

Generates prioritized Virtual Data Room (VDR) request lists based on:
1. Identified gaps from discovery
2. Missing coverage checklist items
3. Risks that need additional information

Produces structured request packs for follow-up with the target company.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from tools_v2.fact_store import FactStore
from tools_v2.coverage import CoverageAnalyzer, COVERAGE_CHECKLISTS
from tools_v2.reasoning_tools import ReasoningStore


# =============================================================================
# VDR REQUEST DATACLASSES
# =============================================================================

@dataclass
class VDRRequest:
    """A single VDR request item."""
    request_id: str
    domain: str
    category: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    source: str  # gap, coverage, risk
    source_id: Optional[str] = None  # G-INFRA-001, R-001, etc.
    suggested_documents: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "domain": self.domain,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "source": self.source,
            "source_id": self.source_id,
            "suggested_documents": self.suggested_documents,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VDRRequest":
        """Create VDRRequest from dictionary."""
        return cls(
            request_id=data.get("request_id", ""),
            domain=data.get("domain", ""),
            category=data.get("category", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
            source=data.get("source", "gap"),
            source_id=data.get("source_id"),
            suggested_documents=data.get("suggested_documents", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class VDRRequestPack:
    """Collection of VDR requests organized by priority."""
    requests: List[VDRRequest] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_request(self, request: VDRRequest) -> None:
        self.requests.append(request)

    def get_by_priority(self, priority: str) -> List[VDRRequest]:
        return [r for r in self.requests if r.priority == priority]

    def get_by_domain(self, domain: str) -> List[VDRRequest]:
        return [r for r in self.requests if r.domain == domain]

    def get_sorted(self) -> List[VDRRequest]:
        """Get requests sorted by priority (critical > high > medium > low)."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(self.requests, key=lambda r: priority_order.get(r.priority, 4))

    @property
    def total_count(self) -> int:
        return len(self.requests)

    @property
    def critical_count(self) -> int:
        return len(self.get_by_priority("critical"))

    @property
    def high_count(self) -> int:
        return len(self.get_by_priority("high"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_requests": self.total_count,
            "by_priority": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": len(self.get_by_priority("medium")),
                "low": len(self.get_by_priority("low")),
            },
            "requests": [r.to_dict() for r in self.get_sorted()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VDRRequestPack":
        """Create VDRRequestPack from dictionary."""
        pack = cls(generated_at=data.get("generated_at", datetime.now().isoformat()))
        for req_data in data.get("requests", []):
            pack.requests.append(VDRRequest.from_dict(req_data))
        return pack


# =============================================================================
# DOCUMENT SUGGESTIONS PER CATEGORY
# =============================================================================

SUGGESTED_DOCUMENTS = {
    # Infrastructure
    "hosting": ["Data center contracts", "Colo agreements", "Facility audit reports"],
    "compute": ["Server inventory", "Virtualization architecture diagrams", "Capacity reports"],
    "storage": ["SAN configuration docs", "Storage capacity reports", "Vendor contracts"],
    "backup_dr": ["DR plan", "Backup policies", "DR test results", "RTO/RPO documentation"],
    "cloud": ["Cloud architecture diagrams", "AWS/Azure/GCP invoices", "Cloud security config"],
    "legacy": ["Legacy system inventory", "EOL roadmap", "Migration plans"],
    "tooling": ["Monitoring architecture", "Automation runbooks", "Tool inventory"],

    # Network
    "wan": ["Network diagrams", "ISP contracts", "Circuit inventory"],
    "lan": ["Network architecture", "Switch inventory", "VLAN documentation"],
    "remote_access": ["VPN architecture", "Remote access policies", "Capacity reports"],
    "dns_dhcp": ["DNS zone files", "DHCP scope documentation"],
    "load_balancing": ["Load balancer configuration", "Traffic reports"],
    "network_security": ["Firewall rule sets", "Network security architecture"],
    "monitoring": ["Network monitoring dashboards", "Alert configurations"],

    # Cybersecurity
    "endpoint": ["EDR deployment report", "AV coverage report", "Endpoint inventory"],
    "perimeter": ["Firewall architecture", "WAF configuration", "Email security reports"],
    "detection": ["SIEM architecture", "SOC procedures", "Log retention policies"],
    "vulnerability": ["Vulnerability scan reports", "Patch management procedures", "Pentest reports"],
    "compliance": ["Compliance certifications", "Audit reports", "Gap assessments"],
    "incident_response": ["IR playbooks", "IR test results", "Incident history"],
    "security_governance": ["Security policies", "Security training records", "Risk assessments"],

    # Applications
    "erp": ["ERP architecture", "Customization inventory", "Support contracts"],
    "crm": ["CRM configuration", "Integration documentation", "License agreements"],
    "custom": ["Application inventory", "Code repositories list", "Technical debt assessment"],
    "saas": ["SaaS application list", "SaaS spend report", "Contract summaries"],
    "integration": ["Integration architecture", "API documentation", "Middleware inventory"],
    "development": ["SDLC documentation", "CI/CD pipeline docs", "Dev environment setup"],
    "database": ["Database inventory", "Database sizing report", "DBA procedures"],

    # Identity & Access
    "directory": ["AD architecture", "Forest/domain documentation", "Azure AD config"],
    "authentication": ["Authentication policies", "Password policy documentation"],
    "privileged_access": ["PAM architecture", "Admin account inventory", "Access policies"],
    "provisioning": ["Provisioning procedures", "User lifecycle documentation"],
    "sso": ["SSO architecture", "Federated app list", "SSO configuration"],
    "mfa": ["MFA rollout status", "MFA policies", "Exemption list"],
    "iam_governance": ["Access review procedures", "RBAC documentation", "Audit logs"],

    # Organization
    "structure": ["IT org chart", "Reporting structure documentation"],
    "staffing": ["IT headcount report", "Role descriptions", "HR records"],
    "vendors": ["Vendor contracts", "SLA documentation", "Vendor risk assessments"],
    "skills": ["Skills matrix", "Training records", "Certification inventory"],
    "processes": ["ITIL documentation", "Change management procedures", "Process maturity assessment"],
    "budget": ["IT budget documentation", "Spending reports", "Cost allocation"],
    "roadmap": ["Technology roadmap", "Strategic initiatives", "Project portfolio"],
}


# =============================================================================
# VDR GENERATOR
# =============================================================================

class VDRGenerator:
    """
    Generates VDR request packs from analysis results.

    Usage:
        generator = VDRGenerator(fact_store, reasoning_store)
        pack = generator.generate()
        print(pack.to_dict())
    """

    def __init__(
        self,
        fact_store: FactStore,
        reasoning_store: Optional[ReasoningStore] = None
    ):
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store
        self.coverage_analyzer = CoverageAnalyzer(fact_store)
        self._request_counter = 0

    def _next_request_id(self) -> str:
        self._request_counter += 1
        return f"VDR-{self._request_counter:03d}"

    def _importance_to_priority(self, importance: str) -> str:
        """Convert coverage importance to VDR priority."""
        mapping = {
            "critical": "critical",
            "important": "high",
            "nice_to_have": "medium",
        }
        return mapping.get(importance, "low")

    def _gap_importance_to_priority(self, importance: str) -> str:
        """Convert gap importance to VDR priority."""
        mapping = {
            "critical": "critical",
            "high": "critical",
            "medium": "high",
            "low": "medium",
        }
        return mapping.get(importance, "medium")

    def _generate_gap_requests(self) -> List[VDRRequest]:
        """Generate VDR requests from identified gaps."""
        requests = []

        for gap in self.fact_store.gaps:
            request = VDRRequest(
                request_id=self._next_request_id(),
                domain=gap.domain,
                category=gap.category,
                title=f"Documentation needed: {gap.description[:50]}",
                description=f"Gap identified during discovery: {gap.description}. "
                           f"Please provide documentation to address this information gap.",
                priority=self._gap_importance_to_priority(gap.importance),
                source="gap",
                source_id=gap.gap_id,
                suggested_documents=SUGGESTED_DOCUMENTS.get(gap.category, []),
            )
            requests.append(request)

        return requests

    def _generate_coverage_requests(self) -> List[VDRRequest]:
        """Generate VDR requests from missing coverage items."""
        requests = []
        coverage = self.coverage_analyzer.calculate_overall_coverage()

        for domain_name, domain_data in coverage["domains"].items():
            for missing in domain_data["missing_critical"]:
                # Get the checklist item details
                checklist = COVERAGE_CHECKLISTS.get(domain_name, {}).get(missing["category"], [])
                item_info = next(
                    (i for i in checklist if i["name"] == missing["item"]),
                    {"importance": "critical"}
                )

                request = VDRRequest(
                    request_id=self._next_request_id(),
                    domain=domain_name,
                    category=missing["category"],
                    title=f"Missing: {missing['description']}",
                    description=f"Coverage analysis identified that {missing['description']} "
                               f"is not documented. This is a {item_info.get('importance', 'critical')} "
                               f"item for IT due diligence.",
                    priority=self._importance_to_priority(item_info.get("importance", "critical")),
                    source="coverage",
                    source_id=None,
                    suggested_documents=SUGGESTED_DOCUMENTS.get(missing["category"], []),
                )
                requests.append(request)

        return requests

    def _generate_risk_requests(self) -> List[VDRRequest]:
        """Generate VDR requests from risks needing more information."""
        requests = []

        if not self.reasoning_store:
            return requests

        # Find risks with low confidence or that need follow-up
        for risk in self.reasoning_store.risks:
            if risk.confidence == "low":
                request = VDRRequest(
                    request_id=self._next_request_id(),
                    domain=risk.domain,
                    category="risk_followup",
                    title=f"Clarification needed: {risk.title[:40]}",
                    description=f"A {risk.severity} severity risk was identified with low confidence: "
                               f"{risk.title}. Additional documentation would help validate "
                               f"or clarify this finding.",
                    priority="high" if risk.severity == "high" else "medium",
                    source="risk",
                    source_id=risk.finding_id,
                    suggested_documents=[],
                )
                requests.append(request)

        return requests

    def _deduplicate_requests(self, requests: List[VDRRequest]) -> List[VDRRequest]:
        """Remove duplicate requests based on domain + category + title similarity."""
        seen = set()
        unique = []

        for req in requests:
            key = f"{req.domain}:{req.category}:{req.title[:30].lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(req)

        return unique

    def generate(self) -> VDRRequestPack:
        """Generate complete VDR request pack."""
        pack = VDRRequestPack()

        # Generate from all sources
        gap_requests = self._generate_gap_requests()
        coverage_requests = self._generate_coverage_requests()
        risk_requests = self._generate_risk_requests()

        # Combine and deduplicate
        all_requests = gap_requests + coverage_requests + risk_requests
        unique_requests = self._deduplicate_requests(all_requests)

        for req in unique_requests:
            pack.add_request(req)

        return pack

    def generate_markdown(self) -> str:
        """Generate markdown-formatted VDR request list."""
        pack = self.generate()
        _ = pack.get_sorted()

        lines = [
            "# VDR Request Pack",
            f"Generated: {pack.generated_at}",
            "",
            "## Summary",
            f"- Total Requests: {pack.total_count}",
            f"- Critical: {pack.critical_count}",
            f"- High: {pack.high_count}",
            f"- Medium: {len(pack.get_by_priority('medium'))}",
            f"- Low: {len(pack.get_by_priority('low'))}",
            "",
        ]

        # Group by priority
        for priority in ["critical", "high", "medium", "low"]:
            priority_requests = pack.get_by_priority(priority)
            if not priority_requests:
                continue

            lines.append(f"## {priority.upper()} Priority ({len(priority_requests)})")
            lines.append("")

            for req in priority_requests:
                lines.append(f"### {req.request_id}: {req.title}")
                lines.append(f"**Domain:** {req.domain} | **Category:** {req.category}")
                lines.append(f"**Source:** {req.source}")
                if req.source_id:
                    lines.append(f"**Source ID:** {req.source_id}")
                lines.append("")
                lines.append(req.description)
                lines.append("")
                if req.suggested_documents:
                    lines.append("**Suggested Documents:**")
                    for doc in req.suggested_documents:
                        lines.append(f"- {doc}")
                lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    def generate_csv_data(self) -> List[Dict[str, str]]:
        """Generate CSV-compatible data for export."""
        pack = self.generate()
        return [
            {
                "Request ID": req.request_id,
                "Priority": req.priority,
                "Domain": req.domain,
                "Category": req.category,
                "Title": req.title,
                "Description": req.description,
                "Source": req.source,
                "Source ID": req.source_id or "",
                "Suggested Documents": "; ".join(req.suggested_documents),
            }
            for req in pack.get_sorted()
        ]
