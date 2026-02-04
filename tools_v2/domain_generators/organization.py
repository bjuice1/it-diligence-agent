"""
Organization Domain Generator

Generates DomainReportData for IT Organization domain.

Section 1 (Inventory) includes:
- Mermaid org chart (reused from presentation.py)
- Leadership table
- Team breakdown
- Vendor/outsourcing relationships
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class OrganizationDomainGenerator(BaseDomainGenerator):
    """Generator for IT Organization domain reports."""

    domain = "organization"
    domain_display_name = "IT Organization"

    def _build_inventory(self) -> tuple:
        """
        Build organization inventory section.

        Returns:
            Tuple of (InventorySummary, org_chart_html)
        """
        # Reuse org chart builder from presentation.py
        from tools_v2.presentation import _build_org_chart_html

        org_chart_html = _build_org_chart_html(self.fact_store, entity=self.entity)

        # Build inventory summary
        summary = self._build_summary()

        return summary, org_chart_html

    def _build_summary(self) -> InventorySummary:
        """Build organization inventory summary."""
        # Count by category
        category_counts = self._count_facts_by_category()

        # Extract key metrics
        total_headcount = 0
        outsourced_pct = 0
        it_budget = 0
        leadership_count = 0
        vendor_count = 0

        for fact in self._domain_facts:
            details = fact.details or {}

            if fact.category == "leadership":
                leadership_count += 1

            if fact.category in ("vendors", "outsourcing", "msp"):
                vendor_count += 1

            if "total_it_headcount" in details:
                total_headcount = details["total_it_headcount"]

            if "outsourced_percentage" in details:
                outsourced_pct = details["outsourced_percentage"]

            if "total_it_budget" in details:
                it_budget = details["total_it_budget"]

        # Build summary text
        summary_parts = []
        if total_headcount:
            summary_parts.append(f"{total_headcount} IT staff")
        if leadership_count:
            summary_parts.append(f"{leadership_count} leadership roles")
        if vendor_count:
            summary_parts.append(f"{vendor_count} key vendors")
        if outsourced_pct:
            summary_parts.append(f"{outsourced_pct}% outsourced")

        summary_text = ", ".join(summary_parts) if summary_parts else "Organization details available"

        # Key items
        key_items = []
        for fact in self._domain_facts:
            if fact.category == "leadership" and fact.item:
                key_items.append(fact.item)
            if len(key_items) >= 5:
                break

        return InventorySummary(
            total_count=len(self._domain_facts),
            by_category=category_counts,
            by_criticality={},  # Not applicable for organization
            key_items=key_items,
            summary_text=summary_text,
        )

    def get_organization_metrics(self) -> dict:
        """Extract organization-specific metrics for benchmarking."""
        metrics = {
            "total_it_headcount": None,
            "outsourced_percentage": None,
            "total_it_budget": None,
            "leadership_count": 0,
            "vendor_count": 0,
        }

        for fact in self._domain_facts:
            details = fact.details or {}

            if fact.category == "leadership":
                metrics["leadership_count"] += 1

            if fact.category in ("vendors", "outsourcing", "msp"):
                metrics["vendor_count"] += 1

            for field in ["total_it_headcount", "outsourced_percentage", "total_it_budget"]:
                if field in details and metrics[field] is None:
                    metrics[field] = details[field]

        return metrics
