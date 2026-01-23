"""
Risk & Synergy Table Generators

Automatically generates structured risk and synergy tables from domain findings.
Ensures all required columns are populated, deduplicates, and prioritizes.

Output formats match executive narrative requirements:
- Risk Table: risk, why_it_matters, likely_impact, mitigation
- Synergy Table: opportunity, why_it_matters, value_mechanism, first_step
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class RiskSeverity(Enum):
    """Risk severity levels for prioritization."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def sort_order(self) -> int:
        """Return sort order (lower = more severe)."""
        return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(self.value, 4)


class ValueMechanism(Enum):
    """Synergy value mechanism categories."""
    COST_ELIMINATION = "cost_elimination"
    COST_AVOIDANCE = "cost_avoidance"
    EFFICIENCY_GAIN = "efficiency_gain"
    CAPABILITY_GAIN = "capability_gain"
    REVENUE_ENABLEMENT = "revenue_enablement"


@dataclass
class RiskRow:
    """A row in the risk table."""
    risk: str
    why_it_matters: str
    likely_impact: str
    mitigation: str
    severity: RiskSeverity = RiskSeverity.MEDIUM
    domain: str = ""
    mna_lens: str = ""
    source_id: str = ""

    def to_dict(self) -> Dict:
        return {
            "risk": self.risk,
            "why_it_matters": self.why_it_matters,
            "likely_impact": self.likely_impact,
            "mitigation": self.mitigation,
            "severity": self.severity.value,
            "domain": self.domain,
            "mna_lens": self.mna_lens,
            "source_id": self.source_id
        }

    def is_complete(self) -> bool:
        """Check if all required columns are populated."""
        return all([
            self.risk.strip(),
            self.why_it_matters.strip(),
            self.likely_impact.strip(),
            self.mitigation.strip()
        ])


@dataclass
class SynergyRow:
    """A row in the synergy table."""
    opportunity: str
    why_it_matters: str
    value_mechanism: str
    first_step: str
    mechanism_type: ValueMechanism = ValueMechanism.COST_ELIMINATION
    estimated_value: str = ""
    domain: str = ""
    timeline: str = ""
    source_id: str = ""

    def to_dict(self) -> Dict:
        return {
            "opportunity": self.opportunity,
            "why_it_matters": self.why_it_matters,
            "value_mechanism": self.value_mechanism,
            "first_step": self.first_step,
            "mechanism_type": self.mechanism_type.value,
            "estimated_value": self.estimated_value,
            "domain": self.domain,
            "timeline": self.timeline,
            "source_id": self.source_id
        }

    def is_complete(self) -> bool:
        """Check if all required columns are populated."""
        return all([
            self.opportunity.strip(),
            self.why_it_matters.strip(),
            self.value_mechanism.strip(),
            self.first_step.strip()
        ])


# =============================================================================
# VALUE MECHANISM DEFINITIONS
# =============================================================================

VALUE_MECHANISM_DEFINITIONS = {
    ValueMechanism.COST_ELIMINATION: {
        "definition": "Remove duplicate spend by retiring/consolidating",
        "keywords": ["eliminate", "retire", "consolidate", "remove", "decommission", "sunset"],
        "example": "Consolidate to single SIEM, eliminate $200K/yr",
        "typical_timeline": "6-18 months"
    },
    ValueMechanism.COST_AVOIDANCE: {
        "definition": "Prevent future spend by leveraging buyer assets",
        "keywords": ["avoid", "prevent", "leverage", "utilize", "use existing"],
        "example": "Avoid target's planned ERP upgrade, save $1.5M",
        "typical_timeline": "Immediate to 12 months"
    },
    ValueMechanism.EFFICIENCY_GAIN: {
        "definition": "Do more with same resources through optimization",
        "keywords": ["optimize", "streamline", "automate", "improve", "standardize"],
        "example": "Combined SOC covers both entities with same headcount",
        "typical_timeline": "12-24 months"
    },
    ValueMechanism.CAPABILITY_GAIN: {
        "definition": "Acquire new capability that buyer lacks",
        "keywords": ["acquire", "gain", "add", "bring", "enable", "fill gap"],
        "example": "Target's data science team fills buyer capability gap",
        "typical_timeline": "Immediate"
    },
    ValueMechanism.REVENUE_ENABLEMENT: {
        "definition": "Enable new revenue through combined capabilities",
        "keywords": ["revenue", "cross-sell", "upsell", "new market", "expand"],
        "example": "Unified platform enables cross-sell to combined customer base",
        "typical_timeline": "12-36 months"
    }
}


# =============================================================================
# IMPACT TEMPLATES
# =============================================================================

IMPACT_TEMPLATES = {
    "timeline": {
        "critical": "Immediate attention required; may delay close or Day-1",
        "high": "Address within first 100 days; impacts integration timeline",
        "medium": "Address within first year; manageable with planning",
        "low": "Address opportunistically; minimal deal impact"
    },
    "cost": {
        "critical": "Significant unbudgeted cost exposure (>$500K)",
        "high": "Material cost exposure ($100K-$500K)",
        "medium": "Moderate cost exposure ($25K-$100K)",
        "low": "Minor cost exposure (<$25K)"
    },
    "operational": {
        "critical": "May cause business disruption or compliance failure",
        "high": "Affects business operations or key systems",
        "medium": "Impacts efficiency or non-critical functions",
        "low": "Minor operational inconvenience"
    }
}

MNA_LENS_IMPACTS = {
    "day_1_continuity": "Day-1 operations at risk if not addressed",
    "tsa_exposure": "Affects TSA scope, duration, or cost",
    "separation_complexity": "Increases separation effort and timeline",
    "synergy_opportunity": "Impacts synergy realization timeline or value",
    "cost_driver": "Affects IT cost structure post-close"
}


# =============================================================================
# RISK TABLE GENERATOR
# =============================================================================

def generate_risk_table(
    domain_findings: Dict[str, Dict],
    deal_type: str = "acquisition",
    min_rows: int = 5,
    max_rows: int = 15
) -> List[RiskRow]:
    """
    Generate risk table from domain findings.

    Args:
        domain_findings: Dict mapping domain to findings
        deal_type: Type of deal for M&A lens emphasis
        min_rows: Minimum rows required
        max_rows: Maximum rows to include

    Returns:
        List of RiskRow objects, sorted by severity
    """
    raw_risks = []

    # Extract risks from each domain
    for domain, findings in domain_findings.items():
        if isinstance(findings, dict):
            risks = findings.get("risks", [])
            for risk in risks:
                risk_row = _convert_finding_to_risk_row(risk, domain)
                if risk_row:
                    raw_risks.append(risk_row)

    # Deduplicate
    deduplicated = _deduplicate_risks(raw_risks)

    # Ensure all columns are populated
    completed = [_ensure_risk_complete(r, deal_type) for r in deduplicated]

    # Sort by severity
    sorted_risks = sorted(completed, key=lambda r: r.severity.sort_order)

    # Ensure minimum rows
    if len(sorted_risks) < min_rows:
        sorted_risks = _pad_risk_table(sorted_risks, min_rows, deal_type)

    # Cap at maximum
    return sorted_risks[:max_rows]


def _convert_finding_to_risk_row(finding: Dict, domain: str) -> Optional[RiskRow]:
    """Convert a finding dict to RiskRow."""
    if not finding:
        return None

    # Extract fields with fallbacks
    title = finding.get("title", finding.get("risk", finding.get("description", "")))
    if not title:
        return None

    severity_str = finding.get("severity", "medium").lower()
    try:
        severity = RiskSeverity(severity_str)
    except ValueError:
        severity = RiskSeverity.MEDIUM

    return RiskRow(
        risk=title,
        why_it_matters=finding.get("mna_implication", finding.get("why_it_matters", "")),
        likely_impact=finding.get("impact", finding.get("likely_impact", "")),
        mitigation=finding.get("mitigation", finding.get("recommendation", "")),
        severity=severity,
        domain=domain,
        mna_lens=finding.get("mna_lens", ""),
        source_id=finding.get("id", finding.get("risk_id", ""))
    )


def _deduplicate_risks(risks: List[RiskRow]) -> List[RiskRow]:
    """Deduplicate risks based on similarity."""
    if not risks:
        return []

    seen_keys = set()
    unique_risks = []

    for risk in risks:
        # Create a normalized key for comparison
        key = _normalize_text(risk.risk)

        # Check for similar existing risks
        is_duplicate = False
        for seen_key in seen_keys:
            if _text_similarity(key, seen_key) > 0.7:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_keys.add(key)
            unique_risks.append(risk)

    return unique_risks


def _ensure_risk_complete(risk: RiskRow, deal_type: str) -> RiskRow:
    """Ensure all required columns are populated."""
    # Fill why_it_matters if empty
    if not risk.why_it_matters.strip():
        if risk.mna_lens and risk.mna_lens in MNA_LENS_IMPACTS:
            risk.why_it_matters = MNA_LENS_IMPACTS[risk.mna_lens]
        else:
            risk.why_it_matters = f"Affects {deal_type} execution and IT integration"

    # Fill likely_impact if empty
    if not risk.likely_impact.strip():
        impact_template = IMPACT_TEMPLATES["timeline"].get(
            risk.severity.value,
            IMPACT_TEMPLATES["timeline"]["medium"]
        )
        risk.likely_impact = impact_template

    # Fill mitigation if empty
    if not risk.mitigation.strip():
        risk.mitigation = f"Assess {risk.risk.lower()} and develop remediation plan"

    return risk


def _pad_risk_table(risks: List[RiskRow], min_rows: int, deal_type: str) -> List[RiskRow]:
    """Add placeholder risks if below minimum."""
    generic_risks = [
        RiskRow(
            risk="Technical debt assessment needed",
            why_it_matters="Undocumented technical debt may impact integration timeline",
            likely_impact="Unknown cost and timeline exposure until assessed",
            mitigation="Conduct technical debt inventory during diligence",
            severity=RiskSeverity.MEDIUM
        ),
        RiskRow(
            risk="Key person dependency",
            why_it_matters="Critical knowledge may be concentrated in few individuals",
            likely_impact="Risk of knowledge loss during transition",
            mitigation="Identify key persons and develop retention/knowledge transfer plan",
            severity=RiskSeverity.MEDIUM
        ),
        RiskRow(
            risk="Vendor contract review required",
            why_it_matters="Contract terms may complicate assignment or integration",
            likely_impact="Potential termination fees or renegotiation costs",
            mitigation="Review key vendor contracts for change of control clauses",
            severity=RiskSeverity.LOW
        )
    ]

    while len(risks) < min_rows and generic_risks:
        risks.append(generic_risks.pop(0))

    return risks


# =============================================================================
# SYNERGY TABLE GENERATOR
# =============================================================================

def generate_synergy_table(
    domain_findings: Dict[str, Dict],
    deal_type: str = "acquisition",
    min_rows: int = 3,
    max_rows: int = 10
) -> List[SynergyRow]:
    """
    Generate synergy table from domain findings.

    Args:
        domain_findings: Dict mapping domain to findings
        deal_type: Type of deal (affects synergy emphasis)
        min_rows: Minimum rows required
        max_rows: Maximum rows to include

    Returns:
        List of SynergyRow objects
    """
    raw_synergies = []

    # Extract synergies from strategic considerations and recommendations
    for domain, findings in domain_findings.items():
        if isinstance(findings, dict):
            # From strategic considerations
            strategic = findings.get("strategic_considerations", [])
            for item in strategic:
                synergy = _convert_to_synergy_row(item, domain, "strategic")
                if synergy:
                    raw_synergies.append(synergy)

            # From recommendations (some may be synergy opportunities)
            recommendations = findings.get("recommendations", [])
            for item in recommendations:
                if _is_synergy_opportunity(item):
                    synergy = _convert_to_synergy_row(item, domain, "recommendation")
                    if synergy:
                        raw_synergies.append(synergy)

    # For carveouts/divestitures, synergies are less relevant
    if deal_type.lower() in ["carveout", "divestiture"]:
        # Convert to TSA/separation opportunities instead
        raw_synergies = _convert_to_separation_opportunities(raw_synergies, deal_type)

    # Deduplicate
    deduplicated = _deduplicate_synergies(raw_synergies)

    # Ensure all columns are populated
    completed = [_ensure_synergy_complete(s, deal_type) for s in deduplicated]

    # Filter out incomplete
    completed = [s for s in completed if s.is_complete()]

    # Ensure minimum rows
    if len(completed) < min_rows:
        completed = _pad_synergy_table(completed, min_rows, deal_type)

    return completed[:max_rows]


def _convert_to_synergy_row(item: Dict, domain: str, source_type: str) -> Optional[SynergyRow]:
    """Convert a finding to SynergyRow."""
    if not item:
        return None

    title = item.get("title", item.get("opportunity", item.get("description", "")))
    if not title:
        return None

    # Detect value mechanism
    mechanism_type = _detect_value_mechanism(item)

    return SynergyRow(
        opportunity=title,
        why_it_matters=item.get("mna_implication", item.get("why_it_matters", "")),
        value_mechanism=item.get("value_mechanism", ""),
        first_step=item.get("first_step", item.get("recommendation", item.get("action", ""))),
        mechanism_type=mechanism_type,
        estimated_value=item.get("estimated_value", item.get("value_range", "")),
        domain=domain,
        timeline=item.get("timeline", ""),
        source_id=item.get("id", "")
    )


def _is_synergy_opportunity(item: Dict) -> bool:
    """Check if a recommendation is a synergy opportunity."""
    synergy_keywords = [
        "consolidat", "eliminate", "synerg", "efficien", "cost sav",
        "reduce", "streamlin", "leverage", "optimize", "combine"
    ]

    text = (item.get("title", "") + " " + item.get("description", "")).lower()
    return any(kw in text for kw in synergy_keywords)


def _detect_value_mechanism(item: Dict) -> ValueMechanism:
    """Detect the value mechanism type from item content."""
    text = (
        item.get("title", "") + " " +
        item.get("description", "") + " " +
        item.get("value_mechanism", "")
    ).lower()

    for mechanism, definition in VALUE_MECHANISM_DEFINITIONS.items():
        if any(kw in text for kw in definition["keywords"]):
            return mechanism

    return ValueMechanism.COST_ELIMINATION  # Default


def _convert_to_separation_opportunities(
    synergies: List[SynergyRow],
    deal_type: str
) -> List[SynergyRow]:
    """Convert acquisition synergies to carveout/divestiture opportunities."""
    converted = []

    for s in synergies:
        # Reframe as separation/TSA opportunity
        if deal_type.lower() == "carveout":
            s.opportunity = s.opportunity.replace("consolidat", "establish standalone")
            s.why_it_matters = f"Enables standalone operations: {s.why_it_matters}"
            s.value_mechanism = "Standalone capability establishment"
        elif deal_type.lower() == "divestiture":
            s.opportunity = s.opportunity.replace("consolidat", "cleanly separate")
            s.why_it_matters = f"Enables clean separation: {s.why_it_matters}"
            s.value_mechanism = "Clean separation enablement"

        converted.append(s)

    return converted


def _deduplicate_synergies(synergies: List[SynergyRow]) -> List[SynergyRow]:
    """Deduplicate synergies based on similarity."""
    if not synergies:
        return []

    seen_keys = set()
    unique = []

    for synergy in synergies:
        key = _normalize_text(synergy.opportunity)

        is_duplicate = False
        for seen_key in seen_keys:
            if _text_similarity(key, seen_key) > 0.7:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_keys.add(key)
            unique.append(synergy)

    return unique


def _ensure_synergy_complete(synergy: SynergyRow, deal_type: str) -> SynergyRow:
    """Ensure all required columns are populated."""
    # Fill why_it_matters if empty
    if not synergy.why_it_matters.strip():
        mechanism_def = VALUE_MECHANISM_DEFINITIONS.get(synergy.mechanism_type, {})
        synergy.why_it_matters = mechanism_def.get(
            "definition",
            f"Supports {deal_type} value creation"
        )

    # Fill value_mechanism if empty
    if not synergy.value_mechanism.strip():
        mechanism_def = VALUE_MECHANISM_DEFINITIONS.get(synergy.mechanism_type, {})
        synergy.value_mechanism = mechanism_def.get(
            "definition",
            synergy.mechanism_type.value.replace("_", " ").title()
        )

    # Fill first_step if empty
    if not synergy.first_step.strip():
        synergy.first_step = f"Assess feasibility and develop implementation plan for {synergy.opportunity.lower()}"

    return synergy


def _pad_synergy_table(synergies: List[SynergyRow], min_rows: int, deal_type: str) -> List[SynergyRow]:
    """Add generic synergies if below minimum."""
    if deal_type.lower() in ["carveout", "divestiture"]:
        generic = [
            SynergyRow(
                opportunity="TSA exit acceleration",
                why_it_matters="Faster TSA exit reduces dependency costs",
                value_mechanism="Cost avoidance through accelerated standalone capability",
                first_step="Identify critical path TSA services and prioritize exit",
                mechanism_type=ValueMechanism.COST_AVOIDANCE
            ),
            SynergyRow(
                opportunity="Standalone infrastructure right-sizing",
                why_it_matters="Opportunity to right-size during separation",
                value_mechanism="Cost optimization through infrastructure modernization",
                first_step="Assess current utilization and define standalone requirements",
                mechanism_type=ValueMechanism.EFFICIENCY_GAIN
            )
        ]
    else:
        generic = [
            SynergyRow(
                opportunity="Application portfolio rationalization",
                why_it_matters="Duplicate applications across buyer and target",
                value_mechanism="Cost elimination through application consolidation",
                first_step="Inventory overlapping applications and identify retirement candidates",
                mechanism_type=ValueMechanism.COST_ELIMINATION
            ),
            SynergyRow(
                opportunity="Infrastructure consolidation",
                why_it_matters="Combined infrastructure can be optimized",
                value_mechanism="Cost elimination and efficiency through DC/cloud consolidation",
                first_step="Map current infrastructure footprint and identify consolidation opportunities",
                mechanism_type=ValueMechanism.COST_ELIMINATION
            ),
            SynergyRow(
                opportunity="Vendor contract leverage",
                why_it_matters="Combined volume enables better pricing",
                value_mechanism="Cost avoidance through volume leverage on renewals",
                first_step="Identify overlapping vendors and renewal timing",
                mechanism_type=ValueMechanism.COST_AVOIDANCE
            )
        ]

    while len(synergies) < min_rows and generic:
        synergies.append(generic.pop(0))

    return synergies


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Remove punctuation, lowercase, remove extra spaces
    text = re.sub(r'[^\w\s]', '', text.lower())
    return ' '.join(text.split())


def _text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (Jaccard)."""
    if not text1 or not text2:
        return 0.0

    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


# =============================================================================
# TABLE FORMATTING FUNCTIONS
# =============================================================================

def risks_to_markdown(risks: List[RiskRow]) -> str:
    """Convert risk table to markdown."""
    if not risks:
        return "No risks identified."

    md = "| Risk | Why it matters | Likely impact | Mitigation |\n"
    md += "|------|----------------|---------------|------------|\n"

    for risk in risks:
        md += f"| {risk.risk} | {risk.why_it_matters} | {risk.likely_impact} | {risk.mitigation} |\n"

    return md


def synergies_to_markdown(synergies: List[SynergyRow]) -> str:
    """Convert synergy table to markdown."""
    if not synergies:
        return "No synergies identified."

    md = "| Opportunity | Why it matters | Value mechanism | First step |\n"
    md += "|-------------|----------------|-----------------|------------|\n"

    for syn in synergies:
        md += f"| {syn.opportunity} | {syn.why_it_matters} | {syn.value_mechanism} | {syn.first_step} |\n"

    return md


def risks_to_dicts(risks: List[RiskRow]) -> List[Dict]:
    """Convert risk table to list of dicts."""
    return [r.to_dict() for r in risks]


def synergies_to_dicts(synergies: List[SynergyRow]) -> List[Dict]:
    """Convert synergy table to list of dicts."""
    return [s.to_dict() for s in synergies]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'RiskSeverity',
    'ValueMechanism',
    # Data classes
    'RiskRow',
    'SynergyRow',
    # Definitions
    'VALUE_MECHANISM_DEFINITIONS',
    'IMPACT_TEMPLATES',
    'MNA_LENS_IMPACTS',
    # Generators
    'generate_risk_table',
    'generate_synergy_table',
    # Formatters
    'risks_to_markdown',
    'synergies_to_markdown',
    'risks_to_dicts',
    'synergies_to_dicts'
]
