"""
Infrastructure Domain Generator

Generates DomainReportData for Infrastructure domain.

Focus areas:
- Hosting/compute
- Cloud vs on-prem
- Backup/DR
- Modernization needs
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class InfrastructureDomainGenerator(BaseDomainGenerator):
    """Generator for Infrastructure domain reports."""

    domain = "infrastructure"
    domain_display_name = "Infrastructure"

    def _build_inventory(self) -> tuple:
        """
        Build infrastructure inventory section.

        Returns:
            Tuple of (InventorySummary, inventory_html)
        """
        # Build custom infrastructure inventory HTML
        inventory_html = self._build_infrastructure_html()

        # Build inventory summary
        summary = self._build_summary()

        return summary, inventory_html

    def _build_summary(self) -> InventorySummary:
        """Build infrastructure inventory summary."""
        # Count by category
        category_counts = self._count_facts_by_category()

        # Extract key metrics
        cloud_items = []
        datacenter_items = []
        storage_items = []
        dr_items = []

        for fact in self._domain_facts:
            category = fact.category.lower() if fact.category else ""

            if "cloud" in category:
                cloud_items.append(fact.item)
            elif "datacenter" in category or "data_center" in category or "server" in category:
                datacenter_items.append(fact.item)
            elif "storage" in category:
                storage_items.append(fact.item)
            elif "dr" in category or "backup" in category or "disaster" in category:
                dr_items.append(fact.item)

        # Build summary parts
        summary_parts = []
        if cloud_items:
            summary_parts.append(f"{len(cloud_items)} cloud services")
        if datacenter_items:
            summary_parts.append(f"{len(datacenter_items)} datacenter/server items")
        if storage_items:
            summary_parts.append(f"{len(storage_items)} storage systems")
        if dr_items:
            summary_parts.append(f"{len(dr_items)} DR/backup items")

        summary_text = ", ".join(summary_parts) if summary_parts else f"{len(self._domain_facts)} infrastructure items"

        # Key items - prioritize datacenter and cloud
        key_items = datacenter_items[:2] + cloud_items[:2] + storage_items[:1]

        return InventorySummary(
            total_count=len(self._domain_facts),
            by_category=category_counts,
            by_criticality={},
            key_items=key_items[:5],
            summary_text=summary_text,
        )

    def _build_infrastructure_html(self) -> str:
        """Build infrastructure inventory HTML table."""
        if not self._domain_facts:
            return "<p>No infrastructure inventory documented</p>"

        # Group by category
        categories = {}
        for fact in self._domain_facts:
            cat = fact.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(fact)

        # Build HTML
        html_parts = []

        # Summary table
        summary_rows = []
        for cat, facts in sorted(categories.items()):
            count = len(facts)
            items = [f.item for f in facts[:3]]
            items_str = ", ".join(items)
            if len(facts) > 3:
                items_str += "..."

            summary_rows.append(f"""
            <tr>
                <td><strong>{cat.replace('_', ' ').title()}</strong></td>
                <td class="count">{count}</td>
                <td>{items_str}</td>
            </tr>
            """)

        if summary_rows:
            html_parts.append(f"""
            <div class="infra-section">
                <h4>Infrastructure Overview</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Count</th>
                            <th>Key Items</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(summary_rows)}
                    </tbody>
                </table>
            </div>
            """)

        # Detailed table for key items
        key_facts = [f for f in self._domain_facts
                    if f.category in ("cloud", "datacenter", "server", "compute", "storage")][:10]

        if key_facts:
            detail_rows = []
            for fact in key_facts:
                details = fact.details or {}
                status = fact.status
                location = details.get("location", details.get("region", "-"))
                provider = details.get("provider", details.get("vendor", "-"))

                detail_rows.append(f"""
                <tr>
                    <td><strong>{fact.item}</strong></td>
                    <td>{fact.category.replace('_', ' ').title()}</td>
                    <td>{provider}</td>
                    <td>{location}</td>
                    <td><span class="status-{status}">{status}</span></td>
                </tr>
                """)

            html_parts.append(f"""
            <div class="infra-section" style="margin-top: 20px;">
                <h4>Key Infrastructure Components</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>Category</th>
                            <th>Provider</th>
                            <th>Location</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(detail_rows)}
                    </tbody>
                </table>
            </div>
            """)

        return f'<div class="infrastructure-inventory">{"".join(html_parts)}</div>'

    def get_infrastructure_metrics(self) -> dict:
        """Extract infrastructure-specific metrics for benchmarking."""
        metrics = {
            "cloud_adoption_pct": None,
            "datacenter_count": 0,
            "server_count": 0,
            "has_dr": False,
            "primary_cloud_provider": None,
        }

        for fact in self._domain_facts:
            details = fact.details or {}
            category = fact.category.lower() if fact.category else ""

            if "cloud_percentage" in details:
                metrics["cloud_adoption_pct"] = details["cloud_percentage"]

            if "cloud_adoption" in details:
                try:
                    pct_str = str(details["cloud_adoption"]).replace("%", "").strip()
                    metrics["cloud_adoption_pct"] = float(pct_str)
                except ValueError:
                    pass

            if "datacenter" in category or "data_center" in category:
                metrics["datacenter_count"] += 1

            if "server" in category:
                metrics["server_count"] += 1

            if "dr" in category or "disaster" in category or "backup" in category:
                metrics["has_dr"] = True

            if "cloud" in category and metrics["primary_cloud_provider"] is None:
                provider = details.get("provider", details.get("vendor", fact.item))
                metrics["primary_cloud_provider"] = provider

        return metrics
