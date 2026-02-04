"""
Network Domain Generator

Generates DomainReportData for Network domain.

Focus areas:
- Connectivity
- Architecture
- Security
- Remote access
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class NetworkDomainGenerator(BaseDomainGenerator):
    """Generator for Network domain reports."""

    domain = "network"
    domain_display_name = "Network"

    def _build_inventory(self) -> tuple:
        """
        Build network inventory section.

        Returns:
            Tuple of (InventorySummary, inventory_html)
        """
        inventory_html = self._build_network_html()
        summary = self._build_summary()
        return summary, inventory_html

    def _build_summary(self) -> InventorySummary:
        """Build network inventory summary."""
        category_counts = self._count_facts_by_category()

        # Extract key metrics
        site_count = 0
        connectivity_items = []
        security_items = []
        vpn_items = []

        for fact in self._domain_facts:
            details = fact.details or {}
            category = fact.category.lower() if fact.category else ""

            if "site_count" in details:
                site_count = details["site_count"]
            if "locations" in details:
                site_count = details["locations"]

            if "connectivity" in category or "wan" in category or "mpls" in category:
                connectivity_items.append(fact.item)
            if "security" in category or "firewall" in category:
                security_items.append(fact.item)
            if "vpn" in category or "remote" in category:
                vpn_items.append(fact.item)

        # Build summary text
        summary_parts = []
        if site_count:
            summary_parts.append(f"{site_count} sites/locations")
        if connectivity_items:
            summary_parts.append(f"{len(connectivity_items)} connectivity components")
        if security_items:
            summary_parts.append(f"{len(security_items)} network security items")

        summary_text = ", ".join(summary_parts) if summary_parts else f"{len(self._domain_facts)} network items"

        # Key items
        key_items = connectivity_items[:2] + security_items[:2] + vpn_items[:1]

        return InventorySummary(
            total_count=len(self._domain_facts),
            by_category=category_counts,
            by_criticality={},
            key_items=key_items[:5],
            summary_text=summary_text,
        )

    def _build_network_html(self) -> str:
        """Build network inventory HTML."""
        if not self._domain_facts:
            return "<p>No network inventory documented</p>"

        # Group by category
        categories = {}
        for fact in self._domain_facts:
            cat = fact.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(fact)

        html_parts = []

        # Overview table
        overview_rows = []
        for cat, facts in sorted(categories.items()):
            items_str = ", ".join([f.item for f in facts[:3]])
            if len(facts) > 3:
                items_str += "..."

            overview_rows.append(f"""
            <tr>
                <td><strong>{cat.replace('_', ' ').title()}</strong></td>
                <td class="count">{len(facts)}</td>
                <td>{items_str}</td>
            </tr>
            """)

        if overview_rows:
            html_parts.append(f"""
            <div class="network-section">
                <h4>Network Overview</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Count</th>
                            <th>Items</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(overview_rows)}
                    </tbody>
                </table>
            </div>
            """)

        # Detailed network components
        key_facts = self._domain_facts[:10]
        if key_facts:
            detail_rows = []
            for fact in key_facts:
                details = fact.details or {}
                vendor = details.get("vendor", details.get("provider", "-"))
                location = details.get("location", details.get("site", "-"))

                detail_rows.append(f"""
                <tr>
                    <td><strong>{fact.item}</strong></td>
                    <td>{fact.category.replace('_', ' ').title() if fact.category else '-'}</td>
                    <td>{vendor}</td>
                    <td>{location}</td>
                    <td><span class="status-{fact.status}">{fact.status}</span></td>
                </tr>
                """)

            html_parts.append(f"""
            <div class="network-section" style="margin-top: 20px;">
                <h4>Network Components</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th>Category</th>
                            <th>Vendor</th>
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

        return f'<div class="network-inventory">{"".join(html_parts)}</div>'

    def get_network_metrics(self) -> dict:
        """Extract network-specific metrics for benchmarking."""
        metrics = {
            "site_count": 0,
            "has_sd_wan": False,
            "has_vpn": False,
            "primary_isp": None,
            "firewall_vendor": None,
        }

        for fact in self._domain_facts:
            details = fact.details or {}
            category = fact.category.lower() if fact.category else ""
            item_lower = fact.item.lower() if fact.item else ""

            if "site_count" in details:
                metrics["site_count"] = details["site_count"]
            elif "locations" in details:
                metrics["site_count"] = details["locations"]

            if "sd-wan" in item_lower or "sd_wan" in category:
                metrics["has_sd_wan"] = True

            if "vpn" in category or "vpn" in item_lower:
                metrics["has_vpn"] = True

            if "firewall" in category and metrics["firewall_vendor"] is None:
                metrics["firewall_vendor"] = details.get("vendor", fact.item)

        return metrics
