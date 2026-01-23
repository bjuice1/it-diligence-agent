"""
Security Inventory - Cybersecurity Domain Depth

Implements Points 41-55 of the Enhancement Plan:
- Security stack inventory (EDR, SIEM, vulnerability scanners, etc.)
- Security tool coverage analysis
- Vulnerability management metrics
- Security framework mapping
- Security maturity scoring
- Incident response assessment

This module provides structured tracking of security posture.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SecurityToolCategory(Enum):
    """Categories of security tools."""
    EDR = "edr"                          # Endpoint Detection & Response
    SIEM = "siem"                        # Security Information & Event Management
    VULNERABILITY_SCANNER = "vuln_scan"  # Vulnerability scanning
    EMAIL_SECURITY = "email_sec"         # Email security gateway
    WEB_SECURITY = "web_sec"            # WAF, web proxy
    NETWORK_SECURITY = "net_sec"        # Firewall, IDS/IPS
    IAM = "iam"                          # Identity & Access Management
    DLP = "dlp"                          # Data Loss Prevention
    ENCRYPTION = "encryption"            # Encryption solutions
    BACKUP = "backup"                    # Backup & recovery
    PAM = "pam"                          # Privileged Access Management
    CASB = "casb"                        # Cloud Access Security Broker
    SOAR = "soar"                        # Security Orchestration
    THREAT_INTEL = "threat_intel"        # Threat intelligence
    OTHER = "other"


class SecurityToolMaturity(Enum):
    """Maturity level of security tool deployment."""
    BEST_IN_CLASS = "best_in_class"      # Industry-leading solution, well-configured
    ADEQUATE = "adequate"                 # Meets requirements, standard configuration
    BASIC = "basic"                       # Minimal deployment, limited features
    GAP = "gap"                          # Tool needed but not present
    UNKNOWN = "unknown"


class VulnerabilityStatus(Enum):
    """Status of vulnerability management."""
    EXCELLENT = "excellent"    # < 5 critical open, patched within SLA
    GOOD = "good"              # < 20 critical open, mostly within SLA
    NEEDS_IMPROVEMENT = "needs_improvement"  # 20-50 critical open
    POOR = "poor"              # > 50 critical open
    UNKNOWN = "unknown"


class SecurityFramework(Enum):
    """Security frameworks for mapping."""
    NIST_CSF = "nist_csf"
    CIS_CONTROLS = "cis"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    CMMC = "cmmc"


class IRMaturity(Enum):
    """Incident Response maturity level."""
    MATURE = "mature"            # Documented plan, tested, dedicated team
    DEVELOPING = "developing"    # Plan exists, some testing
    BASIC = "basic"              # Minimal documentation, ad-hoc response
    NONE = "none"                # No IR capability


class SOCCoverage(Enum):
    """Security Operations Center coverage."""
    INTERNAL_24X7 = "internal_24x7"
    INTERNAL_BUSINESS_HOURS = "internal_business"
    MSSP_24X7 = "mssp_24x7"
    MSSP_BUSINESS_HOURS = "mssp_business"
    NONE = "none"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SecurityTool:
    """A security tool in the stack."""
    tool_id: str
    name: str
    vendor: str
    category: SecurityToolCategory
    version: Optional[str] = None
    license_count: Optional[int] = None
    license_expiry: Optional[date] = None
    coverage_percent: Optional[float] = None  # % of assets covered
    is_transferable: bool = True
    maturity: SecurityToolMaturity = SecurityToolMaturity.UNKNOWN
    notes: str = ""

    # Deployment details
    deployment_type: str = ""  # on-prem, cloud, hybrid
    managed_by: str = ""  # internal, mssp, vendor
    integration_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "vendor": self.vendor,
            "category": self.category.value,
            "version": self.version,
            "license_count": self.license_count,
            "license_expiry": str(self.license_expiry) if self.license_expiry else None,
            "coverage_percent": self.coverage_percent,
            "is_transferable": self.is_transferable,
            "maturity": self.maturity.value,
            "deployment_type": self.deployment_type,
            "managed_by": self.managed_by,
            "notes": self.notes
        }


@dataclass
class VulnerabilityMetrics:
    """Vulnerability management metrics."""
    as_of_date: date

    # Open vulnerability counts
    critical_open: int = 0
    high_open: int = 0
    medium_open: int = 0
    low_open: int = 0

    # SLA information
    critical_sla_days: int = 7
    high_sla_days: int = 30
    medium_sla_days: int = 90
    low_sla_days: int = 180

    # Compliance rates
    critical_sla_compliance: float = 0.0  # % patched within SLA
    high_sla_compliance: float = 0.0

    # Scanning coverage
    scan_coverage_percent: float = 0.0
    last_scan_date: Optional[date] = None
    scan_frequency: str = ""  # weekly, monthly, quarterly

    # Historical trends
    critical_30_day_trend: str = ""  # increasing, stable, decreasing

    def to_dict(self) -> Dict:
        return {
            "as_of_date": str(self.as_of_date),
            "open_counts": {
                "critical": self.critical_open,
                "high": self.high_open,
                "medium": self.medium_open,
                "low": self.low_open,
                "total": self.critical_open + self.high_open + self.medium_open + self.low_open
            },
            "sla_compliance": {
                "critical": self.critical_sla_compliance,
                "high": self.high_sla_compliance
            },
            "coverage": {
                "scan_percent": self.scan_coverage_percent,
                "last_scan": str(self.last_scan_date) if self.last_scan_date else None,
                "frequency": self.scan_frequency
            },
            "trend": self.critical_30_day_trend
        }

    def get_status(self) -> VulnerabilityStatus:
        """Calculate overall vulnerability status."""
        if self.critical_open <= 5 and self.critical_sla_compliance >= 90:
            return VulnerabilityStatus.EXCELLENT
        elif self.critical_open <= 20 and self.critical_sla_compliance >= 70:
            return VulnerabilityStatus.GOOD
        elif self.critical_open <= 50:
            return VulnerabilityStatus.NEEDS_IMPROVEMENT
        elif self.critical_open > 50:
            return VulnerabilityStatus.POOR
        else:
            return VulnerabilityStatus.UNKNOWN


@dataclass
class PenetrationTestFinding:
    """A finding from a penetration test."""
    finding_id: str
    title: str
    severity: str  # critical, high, medium, low
    status: str    # open, remediated, accepted
    description: str
    remediation: str
    test_date: Optional[date] = None
    test_type: str = ""  # external, internal, web_app, social_engineering
    affected_systems: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "test_date": str(self.test_date) if self.test_date else None,
            "test_type": self.test_type,
            "affected_systems": self.affected_systems
        }


@dataclass
class ComplianceStatus:
    """Status for a compliance framework."""
    framework: SecurityFramework
    is_certified: bool = False
    certification_date: Optional[date] = None
    expiry_date: Optional[date] = None
    scope: str = ""  # What's in scope
    auditor: str = ""
    gaps_identified: List[str] = field(default_factory=list)
    last_audit_date: Optional[date] = None
    next_audit_date: Optional[date] = None

    def to_dict(self) -> Dict:
        return {
            "framework": self.framework.value,
            "is_certified": self.is_certified,
            "certification_date": str(self.certification_date) if self.certification_date else None,
            "expiry_date": str(self.expiry_date) if self.expiry_date else None,
            "scope": self.scope,
            "gaps_count": len(self.gaps_identified),
            "gaps": self.gaps_identified
        }


@dataclass
class IncidentResponseAssessment:
    """Assessment of incident response capabilities."""
    has_ir_plan: bool = False
    ir_plan_last_updated: Optional[date] = None
    ir_plan_tested: bool = False
    last_ir_test_date: Optional[date] = None

    # Team structure
    has_dedicated_ir_team: bool = False
    ir_team_size: int = 0
    uses_mssp_for_ir: bool = False
    mssp_name: str = ""

    # Capabilities
    has_forensics_capability: bool = False
    has_threat_hunting: bool = False
    has_playbooks: bool = False
    playbook_count: int = 0

    # Past incidents
    incidents_last_12_months: int = 0
    major_incidents_last_12_months: int = 0
    average_mttr_hours: Optional[float] = None  # Mean time to respond

    def to_dict(self) -> Dict:
        return {
            "plan": {
                "exists": self.has_ir_plan,
                "last_updated": str(self.ir_plan_last_updated) if self.ir_plan_last_updated else None,
                "tested": self.ir_plan_tested,
                "last_test": str(self.last_ir_test_date) if self.last_ir_test_date else None
            },
            "team": {
                "has_dedicated_team": self.has_dedicated_ir_team,
                "size": self.ir_team_size,
                "uses_mssp": self.uses_mssp_for_ir,
                "mssp": self.mssp_name
            },
            "capabilities": {
                "forensics": self.has_forensics_capability,
                "threat_hunting": self.has_threat_hunting,
                "playbooks": self.has_playbooks,
                "playbook_count": self.playbook_count
            },
            "incidents": {
                "last_12_months": self.incidents_last_12_months,
                "major": self.major_incidents_last_12_months,
                "avg_mttr_hours": self.average_mttr_hours
            }
        }

    def get_maturity(self) -> IRMaturity:
        """Calculate IR maturity level."""
        score = 0
        if self.has_ir_plan:
            score += 1
        if self.ir_plan_tested:
            score += 1
        if self.has_dedicated_ir_team or self.uses_mssp_for_ir:
            score += 1
        if self.has_playbooks and self.playbook_count >= 5:
            score += 1
        if self.has_forensics_capability:
            score += 1

        if score >= 4:
            return IRMaturity.MATURE
        elif score >= 2:
            return IRMaturity.DEVELOPING
        elif score >= 1:
            return IRMaturity.BASIC
        else:
            return IRMaturity.NONE


@dataclass
class SOCAssessment:
    """Assessment of Security Operations Center capabilities."""
    has_soc: bool = False
    coverage: SOCCoverage = SOCCoverage.NONE

    # Internal SOC
    internal_soc_size: int = 0
    internal_soc_location: str = ""

    # MSSP details
    mssp_name: str = ""
    mssp_contract_expiry: Optional[date] = None
    mssp_transferable: bool = True

    # Capabilities
    average_daily_alerts: int = 0
    average_escalations: int = 0
    false_positive_rate: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "has_soc": self.has_soc,
            "coverage": self.coverage.value,
            "internal_size": self.internal_soc_size,
            "mssp": {
                "name": self.mssp_name,
                "contract_expiry": str(self.mssp_contract_expiry) if self.mssp_contract_expiry else None,
                "transferable": self.mssp_transferable
            },
            "metrics": {
                "daily_alerts": self.average_daily_alerts,
                "escalations": self.average_escalations,
                "false_positive_rate": self.false_positive_rate
            }
        }


# =============================================================================
# SECURITY FRAMEWORK MAPPING
# =============================================================================

# NIST CSF function mappings
NIST_CSF_FUNCTIONS = {
    "identify": {
        "controls": ["Asset Management", "Business Environment", "Governance", "Risk Assessment", "Risk Management Strategy"],
        "tool_categories": [SecurityToolCategory.VULNERABILITY_SCANNER]
    },
    "protect": {
        "controls": ["Access Control", "Awareness & Training", "Data Security", "Information Protection", "Maintenance", "Protective Technology"],
        "tool_categories": [SecurityToolCategory.IAM, SecurityToolCategory.PAM, SecurityToolCategory.DLP, SecurityToolCategory.ENCRYPTION, SecurityToolCategory.EMAIL_SECURITY, SecurityToolCategory.WEB_SECURITY, SecurityToolCategory.NETWORK_SECURITY]
    },
    "detect": {
        "controls": ["Anomalies & Events", "Security Continuous Monitoring", "Detection Processes"],
        "tool_categories": [SecurityToolCategory.SIEM, SecurityToolCategory.EDR, SecurityToolCategory.THREAT_INTEL]
    },
    "respond": {
        "controls": ["Response Planning", "Communications", "Analysis", "Mitigation", "Improvements"],
        "tool_categories": [SecurityToolCategory.SOAR, SecurityToolCategory.EDR]
    },
    "recover": {
        "controls": ["Recovery Planning", "Improvements", "Communications"],
        "tool_categories": [SecurityToolCategory.BACKUP]
    }
}

# Required tools for each maturity level
MATURITY_REQUIREMENTS = {
    "basic": {
        SecurityToolCategory.NETWORK_SECURITY,
        SecurityToolCategory.BACKUP,
        SecurityToolCategory.EMAIL_SECURITY
    },
    "developing": {
        SecurityToolCategory.NETWORK_SECURITY,
        SecurityToolCategory.BACKUP,
        SecurityToolCategory.EMAIL_SECURITY,
        SecurityToolCategory.EDR,
        SecurityToolCategory.VULNERABILITY_SCANNER,
        SecurityToolCategory.IAM
    },
    "managed": {
        SecurityToolCategory.NETWORK_SECURITY,
        SecurityToolCategory.BACKUP,
        SecurityToolCategory.EMAIL_SECURITY,
        SecurityToolCategory.EDR,
        SecurityToolCategory.VULNERABILITY_SCANNER,
        SecurityToolCategory.IAM,
        SecurityToolCategory.SIEM,
        SecurityToolCategory.DLP
    },
    "optimized": {
        SecurityToolCategory.NETWORK_SECURITY,
        SecurityToolCategory.BACKUP,
        SecurityToolCategory.EMAIL_SECURITY,
        SecurityToolCategory.EDR,
        SecurityToolCategory.VULNERABILITY_SCANNER,
        SecurityToolCategory.IAM,
        SecurityToolCategory.SIEM,
        SecurityToolCategory.DLP,
        SecurityToolCategory.PAM,
        SecurityToolCategory.SOAR,
        SecurityToolCategory.THREAT_INTEL,
        SecurityToolCategory.CASB
    }
}


# =============================================================================
# SECURITY INVENTORY
# =============================================================================

class SecurityInventory:
    """
    Central inventory for security posture assessment.

    Implements Points 41-55: Cybersecurity Domain Depth.
    """

    def __init__(self):
        self.tools: List[SecurityTool] = []
        self.vulnerability_metrics: Optional[VulnerabilityMetrics] = None
        self.pentest_findings: List[PenetrationTestFinding] = []
        self.compliance_statuses: List[ComplianceStatus] = []
        self.ir_assessment: Optional[IncidentResponseAssessment] = None
        self.soc_assessment: Optional[SOCAssessment] = None
        self.created_at = datetime.now().isoformat()

    def add_tool(self, tool: SecurityTool):
        """Add a security tool to the inventory."""
        self.tools.append(tool)

    def add_pentest_finding(self, finding: PenetrationTestFinding):
        """Add a penetration test finding."""
        self.pentest_findings.append(finding)

    def add_compliance_status(self, status: ComplianceStatus):
        """Add compliance framework status."""
        self.compliance_statuses.append(status)

    # -------------------------------------------------------------------------
    # Point 41-42: Security Stack Inventory & Coverage Analysis
    # -------------------------------------------------------------------------

    def get_security_stack(self) -> Dict[str, Any]:
        """
        Get complete security stack inventory.

        Implements Point 41: Create security stack inventory.
        """
        by_category = {}
        for tool in self.tools:
            cat = tool.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(tool.to_dict())

        return {
            "total_tools": len(self.tools),
            "by_category": by_category,
            "tools": [t.to_dict() for t in self.tools]
        }

    def get_coverage_analysis(self) -> Dict[str, Any]:
        """
        Analyze security tool coverage.

        Implements Point 42: Security tool coverage analysis.
        """
        # Check which categories are covered
        covered_categories = {t.category for t in self.tools}
        all_categories = set(SecurityToolCategory)
        missing_categories = all_categories - covered_categories - {SecurityToolCategory.OTHER}

        # Calculate average coverage for tools that have it
        coverage_by_category = {}
        for tool in self.tools:
            if tool.coverage_percent is not None:
                cat = tool.category.value
                if cat not in coverage_by_category:
                    coverage_by_category[cat] = []
                coverage_by_category[cat].append(tool.coverage_percent)

        avg_coverage = {}
        for cat, coverages in coverage_by_category.items():
            avg_coverage[cat] = sum(coverages) / len(coverages)

        return {
            "categories_covered": len(covered_categories),
            "categories_missing": [c.value for c in missing_categories],
            "coverage_by_category": avg_coverage,
            "critical_gaps": self._identify_critical_gaps(missing_categories)
        }

    def _identify_critical_gaps(self, missing: Set[SecurityToolCategory]) -> List[str]:
        """Identify critical security gaps."""
        critical = []
        critical_categories = {
            SecurityToolCategory.EDR: "No endpoint detection/response",
            SecurityToolCategory.SIEM: "No security event monitoring",
            SecurityToolCategory.VULNERABILITY_SCANNER: "No vulnerability scanning",
            SecurityToolCategory.BACKUP: "No backup solution",
            SecurityToolCategory.IAM: "No identity management"
        }
        for cat, message in critical_categories.items():
            if cat in missing:
                critical.append(message)
        return critical

    # -------------------------------------------------------------------------
    # Point 43-44: Security Tool Licensing & Maturity
    # -------------------------------------------------------------------------

    def get_licensing_assessment(self) -> Dict[str, Any]:
        """
        Assess security tool licensing.

        Implements Point 43: Security tool licensing assessment.
        """
        issues = []
        expiring_soon = []
        non_transferable = []

        today = date.today()
        warning_days = 90

        for tool in self.tools:
            # Check expiry
            if tool.license_expiry:
                days_until = (tool.license_expiry - today).days
                if days_until < 0:
                    issues.append(f"{tool.name}: License expired")
                elif days_until < warning_days:
                    expiring_soon.append({
                        "tool": tool.name,
                        "expiry": str(tool.license_expiry),
                        "days_remaining": days_until
                    })

            # Check transferability
            if not tool.is_transferable:
                non_transferable.append({
                    "tool": tool.name,
                    "vendor": tool.vendor,
                    "category": tool.category.value
                })

        return {
            "issues": issues,
            "expiring_within_90_days": expiring_soon,
            "non_transferable_count": len(non_transferable),
            "non_transferable": non_transferable,
            "total_tools_assessed": len(self.tools)
        }

    def get_maturity_scoring(self) -> Dict[str, Any]:
        """
        Score security tool maturity.

        Implements Point 44: Security tool maturity scoring.
        """
        maturity_counts = {}
        for tool in self.tools:
            level = tool.maturity.value
            maturity_counts[level] = maturity_counts.get(level, 0) + 1

        # Calculate overall maturity
        covered = {t.category for t in self.tools}
        if covered >= MATURITY_REQUIREMENTS["optimized"]:
            overall = "optimized"
        elif covered >= MATURITY_REQUIREMENTS["managed"]:
            overall = "managed"
        elif covered >= MATURITY_REQUIREMENTS["developing"]:
            overall = "developing"
        elif covered >= MATURITY_REQUIREMENTS["basic"]:
            overall = "basic"
        else:
            overall = "initial"

        return {
            "overall_maturity": overall,
            "tool_maturity_distribution": maturity_counts,
            "best_in_class_tools": [t.name for t in self.tools if t.maturity == SecurityToolMaturity.BEST_IN_CLASS],
            "gaps_or_basic": [t.name for t in self.tools if t.maturity in [SecurityToolMaturity.GAP, SecurityToolMaturity.BASIC]]
        }

    # -------------------------------------------------------------------------
    # Point 45-48: Vulnerability Management
    # -------------------------------------------------------------------------

    def get_vulnerability_assessment(self) -> Dict[str, Any]:
        """
        Get vulnerability management assessment.

        Implements Points 45-48: Vulnerability management analysis.
        """
        if not self.vulnerability_metrics:
            return {"status": "unknown", "message": "No vulnerability data available"}

        metrics = self.vulnerability_metrics
        status = metrics.get_status()

        return {
            "status": status.value,
            "metrics": metrics.to_dict(),
            "risk_score": self._calculate_vuln_risk_score(metrics),
            "recommendations": self._get_vuln_recommendations(metrics, status)
        }

    def _calculate_vuln_risk_score(self, metrics: VulnerabilityMetrics) -> int:
        """Calculate a risk score from vulnerability metrics (0-100)."""
        score = 0

        # Critical vulnerabilities are heavily weighted
        score += min(50, metrics.critical_open * 5)

        # High vulnerabilities
        score += min(25, metrics.high_open)

        # SLA compliance impact
        if metrics.critical_sla_compliance < 50:
            score += 15
        elif metrics.critical_sla_compliance < 80:
            score += 10

        # Coverage gaps
        if metrics.scan_coverage_percent < 80:
            score += 10

        return min(100, score)

    def _get_vuln_recommendations(
        self,
        metrics: VulnerabilityMetrics,
        status: VulnerabilityStatus
    ) -> List[str]:
        """Generate vulnerability management recommendations."""
        recs = []

        if metrics.critical_open > 10:
            recs.append("Critical: Immediate remediation program needed for open critical vulnerabilities")

        if metrics.critical_sla_compliance < 80:
            recs.append("Improve patching velocity - critical SLA compliance below 80%")

        if metrics.scan_coverage_percent < 90:
            recs.append(f"Increase scan coverage from {metrics.scan_coverage_percent}% to >90%")

        if not metrics.scan_frequency or metrics.scan_frequency == "quarterly":
            recs.append("Increase scan frequency to at least monthly")

        return recs

    # -------------------------------------------------------------------------
    # Point 49-52: Security Framework & Compliance
    # -------------------------------------------------------------------------

    def get_framework_mapping(self) -> Dict[str, Any]:
        """
        Map security controls to frameworks.

        Implements Point 49: Security framework mapping.
        """
        # Map tools to NIST CSF functions
        nist_coverage = {}
        for function, config in NIST_CSF_FUNCTIONS.items():
            covered_tools = [
                t for t in self.tools
                if t.category in config["tool_categories"]
            ]
            nist_coverage[function] = {
                "tools": [t.name for t in covered_tools],
                "coverage": len(covered_tools) / len(config["tool_categories"]) * 100 if config["tool_categories"] else 0
            }

        # Get compliance statuses
        framework_statuses = {
            cs.framework.value: cs.to_dict()
            for cs in self.compliance_statuses
        }

        return {
            "nist_csf_mapping": nist_coverage,
            "compliance_frameworks": framework_statuses,
            "certified_frameworks": [
                cs.framework.value for cs in self.compliance_statuses if cs.is_certified
            ]
        }

    def get_security_maturity_score(self) -> Dict[str, Any]:
        """
        Calculate overall security maturity score.

        Implements Point 50: Security maturity scoring.
        """
        scores = {
            "tooling": 0,
            "vulnerability_mgmt": 0,
            "compliance": 0,
            "incident_response": 0,
            "monitoring": 0
        }

        # Tooling score (0-20)
        tool_maturity = self.get_maturity_scoring()
        maturity_scores = {"optimized": 20, "managed": 15, "developing": 10, "basic": 5, "initial": 0}
        scores["tooling"] = maturity_scores.get(tool_maturity["overall_maturity"], 0)

        # Vulnerability management score (0-20)
        if self.vulnerability_metrics:
            vuln_status = self.vulnerability_metrics.get_status()
            vuln_scores = {
                VulnerabilityStatus.EXCELLENT: 20,
                VulnerabilityStatus.GOOD: 15,
                VulnerabilityStatus.NEEDS_IMPROVEMENT: 8,
                VulnerabilityStatus.POOR: 3,
                VulnerabilityStatus.UNKNOWN: 0
            }
            scores["vulnerability_mgmt"] = vuln_scores.get(vuln_status, 0)

        # Compliance score (0-20)
        certified_count = sum(1 for cs in self.compliance_statuses if cs.is_certified)
        scores["compliance"] = min(20, certified_count * 5)

        # Incident response score (0-20)
        if self.ir_assessment:
            ir_maturity = self.ir_assessment.get_maturity()
            ir_scores = {
                IRMaturity.MATURE: 20,
                IRMaturity.DEVELOPING: 12,
                IRMaturity.BASIC: 5,
                IRMaturity.NONE: 0
            }
            scores["incident_response"] = ir_scores.get(ir_maturity, 0)

        # Monitoring/SOC score (0-20)
        if self.soc_assessment:
            if self.soc_assessment.coverage == SOCCoverage.INTERNAL_24X7:
                scores["monitoring"] = 20
            elif self.soc_assessment.coverage == SOCCoverage.MSSP_24X7:
                scores["monitoring"] = 18
            elif self.soc_assessment.coverage == SOCCoverage.INTERNAL_BUSINESS_HOURS:
                scores["monitoring"] = 12
            elif self.soc_assessment.coverage == SOCCoverage.MSSP_BUSINESS_HOURS:
                scores["monitoring"] = 10
            else:
                scores["monitoring"] = 0

        total = sum(scores.values())

        # Determine overall level
        if total >= 80:
            level = "mature"
        elif total >= 60:
            level = "managed"
        elif total >= 40:
            level = "developing"
        elif total >= 20:
            level = "basic"
        else:
            level = "initial"

        return {
            "total_score": total,
            "max_score": 100,
            "level": level,
            "domain_scores": scores,
            "strengths": [k for k, v in scores.items() if v >= 15],
            "improvement_areas": [k for k, v in scores.items() if v < 10]
        }

    def get_compliance_gaps(self) -> Dict[str, Any]:
        """
        Identify compliance gaps.

        Implements Point 52: Compliance gap identification.
        """
        gaps = []
        for cs in self.compliance_statuses:
            if cs.gaps_identified:
                gaps.append({
                    "framework": cs.framework.value,
                    "gaps": cs.gaps_identified,
                    "gap_count": len(cs.gaps_identified)
                })

        # Check for missing critical frameworks
        required_frameworks = set()
        # This would typically come from deal context or industry

        return {
            "frameworks_with_gaps": len(gaps),
            "total_gaps": sum(len(g["gaps"]) for g in gaps),
            "gap_details": gaps
        }

    # -------------------------------------------------------------------------
    # Point 51: Penetration Test Findings
    # -------------------------------------------------------------------------

    def get_pentest_summary(self) -> Dict[str, Any]:
        """
        Summarize penetration test findings.

        Implements Point 51: Penetration test findings extraction.
        """
        if not self.pentest_findings:
            return {"status": "unknown", "message": "No penetration test data available"}

        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_status = {"open": 0, "remediated": 0, "accepted": 0}

        for finding in self.pentest_findings:
            severity = finding.severity.lower()
            if severity in by_severity:
                by_severity[severity] += 1
            status = finding.status.lower()
            if status in by_status:
                by_status[status] += 1

        open_critical = [f for f in self.pentest_findings
                        if f.severity.lower() == "critical" and f.status.lower() == "open"]

        return {
            "total_findings": len(self.pentest_findings),
            "by_severity": by_severity,
            "by_status": by_status,
            "open_critical_findings": [f.to_dict() for f in open_critical],
            "risk_level": "high" if len(open_critical) > 0 else "medium" if by_severity["high"] > 5 else "low"
        }

    # -------------------------------------------------------------------------
    # Points 53-55: SOC & Incident Response
    # -------------------------------------------------------------------------

    def get_monitoring_assessment(self) -> Dict[str, Any]:
        """
        Assess SOC and monitoring capabilities.

        Implements Point 53: SOC/monitoring capabilities.
        """
        if not self.soc_assessment:
            return {"status": "unknown", "message": "No SOC assessment available"}

        return {
            "soc": self.soc_assessment.to_dict(),
            "coverage_level": self.soc_assessment.coverage.value,
            "recommendations": self._get_soc_recommendations()
        }

    def _get_soc_recommendations(self) -> List[str]:
        """Generate SOC recommendations."""
        recs = []
        if not self.soc_assessment or not self.soc_assessment.has_soc:
            recs.append("Establish security monitoring capability (internal or MSSP)")
            return recs

        if self.soc_assessment.coverage in [SOCCoverage.NONE, SOCCoverage.INTERNAL_BUSINESS_HOURS, SOCCoverage.MSSP_BUSINESS_HOURS]:
            recs.append("Consider 24x7 monitoring coverage for improved detection")

        if self.soc_assessment.false_positive_rate and self.soc_assessment.false_positive_rate > 0.8:
            recs.append("High false positive rate - tune detection rules")

        return recs

    def get_ir_assessment(self) -> Dict[str, Any]:
        """
        Get incident response assessment.

        Implements Points 54-55: Incident response assessment.
        """
        if not self.ir_assessment:
            return {"status": "unknown", "message": "No IR assessment available"}

        maturity = self.ir_assessment.get_maturity()

        return {
            "maturity_level": maturity.value,
            "assessment": self.ir_assessment.to_dict(),
            "recommendations": self._get_ir_recommendations(maturity)
        }

    def _get_ir_recommendations(self, maturity: IRMaturity) -> List[str]:
        """Generate IR recommendations based on maturity."""
        recs = []

        if maturity == IRMaturity.NONE:
            recs.append("Critical: Develop incident response plan immediately")
            recs.append("Identify IR team or engage MSSP for IR services")
        elif maturity == IRMaturity.BASIC:
            recs.append("Formalize and document incident response procedures")
            recs.append("Conduct tabletop exercises to test IR plan")
        elif maturity == IRMaturity.DEVELOPING:
            recs.append("Increase IR testing frequency")
            recs.append("Develop additional playbooks for common scenarios")

        if self.ir_assessment:
            if not self.ir_assessment.has_forensics_capability:
                recs.append("Establish or contract forensics capability")
            if self.ir_assessment.average_mttr_hours and self.ir_assessment.average_mttr_hours > 24:
                recs.append("Work to reduce mean time to respond below 24 hours")

        return recs

    # -------------------------------------------------------------------------
    # Complete Assessment
    # -------------------------------------------------------------------------

    def get_complete_assessment(self) -> Dict[str, Any]:
        """Get complete security assessment."""
        return {
            "metadata": {
                "created_at": self.created_at,
                "assessment_date": datetime.now().isoformat()
            },
            "security_stack": self.get_security_stack(),
            "coverage": self.get_coverage_analysis(),
            "licensing": self.get_licensing_assessment(),
            "tool_maturity": self.get_maturity_scoring(),
            "vulnerability_mgmt": self.get_vulnerability_assessment(),
            "framework_mapping": self.get_framework_mapping(),
            "security_maturity": self.get_security_maturity_score(),
            "compliance_gaps": self.get_compliance_gaps(),
            "pentest_summary": self.get_pentest_summary(),
            "soc_monitoring": self.get_monitoring_assessment(),
            "incident_response": self.get_ir_assessment()
        }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("=== Security Inventory Module Test ===\n")

    inventory = SecurityInventory()

    # Add security tools
    inventory.add_tool(SecurityTool(
        tool_id="ST-001",
        name="CrowdStrike Falcon",
        vendor="CrowdStrike",
        category=SecurityToolCategory.EDR,
        version="6.x",
        license_count=500,
        coverage_percent=95.0,
        maturity=SecurityToolMaturity.BEST_IN_CLASS
    ))

    inventory.add_tool(SecurityTool(
        tool_id="ST-002",
        name="Splunk Enterprise",
        vendor="Splunk",
        category=SecurityToolCategory.SIEM,
        license_count=100,
        coverage_percent=80.0,
        maturity=SecurityToolMaturity.ADEQUATE
    ))

    inventory.add_tool(SecurityTool(
        tool_id="ST-003",
        name="Qualys",
        vendor="Qualys",
        category=SecurityToolCategory.VULNERABILITY_SCANNER,
        coverage_percent=90.0,
        maturity=SecurityToolMaturity.ADEQUATE
    ))

    inventory.add_tool(SecurityTool(
        tool_id="ST-004",
        name="Proofpoint",
        vendor="Proofpoint",
        category=SecurityToolCategory.EMAIL_SECURITY,
        coverage_percent=100.0,
        maturity=SecurityToolMaturity.BEST_IN_CLASS
    ))

    # Add vulnerability metrics
    inventory.vulnerability_metrics = VulnerabilityMetrics(
        as_of_date=date.today(),
        critical_open=8,
        high_open=45,
        medium_open=200,
        low_open=500,
        critical_sla_compliance=85.0,
        high_sla_compliance=75.0,
        scan_coverage_percent=92.0,
        scan_frequency="weekly"
    )

    # Add compliance status
    inventory.add_compliance_status(ComplianceStatus(
        framework=SecurityFramework.SOC2,
        is_certified=True,
        certification_date=date(2025, 6, 1),
        scope="All production systems"
    ))

    # Add IR assessment
    inventory.ir_assessment = IncidentResponseAssessment(
        has_ir_plan=True,
        ir_plan_tested=True,
        has_dedicated_ir_team=False,
        uses_mssp_for_ir=True,
        mssp_name="Secureworks",
        has_playbooks=True,
        playbook_count=8
    )

    # Add SOC assessment
    inventory.soc_assessment = SOCAssessment(
        has_soc=True,
        coverage=SOCCoverage.MSSP_24X7,
        mssp_name="Secureworks",
        average_daily_alerts=250
    )

    # Print results
    print("1. Security Stack")
    stack = inventory.get_security_stack()
    print(f"   Total tools: {stack['total_tools']}")
    print(f"   Categories: {list(stack['by_category'].keys())}")
    print()

    print("2. Coverage Analysis")
    coverage = inventory.get_coverage_analysis()
    print(f"   Categories covered: {coverage['categories_covered']}")
    print(f"   Missing: {coverage['categories_missing'][:3]}...")
    print()

    print("3. Vulnerability Assessment")
    vuln = inventory.get_vulnerability_assessment()
    print(f"   Status: {vuln['status']}")
    print(f"   Critical open: {inventory.vulnerability_metrics.critical_open}")
    print()

    print("4. Security Maturity Score")
    maturity = inventory.get_security_maturity_score()
    print(f"   Total score: {maturity['total_score']}/100")
    print(f"   Level: {maturity['level']}")
    print(f"   Strengths: {maturity['strengths']}")
    print()

    print("5. IR Assessment")
    ir = inventory.get_ir_assessment()
    print(f"   Maturity: {ir['maturity_level']}")
    print()

    print("=== Security Inventory Module Test Complete ===")
