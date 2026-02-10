"""
Anchored Estimation Engine

Combines deterministic cost anchors with fact-based adjustments.

Philosophy:
1. ANCHORS: Market-benchmarked costs (from lookup tables)
2. FACTS: What we know about this specific environment
3. ADJUSTMENTS: How facts impact the anchors (predefined rules)
4. RATIONALE: Why each adjustment was made (traceable to facts)

This gives us:
- Defensible starting points (not pulled from thin air)
- Company-specific estimates (not generic buckets)
- Transparent reasoning (every adjustment tied to a fact)
- Reproducible results (same facts = same adjustments)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
import json
import hashlib

from tools_v2.deterministic_estimator import (
    DeterministicEstimator,
)


# =============================================================================
# ADJUSTMENT RULES - Facts that impact costs
# =============================================================================

@dataclass
class AdjustmentRule:
    """A rule that adjusts an anchor based on a fact pattern."""
    rule_id: str
    name: str
    description: str
    fact_patterns: List[str]  # Keywords/patterns to look for in facts
    affected_categories: List[str]  # Which cost categories this affects
    adjustment_factor: float  # Multiplier (0.7 = -30%, 1.3 = +30%)
    adjustment_type: str  # "multiply" or "add_fixed"
    fixed_amount: float = 0  # For add_fixed type
    rationale_template: str = ""  # Explanation template


# Predefined adjustment rules based on common IT DD patterns
ADJUSTMENT_RULES = [
    # Cloud maturity adjustments
    AdjustmentRule(
        rule_id="ADJ-CLOUD-HIGH",
        name="High Cloud Adoption",
        description="Already >60% cloud reduces infrastructure migration cost",
        fact_patterns=["cloud", ">60%", "aws", "azure", "gcp", "saas", "cloud-first"],
        affected_categories=["infrastructure_migration", "dc_migration", "hosting"],
        adjustment_factor=0.7,
        adjustment_type="multiply",
        rationale_template="Cloud adoption >60% reduces infrastructure migration scope by ~30%"
    ),
    AdjustmentRule(
        rule_id="ADJ-CLOUD-LOW",
        name="Low Cloud Adoption",
        description="<30% cloud increases migration complexity",
        fact_patterns=["on-prem", "legacy", "mainframe", "<30% cloud", "data center heavy"],
        affected_categories=["infrastructure_migration", "dc_migration"],
        adjustment_factor=1.25,
        adjustment_type="multiply",
        rationale_template="Heavy on-prem footprint increases migration complexity by ~25%"
    ),

    # ERP complexity adjustments
    AdjustmentRule(
        rule_id="ADJ-ERP-DUAL",
        name="Dual ERP Complexity",
        description="Multiple ERP systems increase integration/separation risk",
        fact_patterns=["dual erp", "two erp", "multiple erp", "sap and oracle",
                       "netsuite and sap", "both erp"],
        affected_categories=["erp_migration", "application_separation", "integration"],
        adjustment_factor=1.35,
        adjustment_type="multiply",
        rationale_template="Dual ERP environment adds ~35% complexity to application workstreams"
    ),
    AdjustmentRule(
        rule_id="ADJ-ERP-MODERN",
        name="Modern ERP",
        description="Cloud-native ERP simplifies separation",
        fact_patterns=["netsuite", "workday", "saas erp", "cloud erp", "s/4hana cloud"],
        affected_categories=["erp_migration", "application_separation"],
        adjustment_factor=0.85,
        adjustment_type="multiply",
        rationale_template="Cloud-native ERP reduces separation complexity by ~15%"
    ),
    AdjustmentRule(
        rule_id="ADJ-ERP-LEGACY",
        name="Legacy ERP",
        description="End-of-support ERP increases risk and cost",
        fact_patterns=["ecc 6.0", "end of support", "unsupported", "legacy erp",
                       "oracle ebs", "jd edwards"],
        affected_categories=["erp_migration", "application_separation", "risk_contingency"],
        adjustment_factor=1.4,
        adjustment_type="multiply",
        rationale_template="Legacy ERP (approaching/past end of support) adds ~40% risk premium"
    ),

    # Security posture adjustments
    AdjustmentRule(
        rule_id="ADJ-SEC-MATURE",
        name="Mature Security Posture",
        description="Modern security stack reduces remediation needs",
        fact_patterns=["soc 2", "iso 27001", "modern security", "crowdstrike",
                       "sentinelone", "zero trust", "mfa deployed"],
        affected_categories=["security_remediation", "compliance"],
        adjustment_factor=0.75,
        adjustment_type="multiply",
        rationale_template="Mature security posture reduces remediation scope by ~25%"
    ),
    AdjustmentRule(
        rule_id="ADJ-SEC-GAPS",
        name="Security Gaps",
        description="Security deficiencies require remediation investment",
        fact_patterns=["no mfa", "no siem", "security gaps", "audit findings",
                       "compliance issues", "no edr"],
        affected_categories=["security_remediation", "compliance", "risk_contingency"],
        adjustment_factor=1.3,
        adjustment_type="multiply",
        rationale_template="Security gaps require ~30% additional remediation investment"
    ),

    # Outsourcing adjustments
    AdjustmentRule(
        rule_id="ADJ-OUTSOURCE-HIGH",
        name="High Outsourcing",
        description=">40% outsourced increases MSP transition complexity",
        fact_patterns=[">40% outsourced", "heavily outsourced", "msp dependent",
                       "managed services", "contractor heavy"],
        affected_categories=["msp_transition", "tsa", "knowledge_transfer"],
        adjustment_factor=1.2,
        adjustment_type="multiply",
        rationale_template="High outsourcing (>40%) increases MSP transition risk by ~20%"
    ),
    AdjustmentRule(
        rule_id="ADJ-OUTSOURCE-LOW",
        name="Strong Internal Team",
        description="<15% outsourced simplifies transition",
        fact_patterns=["internal team", "<15% outsourced", "in-house", "low outsourcing"],
        affected_categories=["msp_transition", "knowledge_transfer"],
        adjustment_factor=0.85,
        adjustment_type="multiply",
        rationale_template="Strong internal team reduces transition risk by ~15%"
    ),

    # Data center constraints
    AdjustmentRule(
        rule_id="ADJ-DC-LEASE",
        name="DC Lease Constraint",
        description="Non-cancellable lease creates stranded cost",
        fact_patterns=["non-cancellable", "lease constraint", "lease obligation",
                       "12 month lease", "long-term lease"],
        affected_categories=["dc_migration", "stranded_cost"],
        adjustment_factor=1.0,
        adjustment_type="add_fixed",
        fixed_amount=1_000_000,  # Add $1M stranded cost risk
        rationale_template="DC lease constraint adds ~$1M stranded cost risk"
    ),
    AdjustmentRule(
        rule_id="ADJ-DC-OWNED",
        name="Owned Data Center",
        description="Owned facility has disposal/transition complexity",
        fact_patterns=["owned data center", "owned facility", "company-owned dc"],
        affected_categories=["dc_migration", "infrastructure_separation"],
        adjustment_factor=1.15,
        adjustment_type="multiply",
        rationale_template="Owned DC facility adds ~15% disposal/transition complexity"
    ),

    # Tool overlap (synergy opportunity)
    AdjustmentRule(
        rule_id="ADJ-TOOL-OVERLAP",
        name="Tool Rationalization Opportunity",
        description="Overlapping tools present consolidation savings",
        fact_patterns=["dual tool", "overlapping", "both sentinelone and crowdstrike",
                       "multiple siem", "redundant tools"],
        affected_categories=["synergy_opportunity", "tool_rationalization"],
        adjustment_factor=0.9,
        adjustment_type="multiply",
        rationale_template="Tool overlap presents ~10% rationalization opportunity in Year 2+"
    ),

    # Shared services complexity
    AdjustmentRule(
        rule_id="ADJ-SHARED-HEAVY",
        name="Heavy Shared Services",
        description="Deep shared services entanglement increases TSA scope",
        fact_patterns=["shared services", "parent identity", "parent email",
                       "corporate it", "parent-provided", "shared infrastructure"],
        affected_categories=["tsa", "identity_separation", "email_migration"],
        adjustment_factor=1.25,
        adjustment_type="multiply",
        rationale_template="Deep shared services entanglement adds ~25% to separation workstreams"
    ),

    # Geographic complexity
    AdjustmentRule(
        rule_id="ADJ-GEO-GLOBAL",
        name="Global Operations",
        description="Multi-region operations add complexity",
        fact_patterns=["global", "multi-region", "international", "apac", "emea",
                       "multiple countries", "data residency"],
        affected_categories=["infrastructure_migration", "compliance", "network"],
        adjustment_factor=1.2,
        adjustment_type="multiply",
        rationale_template="Global operations add ~20% complexity for data residency and regional requirements"
    ),

    # Employee count adjustments (scale factors)
    AdjustmentRule(
        rule_id="ADJ-SCALE-LARGE",
        name="Large Scale (>5000 employees)",
        description="Scale increases project complexity",
        fact_patterns=[">5000 employees", ">5,000 employees", "large organization",
                       "enterprise scale"],
        affected_categories=["identity_separation", "email_migration", "training"],
        adjustment_factor=1.15,
        adjustment_type="multiply",
        rationale_template="Large scale (>5000 employees) adds ~15% to user-impacting workstreams"
    ),
    AdjustmentRule(
        rule_id="ADJ-SCALE-SMALL",
        name="Small Scale (<500 employees)",
        description="Smaller scale simplifies execution",
        fact_patterns=["<500 employees", "small organization", "startup", "smb"],
        affected_categories=["identity_separation", "email_migration", "training"],
        adjustment_factor=0.85,
        adjustment_type="multiply",
        rationale_template="Smaller scale (<500 employees) reduces complexity by ~15%"
    ),
]


# =============================================================================
# COST CATEGORIES - What we're estimating
# =============================================================================

@dataclass
class CostCategory:
    """A category of costs with anchor and adjustments."""
    category_id: str
    name: str
    anchor_low: float
    anchor_high: float
    anchor_source: str  # Where the anchor comes from
    adjustments: List[Dict] = field(default_factory=list)
    adjusted_low: float = 0
    adjusted_high: float = 0
    rationale: List[str] = field(default_factory=list)


# =============================================================================
# ANCHORED ESTIMATOR
# =============================================================================

class AnchoredEstimator:
    """
    Produces company-specific estimates by adjusting market anchors based on facts.

    Process:
    1. Load anchors from deterministic lookup tables
    2. Match facts to adjustment rules
    3. Apply adjustments with rationale
    4. Produce final estimate with full traceability
    """

    def __init__(self):
        self.deterministic = DeterministicEstimator()
        self.rules = ADJUSTMENT_RULES
        self._matched_rules: List[AdjustmentRule] = []
        self._facts_used: List[str] = []

    def match_facts_to_rules(self, facts: List[Dict]) -> List[Tuple[AdjustmentRule, List[str]]]:
        """
        Match extracted facts to adjustment rules.

        Returns list of (rule, matching_fact_ids) tuples.
        """
        matched = []

        for rule in self.rules:
            matching_facts = []

            for fact in facts:
                content = fact.get("content", "").lower()
                fact_id = fact.get("fact_id", "unknown")

                # Check if any pattern matches
                for pattern in rule.fact_patterns:
                    if pattern.lower() in content:
                        matching_facts.append(fact_id)
                        break

            if matching_facts:
                matched.append((rule, matching_facts))

        self._matched_rules = [m[0] for m in matched]
        self._facts_used = list(set(f for _, facts in matched for f in facts))

        return matched

    def calculate_adjusted_cost(
        self,
        category: str,
        anchor_low: float,
        anchor_high: float,
        matched_rules: List[Tuple[AdjustmentRule, List[str]]]
    ) -> Tuple[float, float, List[str]]:
        """
        Apply adjustments to anchor costs for a category.

        Returns (adjusted_low, adjusted_high, rationale_list).
        """
        adjusted_low = anchor_low
        adjusted_high = anchor_high
        rationale = []

        for rule, fact_ids in matched_rules:
            if category not in rule.affected_categories:
                continue

            if rule.adjustment_type == "multiply":
                adjusted_low *= rule.adjustment_factor
                adjusted_high *= rule.adjustment_factor
                direction = "↑" if rule.adjustment_factor > 1 else "↓"
                pct = abs(1 - rule.adjustment_factor) * 100
                rationale.append(
                    f"{direction} {pct:.0f}%: {rule.rationale_template} "
                    f"(based on {', '.join(fact_ids[:2])})"
                )
            elif rule.adjustment_type == "add_fixed":
                adjusted_low += rule.fixed_amount
                adjusted_high += rule.fixed_amount
                rationale.append(
                    f"+ ${rule.fixed_amount:,.0f}: {rule.rationale_template} "
                    f"(based on {', '.join(fact_ids[:2])})"
                )

        return adjusted_low, adjusted_high, rationale

    def identify_tsa_exposure(self, facts: List[Dict]) -> List[Dict]:
        """
        Identify services/functions that will likely require TSA coverage.

        NOTE: We do NOT estimate TSA costs - seller provides pricing.
        We identify WHAT needs TSA so buyer knows what to negotiate.
        """
        tsa_patterns = {
            "identity_services": {
                "patterns": ["parent ad", "parent azure", "corporate okta", "federated",
                            "shared identity", "parent-managed identity"],
                "service": "Identity & Authentication",
                "typical_duration": "6-12 months",
                "criticality": "Day-1 Critical"
            },
            "email_services": {
                "patterns": ["parent email", "corporate exchange", "shared microsoft 365",
                            "parent m365", "corporate email"],
                "service": "Email & Collaboration",
                "typical_duration": "3-6 months",
                "criticality": "Day-1 Critical"
            },
            "service_desk": {
                "patterns": ["parent service desk", "corporate helpdesk", "shared itsm",
                            "parent-managed tickets", "parent support"],
                "service": "Service Desk / IT Support",
                "typical_duration": "6-12 months",
                "criticality": "Day-1 Important"
            },
            "infrastructure": {
                "patterns": ["parent data center", "shared hosting", "corporate network",
                            "parent wan", "shared infrastructure", "parent-hosted"],
                "service": "Infrastructure & Hosting",
                "typical_duration": "12-18 months",
                "criticality": "Day-1 Critical"
            },
            "security_services": {
                "patterns": ["parent soc", "corporate security", "shared siem",
                            "parent-managed security", "corporate firewall"],
                "service": "Security Operations",
                "typical_duration": "6-12 months",
                "criticality": "Day-1 Critical"
            },
            "erp_support": {
                "patterns": ["parent erp support", "shared erp", "corporate sap",
                            "parent-managed erp"],
                "service": "ERP Support & Maintenance",
                "typical_duration": "12-24 months",
                "criticality": "Day-1 Important"
            },
            "network_services": {
                "patterns": ["parent network", "corporate wan", "shared mpls",
                            "parent internet", "corporate vpn"],
                "service": "Network & Connectivity",
                "typical_duration": "6-12 months",
                "criticality": "Day-1 Critical"
            },
        }

        exposures = []

        for category, config in tsa_patterns.items():
            matching_facts = []
            for fact in facts:
                content = fact.get("content", "").lower()
                for pattern in config["patterns"]:
                    if pattern in content:
                        matching_facts.append(fact.get("fact_id", "unknown"))
                        break

            if matching_facts:
                exposures.append({
                    "category": category,
                    "service": config["service"],
                    "typical_duration": config["typical_duration"],
                    "criticality": config["criticality"],
                    "supporting_facts": matching_facts,
                    "action": f"Confirm TSA coverage for {config['service']} in seller proposal"
                })

        return exposures

    def estimate_separation_cost(
        self,
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        has_shared_services: bool = True,
        has_parent_licenses: bool = True,
        dc_count: int = 1
    ) -> Dict[str, Any]:
        """
        Produce a complete anchored estimate with fact-based adjustments.

        Returns detailed breakdown with:
        - Anchor costs (from lookup tables)
        - Matched rules and facts
        - Adjusted costs with rationale
        - Final estimate with confidence
        """
        # Step 1: Match facts to rules
        matched_rules = self.match_facts_to_rules(facts)

        # Step 2: Build cost categories with anchors
        categories = []

        # License transition
        if has_parent_licenses:
            license_est = self.deterministic.estimate_license_transition_cost(
                "microsoft_ea_standalone", user_count, years=1
            )
            anchor_low, anchor_high = license_est["annual_cost_range"]
            adj_low, adj_high, rationale = self.calculate_adjusted_cost(
                "license_transition", anchor_low, anchor_high, matched_rules
            )
            categories.append(CostCategory(
                category_id="license_transition",
                name="License Transition",
                anchor_low=anchor_low,
                anchor_high=anchor_high,
                anchor_source="Market benchmark: Microsoft EA standalone pricing",
                adjusted_low=adj_low,
                adjusted_high=adj_high,
                rationale=rationale if rationale else ["No adjustments - standard market rates apply"]
            ))

        # NOTE: TSA costs are NOT estimated here - seller provides TSA pricing
        # Instead, we identify TSA-exposed services for negotiation
        # See tsa_exposure_flags in result for what needs TSA coverage

        # Identity separation (carveout)
        if deal_type == "carveout":
            size = "small" if user_count < 1000 else "medium" if user_count < 5000 else "large"
            identity_est = self.deterministic.estimate_migration_cost(
                "identity_separation", size
            )
            anchor_low, anchor_high = identity_est["cost_range"]
            adj_low, adj_high, rationale = self.calculate_adjusted_cost(
                "identity_separation", anchor_low, anchor_high, matched_rules
            )
            categories.append(CostCategory(
                category_id="identity_separation",
                name="Identity Separation",
                anchor_low=anchor_low,
                anchor_high=anchor_high,
                anchor_source=f"Market benchmark: Identity separation ({size} org)",
                adjusted_low=adj_low,
                adjusted_high=adj_high,
                rationale=rationale if rationale else ["No adjustments - standard complexity"]
            ))

        # Infrastructure migration
        if dc_count > 0:
            server_count = dc_count * 20  # Assumption: 20 servers per DC
            infra_est = self.deterministic.estimate_migration_cost(
                "cloud_lift_shift", "medium", unit_count=server_count
            )
            anchor_low, anchor_high = infra_est["cost_range"]
            adj_low, adj_high, rationale = self.calculate_adjusted_cost(
                "infrastructure_migration", anchor_low, anchor_high, matched_rules
            )
            # Also check for DC-specific adjustments
            dc_adj_low, dc_adj_high, dc_rationale = self.calculate_adjusted_cost(
                "dc_migration", adj_low, adj_high, matched_rules
            )
            categories.append(CostCategory(
                category_id="infrastructure_migration",
                name="Infrastructure Migration",
                anchor_low=anchor_low,
                anchor_high=anchor_high,
                anchor_source=f"Market benchmark: Cloud migration (~{server_count} servers)",
                adjusted_low=dc_adj_low,
                adjusted_high=dc_adj_high,
                rationale=(rationale + dc_rationale) if (rationale or dc_rationale)
                          else ["No adjustments - standard migration complexity"]
            ))

        # Security remediation (if gaps identified)
        sec_adj_low, sec_adj_high, sec_rationale = self.calculate_adjusted_cost(
            "security_remediation", 200_000, 500_000, matched_rules  # Base anchor
        )
        if sec_rationale:  # Only include if adjustments were made
            categories.append(CostCategory(
                category_id="security_remediation",
                name="Security Remediation",
                anchor_low=200_000,
                anchor_high=500_000,
                anchor_source="Base estimate: Security assessment and remediation",
                adjusted_low=sec_adj_low,
                adjusted_high=sec_adj_high,
                rationale=sec_rationale
            ))

        # Step 3: Calculate totals
        subtotal_anchor_low = sum(c.anchor_low for c in categories)
        subtotal_anchor_high = sum(c.anchor_high for c in categories)
        subtotal_adjusted_low = sum(c.adjusted_low for c in categories)
        subtotal_adjusted_high = sum(c.adjusted_high for c in categories)

        # Contingency (15-25% of adjusted)
        contingency_low = subtotal_adjusted_low * 0.15
        contingency_high = subtotal_adjusted_high * 0.25

        total_low = subtotal_adjusted_low + contingency_low
        total_high = subtotal_adjusted_high + contingency_high

        # Step 4: Build result
        result = {
            "deal_type": deal_type,
            "user_count": user_count,

            # Facts and rules used
            "facts_analyzed": len(facts),
            "facts_matched": len(self._facts_used),
            "rules_triggered": len(matched_rules),
            "matched_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "facts": fact_ids
                }
                for rule, fact_ids in matched_rules
            ],

            # Cost breakdown
            "categories": [
                {
                    "id": c.category_id,
                    "name": c.name,
                    "anchor_range": (round(c.anchor_low, -3), round(c.anchor_high, -3)),
                    "anchor_source": c.anchor_source,
                    "adjusted_range": (round(c.adjusted_low, -3), round(c.adjusted_high, -3)),
                    "adjustment_rationale": c.rationale
                }
                for c in categories
            ],

            # Totals
            "subtotal_anchor": (round(subtotal_anchor_low, -3), round(subtotal_anchor_high, -3)),
            "subtotal_adjusted": (round(subtotal_adjusted_low, -3), round(subtotal_adjusted_high, -3)),
            "contingency": (round(contingency_low, -3), round(contingency_high, -3)),
            "total_range": (round(total_low, -3), round(total_high, -3)),
            "total_midpoint": round((total_low + total_high) / 2, -3),

            # Net adjustment effect
            "net_adjustment_pct": round(
                ((subtotal_adjusted_low + subtotal_adjusted_high) /
                 max(subtotal_anchor_low + subtotal_anchor_high, 1) - 1) * 100, 1
            ),

            # TSA Exposure (NOT costs - seller provides pricing)
            # This identifies WHAT needs TSA for negotiation
            "tsa_exposure": self.identify_tsa_exposure(facts),

            # Note about TSA
            "tsa_note": "TSA costs not estimated - seller provides pricing. Above identifies services requiring TSA coverage.",

            # Methodology
            "methodology": "anchored_estimation",
            "input_hash": self._get_input_hash({
                "user_count": user_count,
                "deal_type": deal_type,
                "facts_hash": hashlib.sha256(
                    json.dumps([f.get("content", "") for f in facts], sort_keys=True).encode()
                ).hexdigest()[:8]
            })
        }

        return result

    def _get_input_hash(self, inputs: Dict) -> str:
        """Generate hash for reproducibility verification."""
        return hashlib.sha256(
            json.dumps(inputs, sort_keys=True).encode()
        ).hexdigest()[:12]

    def format_estimate_for_display(self, estimate: Dict) -> str:
        """Format estimate for human-readable display."""
        lines = [
            "=" * 70,
            "ANCHORED COST ESTIMATE",
            "=" * 70,
            "",
            f"Deal Type: {estimate['deal_type'].upper()}",
            f"Users: {estimate['user_count']:,}",
            f"Facts Analyzed: {estimate['facts_analyzed']} | Matched: {estimate['facts_matched']}",
            f"Rules Triggered: {estimate['rules_triggered']}",
            "",
            "-" * 70,
            "COST BREAKDOWN (Anchor → Adjusted)",
            "-" * 70,
        ]

        for cat in estimate["categories"]:
            anchor_low, anchor_high = cat["anchor_range"]
            adj_low, adj_high = cat["adjusted_range"]

            lines.append(f"\n{cat['name']}:")
            lines.append(f"  Anchor: ${anchor_low:,.0f} - ${anchor_high:,.0f}")
            lines.append(f"  Source: {cat['anchor_source']}")
            lines.append(f"  Adjusted: ${adj_low:,.0f} - ${adj_high:,.0f}")

            if cat["adjustment_rationale"]:
                lines.append("  Adjustments:")
                for r in cat["adjustment_rationale"]:
                    lines.append(f"    • {r}")

        lines.extend([
            "",
            "-" * 70,
            "TOTALS (Buyer One-Time Costs)",
            "-" * 70,
            f"Subtotal (Anchor):   ${estimate['subtotal_anchor'][0]:,.0f} - ${estimate['subtotal_anchor'][1]:,.0f}",
            f"Subtotal (Adjusted): ${estimate['subtotal_adjusted'][0]:,.0f} - ${estimate['subtotal_adjusted'][1]:,.0f}",
            f"Net Adjustment:      {estimate['net_adjustment_pct']:+.1f}%",
            f"Contingency (15-25%): ${estimate['contingency'][0]:,.0f} - ${estimate['contingency'][1]:,.0f}",
            "",
            f"TOTAL ESTIMATE: ${estimate['total_range'][0]:,.0f} - ${estimate['total_range'][1]:,.0f}",
            f"Midpoint: ${estimate['total_midpoint']:,.0f}",
        ])

        # TSA Exposure section
        tsa_exposure = estimate.get("tsa_exposure", [])
        if tsa_exposure:
            lines.extend([
                "",
                "-" * 70,
                "TSA EXPOSURE (Confirm Coverage with Seller)",
                "-" * 70,
                "Note: TSA costs provided by seller - below identifies services needing coverage",
                "",
            ])
            for exp in tsa_exposure:
                lines.append(f"  ⚠️ {exp['service']}")
                lines.append(f"     Typical Duration: {exp['typical_duration']}")
                lines.append(f"     Criticality: {exp['criticality']}")
                lines.append(f"     Facts: {', '.join(exp['supporting_facts'][:2])}")
                lines.append("")

        lines.extend([
            "-" * 70,
            f"Methodology: {estimate['methodology']}",
            f"Input Hash: {estimate['input_hash']}",
            "=" * 70,
        ])

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'AdjustmentRule',
    'ADJUSTMENT_RULES',
    'CostCategory',
    'AnchoredEstimator',
]
