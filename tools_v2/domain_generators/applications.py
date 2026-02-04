"""
Applications Domain Generator

Generates DomainReportData for Applications domain.

Section 1 (Inventory) includes:
- App landscape (reused from presentation.py)
- Key systems (ERP, CRM, HCM)
- App count by category
- Data management overview
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class ApplicationsDomainGenerator(BaseDomainGenerator):
    """Generator for Applications domain reports."""

    domain = "applications"
    domain_display_name = "Applications"

    def _build_inventory(self) -> tuple:
        """
        Build applications inventory section.

        Returns:
            Tuple of (InventorySummary, app_landscape_html)
        """
        # Reuse app landscape builder from presentation.py
        from tools_v2.presentation import _build_app_landscape_html

        app_landscape_html = _build_app_landscape_html(self.fact_store, entity=self.entity)

        # Build inventory summary
        summary = self._build_summary()

        return summary, app_landscape_html

    def _build_summary(self) -> InventorySummary:
        """Build applications inventory summary."""
        # Count by category
        category_counts = self._count_facts_by_category()

        # Count by criticality
        criticality_counts = {"high": 0, "medium": 0, "low": 0}
        for fact in self._domain_facts:
            details = fact.details or {}
            criticality = details.get("criticality", details.get("business_criticality", "")).lower()
            if criticality in criticality_counts:
                criticality_counts[criticality] += 1

        # Filter out non-app facts (costs, budget, etc.)
        app_facts = [f for f in self._domain_facts if f.category not in ("costs", "budget", "spending")]
        total_apps = len(app_facts)

        # Identify key systems
        key_systems = []
        key_categories = ["erp", "crm", "hcm", "finance"]
        for fact in self._domain_facts:
            if fact.category in key_categories:
                key_systems.append(f"{fact.category.upper()}: {fact.item}")
                if len(key_systems) >= 5:
                    break

        # Count custom apps
        custom_count = len([f for f in self._domain_facts if f.category == "custom"])

        # Build summary text
        summary_parts = [f"{total_apps} applications"]
        if custom_count > 0:
            summary_parts.append(f"{custom_count} custom/proprietary")
        if criticality_counts["high"] > 0:
            summary_parts.append(f"{criticality_counts['high']} high-criticality")

        summary_text = ", ".join(summary_parts)

        return InventorySummary(
            total_count=total_apps,
            by_category=category_counts,
            by_criticality=criticality_counts,
            key_items=key_systems,
            summary_text=summary_text,
        )

    def get_application_metrics(self) -> dict:
        """Extract application-specific metrics for benchmarking."""
        app_facts = [f for f in self._domain_facts if f.category not in ("costs", "budget", "spending")]

        metrics = {
            "total_apps": len(app_facts),
            "custom_apps": len([f for f in app_facts if f.category == "custom"]),
            "saas_apps": len([f for f in app_facts if f.category == "saas"]),
            "erp_system": None,
            "crm_system": None,
            "high_criticality_count": 0,
        }

        for fact in self._domain_facts:
            details = fact.details or {}

            if fact.category == "erp" and metrics["erp_system"] is None:
                version = details.get("version", "")
                metrics["erp_system"] = f"{fact.item} {version}".strip()

            if fact.category == "crm" and metrics["crm_system"] is None:
                metrics["crm_system"] = fact.item

            criticality = details.get("criticality", details.get("business_criticality", "")).lower()
            if criticality == "high" or criticality == "critical":
                metrics["high_criticality_count"] += 1

        return metrics
