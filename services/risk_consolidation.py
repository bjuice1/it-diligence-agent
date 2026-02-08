"""
Risk Consolidation Service (C1 Fix)

Groups related or duplicate risks into consolidated findings using
graph-based clustering. Only consolidates validated risks (not gaps/observations).

Key features:
- Graph-based clustering using connected components
- Domain-first consolidation (within domain, then cross-domain)
- Evidence provenance tracking (no new claims allowed)
- Rule-based grouping with optional LLM summarization

Usage:
    from services.risk_consolidation import RiskConsolidator

    consolidator = RiskConsolidator(deal_id)
    results = consolidator.consolidate()
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Try to import networkx for graph clustering
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("networkx not installed - using fallback clustering")


# =============================================================================
# GROUPING RULES
# =============================================================================

# Keywords that indicate related risks when shared
GROUPING_KEYWORDS = {
    # ERP/Core Systems
    'erp': ['erp', 'sap', 'oracle', 'netsuite', 'dynamics', 'sage', 'workday'],
    'crm': ['crm', 'salesforce', 'hubspot', 'zoho', 'dynamics'],
    'hcm': ['hcm', 'hr', 'payroll', 'workday', 'adp', 'ceridian', 'bamboohr'],

    # Infrastructure
    'cloud': ['aws', 'azure', 'gcp', 'cloud', 'iaas', 'paas'],
    'network': ['network', 'vpn', 'wan', 'lan', 'firewall', 'router', 'switch'],
    'server': ['server', 'vm', 'virtual', 'hypervisor', 'vmware', 'hyper-v'],

    # Security
    'security_tools': ['edr', 'siem', 'antivirus', 'firewall', 'ids', 'ips'],
    'identity': ['identity', 'iam', 'sso', 'mfa', 'active directory', 'okta', 'azure ad'],
    'backup': ['backup', 'disaster recovery', 'dr', 'replication', 'failover'],

    # Integration
    'integration': ['integration', 'api', 'middleware', 'etl', 'mulesoft', 'boomi'],
    'database': ['database', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb'],
}

# Severity ordering for max calculation
SEVERITY_ORDER = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GroupingResult:
    """Result of grouping operation."""
    group_id: int
    risk_ids: List[str]
    reason: str
    shared_keywords: List[str] = field(default_factory=list)
    shared_systems: List[str] = field(default_factory=list)
    shared_facts: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class ConsolidationResult:
    """Result of consolidation for a single group."""
    title: str
    description: str
    severity: str
    child_risk_ids: List[str]
    supporting_facts: List[str]
    key_systems: List[str]
    field_provenance: Dict[str, str]
    grouping_reason: str
    grouping_confidence: float
    method: str = 'rule_based'


@dataclass
class ValidationResult:
    """Result of validating a consolidated risk."""
    valid: bool
    issues: List[str] = field(default_factory=list)
    new_systems: List[str] = field(default_factory=list)


# =============================================================================
# RISK CONSOLIDATOR
# =============================================================================

class RiskConsolidator:
    """
    Consolidates related risks into unified findings.

    Uses graph-based clustering to group related risks, then generates
    consolidated summaries that cite all supporting evidence.
    """

    def __init__(self, deal_id: str, entity: str = 'target'):
        self.deal_id = deal_id
        self.entity = entity
        self._risks: List[Any] = []
        self._risks_by_id: Dict[str, Any] = {}

    def load_risks(self) -> List[Any]:
        """Load validated risks from database."""
        try:
            from web.database import Finding, db
            # Only consolidate validated risks, not gaps/observations
            self._risks = Finding.query.filter(
                Finding.deal_id == self.deal_id,
                Finding.finding_type == 'risk',
                Finding.deleted_at.is_(None),
            ).all()
            self._risks_by_id = {r.id: r for r in self._risks}
            logger.info(f"C1: Loaded {len(self._risks)} risks for consolidation")
            return self._risks
        except Exception as e:
            logger.error(f"C1: Failed to load risks: {e}")
            return []

    def consolidate(self) -> Dict[str, List[ConsolidationResult]]:
        """
        Main consolidation entry point.

        Returns:
            Dict mapping domain -> list of ConsolidationResult
        """
        if not self._risks:
            self.load_risks()

        if not self._risks:
            logger.info("C1: No risks to consolidate")
            return {}

        # Step 1: Group by domain first (GPT FEEDBACK - domain-first consolidation)
        by_domain = self._group_by_domain()

        # Step 2: Cluster within each domain
        results = {}
        for domain, domain_risks in by_domain.items():
            groups = self._cluster_risks(domain_risks)
            consolidations = []

            for group in groups:
                if len(group.risk_ids) > 1:
                    # Multiple risks - consolidate
                    consolidated = self._create_consolidated_risk(group)
                    if consolidated and self._validate_consolidated(consolidated):
                        consolidations.append(consolidated)
                # Single risk - no consolidation needed

            if consolidations:
                results[domain] = consolidations
                logger.info(f"C1: Domain '{domain}': {len(consolidations)} consolidated groups")

        return results

    def consolidate_and_save(self) -> int:
        """
        Consolidate risks and save to database.

        Returns:
            Number of consolidated risks created
        """
        results = self.consolidate()
        count = 0

        try:
            from web.database import ConsolidatedRisk, db

            # Clear existing consolidations for this deal/entity
            ConsolidatedRisk.query.filter_by(
                deal_id=self.deal_id,
                entity=self.entity
            ).delete()

            # Create new consolidated risks
            for domain, consolidations in results.items():
                for c in consolidations:
                    cr = ConsolidatedRisk(
                        deal_id=self.deal_id,
                        domain=domain,
                        entity=self.entity,
                        title=c.title,
                        description=c.description,
                        severity=c.severity,
                        child_risk_ids=c.child_risk_ids,
                        supporting_facts=c.supporting_facts,
                        key_systems=c.key_systems,
                        field_provenance=c.field_provenance,
                        consolidation_method=c.method,
                        grouping_confidence=c.grouping_confidence,
                        grouping_reason=c.grouping_reason,
                    )
                    db.session.add(cr)
                    count += 1

            db.session.commit()
            logger.info(f"C1: Saved {count} consolidated risks to database")

        except Exception as e:
            logger.error(f"C1: Failed to save consolidated risks: {e}")
            from web.database import db
            db.session.rollback()

        return count

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _group_by_domain(self) -> Dict[str, List[Any]]:
        """Group risks by domain."""
        by_domain = defaultdict(list)
        for risk in self._risks:
            by_domain[risk.domain or 'other'].append(risk)
        return dict(by_domain)

    def _cluster_risks(self, risks: List[Any]) -> List[GroupingResult]:
        """
        Cluster related risks using graph-based connected components.

        GPT FEEDBACK: Use graph clustering instead of pairwise thresholds
        to avoid A~B, B~C but A not~C issues.
        """
        if not risks:
            return []

        if len(risks) == 1:
            return [GroupingResult(
                group_id=0,
                risk_ids=[risks[0].id],
                reason='single_risk',
                confidence=1.0
            )]

        if HAS_NETWORKX:
            return self._cluster_with_networkx(risks)
        else:
            return self._cluster_fallback(risks)

    def _cluster_with_networkx(self, risks: List[Any]) -> List[GroupingResult]:
        """Graph-based clustering using networkx."""
        G = nx.Graph()

        # Add all risks as nodes
        for risk in risks:
            G.add_node(risk.id, risk=risk)

        # Add edges between related risks
        for i, risk_a in enumerate(risks):
            for risk_b in risks[i + 1:]:
                should_group, reason, confidence, shared = self._should_group(risk_a, risk_b)
                if should_group:
                    G.add_edge(risk_a.id, risk_b.id, reason=reason, confidence=confidence, shared=shared)

        # Find connected components
        groups = []
        for idx, component in enumerate(nx.connected_components(G)):
            risk_ids = list(component)

            # Collect all edge data for this component
            reasons = []
            shared_keywords = set()
            shared_systems = set()
            shared_facts = set()
            confidences = []

            for node_id in risk_ids:
                for neighbor in G.neighbors(node_id):
                    if neighbor in component:
                        edge_data = G.edges[node_id, neighbor]
                        reasons.append(edge_data.get('reason', ''))
                        confidences.append(edge_data.get('confidence', 1.0))
                        shared = edge_data.get('shared', {})
                        shared_keywords.update(shared.get('keywords', []))
                        shared_systems.update(shared.get('systems', []))
                        shared_facts.update(shared.get('facts', []))

            groups.append(GroupingResult(
                group_id=idx,
                risk_ids=risk_ids,
                reason='; '.join(set(reasons)) if reasons else 'connected_component',
                shared_keywords=list(shared_keywords),
                shared_systems=list(shared_systems),
                shared_facts=list(shared_facts),
                confidence=sum(confidences) / len(confidences) if confidences else 1.0
            ))

        return groups

    def _cluster_fallback(self, risks: List[Any]) -> List[GroupingResult]:
        """Simple fallback clustering without networkx."""
        # Use union-find for connected components
        parent = {r.id: r.id for r in risks}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Connect related risks
        for i, risk_a in enumerate(risks):
            for risk_b in risks[i + 1:]:
                should_group, _, _, _ = self._should_group(risk_a, risk_b)
                if should_group:
                    union(risk_a.id, risk_b.id)

        # Build groups
        groups_map = defaultdict(list)
        for risk in risks:
            root = find(risk.id)
            groups_map[root].append(risk.id)

        return [
            GroupingResult(
                group_id=idx,
                risk_ids=risk_ids,
                reason='related_risks',
                confidence=0.8
            )
            for idx, risk_ids in enumerate(groups_map.values())
        ]

    def _should_group(self, risk_a: Any, risk_b: Any) -> Tuple[bool, str, float, Dict]:
        """
        Determine if two risks should be grouped.

        Returns:
            (should_group, reason, confidence, shared_data)
        """
        reasons = []
        confidence = 0.0
        shared = {'keywords': [], 'systems': [], 'facts': []}

        # Extract text for comparison
        text_a = f"{risk_a.title} {risk_a.description}".lower()
        text_b = f"{risk_b.title} {risk_b.description}".lower()

        # Rule 1: Shared supporting facts (strongest signal)
        facts_a = set(risk_a.based_on_facts or [])
        facts_b = set(risk_b.based_on_facts or [])
        common_facts = facts_a & facts_b
        if common_facts:
            reasons.append('shared_facts')
            shared['facts'] = list(common_facts)
            confidence = max(confidence, 0.9)

        # Rule 2: Same key systems mentioned
        systems_a = self._extract_systems(text_a)
        systems_b = self._extract_systems(text_b)
        common_systems = systems_a & systems_b
        if common_systems:
            reasons.append('same_systems')
            shared['systems'] = list(common_systems)
            confidence = max(confidence, 0.85)

        # Rule 3: Same keyword families
        keywords_a = self._extract_keywords(text_a)
        keywords_b = self._extract_keywords(text_b)
        common_keywords = keywords_a & keywords_b
        if common_keywords:
            reasons.append('shared_keywords')
            shared['keywords'] = list(common_keywords)
            confidence = max(confidence, 0.7)

        # Rule 4: Similar risk category
        if risk_a.category and risk_b.category and risk_a.category == risk_b.category:
            reasons.append('same_category')
            confidence = max(confidence, 0.6)

        should_group = len(reasons) >= 1 and confidence >= 0.6
        return should_group, '; '.join(reasons), confidence, shared

    def _extract_systems(self, text: str) -> Set[str]:
        """Extract system/application names from text."""
        systems = set()
        # Common system patterns
        patterns = [
            r'\b(sap\s*(?:s/4hana|ecc|r/3)?)\b',
            r'\b(oracle\s*(?:ebs|cloud|financials)?)\b',
            r'\b(salesforce)\b',
            r'\b(workday)\b',
            r'\b(servicenow)\b',
            r'\b(microsoft\s*(?:365|dynamics|azure)?)\b',
            r'\b(netsuite)\b',
            r'\b(crowdstrike)\b',
            r'\b(sentinelone)\b',
            r'\b(splunk)\b',
            r'\b(elastic)\b',
            r'\b(okta)\b',
            r'\b(aws)\b',
            r'\b(azure)\b',
            r'\b(gcp)\b',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            systems.update(matches)
        return systems

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keyword families from text."""
        keywords = set()
        for family, terms in GROUPING_KEYWORDS.items():
            if any(term in text for term in terms):
                keywords.add(family)
        return keywords

    def _create_consolidated_risk(self, group: GroupingResult) -> Optional[ConsolidationResult]:
        """Create a consolidated risk from a group of related risks."""
        risks = [self._risks_by_id[rid] for rid in group.risk_ids if rid in self._risks_by_id]

        if not risks:
            return None

        # Collect all evidence
        all_facts = set()
        all_systems = set()
        provenance = {}

        for risk in risks:
            facts = risk.based_on_facts or []
            all_facts.update(facts)

            text = f"{risk.title} {risk.description}"
            systems = self._extract_systems(text.lower())
            all_systems.update(systems)

            # Track which risk contributed what
            for fact_id in facts:
                if fact_id not in provenance:
                    provenance[fact_id] = risk.id

        # Calculate severity = max of children
        severity = self._max_severity(risks)

        # Generate title (from most severe or first)
        primary_risk = max(risks, key=lambda r: SEVERITY_ORDER.get(r.severity or 'low', 0))
        title = self._generate_title(risks, group)

        # Generate description combining all risks
        description = self._generate_description(risks, group)

        return ConsolidationResult(
            title=title,
            description=description,
            severity=severity,
            child_risk_ids=group.risk_ids,
            supporting_facts=list(all_facts),
            key_systems=list(all_systems) + group.shared_systems,
            field_provenance=provenance,
            grouping_reason=group.reason,
            grouping_confidence=group.confidence,
            method='rule_based'
        )

    def _max_severity(self, risks: List[Any]) -> str:
        """Get maximum severity from a list of risks."""
        max_sev = 'low'
        max_order = 0
        for risk in risks:
            sev = (risk.severity or 'low').lower()
            order = SEVERITY_ORDER.get(sev, 0)
            if order > max_order:
                max_order = order
                max_sev = sev
        return max_sev.title()

    def _generate_title(self, risks: List[Any], group: GroupingResult) -> str:
        """Generate a consolidated title."""
        # Use shared systems if available
        if group.shared_systems:
            system = group.shared_systems[0].title()
            return f"Multiple {system} Related Risks"

        if group.shared_keywords:
            keyword = group.shared_keywords[0].upper()
            return f"Multiple {keyword} Risks"

        # Fall back to first risk title with count
        count = len(risks)
        base_title = risks[0].title[:50] if risks[0].title else "Related Risks"
        return f"{base_title} (+{count - 1} related)" if count > 1 else base_title

    def _generate_description(self, risks: List[Any], group: GroupingResult) -> str:
        """Generate a consolidated description."""
        lines = []

        # Overview
        lines.append(f"This consolidates {len(risks)} related risks.")

        # Summary of concerns
        lines.append("\nKey concerns:")
        for risk in risks[:5]:  # Limit to first 5
            concern = risk.title or risk.description[:80]
            lines.append(f"- {concern}")

        if len(risks) > 5:
            lines.append(f"- ... and {len(risks) - 5} more")

        # Shared context
        if group.shared_systems:
            lines.append(f"\nAffected systems: {', '.join(group.shared_systems[:5])}")

        if group.shared_facts:
            lines.append(f"\nBased on {len(group.shared_facts)} shared evidence points")

        return '\n'.join(lines)

    def _validate_consolidated(self, consolidated: ConsolidationResult) -> bool:
        """
        Validate that consolidated risk doesn't introduce new claims.

        GPT FEEDBACK: Consolidated descriptions must not introduce new claims
        not supported by child facts.
        """
        result = ValidationResult(valid=True)

        # Check that all key_systems are from children
        child_risks = [self._risks_by_id[rid] for rid in consolidated.child_risk_ids if rid in self._risks_by_id]
        child_systems = set()
        for risk in child_risks:
            text = f"{risk.title} {risk.description}".lower()
            child_systems.update(self._extract_systems(text))

        consolidated_systems = set(s.lower() for s in consolidated.key_systems)
        new_systems = consolidated_systems - child_systems

        if new_systems:
            logger.warning(f"C1 Validation: Consolidated risk introduces new systems: {new_systems}")
            result.valid = False
            result.new_systems = list(new_systems)
            result.issues.append(f"New systems not in children: {new_systems}")

        return result.valid


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def consolidate_deal_risks(deal_id: str, entity: str = 'target') -> Dict[str, List[ConsolidationResult]]:
    """
    Consolidate risks for a deal (convenience function).

    Args:
        deal_id: Deal to consolidate
        entity: Entity filter (target/buyer)

    Returns:
        Dict mapping domain -> list of consolidated risks
    """
    consolidator = RiskConsolidator(deal_id, entity)
    return consolidator.consolidate()


def consolidate_and_save(deal_id: str, entity: str = 'target') -> int:
    """
    Consolidate risks and save to database.

    Args:
        deal_id: Deal to consolidate
        entity: Entity filter

    Returns:
        Number of consolidated risks created
    """
    consolidator = RiskConsolidator(deal_id, entity)
    return consolidator.consolidate_and_save()


def get_consolidation_stats(deal_id: str) -> Dict[str, Any]:
    """Get consolidation statistics for a deal."""
    try:
        from web.database import Finding, ConsolidatedRisk

        total_risks = Finding.query.filter(
            Finding.deal_id == deal_id,
            Finding.finding_type == 'risk',
            Finding.deleted_at.is_(None)
        ).count()

        consolidated = ConsolidatedRisk.query.filter_by(deal_id=deal_id).all()
        consolidated_count = len(consolidated)
        child_count = sum(len(c.child_risk_ids or []) for c in consolidated)
        standalone_count = total_risks - child_count

        return {
            'total_risks': total_risks,
            'consolidated_groups': consolidated_count,
            'risks_in_groups': child_count,
            'standalone_risks': standalone_count,
            'reduction_rate': round((child_count - consolidated_count) / total_risks * 100, 1) if total_risks > 0 else 0
        }
    except Exception as e:
        logger.error(f"C1: Failed to get stats: {e}")
        return {}
