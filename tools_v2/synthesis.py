"""
Synthesis Phase - Cross-Domain Consistency

Performs cross-domain analysis to:
1. Identify consistency issues across domains
2. Detect conflicting findings
3. Connect related risks/work items
4. Aggregate costs and priorities
5. Generate executive summary data
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Set
from datetime import datetime
from stores.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore, COST_RANGE_VALUES
from tools_v2.coverage import CoverageAnalyzer

# Import caching
try:
    from tools_v2.cache import cached_synthesis
except ImportError:
    # Fallback if cache not available
    def cached_synthesis(func):
        return func


# =============================================================================
# CONSISTENCY CHECKS
# =============================================================================

# Keywords to check for consistency across domains
CROSS_DOMAIN_KEYWORDS = {
    # Cloud provider consistency
    "aws": ["amazon", "aws", "ec2", "s3", "lambda", "rds"],
    "azure": ["azure", "microsoft cloud", "entra", "office 365", "o365"],
    "gcp": ["google cloud", "gcp", "gke", "bigquery"],

    # ERP consistency
    "sap": ["sap", "s/4hana", "hana"],
    "oracle_erp": ["oracle erp", "oracle cloud", "netsuite"],
    "dynamics": ["dynamics 365", "dynamics ax", "dynamics nav"],

    # Identity provider consistency
    "okta": ["okta"],
    "azure_ad": ["azure ad", "entra id", "azure active directory"],
    "ping": ["ping identity", "pingfederate"],

    # Security tools
    "crowdstrike": ["crowdstrike", "falcon"],
    "microsoft_defender": ["defender", "microsoft defender"],
    "palo_alto": ["palo alto", "pan-os", "cortex"],
}


@dataclass
class ConsistencyIssue:
    """A detected consistency issue across domains."""
    issue_id: str
    issue_type: str  # conflict, missing_reference, inconsistent_data
    domains_involved: List[str]
    description: str
    severity: str  # high, medium, low
    fact_ids: List[str]
    recommendation: str


@dataclass
class RelatedFinding:
    """A group of related findings across domains."""
    group_id: str
    theme: str  # e.g., "cloud_migration", "security_gaps", "eol_systems"
    findings: List[Dict[str, str]]  # [{type, id, domain, title}]
    total_cost_low: int
    total_cost_high: int


# =============================================================================
# SYNTHESIS ANALYZER
# =============================================================================

class SynthesisAnalyzer:
    """
    Performs cross-domain synthesis and consistency analysis.

    Usage:
        analyzer = SynthesisAnalyzer(fact_store, reasoning_store)
        results = analyzer.analyze()
    """

    def __init__(
        self,
        fact_store: FactStore,
        reasoning_store: ReasoningStore
    ):
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store
        self.coverage_analyzer = CoverageAnalyzer(fact_store)
        self._issue_counter = 0
        self._group_counter = 0

    def _next_issue_id(self) -> str:
        self._issue_counter += 1
        return f"CI-{self._issue_counter:03d}"

    def _next_group_id(self) -> str:
        self._group_counter += 1
        return f"RG-{self._group_counter:03d}"

    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract known keywords from text."""
        text_lower = text.lower()
        found = set()

        for keyword_group, variations in CROSS_DOMAIN_KEYWORDS.items():
            for var in variations:
                if var in text_lower:
                    found.add(keyword_group)
                    break

        return found

    def _get_domain_keywords(self, domain: str) -> Set[str]:
        """Get all keywords mentioned in a domain's facts."""
        keywords = set()

        for fact in self.fact_store.facts:
            if fact.domain == domain:
                # Check item name
                keywords.update(self._extract_keywords_from_text(fact.item))
                # Check details
                for key, value in fact.details.items():
                    if isinstance(value, str):
                        keywords.update(self._extract_keywords_from_text(value))
                # Check evidence
                if "exact_quote" in fact.evidence:
                    keywords.update(
                        self._extract_keywords_from_text(fact.evidence["exact_quote"])
                    )

        return keywords

    def check_cloud_provider_consistency(self) -> List[ConsistencyIssue]:
        """Check if cloud provider references are consistent across domains."""
        issues = []

        # Get cloud keywords per domain
        domain_clouds = {}
        for domain in ["infrastructure", "applications", "network", "cybersecurity"]:
            keywords = self._get_domain_keywords(domain)
            clouds = keywords & {"aws", "azure", "gcp"}
            if clouds:
                domain_clouds[domain] = clouds

        # Check for inconsistencies
        all_clouds = set()
        for clouds in domain_clouds.values():
            all_clouds.update(clouds)

        if len(all_clouds) > 1:
            # Multiple cloud providers mentioned - check if intentional
            for cloud in all_clouds:
                mentioning_domains = [
                    d for d, c in domain_clouds.items() if cloud in c
                ]
                not_mentioning = [
                    d for d in domain_clouds.keys() if d not in mentioning_domains
                ]

                if mentioning_domains and not_mentioning:
                    issues.append(ConsistencyIssue(
                        issue_id=self._next_issue_id(),
                        issue_type="inconsistent_data",
                        domains_involved=mentioning_domains + not_mentioning,
                        description=f"Cloud provider '{cloud.upper()}' mentioned in "
                                  f"{', '.join(mentioning_domains)} but not in "
                                  f"{', '.join(not_mentioning)}. Verify if this is "
                                  f"intentional multi-cloud or an inconsistency.",
                        severity="medium",
                        fact_ids=[],
                        recommendation="Clarify cloud strategy and ensure all domains "
                                      "reflect accurate cloud provider usage."
                    ))

        return issues

    def check_security_tool_consistency(self) -> List[ConsistencyIssue]:
        """Check if security tools are consistently referenced."""
        issues = []

        # Check endpoint security
        cyber_keywords = self._get_domain_keywords("cybersecurity")
        infra_keywords = self._get_domain_keywords("infrastructure")

        # If cybersecurity mentions an EDR, infrastructure should too
        edr_tools = cyber_keywords & {"crowdstrike", "microsoft_defender"}
        infra_edr = infra_keywords & {"crowdstrike", "microsoft_defender"}

        if edr_tools and not infra_edr:
            issues.append(ConsistencyIssue(
                issue_id=self._next_issue_id(),
                issue_type="missing_reference",
                domains_involved=["cybersecurity", "infrastructure"],
                description=f"EDR tool mentioned in cybersecurity "
                          f"({', '.join(edr_tools)}) but not in infrastructure. "
                          f"Infrastructure should reference endpoint protection.",
                severity="low",
                fact_ids=[],
                recommendation="Verify endpoint protection is documented in both "
                              "cybersecurity and infrastructure inventories."
            ))

        return issues

    def check_identity_consistency(self) -> List[ConsistencyIssue]:
        """Check identity provider consistency."""
        issues = []

        iam_keywords = self._get_domain_keywords("identity_access")
        app_keywords = self._get_domain_keywords("applications")

        # Check SSO provider alignment
        iam_sso = iam_keywords & {"okta", "azure_ad", "ping"}
        app_sso = app_keywords & {"okta", "azure_ad", "ping"}

        if iam_sso and app_sso and iam_sso != app_sso:
            issues.append(ConsistencyIssue(
                issue_id=self._next_issue_id(),
                issue_type="conflict",
                domains_involved=["identity_access", "applications"],
                description=f"Different SSO providers referenced: "
                          f"identity_access mentions {', '.join(iam_sso)}, "
                          f"applications mentions {', '.join(app_sso)}.",
                severity="high",
                fact_ids=[],
                recommendation="Clarify which SSO provider is authoritative and "
                              "ensure consistent documentation."
            ))

        return issues

    def find_related_findings(self) -> List[RelatedFinding]:
        """Group related findings across domains."""
        groups = []

        # Group by theme using keyword analysis
        themes = {
            "eol_remediation": ["eol", "end of life", "end-of-life", "unsupported", "deprecated"],
            "cloud_modernization": ["cloud", "migration", "aws", "azure", "gcp", "modernization"],
            "security_gaps": ["security", "vulnerability", "compliance", "audit", "risk"],
            "integration_work": ["integration", "api", "middleware", "migration", "consolidation"],
        }

        for theme_name, keywords in themes.items():
            related = []

            # Check risks
            for risk in self.reasoning_store.risks:
                text = f"{risk.title} {risk.description}".lower()
                if any(kw in text for kw in keywords):
                    related.append({
                        "type": "risk",
                        "id": risk.finding_id,
                        "domain": risk.domain,
                        "title": risk.title,
                        "severity": risk.severity,
                    })

            # Check work items
            for wi in self.reasoning_store.work_items:
                text = f"{wi.title} {wi.description}".lower()
                if any(kw in text for kw in keywords):
                    cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {"low": 0, "high": 0})
                    related.append({
                        "type": "work_item",
                        "id": wi.finding_id,
                        "domain": wi.domain,
                        "title": wi.title,
                        "phase": wi.phase,
                        "cost_low": cost_range["low"],
                        "cost_high": cost_range["high"],
                    })

            if related:
                # Calculate total costs
                total_low = sum(
                    r.get("cost_low", 0) for r in related if r["type"] == "work_item"
                )
                total_high = sum(
                    r.get("cost_high", 0) for r in related if r["type"] == "work_item"
                )

                groups.append(RelatedFinding(
                    group_id=self._next_group_id(),
                    theme=theme_name,
                    findings=related,
                    total_cost_low=total_low,
                    total_cost_high=total_high,
                ))

        return groups

    def aggregate_costs(self) -> Dict[str, Any]:
        """Aggregate costs across all work items."""
        by_phase = {"Day_1": {"low": 0, "high": 0, "count": 0},
                    "Day_100": {"low": 0, "high": 0, "count": 0},
                    "Post_100": {"low": 0, "high": 0, "count": 0}}

        by_domain = {}
        by_owner = {}

        for wi in self.reasoning_store.work_items:
            cost_range = COST_RANGE_VALUES.get(wi.cost_estimate, {"low": 0, "high": 0})

            # By phase
            if wi.phase in by_phase:
                by_phase[wi.phase]["low"] += cost_range["low"]
                by_phase[wi.phase]["high"] += cost_range["high"]
                by_phase[wi.phase]["count"] += 1

            # By domain
            if wi.domain not in by_domain:
                by_domain[wi.domain] = {"low": 0, "high": 0, "count": 0}
            by_domain[wi.domain]["low"] += cost_range["low"]
            by_domain[wi.domain]["high"] += cost_range["high"]
            by_domain[wi.domain]["count"] += 1

            # By owner
            if wi.owner_type not in by_owner:
                by_owner[wi.owner_type] = {"low": 0, "high": 0, "count": 0}
            by_owner[wi.owner_type]["low"] += cost_range["low"]
            by_owner[wi.owner_type]["high"] += cost_range["high"]
            by_owner[wi.owner_type]["count"] += 1

        total_low = sum(p["low"] for p in by_phase.values())
        total_high = sum(p["high"] for p in by_phase.values())

        return {
            "total": {"low": total_low, "high": total_high,
                     "count": len(self.reasoning_store.work_items)},
            "by_phase": by_phase,
            "by_domain": by_domain,
            "by_owner": by_owner,
        }

    def aggregate_risks(self) -> Dict[str, Any]:
        """Aggregate risks by severity and domain."""
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_domain = {}
        integration_dependent = 0

        for risk in self.reasoning_store.risks:
            by_severity[risk.severity] = by_severity.get(risk.severity, 0) + 1

            if risk.domain not in by_domain:
                by_domain[risk.domain] = {"total": 0, "high": 0, "critical": 0}
            by_domain[risk.domain]["total"] += 1
            if risk.severity in ["high", "critical"]:
                by_domain[risk.domain][risk.severity] += 1

            if risk.integration_dependent:
                integration_dependent += 1

        return {
            "total": len(self.reasoning_store.risks),
            "by_severity": by_severity,
            "by_domain": by_domain,
            "integration_dependent": integration_dependent,
        }

    @cached_synthesis
    def analyze(self) -> Dict[str, Any]:
        """Perform full synthesis analysis."""
        # Run consistency checks
        consistency_issues = []
        consistency_issues.extend(self.check_cloud_provider_consistency())
        consistency_issues.extend(self.check_security_tool_consistency())
        consistency_issues.extend(self.check_identity_consistency())

        # Find related findings
        related_groups = self.find_related_findings()

        # Aggregate costs and risks
        cost_summary = self.aggregate_costs()
        risk_summary = self.aggregate_risks()

        # Get coverage summary
        coverage = self.coverage_analyzer.calculate_overall_coverage()

        return {
            "synthesis_timestamp": datetime.now().isoformat(),
            "consistency": {
                "issues": [
                    {
                        "id": issue.issue_id,
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "domains": issue.domains_involved,
                        "description": issue.description,
                        "recommendation": issue.recommendation,
                    }
                    for issue in consistency_issues
                ],
                "total_issues": len(consistency_issues),
                "high_severity_issues": sum(
                    1 for i in consistency_issues if i.severity == "high"
                ),
            },
            "related_findings": [
                {
                    "group_id": group.group_id,
                    "theme": group.theme,
                    "finding_count": len(group.findings),
                    "findings": group.findings,
                    "total_cost_range": {
                        "low": group.total_cost_low,
                        "high": group.total_cost_high,
                    },
                }
                for group in related_groups
            ],
            "cost_summary": cost_summary,
            "risk_summary": risk_summary,
            "coverage_summary": {
                "overall_percent": coverage["summary"]["overall_coverage_percent"],
                "critical_percent": coverage["summary"]["critical_coverage_percent"],
                "missing_critical_count": len(coverage["missing_critical"]),
            },
            "totals": {
                "facts": len(self.fact_store.facts),
                "gaps": len(self.fact_store.gaps),
                "risks": len(self.reasoning_store.risks),
                "work_items": len(self.reasoning_store.work_items),
                "strategic_considerations": len(self.reasoning_store.strategic_considerations),
                "recommendations": len(self.reasoning_store.recommendations),
            },
        }

    def get_executive_summary(self) -> str:
        """Generate executive summary text."""
        analysis = self.analyze()

        lines = [
            "# Executive Summary",
            "",
            "## Overview",
            f"- Total Facts Discovered: {analysis['totals']['facts']}",
            f"- Information Gaps: {analysis['totals']['gaps']}",
            f"- Risks Identified: {analysis['totals']['risks']}",
            f"- Work Items: {analysis['totals']['work_items']}",
            "",
            "## Coverage Quality",
            f"- Overall Coverage: {analysis['coverage_summary']['overall_percent']:.1f}%",
            f"- Critical Item Coverage: {analysis['coverage_summary']['critical_percent']:.1f}%",
            f"- Missing Critical Items: {analysis['coverage_summary']['missing_critical_count']}",
            "",
            "## Risk Summary",
        ]

        risk_sum = analysis["risk_summary"]
        lines.extend([
            f"- Critical Risks: {risk_sum['by_severity'].get('critical', 0)}",
            f"- High Risks: {risk_sum['by_severity'].get('high', 0)}",
            f"- Integration-Dependent: {risk_sum['integration_dependent']}",
            "",
            "## Cost Estimates",
        ])

        cost_sum = analysis["cost_summary"]
        lines.extend([
            f"- Total Range: ${cost_sum['total']['low']:,} - ${cost_sum['total']['high']:,}",
            "",
            "### By Phase:",
        ])

        for phase in ["Day_1", "Day_100", "Post_100"]:
            phase_data = cost_sum["by_phase"].get(phase, {})
            if phase_data.get("count", 0) > 0:
                lines.append(
                    f"  - {phase}: ${phase_data['low']:,} - ${phase_data['high']:,} "
                    f"({phase_data['count']} items)"
                )

        lines.append("")
        lines.append("### By Owner:")
        for owner, data in cost_sum["by_owner"].items():
            lines.append(
                f"  - {owner}: ${data['low']:,} - ${data['high']:,} ({data['count']} items)"
            )

        if analysis["consistency"]["total_issues"] > 0:
            lines.extend([
                "",
                "## Consistency Issues",
                f"- Total Issues: {analysis['consistency']['total_issues']}",
                f"- High Severity: {analysis['consistency']['high_severity_issues']}",
            ])

        if analysis["related_findings"]:
            lines.extend([
                "",
                "## Related Finding Themes",
            ])
            for group in analysis["related_findings"]:
                cost_range = group["total_cost_range"]
                lines.append(
                    f"- {group['theme'].replace('_', ' ').title()}: "
                    f"{group['finding_count']} findings "
                    f"(${cost_range['low']:,} - ${cost_range['high']:,})"
                )

        return "\n".join(lines)
