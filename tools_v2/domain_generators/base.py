"""
Base Domain Generator

Provides common functionality for all domain generators.
Subclasses implement domain-specific logic.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from abc import ABC, abstractmethod

from tools_v2.pe_report_schemas import (
    DomainReportData,
    BenchmarkAssessment,
    ActionItem,
    ResourceNeed,
    InventorySummary,
    WorkItemTaxonomy,
    DealContext,
    DOMAIN_DISPLAY_NAMES,
)
from tools_v2.pe_costs import get_domain_costs, extract_run_rate_costs
from tools_v2.pe_narrative import (
    generate_top_implications,
    generate_top_actions,
    identify_resource_needs,
    extract_integration_considerations,
    get_overlap_ids,
)
from tools_v2.cost_calculator import COST_RANGE_VALUES

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class BaseDomainGenerator(ABC):
    """
    Base class for domain report generators.

    Provides:
    - Common data extraction methods
    - Standard report structure building
    - Benchmark assessment integration

    Subclasses implement:
    - Domain-specific inventory building
    - Domain-specific metrics extraction
    - Custom benchmark prompts
    """

    domain: str = "unknown"
    domain_display_name: str = "Unknown"

    def __init__(
        self,
        fact_store: "FactStore",
        reasoning_store: "ReasoningStore",
        deal_context: Optional[DealContext] = None,
        entity: str = "target"
    ):
        """
        Initialize generator.

        Args:
            fact_store: Fact store with discovered facts
            reasoning_store: Reasoning store with findings
            deal_context: Optional deal context
            entity: Entity to filter by ("target" or "buyer")
        """
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store
        self.deal_context = deal_context
        self.entity = entity

        # Pre-filter facts for this domain
        self._domain_facts = [
            f for f in fact_store.facts
            if f.domain == self.domain and getattr(f, "entity", "target") == entity
        ]

        # Pre-filter risks and work items for this domain
        self._domain_risks = [r for r in reasoning_store.risks if r.domain == self.domain]
        self._domain_work_items = [wi for wi in reasoning_store.work_items if wi.domain == self.domain]

    def generate(
        self,
        benchmark_assessment: Optional[BenchmarkAssessment] = None
    ) -> DomainReportData:
        """
        Generate complete domain report data.

        Args:
            benchmark_assessment: Optional pre-generated benchmark assessment

        Returns:
            DomainReportData instance
        """
        # Build inventory section
        inventory_summary, inventory_html = self._build_inventory()

        # Get costs
        run_rate_cost, total_investment = get_domain_costs(
            self.fact_store, self.reasoning_store, self.domain, self.entity
        )

        # Get cost breakdown
        cost_breakdown = self._build_cost_breakdown()

        # Use provided benchmark or build default
        if benchmark_assessment is None:
            benchmark_assessment = self._build_default_benchmark()

        # Generate top actions
        top_actions = generate_top_actions(self.domain, self.reasoning_store)

        # Build work items list
        work_items = self._build_work_items_list()

        # Generate implications
        top_implications = generate_top_implications(
            self.domain, self.reasoning_store, benchmark_assessment
        )

        # Identify resource needs
        resource_needs = identify_resource_needs(
            self.domain, self.fact_store, self.reasoning_store
        )

        # Get integration considerations
        integration_considerations = extract_integration_considerations(
            self.domain, self.reasoning_store
        )
        overlap_ids = get_overlap_ids(self.domain, self.reasoning_store)

        # Get critical risks
        critical_risks = [
            r.title for r in self._domain_risks
            if r.severity in ("critical", "high")
        ][:5]

        # Get cost facts
        cost_facts = self._extract_cost_facts()

        return DomainReportData(
            domain=self.domain,
            domain_display_name=self.domain_display_name,
            inventory_summary=inventory_summary,
            inventory_html=inventory_html,
            inventory_facts=[f.to_dict() for f in self._domain_facts[:20]],
            run_rate_cost=run_rate_cost,
            cost_breakdown=cost_breakdown,
            cost_facts_cited=cost_facts,
            benchmark_assessment=benchmark_assessment,
            top_actions=top_actions,
            work_items=work_items,
            work_item_count=len(self._domain_work_items),
            total_investment=total_investment,
            top_implications=top_implications,
            resource_needs=resource_needs,
            integration_considerations=integration_considerations,
            overlap_ids=overlap_ids,
            risk_count=len(self._domain_risks),
            critical_risks=critical_risks,
            fact_count=len(self._domain_facts),
            gap_count=len([g for g in self.fact_store.gaps if g.domain == self.domain]),
        )

    @abstractmethod
    def _build_inventory(self) -> tuple:
        """
        Build inventory section.

        Returns:
            Tuple of (InventorySummary, inventory_html string)
        """
        pass

    def _build_cost_breakdown(self) -> Dict[str, tuple]:
        """Build cost breakdown by category."""
        breakdown = {}

        # Group facts by category and sum costs
        for fact in self._domain_facts:
            details = fact.details or {}
            category = fact.category

            # Look for cost values
            cost = None
            for field in ["annual_cost", "cost", "spend", "annual_spend"]:
                if field in details and isinstance(details[field], (int, float)):
                    cost = details[field]
                    break

            if cost is not None:
                if category not in breakdown:
                    breakdown[category] = [0, 0]
                breakdown[category][0] += cost
                breakdown[category][1] += cost

        # Convert to tuples
        return {k: tuple(v) for k, v in breakdown.items()}

    def _build_work_items_list(self) -> List[WorkItemTaxonomy]:
        """Build list of work items with taxonomy."""
        items = []

        for wi in self._domain_work_items:
            # Get cost values
            cost_estimate = getattr(wi, "cost_estimate", "25k_to_100k")
            cost_range = COST_RANGE_VALUES.get(cost_estimate, {"low": 25000, "high": 100000})

            # Determine type
            wi_type = getattr(wi, "type", None)
            if not wi_type:
                wi_type = self._infer_work_item_type(wi)

            item = WorkItemTaxonomy(
                work_item_id=wi.finding_id,
                title=wi.title,
                type=wi_type,
                phase=wi.phase,
                priority=wi.priority,
                owner_type=wi.owner_type,
                cost_estimate_low=cost_range["low"],
                cost_estimate_high=cost_range["high"],
                domain=self.domain,
            )
            items.append(item)

        return items

    def _infer_work_item_type(self, work_item: Any) -> str:
        """Infer work item type from title/description."""
        title_lower = work_item.title.lower()
        desc_lower = (work_item.description or "").lower()
        combined = title_lower + " " + desc_lower

        if any(kw in combined for kw in ["tsa", "transition service"]):
            return "tsa"
        elif any(kw in combined for kw in ["separat", "standalone", "carve"]):
            return "separation"
        elif any(kw in combined for kw in ["integrat", "consolid", "harmoni", "merge"]):
            return "integration"
        elif any(kw in combined for kw in ["transform", "moderniz", "upgrade"]):
            return "transform"
        else:
            return "run"

    def _extract_cost_facts(self) -> List[str]:
        """Extract fact IDs that contain cost information."""
        cost_facts = []

        for fact in self._domain_facts:
            details = fact.details or {}
            for field in ["annual_cost", "cost", "spend", "annual_spend", "budget"]:
                if field in details and isinstance(details[field], (int, float)):
                    cost_facts.append(fact.fact_id)
                    break

        return cost_facts

    def _build_default_benchmark(self) -> BenchmarkAssessment:
        """Build a default benchmark assessment without LLM."""
        from tools_v2.pe_benchmarking import assess_domain_without_llm

        return assess_domain_without_llm(
            self.domain, self.fact_store, self.deal_context
        )

    def _count_facts_by_category(self) -> Dict[str, int]:
        """Count facts by category."""
        counts = {}
        for fact in self._domain_facts:
            cat = fact.category
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _extract_key_items(self, categories: List[str], max_items: int = 5) -> List[str]:
        """Extract key item names from specified categories."""
        items = []
        for fact in self._domain_facts:
            if fact.category in categories and fact.item:
                if fact.item not in items:
                    items.append(fact.item)
                    if len(items) >= max_items:
                        break
        return items
