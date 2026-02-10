"""
DealData Facade for Phase 2 Database-First Architecture

Provides a clean interface for routes to access deal data from the database.
Automatically uses flask.g context for deal_id and run_id when available.

Usage in routes:
    from web.context import load_deal_context
    from web.deal_data import DealData

    @app.route('/deal/<deal_id>/applications')
    def applications_overview(deal_id):
        load_deal_context(deal_id)
        data = DealData()
        apps = data.get_applications()
        return render_template('applications/overview.html', applications=apps)
"""

from typing import List, Dict, Any, Optional, Tuple
from flask import g

from web.repositories import (
    FactRepository,
    FindingRepository,
    GapRepository,
    AnalysisRunRepository,
)


class DealData:
    """
    Facade for accessing deal data from the database.

    Uses flask.g context for deal/run context when available,
    or accepts explicit deal_id/run_id parameters.

    Entity Filtering:
        By default, methods return data for BOTH target and buyer.
        Pass entity='target' or entity='buyer' to filter by entity.
        Use convenience methods like get_target_applications() for entity-specific queries.
    """

    def __init__(self, deal_id: str = None, run_id: str = None, entity: str = None):
        """
        Initialize DealData.

        Args:
            deal_id: Deal ID (uses flask.g.deal_id if not provided)
            run_id: Analysis run ID to scope data (uses flask.g.run_id if not provided)
            entity: Default entity filter ('target' or 'buyer'). If set, all queries
                    will filter by this entity unless overridden in method calls.
        """
        # Use flask.g context if available, otherwise use explicit params
        self.deal_id = deal_id or getattr(g, 'deal_id', None)
        self.run_id = run_id or getattr(g, 'run_id', None)
        self.default_entity = entity  # Store default entity filter

        if not self.deal_id:
            raise ValueError("deal_id required - either pass explicitly or call load_deal_context() first")

        # Initialize repository instances
        self._fact_repo = FactRepository()
        self._finding_repo = FindingRepository()
        self._gap_repo = GapRepository()
        self._run_repo = AnalysisRunRepository()

    # =========================================================================
    # FACTS - Domain-specific accessors
    # =========================================================================

    def _resolve_entity(self, entity: str = None) -> str:
        """Resolve entity parameter, using default_entity if not specified."""
        if entity is not None:
            return entity
        return self.default_entity  # May be None (return all)

    def get_applications(self, entity: str = None) -> List:
        """Get application facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_applications(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_organization(self, entity: str = None) -> List:
        """Get organization facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_organization(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_infrastructure(self, entity: str = None) -> List:
        """Get infrastructure facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_infrastructure(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_cybersecurity(self, entity: str = None) -> List:
        """Get cybersecurity facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_cybersecurity(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_network(self, entity: str = None) -> List:
        """Get network facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_network(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_identity_access(self, entity: str = None) -> List:
        """Get identity/access facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_identity_access(self.deal_id, self.run_id, entity=self._resolve_entity(entity))

    def get_facts_by_domain(self, domain: str, entity: str = None) -> List:
        """Get facts for a specific domain, optionally filtered by entity."""
        return self._fact_repo.get_by_deal(self.deal_id, run_id=self.run_id, domain=domain, entity=self._resolve_entity(entity))

    def get_facts_paginated(
        self,
        domain: str = None,
        entity: str = None,
        status: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List, int]:
        """
        Get paginated facts with filtering.

        Args:
            entity: Filter by entity ('target' or 'buyer')

        Returns:
            Tuple of (items, total_count)
        """
        return self._fact_repo.get_paginated(
            deal_id=self.deal_id,
            run_id=self.run_id,
            domain=domain,
            entity=self._resolve_entity(entity),
            status=status,
            search=search,
            page=page,
            per_page=per_page
        )

    def get_all_facts(self, entity: str = None) -> List:
        """Get all facts for this deal/run, optionally filtered by entity."""
        return self._fact_repo.get_by_deal(self.deal_id, run_id=self.run_id, entity=self._resolve_entity(entity))

    # =========================================================================
    # FACTS - Entity-specific convenience methods
    # =========================================================================

    def get_target_applications(self) -> List:
        """Get only TARGET application facts."""
        return self.get_applications(entity='target')

    def get_buyer_applications(self) -> List:
        """Get only BUYER application facts."""
        return self.get_applications(entity='buyer')

    def get_target_organization(self) -> List:
        """Get only TARGET organization facts."""
        return self.get_organization(entity='target')

    def get_buyer_organization(self) -> List:
        """Get only BUYER organization facts."""
        return self.get_organization(entity='buyer')

    def get_target_infrastructure(self) -> List:
        """Get only TARGET infrastructure facts."""
        return self.get_infrastructure(entity='target')

    def get_buyer_infrastructure(self) -> List:
        """Get only BUYER infrastructure facts."""
        return self.get_infrastructure(entity='buyer')

    def get_target_facts(self) -> List:
        """Get all TARGET facts across all domains."""
        return self.get_all_facts(entity='target')

    def get_buyer_facts(self) -> List:
        """Get all BUYER facts across all domains."""
        return self.get_all_facts(entity='buyer')

    # =========================================================================
    # FINDINGS - Risks, Work Items, etc.
    # =========================================================================

    def get_risks(self, severity: str = None) -> List:
        """Get all risks for this deal/run."""
        return self._finding_repo.get_risks(self.deal_id, self.run_id, severity)

    def get_work_items(self, phase: str = None) -> List:
        """Get all work items for this deal/run."""
        return self._finding_repo.get_work_items(self.deal_id, self.run_id, phase)

    def get_recommendations(self, urgency: str = None) -> List:
        """Get all recommendations for this deal/run."""
        return self._finding_repo.get_recommendations(self.deal_id, self.run_id, urgency)

    def get_strategic_considerations(self) -> List:
        """Get all strategic considerations for this deal/run."""
        return self._finding_repo.get_strategic_considerations(self.deal_id, self.run_id)

    def get_top_risks(self, limit: int = 5) -> List:
        """Get highest severity risks for dashboard."""
        return self._finding_repo.get_top_risks(self.deal_id, self.run_id, limit)

    def get_findings_paginated(
        self,
        finding_type: str = None,
        domain: str = None,
        severity: str = None,
        phase: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50,
        order_by_severity: bool = False
    ) -> Tuple[List, int]:
        """
        Get paginated findings with filtering.

        Args:
            finding_type: Filter by type (risk, work_item, recommendation, etc.)
            domain: Filter by domain (applications, organization, etc.)
            severity: Filter by severity (critical, high, medium, low)
            phase: Filter work items by phase (Day_1, Day_100, Post_100)
            search: Search in title and description
            page: Page number (1-indexed)
            per_page: Items per page
            order_by_severity: If True, order by severity instead of created_at

        Returns:
            Tuple of (items, total_count)
        """
        return self._finding_repo.get_paginated(
            deal_id=self.deal_id,
            run_id=self.run_id,
            finding_type=finding_type,
            domain=domain,
            severity=severity,
            phase=phase,
            search=search,
            page=page,
            per_page=per_page,
            order_by_severity=order_by_severity
        )

    # =========================================================================
    # GAPS
    # =========================================================================

    def get_gaps(self) -> List:
        """Get all gaps for this deal/run."""
        return self._gap_repo.get_by_deal(self.deal_id, run_id=self.run_id)

    def get_gaps_by_domain(self, domain: str) -> List:
        """Get gaps for a specific domain."""
        return self._gap_repo.get_by_domain(self.deal_id, domain, self.run_id)

    def get_open_gaps(self) -> List:
        """Get all open (unresolved) gaps."""
        return self._gap_repo.get_open_gaps(self.deal_id, self.run_id)

    def get_critical_gaps(self) -> List:
        """Get all critical importance gaps."""
        return self._gap_repo.get_critical_gaps(self.deal_id, self.run_id)

    # =========================================================================
    # SUMMARIES - Dashboard & aggregations
    # =========================================================================

    def get_dashboard_summary(self, entity: str = None) -> Dict[str, Any]:
        """
        Get aggregated data for the deal dashboard.

        Args:
            entity: Filter facts by entity ('target' or 'buyer')

        Returns:
            Dict with fact_counts, top_risks, gap_counts, analysis_run
        """
        resolved_entity = self._resolve_entity(entity)
        return {
            'fact_counts': self._fact_repo.count_by_domain(self.deal_id, self.run_id, entity=resolved_entity),
            'top_risks': self.get_top_risks(5),
            'gap_counts': self._gap_repo.count_by_importance(self.deal_id, self.run_id),
            'risk_summary': self._finding_repo.get_risk_summary(self.deal_id, self.run_id),
            'work_item_summary': self._finding_repo.get_work_item_summary(self.deal_id, self.run_id),
            'analysis_run': self._run_repo.get_by_id(self.run_id) if self.run_id else None,
        }

    def get_cost_summary_by_phase(self) -> Dict[str, Dict[str, int]]:
        """
        Get cost summary by phase (Day_1, Day_100, Post_100).

        Returns:
            Dict with phase keys, each containing {count, low, high}
        """
        from tools_v2.reasoning_tools import COST_RANGE_VALUES

        by_phase = {
            "Day_1": {"low": 0, "high": 0, "count": 0},
            "Day_100": {"low": 0, "high": 0, "count": 0},
            "Post_100": {"low": 0, "high": 0, "count": 0}
        }

        work_items = self.get_work_items()
        for wi in work_items:
            phase = wi.phase if hasattr(wi, 'phase') else None
            cost_estimate = wi.cost_estimate if hasattr(wi, 'cost_estimate') else None
            if phase in by_phase and cost_estimate and cost_estimate in COST_RANGE_VALUES:
                cost_range = COST_RANGE_VALUES[cost_estimate]
                by_phase[phase]["low"] += cost_range.get("low", 0)
                by_phase[phase]["high"] += cost_range.get("high", 0)
                by_phase[phase]["count"] += 1

        return by_phase

    def get_fact_summary_by_domain(self) -> Dict[str, Dict[str, int]]:
        """Get fact counts by domain and status."""
        return self._fact_repo.get_summary_by_domain(self.deal_id, self.run_id)

    def get_finding_summary_by_domain(self) -> Dict[str, Dict[str, int]]:
        """Get finding counts by domain and type."""
        return self._finding_repo.get_summary_by_domain(self.deal_id, self.run_id)

    def get_gap_summary_by_domain(self) -> Dict[str, Dict[str, int]]:
        """Get gap counts by domain and importance."""
        return self._gap_repo.get_summary_by_domain(self.deal_id, self.run_id)

    # =========================================================================
    # ANALYSIS RUN INFO
    # =========================================================================

    def get_analysis_run(self):
        """Get the current analysis run (if any)."""
        if self.run_id:
            return self._run_repo.get_by_id(self.run_id)
        return None

    def get_latest_run(self):
        """Get the latest analysis run (any status) for status checks."""
        return self._run_repo.get_latest(self.deal_id)

    def get_run_history(self, limit: int = 10) -> List:
        """Get recent analysis runs for this deal."""
        return self._run_repo.get_by_deal(self.deal_id, limit=limit)


class EmptyDealData:
    """
    Fallback when no deal context exists.

    Returns empty collections so templates don't crash.
    Use this when you need a DealData-like interface but may not have
    a valid deal context.
    """

    deal_id = None
    run_id = None
    default_entity = None

    # Facts - with entity support
    def get_applications(self, entity=None): return []
    def get_organization(self, entity=None): return []
    def get_infrastructure(self, entity=None): return []
    def get_cybersecurity(self, entity=None): return []
    def get_network(self, entity=None): return []
    def get_identity_access(self, entity=None): return []
    def get_facts_by_domain(self, domain, entity=None): return []
    def get_facts_paginated(self, **kwargs): return [], 0
    def get_all_facts(self, entity=None): return []

    # Entity-specific convenience methods
    def get_target_applications(self): return []
    def get_buyer_applications(self): return []
    def get_target_organization(self): return []
    def get_buyer_organization(self): return []
    def get_target_infrastructure(self): return []
    def get_buyer_infrastructure(self): return []
    def get_target_facts(self): return []
    def get_buyer_facts(self): return []

    # Findings
    def get_risks(self, severity=None): return []
    def get_work_items(self, phase=None): return []
    def get_recommendations(self, urgency=None): return []
    def get_strategic_considerations(self): return []
    def get_top_risks(self, limit=5): return []
    def get_findings_paginated(self, **kwargs): return [], 0

    # Gaps
    def get_gaps(self): return []
    def get_gaps_by_domain(self, domain): return []
    def get_open_gaps(self): return []
    def get_critical_gaps(self): return []

    # Summaries
    def get_dashboard_summary(self, entity=None):
        return {
            'fact_counts': {},
            'top_risks': [],
            'gap_counts': {},
            'risk_summary': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'total': 0},
            'work_item_summary': {'Day_1': 0, 'Day_100': 0, 'Post_100': 0, 'total': 0},
            'analysis_run': None,
        }

    def get_cost_summary_by_phase(self):
        return {
            "Day_1": {"low": 0, "high": 0, "count": 0},
            "Day_100": {"low": 0, "high": 0, "count": 0},
            "Post_100": {"low": 0, "high": 0, "count": 0}
        }

    def get_fact_summary_by_domain(self): return {}
    def get_finding_summary_by_domain(self): return {}
    def get_gap_summary_by_domain(self): return {}

    # Analysis run
    def get_analysis_run(self): return None
    def get_latest_run(self): return None
    def get_run_history(self, limit=10): return []


def get_deal_data(deal_id: str = None, run_id: str = None) -> DealData:
    """
    Factory function to get a DealData instance.

    Tries to use flask.g context first, falls back to explicit params.
    Returns EmptyDealData if no valid context can be established.
    """
    try:
        return DealData(deal_id=deal_id, run_id=run_id)
    except ValueError:
        return EmptyDealData()


# =============================================================================
# ADAPTERS: Bridge DB models to existing service functions
# =============================================================================

class FactStoreAdapter:
    """
    Adapter that makes DB facts compatible with existing service functions
    that expect a FactStore object with `.facts` and `.gaps` attributes.

    This allows gradual migration: routes use DealData to get DB facts,
    then wrap them in this adapter to use existing bridge functions.

    Usage:
        data = DealData()
        facts = data.get_applications()
        adapter = FactStoreAdapter(facts)
        inventory, status = build_applications_inventory(adapter)
    """

    def __init__(self, facts: List = None, gaps: List = None):
        self.facts = facts or []
        self.gaps = gaps or []

    def __len__(self):
        return len(self.facts)


class DBFactWrapper:
    """
    Wrapper that ensures DB Fact model attributes match what bridge functions expect.

    DB Fact models are SQLAlchemy objects; this provides a consistent interface
    that works whether the fact came from DB or from the in-memory FactStore.
    """

    def __init__(self, db_fact):
        self._fact = db_fact

    @property
    def id(self):
        return self._fact.id

    @property
    def fact_id(self):
        return self._fact.id

    @property
    def domain(self):
        return self._fact.domain

    @property
    def category(self):
        return self._fact.category or ''

    @property
    def entity(self):
        return self._fact.entity or 'target'

    @property
    def item(self):
        return self._fact.item or ''

    @property
    def status(self):
        return self._fact.status or 'documented'

    @property
    def details(self):
        return self._fact.details or {}

    @property
    def evidence(self):
        return self._fact.evidence or {}

    @property
    def source_document(self):
        return self._fact.source_document or ''

    @property
    def source_quote(self):
        return self._fact.source_quote or ''

    @property
    def confidence_score(self):
        return self._fact.confidence_score or 0.5

    @property
    def verified(self):
        return getattr(self._fact, 'verified', False)

    @property
    def needs_review(self):
        return getattr(self._fact, 'needs_review', False)

    def __getattr__(self, name):
        # Fallback: delegate to underlying fact
        return getattr(self._fact, name)


def wrap_db_facts(db_facts: List) -> FactStoreAdapter:
    """
    Wrap DB facts in an adapter compatible with bridge functions.

    Args:
        db_facts: List of Fact model instances from database

    Returns:
        FactStoreAdapter with wrapped facts
    """
    wrapped = [DBFactWrapper(f) for f in db_facts]
    return FactStoreAdapter(facts=wrapped)


def wrap_db_facts_and_gaps(db_facts: List, db_gaps: List = None) -> FactStoreAdapter:
    """
    Wrap DB facts and gaps in an adapter compatible with bridge functions.

    Args:
        db_facts: List of Fact model instances
        db_gaps: List of Gap model instances (optional)

    Returns:
        FactStoreAdapter with wrapped facts and gaps
    """
    wrapped_facts = [DBFactWrapper(f) for f in db_facts]
    # Gaps can be passed directly as they have simpler structure
    return FactStoreAdapter(facts=wrapped_facts, gaps=db_gaps or [])


class DBFindingWrapper:
    """
    Wrapper that ensures DB Finding model attributes match what PE generators expect.

    Key differences bridged:
    - DB uses .id, generators expect .finding_id
    - DB lacks .target_action, generators use it for "so what" fallback
    - Provides safe defaults for optional fields
    """

    def __init__(self, db_finding):
        self._finding = db_finding

    @property
    def id(self):
        return self._finding.id

    @property
    def finding_id(self):
        """Generators access .finding_id, DB uses .id"""
        return self._finding.id

    @property
    def domain(self):
        return self._finding.domain or ''

    @property
    def title(self):
        return self._finding.title or ''

    @property
    def description(self):
        return self._finding.description or ''

    @property
    def severity(self):
        return self._finding.severity or 'medium'

    @property
    def priority(self):
        return self._finding.priority or 'medium'

    @property
    def phase(self):
        return self._finding.phase or 'Day_100'

    @property
    def owner_type(self):
        return self._finding.owner_type or 'target'

    @property
    def cost_estimate(self):
        return self._finding.cost_estimate or ''

    @property
    def mna_implication(self):
        return self._finding.mna_implication or ''

    @property
    def mna_lens(self):
        return self._finding.mna_lens or ''

    @property
    def target_action(self):
        """Not a DB column — return empty string as safe fallback."""
        return getattr(self._finding, 'target_action', '') or ''

    @property
    def based_on_facts(self):
        return self._finding.based_on_facts or []

    @property
    def triggered_by_risks(self):
        return self._finding.triggered_by_risks or []

    @property
    def confidence(self):
        return self._finding.confidence or 'medium'

    @property
    def reasoning(self):
        return self._finding.reasoning or ''

    @property
    def mitigation(self):
        return self._finding.mitigation or ''

    @property
    def category(self):
        return getattr(self._finding, 'category', '') or ''

    @property
    def integration_dependent(self):
        return getattr(self._finding, 'integration_dependent', False)

    @property
    def timeline(self):
        return getattr(self._finding, 'timeline', None)

    @property
    def lens(self):
        return getattr(self._finding, 'lens', '') or ''

    @property
    def implication(self):
        return getattr(self._finding, 'implication', '') or ''

    @property
    def finding_type(self):
        return self._finding.finding_type or ''

    @property
    def dependencies(self):
        return getattr(self._finding, 'dependencies', []) or []

    def __getattr__(self, name):
        # Fallback: delegate to underlying finding
        return getattr(self._finding, name)


def wrap_db_findings(db_findings: List) -> List:
    """Wrap DB Finding objects for compatibility with PE generators."""
    return [DBFindingWrapper(f) for f in db_findings]


class ReasoningStoreAdapter:
    """
    Adapter that makes DB findings compatible with existing service functions
    that expect a ReasoningStore object with `.risks` and `.work_items` attributes.

    Usage:
        data = DealData()
        risks = data.get_risks()
        work_items = data.get_work_items()
        adapter = ReasoningStoreAdapter(risks=risks, work_items=work_items)
    """

    def __init__(self, risks: List = None, work_items: List = None,
                 recommendations: List = None, strategic_considerations: List = None):
        self.risks = risks or []
        self.work_items = work_items or []
        self.recommendations = recommendations or []
        self.strategic_considerations = strategic_considerations or []

    def __len__(self):
        return len(self.risks) + len(self.work_items)


def create_store_adapters_from_deal_data(data: 'DealData', entity: str = None):
    """
    Create both FactStoreAdapter and ReasoningStoreAdapter from DealData.

    This is a convenience function for routes that need both stores.

    Args:
        data: DealData instance
        entity: Optional entity filter ('target' or 'buyer'). If not provided,
                uses data.default_entity. Pass entity explicitly to ensure
                correct filtering for organization/applications/inventory views.

    Returns:
        Tuple of (FactStoreAdapter, ReasoningStoreAdapter)
    """
    # Use explicit entity, fall back to DealData's default_entity
    effective_entity = entity if entity is not None else data.default_entity

    # Get facts filtered by entity (CRITICAL for org/apps/inventory separation)
    facts = data.get_all_facts(entity=effective_entity)
    gaps = data.get_gaps()
    risks = data.get_risks()
    work_items = data.get_work_items()
    recommendations = data.get_recommendations()
    strategic = data.get_strategic_considerations()

    fact_adapter = wrap_db_facts_and_gaps(facts, gaps)

    # Wrap findings so DB Finding models have .finding_id, .target_action, etc.
    reasoning_adapter = ReasoningStoreAdapter(
        risks=wrap_db_findings(risks),
        work_items=wrap_db_findings(work_items),
        recommendations=wrap_db_findings(recommendations),
        strategic_considerations=wrap_db_findings(strategic)
    )

    return fact_adapter, reasoning_adapter
