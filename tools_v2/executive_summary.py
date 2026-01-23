"""
Executive Summary Generator

Implements Points 96-99 of the Enhancement Plan:
96. Create one-page executive summary
97. Implement deal-breaker flagging
98. Add key investment areas summary
99. Build integration complexity score

Generates a deal-committee-ready executive summary from analysis results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class DealImpactLevel(Enum):
    """Level of impact on deal terms/valuation."""
    DEAL_BREAKER = "deal_breaker"         # Could kill the deal
    SIGNIFICANT = "significant"           # Could affect deal terms/price
    MODERATE = "moderate"                 # Requires attention but manageable
    MINOR = "minor"                       # Standard integration items


class IntegrationComplexity(Enum):
    """Overall IT integration complexity rating."""
    LOW = "low"              # Straightforward integration, minimal risk
    MODERATE = "moderate"    # Standard complexity, some challenges
    HIGH = "high"            # Significant complexity, careful planning needed
    VERY_HIGH = "very_high"  # Major complexity, extended timeline/budget
    CRITICAL = "critical"    # Extreme complexity, may affect deal viability


# Deal-breaker patterns - keywords and conditions that indicate potential deal issues
DEAL_BREAKER_PATTERNS = {
    "regulatory_compliance": [
        "regulatory breach", "non-compliance", "failed audit",
        "pending investigation", "license revocation", "gdpr violation",
        "hipaa violation", "pci violation", "sox failure"
    ],
    "security_incident": [
        "data breach", "ransomware", "active compromise",
        "ongoing attack", "critical vulnerability", "zero-day"
    ],
    "legal_ip": [
        "license dispute", "ip litigation", "patent issue",
        "source code ownership", "open source violation"
    ],
    "technical_debt": [
        "unsupported system", "eol critical", "no documentation",
        "single point of failure", "key person dependency"
    ],
    "contractual": [
        "change of control", "termination clause", "non-transferable",
        "exclusive agreement", "vendor lock-in"
    ]
}

# Investment area categorization
INVESTMENT_AREAS = {
    "infrastructure_modernization": {
        "keywords": ["eol", "refresh", "upgrade", "legacy", "modernize", "migrate"],
        "domains": ["infrastructure"]
    },
    "security_remediation": {
        "keywords": ["security", "vulnerability", "patch", "compliance", "audit"],
        "domains": ["cybersecurity"]
    },
    "network_connectivity": {
        "keywords": ["network", "connectivity", "wan", "vpn", "firewall"],
        "domains": ["network"]
    },
    "identity_integration": {
        "keywords": ["identity", "sso", "mfa", "active directory", "authentication"],
        "domains": ["identity_access"]
    },
    "application_portfolio": {
        "keywords": ["application", "migration", "integration", "replatform"],
        "domains": ["applications"]
    },
    "organizational_transition": {
        "keywords": ["tsa", "transition", "knowledge transfer", "staffing"],
        "domains": ["organization"]
    }
}

# Complexity scoring weights
COMPLEXITY_WEIGHTS = {
    "risk_severity": {
        "critical": 25,
        "high": 15,
        "medium": 5,
        "low": 1
    },
    "work_item_phase": {
        "Day_1": 20,
        "Day_30": 15,
        "Day_100": 10,
        "Post_100": 5
    },
    "coverage_gap_penalty": 2,  # Per percentage point below 80%
    "deal_breaker_penalty": 30,
    "consistency_issue_penalty": 10
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DealBreaker:
    """A potential deal-breaking finding."""
    finding_id: str
    finding_type: str  # risk, gap, consistency_issue
    title: str
    description: str
    category: str
    severity: str
    impact_on_deal: str
    recommended_action: str
    supporting_facts: List[str]


@dataclass
class InvestmentArea:
    """A key area requiring investment attention."""
    area_name: str
    priority: str  # critical, high, medium, low
    domains_involved: List[str]
    risk_count: int
    work_item_count: int
    key_findings: List[str]
    rationale: str


@dataclass
class IntegrationScore:
    """Overall integration complexity score and breakdown."""
    overall_score: int  # 0-100
    complexity_level: IntegrationComplexity
    risk_score: int
    coverage_score: int
    work_item_score: int
    special_factors_score: int
    breakdown: Dict[str, Any]
    recommendation: str


@dataclass
class ExecutiveSummary:
    """Complete executive summary for deal committee."""
    generated_at: str
    target_name: str
    deal_type: str

    # Key metrics
    facts_count: int
    gaps_count: int
    risks_count: int
    work_items_count: int
    coverage_percent: float

    # Deal-breakers
    deal_breakers: List[DealBreaker]
    has_deal_breakers: bool

    # Investment areas
    investment_areas: List[InvestmentArea]
    top_investment_priority: str

    # Integration complexity
    integration_score: IntegrationScore

    # Risk summary
    critical_risks: List[Dict[str, str]]
    high_risks: List[Dict[str, str]]

    # Cost summary
    total_cost_low: int
    total_cost_high: int
    day_1_cost_low: int
    day_1_cost_high: int

    # Narrative sections
    headline: str
    key_findings: List[str]
    immediate_actions: List[str]
    open_questions: List[str]


# =============================================================================
# EXECUTIVE SUMMARY GENERATOR
# =============================================================================

class ExecutiveSummaryGenerator:
    """
    Generates deal-committee-ready executive summaries.

    Implements Points 96-99 of the enhancement plan.
    """

    def __init__(
        self,
        fact_store=None,
        reasoning_store=None,
        synthesis_results: Optional[Dict[str, Any]] = None
    ):
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store
        self.synthesis_results = synthesis_results or {}

    def generate(
        self,
        target_name: str = "Target Company",
        deal_type: str = "acquisition"
    ) -> ExecutiveSummary:
        """
        Generate a complete executive summary.

        Args:
            target_name: Name of the target company
            deal_type: Type of deal (acquisition, carveout, merger)

        Returns:
            ExecutiveSummary with all sections populated
        """
        # Gather base metrics
        facts_count = len(self.fact_store.facts) if self.fact_store else 0
        gaps_count = len(self.fact_store.gaps) if self.fact_store else 0
        risks = list(self.reasoning_store.risks) if self.reasoning_store else []
        work_items = list(self.reasoning_store.work_items) if self.reasoning_store else []

        # Calculate coverage
        coverage_percent = self._calculate_coverage_percent()

        # Identify deal-breakers (Point 97)
        deal_breakers = self._identify_deal_breakers()

        # Identify investment areas (Point 98)
        investment_areas = self._identify_investment_areas()

        # Calculate integration complexity (Point 99)
        integration_score = self._calculate_integration_complexity(
            deal_breakers, coverage_percent
        )

        # Get risk summary
        critical_risks, high_risks = self._get_risk_summary()

        # Get cost summary
        cost_summary = self._get_cost_summary()

        # Generate narrative elements (Point 96)
        headline = self._generate_headline(
            integration_score.complexity_level,
            len(deal_breakers),
            len(critical_risks)
        )
        key_findings = self._generate_key_findings()
        immediate_actions = self._generate_immediate_actions(deal_breakers)
        open_questions = self._get_open_questions()

        return ExecutiveSummary(
            generated_at=datetime.now().isoformat(),
            target_name=target_name,
            deal_type=deal_type,
            facts_count=facts_count,
            gaps_count=gaps_count,
            risks_count=len(risks),
            work_items_count=len(work_items),
            coverage_percent=coverage_percent,
            deal_breakers=deal_breakers,
            has_deal_breakers=len(deal_breakers) > 0,
            investment_areas=investment_areas,
            top_investment_priority=investment_areas[0].area_name if investment_areas else "None identified",
            integration_score=integration_score,
            critical_risks=critical_risks,
            high_risks=high_risks,
            total_cost_low=cost_summary["total"]["low"],
            total_cost_high=cost_summary["total"]["high"],
            day_1_cost_low=cost_summary["day_1"]["low"],
            day_1_cost_high=cost_summary["day_1"]["high"],
            headline=headline,
            key_findings=key_findings,
            immediate_actions=immediate_actions,
            open_questions=open_questions
        )

    def _calculate_coverage_percent(self) -> float:
        """Calculate overall coverage percentage."""
        if self.synthesis_results and "coverage_summary" in self.synthesis_results:
            return self.synthesis_results["coverage_summary"].get("overall_percent", 0.0)
        # Fallback calculation
        if self.fact_store:
            facts = len(self.fact_store.facts)
            gaps = len(self.fact_store.gaps)
            total = facts + gaps
            return (facts / total * 100) if total > 0 else 0.0
        return 0.0

    def _identify_deal_breakers(self) -> List[DealBreaker]:
        """
        Identify potential deal-breaking findings.

        Implements Point 97: Deal-breaker flagging.
        """
        deal_breakers = []

        if not self.reasoning_store:
            return deal_breakers

        # Check critical risks
        for risk in self.reasoning_store.risks:
            if risk.severity == "critical":
                # Check if matches deal-breaker patterns
                category = self._match_deal_breaker_category(
                    risk.title + " " + risk.description
                )
                if category:
                    deal_breakers.append(DealBreaker(
                        finding_id=risk.finding_id,
                        finding_type="risk",
                        title=risk.title,
                        description=risk.description,
                        category=category,
                        severity="critical",
                        impact_on_deal=self._assess_deal_impact(category, risk),
                        recommended_action=self._get_deal_breaker_action(category),
                        supporting_facts=risk.based_on_facts
                    ))

        # Check high-severity risks with specific patterns
        for risk in self.reasoning_store.risks:
            if risk.severity == "high":
                category = self._match_deal_breaker_category(
                    risk.title + " " + risk.description
                )
                if category in ["regulatory_compliance", "security_incident", "legal_ip"]:
                    deal_breakers.append(DealBreaker(
                        finding_id=risk.finding_id,
                        finding_type="risk",
                        title=risk.title,
                        description=risk.description,
                        category=category,
                        severity="high",
                        impact_on_deal=self._assess_deal_impact(category, risk),
                        recommended_action=self._get_deal_breaker_action(category),
                        supporting_facts=risk.based_on_facts
                    ))

        # Check gaps for deal-breaker indicators
        if self.fact_store:
            for gap in self.fact_store.gaps:
                gap_text = gap.description if hasattr(gap, 'description') else str(gap)
                category = self._match_deal_breaker_category(gap_text)
                if category in ["regulatory_compliance", "legal_ip"]:
                    deal_breakers.append(DealBreaker(
                        finding_id=gap.gap_id if hasattr(gap, 'gap_id') else "G-unknown",
                        finding_type="gap",
                        title=f"Missing information: {gap.description[:50]}..." if len(gap.description) > 50 else gap.description,
                        description=gap.description,
                        category=category,
                        severity="high",
                        impact_on_deal="Cannot assess risk without this information",
                        recommended_action="Request documentation immediately",
                        supporting_facts=[]
                    ))

        return deal_breakers

    def _match_deal_breaker_category(self, text: str) -> Optional[str]:
        """Match text against deal-breaker patterns."""
        text_lower = text.lower()
        for category, patterns in DEAL_BREAKER_PATTERNS.items():
            if any(pattern in text_lower for pattern in patterns):
                return category
        return None

    def _assess_deal_impact(self, category: str, risk) -> str:
        """Assess the impact on deal terms."""
        impacts = {
            "regulatory_compliance": "May require compliance remediation before close or indemnification",
            "security_incident": "Requires immediate security assessment and potential breach disclosure",
            "legal_ip": "May affect IP ownership or licensing terms in the deal",
            "technical_debt": "May require significant post-close investment or price adjustment",
            "contractual": "May require vendor consent or contract renegotiation"
        }
        return impacts.get(category, "Requires further assessment")

    def _get_deal_breaker_action(self, category: str) -> str:
        """Get recommended action for deal-breaker category."""
        actions = {
            "regulatory_compliance": "Engage legal counsel; request compliance audit reports",
            "security_incident": "Request incident reports; engage security assessor",
            "legal_ip": "Request IP ownership documentation; engage IP counsel",
            "technical_debt": "Request detailed technical assessment; quantify remediation",
            "contractual": "Request all vendor contracts; identify change-of-control clauses"
        }
        return actions.get(category, "Escalate to deal team for assessment")

    def _identify_investment_areas(self) -> List[InvestmentArea]:
        """
        Identify key areas requiring investment attention.

        Implements Point 98: Key investment areas summary.
        """
        areas = []

        if not self.reasoning_store:
            return areas

        # Count risks and work items by investment area
        area_metrics = {area: {"risk_count": 0, "wi_count": 0, "findings": []}
                       for area in INVESTMENT_AREAS.keys()}

        # Analyze risks
        for risk in self.reasoning_store.risks:
            for area_name, area_config in INVESTMENT_AREAS.items():
                if risk.domain in area_config["domains"]:
                    area_metrics[area_name]["risk_count"] += 1
                    if risk.severity in ["critical", "high"]:
                        area_metrics[area_name]["findings"].append(risk.title)
                elif any(kw in risk.title.lower() or kw in risk.description.lower()
                        for kw in area_config["keywords"]):
                    area_metrics[area_name]["risk_count"] += 1

        # Analyze work items
        for wi in self.reasoning_store.work_items:
            for area_name, area_config in INVESTMENT_AREAS.items():
                if wi.domain in area_config["domains"]:
                    area_metrics[area_name]["wi_count"] += 1
                elif any(kw in wi.title.lower() or kw in wi.description.lower()
                        for kw in area_config["keywords"]):
                    area_metrics[area_name]["wi_count"] += 1

        # Create investment areas with priority
        for area_name, metrics in area_metrics.items():
            if metrics["risk_count"] > 0 or metrics["wi_count"] > 0:
                priority = self._calculate_investment_priority(metrics)
                areas.append(InvestmentArea(
                    area_name=area_name.replace("_", " ").title(),
                    priority=priority,
                    domains_involved=INVESTMENT_AREAS[area_name]["domains"],
                    risk_count=metrics["risk_count"],
                    work_item_count=metrics["wi_count"],
                    key_findings=metrics["findings"][:3],  # Top 3 findings
                    rationale=self._generate_investment_rationale(area_name, metrics)
                ))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        areas.sort(key=lambda a: priority_order.get(a.priority, 4))

        return areas

    def _calculate_investment_priority(self, metrics: Dict) -> str:
        """Calculate investment priority based on metrics."""
        score = metrics["risk_count"] * 3 + metrics["wi_count"]
        if score >= 10:
            return "critical"
        elif score >= 5:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_investment_rationale(self, area_name: str, metrics: Dict) -> str:
        """Generate rationale for investment area."""
        risk_text = f"{metrics['risk_count']} risks" if metrics['risk_count'] > 0 else ""
        wi_text = f"{metrics['wi_count']} work items" if metrics['wi_count'] > 0 else ""
        parts = [p for p in [risk_text, wi_text] if p]
        return f"{area_name.replace('_', ' ').title()} requires attention: {' and '.join(parts)} identified"

    def _calculate_integration_complexity(
        self,
        deal_breakers: List[DealBreaker],
        coverage_percent: float
    ) -> IntegrationScore:
        """
        Calculate overall integration complexity score.

        Implements Point 99: Integration complexity score.
        """
        # Initialize scores
        risk_score = 0
        coverage_score = 0
        work_item_score = 0
        special_factors_score = 0

        breakdown = {
            "risk_contribution": {},
            "work_item_contribution": {},
            "coverage_contribution": 0,
            "special_factors": []
        }

        # Risk scoring
        if self.reasoning_store:
            for risk in self.reasoning_store.risks:
                weight = COMPLEXITY_WEIGHTS["risk_severity"].get(risk.severity, 0)
                risk_score += weight
                severity = risk.severity
                breakdown["risk_contribution"][severity] = \
                    breakdown["risk_contribution"].get(severity, 0) + weight

        # Work item scoring
        if self.reasoning_store:
            for wi in self.reasoning_store.work_items:
                weight = COMPLEXITY_WEIGHTS["work_item_phase"].get(wi.phase, 5)
                work_item_score += weight
                phase = wi.phase
                breakdown["work_item_contribution"][phase] = \
                    breakdown["work_item_contribution"].get(phase, 0) + weight

        # Coverage penalty
        if coverage_percent < 80:
            coverage_penalty = (80 - coverage_percent) * COMPLEXITY_WEIGHTS["coverage_gap_penalty"]
            coverage_score = int(coverage_penalty)
            breakdown["coverage_contribution"] = coverage_score

        # Deal-breaker penalty
        deal_breaker_penalty = len(deal_breakers) * COMPLEXITY_WEIGHTS["deal_breaker_penalty"]
        special_factors_score += deal_breaker_penalty
        if deal_breakers:
            breakdown["special_factors"].append(f"Deal-breakers: +{deal_breaker_penalty}")

        # Consistency issues penalty
        if self.synthesis_results:
            consistency = self.synthesis_results.get("consistency", {})
            issue_count = consistency.get("total_issues", 0)
            consistency_penalty = issue_count * COMPLEXITY_WEIGHTS["consistency_issue_penalty"]
            special_factors_score += consistency_penalty
            if issue_count > 0:
                breakdown["special_factors"].append(f"Consistency issues: +{consistency_penalty}")

        # Calculate total (cap at 100)
        total_raw = risk_score + work_item_score + coverage_score + special_factors_score
        overall_score = min(100, total_raw)

        # Determine complexity level
        complexity_level = self._score_to_complexity_level(overall_score, len(deal_breakers))

        # Generate recommendation
        recommendation = self._generate_complexity_recommendation(
            complexity_level, deal_breakers, coverage_percent
        )

        return IntegrationScore(
            overall_score=overall_score,
            complexity_level=complexity_level,
            risk_score=risk_score,
            coverage_score=coverage_score,
            work_item_score=work_item_score,
            special_factors_score=special_factors_score,
            breakdown=breakdown,
            recommendation=recommendation
        )

    def _score_to_complexity_level(
        self,
        score: int,
        deal_breaker_count: int
    ) -> IntegrationComplexity:
        """Convert numeric score to complexity level."""
        if deal_breaker_count > 2 or score >= 80:
            return IntegrationComplexity.CRITICAL
        elif deal_breaker_count > 0 or score >= 60:
            return IntegrationComplexity.VERY_HIGH
        elif score >= 40:
            return IntegrationComplexity.HIGH
        elif score >= 20:
            return IntegrationComplexity.MODERATE
        else:
            return IntegrationComplexity.LOW

    def _generate_complexity_recommendation(
        self,
        level: IntegrationComplexity,
        deal_breakers: List[DealBreaker],
        coverage: float
    ) -> str:
        """Generate recommendation based on complexity."""
        recommendations = {
            IntegrationComplexity.CRITICAL: (
                "Critical integration complexity detected. Recommend extended due diligence, "
                "potential deal structure modifications, and contingency planning."
            ),
            IntegrationComplexity.VERY_HIGH: (
                "Very high integration complexity. Recommend detailed integration planning, "
                "dedicated PMO, and sufficient budget contingency."
            ),
            IntegrationComplexity.HIGH: (
                "High integration complexity. Recommend thorough Day 1 planning and "
                "clear ownership of critical work items."
            ),
            IntegrationComplexity.MODERATE: (
                "Moderate integration complexity. Standard integration approach should suffice "
                "with focus on identified risk areas."
            ),
            IntegrationComplexity.LOW: (
                "Low integration complexity. Straightforward integration expected with "
                "minimal special considerations."
            )
        }

        base = recommendations.get(level, "")

        if deal_breakers:
            base += f" Note: {len(deal_breakers)} potential deal-breaking item(s) require immediate attention."

        if coverage < 50:
            base += " Warning: Low documentation coverage increases uncertainty."

        return base

    def _get_risk_summary(self) -> Tuple[List[Dict], List[Dict]]:
        """Get critical and high risk summaries."""
        critical = []
        high = []

        if self.reasoning_store:
            for risk in self.reasoning_store.risks:
                summary = {
                    "id": risk.finding_id,
                    "title": risk.title,
                    "domain": risk.domain
                }
                if risk.severity == "critical":
                    critical.append(summary)
                elif risk.severity == "high":
                    high.append(summary)

        return critical[:5], high[:10]  # Limit for executive summary

    def _get_cost_summary(self) -> Dict[str, Dict[str, int]]:
        """Get cost summary by phase."""
        summary = {
            "total": {"low": 0, "high": 0},
            "day_1": {"low": 0, "high": 0}
        }

        if self.synthesis_results and "cost_summary" in self.synthesis_results:
            cost_data = self.synthesis_results["cost_summary"]
            summary["total"] = cost_data.get("total", summary["total"])
            summary["day_1"] = cost_data.get("by_phase", {}).get("Day_1", summary["day_1"])

        return summary

    def _generate_headline(
        self,
        complexity: IntegrationComplexity,
        deal_breaker_count: int,
        critical_risk_count: int
    ) -> str:
        """Generate the executive summary headline."""
        if deal_breaker_count > 0:
            return f"IT Due Diligence: {deal_breaker_count} potential deal-impacting item(s) identified"
        elif complexity == IntegrationComplexity.CRITICAL:
            return "IT Due Diligence: Critical integration complexity - requires careful review"
        elif complexity == IntegrationComplexity.VERY_HIGH:
            return "IT Due Diligence: Significant IT integration requirements identified"
        elif critical_risk_count > 0:
            return f"IT Due Diligence: {critical_risk_count} critical risk(s) require attention"
        else:
            return "IT Due Diligence: Standard integration complexity"

    def _generate_key_findings(self) -> List[str]:
        """Generate list of key findings for executive summary."""
        findings = []

        if not self.reasoning_store:
            return ["Analysis pending - no findings available"]

        # Add critical risks
        critical_risks = [r for r in self.reasoning_store.risks if r.severity == "critical"]
        for risk in critical_risks[:2]:
            findings.append(f"[CRITICAL] {risk.title}")

        # Add high-severity risks
        high_risks = [r for r in self.reasoning_store.risks if r.severity == "high"]
        for risk in high_risks[:3]:
            findings.append(f"[HIGH] {risk.title}")

        # Add strategic considerations
        for sc in list(self.reasoning_store.strategic_considerations)[:2]:
            findings.append(f"[STRATEGIC] {sc.title}")

        return findings[:7]  # Limit to 7 key findings

    def _generate_immediate_actions(self, deal_breakers: List[DealBreaker]) -> List[str]:
        """Generate list of immediate actions."""
        actions = []

        # Actions for deal-breakers
        for db in deal_breakers[:3]:
            actions.append(f"Address {db.category.replace('_', ' ')}: {db.recommended_action}")

        # Add standard Day 1 actions if no deal-breakers
        if not deal_breakers and self.reasoning_store:
            day_1_items = [wi for wi in self.reasoning_store.work_items if wi.phase == "Day_1"]
            for wi in day_1_items[:3]:
                actions.append(f"Day 1 Required: {wi.title}")

        if not actions:
            actions.append("No immediate actions required - proceed with standard integration planning")

        return actions

    def _get_open_questions(self) -> List[str]:
        """Get high-priority open questions from gaps."""
        questions = []

        if self.fact_store:
            # Get gaps and convert to questions
            gaps = list(self.fact_store.gaps)
            for gap in gaps[:5]:
                description = gap.description if hasattr(gap, 'description') else str(gap)
                questions.append(f"Request: {description[:100]}...")

        return questions

    def to_markdown(self, summary: ExecutiveSummary) -> str:
        """
        Convert executive summary to markdown format.

        Implements Point 96: One-page executive summary.
        """
        lines = [
            f"# IT Due Diligence Executive Summary",
            f"**Target:** {summary.target_name}  ",
            f"**Deal Type:** {summary.deal_type.title()}  ",
            f"**Generated:** {summary.generated_at[:10]}",
            "",
            "---",
            "",
            f"## {summary.headline}",
            "",
        ]

        # Deal-breakers section (if any)
        if summary.has_deal_breakers:
            lines.extend([
                "### DEAL IMPACT ITEMS",
                "",
            ])
            for db in summary.deal_breakers:
                lines.append(f"- **[{db.severity.upper()}]** {db.title}")
                lines.append(f"  - Category: {db.category.replace('_', ' ').title()}")
                lines.append(f"  - Action: {db.recommended_action}")
            lines.append("")

        # Key metrics box
        lines.extend([
            "### Key Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Facts Discovered | {summary.facts_count} |",
            f"| Information Gaps | {summary.gaps_count} |",
            f"| Risks Identified | {summary.risks_count} |",
            f"| Work Items | {summary.work_items_count} |",
            f"| Coverage | {summary.coverage_percent:.0f}% |",
            "",
        ])

        # Integration complexity
        lines.extend([
            "### Integration Complexity",
            "",
            f"**Overall Score:** {summary.integration_score.overall_score}/100 "
            f"({summary.integration_score.complexity_level.value.upper()})",
            "",
            f"> {summary.integration_score.recommendation}",
            "",
        ])

        # Key findings
        lines.extend([
            "### Key Findings",
            "",
        ])
        for finding in summary.key_findings:
            lines.append(f"- {finding}")
        lines.append("")

        # Investment areas
        if summary.investment_areas:
            lines.extend([
                "### Key Investment Areas",
                "",
            ])
            for area in summary.investment_areas[:4]:
                lines.append(
                    f"- **{area.area_name}** ({area.priority.upper()}): "
                    f"{area.risk_count} risks, {area.work_item_count} work items"
                )
            lines.append("")

        # Cost summary
        lines.extend([
            "### Cost Estimate Summary",
            "",
            f"- **Total Range:** ${summary.total_cost_low:,} - ${summary.total_cost_high:,}",
            f"- **Day 1 Critical:** ${summary.day_1_cost_low:,} - ${summary.day_1_cost_high:,}",
            "",
        ])

        # Immediate actions
        lines.extend([
            "### Immediate Actions",
            "",
        ])
        for i, action in enumerate(summary.immediate_actions, 1):
            lines.append(f"{i}. {action}")
        lines.append("")

        # Open questions
        if summary.open_questions:
            lines.extend([
                "### Open Questions / VDR Requests",
                "",
            ])
            for q in summary.open_questions[:5]:
                lines.append(f"- {q}")
            lines.append("")

        lines.extend([
            "---",
            f"*This summary is generated from {summary.facts_count} facts and {summary.risks_count} risks. "
            "Human review is required before distribution.*",
        ])

        return "\n".join(lines)

    def to_dict(self, summary: ExecutiveSummary) -> Dict[str, Any]:
        """Convert executive summary to dictionary format."""
        return {
            "metadata": {
                "generated_at": summary.generated_at,
                "target_name": summary.target_name,
                "deal_type": summary.deal_type
            },
            "metrics": {
                "facts_count": summary.facts_count,
                "gaps_count": summary.gaps_count,
                "risks_count": summary.risks_count,
                "work_items_count": summary.work_items_count,
                "coverage_percent": summary.coverage_percent
            },
            "deal_breakers": {
                "has_deal_breakers": summary.has_deal_breakers,
                "count": len(summary.deal_breakers),
                "items": [
                    {
                        "id": db.finding_id,
                        "title": db.title,
                        "category": db.category,
                        "severity": db.severity,
                        "impact": db.impact_on_deal,
                        "action": db.recommended_action
                    }
                    for db in summary.deal_breakers
                ]
            },
            "investment_areas": [
                {
                    "name": area.area_name,
                    "priority": area.priority,
                    "risks": area.risk_count,
                    "work_items": area.work_item_count
                }
                for area in summary.investment_areas
            ],
            "integration_complexity": {
                "score": summary.integration_score.overall_score,
                "level": summary.integration_score.complexity_level.value,
                "recommendation": summary.integration_score.recommendation,
                "breakdown": summary.integration_score.breakdown
            },
            "costs": {
                "total_low": summary.total_cost_low,
                "total_high": summary.total_cost_high,
                "day_1_low": summary.day_1_cost_low,
                "day_1_high": summary.day_1_cost_high
            },
            "narrative": {
                "headline": summary.headline,
                "key_findings": summary.key_findings,
                "immediate_actions": summary.immediate_actions,
                "open_questions": summary.open_questions
            }
        }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("=== Executive Summary Generator Test ===\n")

    # Create mock stores for testing
    from dataclasses import dataclass as dc, field as f

    @dc
    class MockFact:
        fact_id: str
        domain: str
        fact: str

    @dc
    class MockGap:
        gap_id: str
        description: str

    @dc
    class MockRisk:
        finding_id: str
        domain: str
        title: str
        description: str
        severity: str
        based_on_facts: List[str] = f(default_factory=list)
        integration_dependent: bool = False

    @dc
    class MockWorkItem:
        finding_id: str
        domain: str
        title: str
        description: str
        phase: str
        cost_estimate: str
        triggered_by_risks: List[str] = f(default_factory=list)

    @dc
    class MockStrategicConsideration:
        finding_id: str
        domain: str
        title: str

    class MockFactStore:
        def __init__(self):
            self.facts = [
                MockFact("F-001", "infrastructure", "VMware 6.5 in use"),
                MockFact("F-002", "infrastructure", "50 servers in datacenter"),
                MockFact("F-003", "cybersecurity", "No MFA on VPN"),
            ]
            self.gaps = [
                MockGap("G-001", "DR plan documentation missing"),
                MockGap("G-002", "License audit results not provided"),
            ]

    class MockReasoningStore:
        def __init__(self):
            self.risks = [
                MockRisk("R-001", "infrastructure", "EOL VMware Platform",
                        "VMware 6.5 reaches end of support", "critical",
                        ["F-001"]),
                MockRisk("R-002", "cybersecurity", "MFA Gap on Remote Access",
                        "VPN lacks multi-factor authentication", "high",
                        ["F-003"]),
                MockRisk("R-003", "cybersecurity", "Potential Data Breach Risk",
                        "Security controls insufficient", "critical",
                        ["F-003"]),
            ]
            self.work_items = [
                MockWorkItem("WI-001", "infrastructure", "Upgrade VMware",
                            "Migrate to VMware 7.0", "Day_100", "100k_to_500k",
                            ["R-001"]),
                MockWorkItem("WI-002", "cybersecurity", "Implement MFA",
                            "Deploy MFA on VPN", "Day_1", "25k_to_100k",
                            ["R-002"]),
            ]
            self.strategic_considerations = [
                MockStrategicConsideration("SC-001", "infrastructure",
                                          "Cloud migration opportunity")
            ]
            self.recommendations = []

    # Create generator
    fact_store = MockFactStore()
    reasoning_store = MockReasoningStore()

    generator = ExecutiveSummaryGenerator(
        fact_store=fact_store,
        reasoning_store=reasoning_store,
        synthesis_results={
            "coverage_summary": {"overall_percent": 65.0},
            "cost_summary": {
                "total": {"low": 125000, "high": 600000},
                "by_phase": {
                    "Day_1": {"low": 25000, "high": 100000},
                    "Day_100": {"low": 100000, "high": 500000}
                }
            },
            "consistency": {"total_issues": 1}
        }
    )

    # Generate summary
    summary = generator.generate(
        target_name="Acme Corp",
        deal_type="acquisition"
    )

    # Print markdown version
    markdown = generator.to_markdown(summary)
    print(markdown)
    print("\n" + "="*60 + "\n")

    # Print key metrics
    print("Key Summary Metrics:")
    print(f"  Has Deal Breakers: {summary.has_deal_breakers}")
    print(f"  Deal Breakers Count: {len(summary.deal_breakers)}")
    print(f"  Integration Score: {summary.integration_score.overall_score}/100")
    print(f"  Complexity Level: {summary.integration_score.complexity_level.value}")
    print(f"  Investment Areas: {len(summary.investment_areas)}")
    print()

    print("=== Executive Summary Generator Test Complete ===")
