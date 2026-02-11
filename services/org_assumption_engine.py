"""
Organization Assumption Engine

Generates synthetic organizational structure assumptions when source documents
lack management hierarchy data. Part of adaptive organization extraction (spec 09).

Uses industry benchmarks and company size heuristics (not LLM generation) for:
- Deterministic, testable behavior
- Fast execution (<50ms)
- Transparent audit trail
- No API costs

Algorithm:
- FULL hierarchy → no assumptions
- PARTIAL hierarchy → fill gaps (reports_to, span data)
- MISSING hierarchy → generate full structure
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from stores.fact_store import FactStore
from services.org_hierarchy_detector import HierarchyPresence, HierarchyPresenceStatus

logger = logging.getLogger(__name__)


# Industry Benchmarks (Gartner, Forrester, industry research)
INDUSTRY_ORG_DEPTH = {
    'technology': {
        'typical_layers': 3,
        'span_leadership': 8,  # CXO direct reports
        'span_middle': 6,      # Manager direct reports
        'rationale': 'Flat orgs, agile teams, minimal hierarchy'
    },
    'manufacturing': {
        'typical_layers': 5,
        'span_leadership': 5,
        'span_middle': 7,
        'rationale': 'Traditional hierarchy, plant/regional structure'
    },
    'retail': {
        'typical_layers': 4,
        'span_leadership': 6,
        'span_middle': 8,
        'rationale': 'Store operations, regional managers, HQ'
    },
    'healthcare': {
        'typical_layers': 4,
        'span_leadership': 6,
        'span_middle': 5,
        'rationale': 'Clinical vs administrative hierarchies'
    },
    'financial_services': {
        'typical_layers': 4,
        'span_leadership': 7,
        'span_middle': 6,
        'rationale': 'Regulatory compliance, risk management layers'
    },
    'default': {
        'typical_layers': 4,
        'span_leadership': 6,
        'span_middle': 6,
        'rationale': 'Conservative average across industries'
    }
}

# Industry keyword mapping
INDUSTRY_MAPPING = {
    'technology': ['tech', 'software', 'saas', 'cloud', 'it services', 'digital'],
    'manufacturing': ['manufacturing', 'industrial', 'production', 'factory', 'automotive'],
    'retail': ['retail', 'consumer', 'e-commerce', 'commerce', 'store'],
    'healthcare': ['healthcare', 'medical', 'hospital', 'pharma', 'biotech'],
    'financial_services': ['financial', 'banking', 'insurance', 'fintech', 'capital']
}

# Role hierarchy levels
ROLE_HIERARCHY_LEVELS = {
    # Layer 0 (C-Suite)
    'cio': 0,
    'cto': 0,
    'ciso': 0,
    'chief information officer': 0,
    'chief technology officer': 0,
    'chief information security officer': 0,

    # Layer 1 (VPs)
    'vp': 1,
    'vice president': 1,
    'svp': 1,
    'senior vice president': 1,
    'head of': 1,

    # Layer 2 (Directors)
    'director': 2,
    'senior director': 2,
    'associate director': 2,

    # Layer 3 (Managers)
    'manager': 3,
    'senior manager': 3,
    'lead': 3,
    'team lead': 3,
    'supervisor': 3,

    # Layer 4 (ICs)
    'engineer': 4,
    'senior engineer': 4,
    'analyst': 4,
    'senior analyst': 4,
    'specialist': 4,
    'administrator': 4,
    'architect': 4,
    'consultant': 4
}


@dataclass
class OrganizationAssumption:
    """Single assumed organizational fact.

    Represents a synthetic data point generated when source documents
    lack hierarchy data. Includes confidence score and rationale.
    """
    item: str                    # Role/position name
    category: str                # leadership, central_it, roles, app_teams
    details: Dict[str, Any]      # reports_to, layer, span_of_control
    confidence: float            # 0.6-0.8 (lower than observed data)
    assumption_basis: str        # Why this assumption was made
    entity: str                  # target or buyer

    def to_fact(self, deal_id: str) -> Dict[str, Any]:
        """Convert assumption to fact dict for FactStore.

        Returns dict suitable for FactStore.add_fact() with:
        - data_source='assumed' flag
        - confidence in 0.6-0.8 range
        - assumption_basis in evidence
        """
        return {
            'domain': 'organization',
            'category': self.category,
            'item': self.item,
            'details': {
                **self.details,
                'data_source': 'assumed'  # CRITICAL: Mark as synthetic
            },
            'status': 'documented',
            'evidence': {
                'exact_quote': self.assumption_basis,
                'confidence': self.confidence,
                'source': 'assumption_engine'
            },
            'entity': self.entity
        }


def generate_org_assumptions(
    fact_store: FactStore,
    hierarchy_presence: HierarchyPresence,
    entity: str = "target",
    company_profile: Optional[Dict[str, Any]] = None
) -> List[OrganizationAssumption]:
    """
    Generate organizational structure assumptions based on hierarchy status.

    Args:
        fact_store: FactStore with observed organization facts
        hierarchy_presence: Detection result from org_hierarchy_detector
        entity: "target" or "buyer"
        company_profile: Optional business context (industry, headcount)

    Returns:
        List of OrganizationAssumption objects

    Algorithm:
        1. Extract company profile (industry, headcount)
        2. Determine industry benchmarks
        3. Adjust for company size
        4. Generate assumptions based on hierarchy status:
           - FULL → empty list (no assumptions needed)
           - PARTIAL → fill gaps only
           - MISSING → generate full structure
    """
    if hierarchy_presence.status == HierarchyPresenceStatus.FULL:
        logger.info(f"FULL hierarchy detected for {entity}, no assumptions needed")
        return []

    if hierarchy_presence.status == HierarchyPresenceStatus.UNKNOWN:
        logger.warning(f"UNKNOWN hierarchy status for {entity}, cannot generate assumptions")
        return []

    # Extract company profile
    industry = _determine_industry(company_profile, fact_store, entity)
    headcount = _extract_total_headcount(company_profile, fact_store, entity)

    logger.info(
        f"Generating assumptions for {entity}: "
        f"industry={industry}, headcount={headcount}, status={hierarchy_presence.status.value}"
    )

    # Get industry benchmarks
    benchmarks = INDUSTRY_ORG_DEPTH.get(industry, INDUSTRY_ORG_DEPTH['default'])

    # Adjust for company size
    adjusted_benchmarks = _adjust_for_company_size(benchmarks, headcount)

    # Generate assumptions based on status
    if hierarchy_presence.status == HierarchyPresenceStatus.MISSING:
        assumptions = _generate_full_structure_assumptions(
            fact_store=fact_store,
            entity=entity,
            benchmarks=adjusted_benchmarks,
            headcount=headcount,
            industry=industry
        )
    else:  # PARTIAL
        assumptions = _generate_gap_filling_assumptions(
            fact_store=fact_store,
            entity=entity,
            hierarchy_presence=hierarchy_presence,
            benchmarks=adjusted_benchmarks,
            headcount=headcount,
            industry=industry
        )

    logger.info(f"Generated {len(assumptions)} assumptions for {entity}")
    return assumptions


def _determine_industry(
    company_profile: Optional[Dict[str, Any]],
    fact_store: FactStore,
    entity: str
) -> str:
    """Determine industry from company profile or facts."""
    # Try company_profile first
    if company_profile and 'industry' in company_profile:
        industry = company_profile['industry'].lower()
        # Check if it matches a known industry
        for known_industry, keywords in INDUSTRY_MAPPING.items():
            if industry in keywords or any(kw in industry for kw in keywords):
                return known_industry

    # Try extracting from facts (look for business context)
    org_facts = [f for f in fact_store.facts
                 if f.domain == 'organization' and f.entity == entity]

    for fact in org_facts:
        if fact.category == 'business_context':
            details_str = str(fact.details).lower()
            for known_industry, keywords in INDUSTRY_MAPPING.items():
                if any(kw in details_str for kw in keywords):
                    return known_industry

    logger.info(f"Could not determine industry for {entity}, using default")
    return 'default'


def _extract_total_headcount(
    company_profile: Optional[Dict[str, Any]],
    fact_store: FactStore,
    entity: str
) -> int:
    """Extract total employee headcount from profile or facts."""
    # Try company_profile first
    if company_profile:
        if 'headcount' in company_profile:
            return int(company_profile['headcount'])
        if 'employee_count' in company_profile:
            return int(company_profile['employee_count'])

    # Try extracting from facts
    org_facts = [f for f in fact_store.facts
                 if f.domain == 'organization' and f.entity == entity]

    # Look for headcount in details
    for fact in org_facts:
        details = fact.details or {}
        if 'headcount' in details:
            try:
                return int(details['headcount'])
            except (ValueError, TypeError):
                pass
        if 'total_headcount' in details:
            try:
                return int(details['total_headcount'])
            except (ValueError, TypeError):
                pass

    # Default: conservative estimate
    logger.info(f"Could not determine headcount for {entity}, using default 50")
    return 50


def _adjust_for_company_size(benchmarks: Dict[str, Any], headcount: int) -> Dict[str, Any]:
    """Adjust org depth and span based on company size.

    Rules:
    - Very small (<20): Flat structure, 2 layers, wide span
    - Small (20-50): Minimal hierarchy, 3 layers
    - Medium (50-150): Standard hierarchy, use benchmarks
    - Large (150-500): Add 1 layer, tighter span
    - Very large (500+): Add 2 layers, formalized structure
    """
    adjusted = benchmarks.copy()
    base_layers = adjusted['typical_layers']

    if headcount < 20:
        # Very small: everyone reports to owner/CIO
        adjusted['typical_layers'] = 2
        adjusted['span_leadership'] = 10
        adjusted['span_middle'] = 8
    elif headcount < 50:
        # Small: minimal middle management
        adjusted['typical_layers'] = 3
        adjusted['span_leadership'] = 8
        adjusted['span_middle'] = 7
    elif headcount < 150:
        # Medium: use benchmarks as-is
        pass
    elif headcount < 500:
        # Large: add management layer
        adjusted['typical_layers'] = base_layers + 1
        adjusted['span_leadership'] = max(4, adjusted['span_leadership'] - 1)
        adjusted['span_middle'] = max(4, adjusted['span_middle'] - 1)
    else:
        # Very large: formalized hierarchy
        adjusted['typical_layers'] = base_layers + 2
        adjusted['span_leadership'] = max(4, adjusted['span_leadership'] - 2)
        adjusted['span_middle'] = max(4, adjusted['span_middle'] - 1)

    return adjusted


def _infer_layer_from_title(title: str) -> Optional[int]:
    """Infer management layer from role title.

    Returns layer number (0=C-suite, 4=IC) or None if ambiguous.

    Note: Checks keywords from longest to shortest to avoid partial matches
    (e.g., "director" should match before "cio" even though both might
    technically be substrings).
    """
    title_lower = title.lower()

    # Sort keywords by length (longest first) to match most specific first
    sorted_keywords = sorted(ROLE_HIERARCHY_LEVELS.items(),
                           key=lambda x: len(x[0]),
                           reverse=True)

    for keyword, layer in sorted_keywords:
        if keyword in title_lower:
            return layer

    return None


def _generate_full_structure_assumptions(
    fact_store: FactStore,
    entity: str,
    benchmarks: Dict[str, Any],
    headcount: int,
    industry: str
) -> List[OrganizationAssumption]:
    """Generate complete organizational structure for MISSING hierarchy.

    Creates assumptions for:
    - CIO (Layer 0)
    - VPs/Directors reporting to CIO (Layer 1-2)
    - Manager roles (Layer 3)
    - Structure notes (layers, span)
    """
    assumptions = []
    layers = benchmarks['typical_layers']
    span_leadership = benchmarks['span_leadership']
    span_middle = benchmarks['span_middle']

    basis = f"Industry benchmark ({industry}): {layers} layers, span {span_leadership}/{span_middle}"

    # Layer 0: CIO
    assumptions.append(OrganizationAssumption(
        item="Chief Information Officer (CIO)",
        category="leadership",
        details={
            'layer': 0,
            'title': 'CIO',
            'reports_to': 'CEO'
        },
        confidence=0.75,
        assumption_basis=f"Standard IT leadership role. {basis}",
        entity=entity
    ))

    # Layer 1: VPs (based on headcount)
    vp_count = min(4, max(2, headcount // 30))  # 2-4 VPs typically
    vp_roles = ['VP of Infrastructure', 'VP of Applications', 'VP of Security', 'VP of Operations']

    for i in range(vp_count):
        assumptions.append(OrganizationAssumption(
            item=vp_roles[i],
            category="leadership",
            details={
                'layer': 1,
                'title': 'VP',
                'reports_to': 'CIO',
                'span_of_control': span_leadership
            },
            confidence=0.70,
            assumption_basis=f"Standard VP-level structure. {basis}",
            entity=entity
        ))

    # Layer 2: Directors (if org is deep enough)
    if layers >= 4:
        director_count = min(6, vp_count * 2)
        for i in range(director_count):
            assumptions.append(OrganizationAssumption(
                item=f"Director of IT Services {i+1}",
                category="central_it",
                details={
                    'layer': 2,
                    'title': 'Director',
                    'reports_to': f'VP {(i % vp_count) + 1}',
                    'span_of_control': span_middle
                },
                confidence=0.65,
                assumption_basis=f"Director layer typical for {headcount} employees. {basis}",
                entity=entity
            ))

    # Layer 3: Managers (always present if >20 employees)
    if headcount >= 20:
        manager_count = min(10, headcount // 10)
        for i in range(manager_count):
            assumptions.append(OrganizationAssumption(
                item=f"IT Manager {i+1}",
                category="central_it",
                details={
                    'layer': 3,
                    'title': 'Manager',
                    'reports_to': 'Director' if layers >= 4 else 'VP',
                    'span_of_control': span_middle
                },
                confidence=0.65,
                assumption_basis=f"Manager layer for {headcount} employees. {basis}",
                entity=entity
            ))

    # Structure notes
    assumptions.append(OrganizationAssumption(
        item="Organization Structure Summary",
        category="leadership",
        details={
            'layers': layers,
            'span_leadership': span_leadership,
            'span_middle': span_middle,
            'total_it_headcount': headcount
        },
        confidence=0.70,
        assumption_basis=f"Assumed structure based on {industry} benchmarks and {headcount} employees",
        entity=entity
    ))

    return assumptions


def _generate_gap_filling_assumptions(
    fact_store: FactStore,
    entity: str,
    hierarchy_presence: HierarchyPresence,
    benchmarks: Dict[str, Any],
    headcount: int,
    industry: str
) -> List[OrganizationAssumption]:
    """Fill gaps in PARTIAL hierarchy.

    Only generates assumptions for missing data:
    - reports_to if missing
    - span_of_control if missing
    - layers if not explicit

    Does NOT duplicate existing observed data.
    """
    assumptions = []
    basis = f"Gap-fill based on {industry} benchmarks"

    # Get existing roles
    org_facts = [f for f in fact_store.facts
                 if f.domain == 'organization' and f.entity == entity]

    # Check what's missing from hierarchy_presence.gaps
    needs_reports_to = not hierarchy_presence.has_reports_to
    needs_layers = not hierarchy_presence.has_explicit_layers
    needs_span = not hierarchy_presence.has_span_data

    # If missing reports_to, infer from titles
    if needs_reports_to:
        for fact in org_facts:
            if fact.category in ('leadership', 'central_it', 'roles'):
                # Try to infer layer from title
                layer = _infer_layer_from_title(fact.item)
                if layer is not None and layer > 0:
                    # Infer who they report to
                    if layer == 1:
                        reports_to = 'CIO'
                    elif layer == 2:
                        reports_to = 'VP'
                    elif layer == 3:
                        reports_to = 'Director'
                    else:
                        reports_to = 'Manager'

                    assumptions.append(OrganizationAssumption(
                        item=f"{fact.item} (reporting line)",
                        category=fact.category,
                        details={
                            'reports_to': reports_to,
                            'layer': layer
                        },
                        confidence=0.60,
                        assumption_basis=f"Inferred from title '{fact.item}'. {basis}",
                        entity=entity
                    ))

    # If missing layers, add structure note
    if needs_layers:
        assumptions.append(OrganizationAssumption(
            item="Estimated Organization Depth",
            category="leadership",
            details={
                'layers': benchmarks['typical_layers'],
                'source': 'estimated'
            },
            confidence=0.65,
            assumption_basis=f"Estimated {benchmarks['typical_layers']} layers based on {industry} industry",
            entity=entity
        ))

    # If missing span data, add span estimates
    if needs_span:
        assumptions.append(OrganizationAssumption(
            item="Estimated Span of Control",
            category="leadership",
            details={
                'span_leadership': benchmarks['span_leadership'],
                'span_middle': benchmarks['span_middle'],
                'source': 'estimated'
            },
            confidence=0.65,
            assumption_basis=f"Estimated span based on {industry} benchmarks",
            entity=entity
        ))

    return assumptions
