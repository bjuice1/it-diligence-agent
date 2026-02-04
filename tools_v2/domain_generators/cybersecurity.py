"""
Cybersecurity Domain Generator

Generates DomainReportData for Cybersecurity domain.

Focus areas:
- Controls inventory
- Maturity assessment
- Gap analysis (NIST, ISO)
- Incident response capability
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class CybersecurityDomainGenerator(BaseDomainGenerator):
    """Generator for Cybersecurity domain reports."""

    domain = "cybersecurity"
    domain_display_name = "Cybersecurity"

    def _build_inventory(self) -> tuple:
        """
        Build cybersecurity inventory section.

        Returns:
            Tuple of (InventorySummary, inventory_html)
        """
        inventory_html = self._build_security_html()
        summary = self._build_summary()
        return summary, inventory_html

    def _build_summary(self) -> InventorySummary:
        """Build cybersecurity inventory summary."""
        category_counts = self._count_facts_by_category()

        # Extract key metrics
        endpoint_items = []
        perimeter_items = []
        detection_items = []
        governance_items = []

        for fact in self._domain_facts:
            category = fact.category.lower() if fact.category else ""

            if "endpoint" in category or "edr" in category or "av" in category:
                endpoint_items.append(fact.item)
            elif "perimeter" in category or "firewall" in category or "waf" in category:
                perimeter_items.append(fact.item)
            elif "siem" in category or "detection" in category or "monitoring" in category:
                detection_items.append(fact.item)
            elif "governance" in category or "policy" in category or "compliance" in category:
                governance_items.append(fact.item)

        # Build summary text
        summary_parts = []
        if endpoint_items:
            summary_parts.append(f"{len(endpoint_items)} endpoint security controls")
        if perimeter_items:
            summary_parts.append(f"{len(perimeter_items)} perimeter controls")
        if detection_items:
            summary_parts.append(f"{len(detection_items)} detection/monitoring tools")

        summary_text = ", ".join(summary_parts) if summary_parts else f"{len(self._domain_facts)} security items"

        # Key items
        key_items = endpoint_items[:2] + perimeter_items[:1] + detection_items[:2]

        return InventorySummary(
            total_count=len(self._domain_facts),
            by_category=category_counts,
            by_criticality={},
            key_items=key_items[:5],
            summary_text=summary_text,
        )

    def _build_security_html(self) -> str:
        """Build cybersecurity inventory HTML."""
        if not self._domain_facts:
            return "<p>No cybersecurity inventory documented</p>"

        # Group by category
        categories = {}
        for fact in self._domain_facts:
            cat = fact.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(fact)

        html_parts = []

        # Security controls overview
        control_categories = [
            ("endpoint", "Endpoint Security"),
            ("perimeter", "Perimeter Security"),
            ("detection", "Detection & Response"),
            ("email", "Email Security"),
            ("data", "Data Security"),
            ("governance", "Governance"),
        ]

        control_rows = []
        for cat_key, cat_label in control_categories:
            matching = [f for f in self._domain_facts
                       if cat_key in (f.category or "").lower()]
            if matching:
                items = [f.item for f in matching[:3]]
                items_str = ", ".join(items)
                if len(matching) > 3:
                    items_str += "..."

                control_rows.append(f"""
                <tr>
                    <td><strong>{cat_label}</strong></td>
                    <td class="count">{len(matching)}</td>
                    <td>{items_str}</td>
                </tr>
                """)

        # Add remaining categories
        covered = [c[0] for c in control_categories]
        for cat, facts in categories.items():
            if cat.lower() not in covered and cat != "other":
                items_str = ", ".join([f.item for f in facts[:3]])
                if len(facts) > 3:
                    items_str += "..."

                control_rows.append(f"""
                <tr>
                    <td><strong>{cat.replace('_', ' ').title()}</strong></td>
                    <td class="count">{len(facts)}</td>
                    <td>{items_str}</td>
                </tr>
                """)

        if control_rows:
            html_parts.append(f"""
            <div class="security-section">
                <h4>Security Controls Overview</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Control Category</th>
                            <th>Count</th>
                            <th>Tools/Products</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(control_rows)}
                    </tbody>
                </table>
            </div>
            """)

        # Detailed security tools
        key_facts = self._domain_facts[:10]
        if key_facts:
            detail_rows = []
            for fact in key_facts:
                details = fact.details or {}
                vendor = details.get("vendor", details.get("provider", "-"))
                coverage = details.get("coverage", details.get("scope", "-"))

                detail_rows.append(f"""
                <tr>
                    <td><strong>{fact.item}</strong></td>
                    <td>{fact.category.replace('_', ' ').title() if fact.category else '-'}</td>
                    <td>{vendor}</td>
                    <td>{coverage}</td>
                    <td><span class="status-{fact.status}">{fact.status}</span></td>
                </tr>
                """)

            html_parts.append(f"""
            <div class="security-section" style="margin-top: 20px;">
                <h4>Security Tools & Products</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Tool/Product</th>
                            <th>Category</th>
                            <th>Vendor</th>
                            <th>Coverage</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(detail_rows)}
                    </tbody>
                </table>
            </div>
            """)

        return f'<div class="security-inventory">{"".join(html_parts)}</div>'

    def get_security_metrics(self) -> dict:
        """Extract cybersecurity-specific metrics for benchmarking."""
        metrics = {
            "has_edr": False,
            "has_siem": False,
            "has_mfa": False,
            "has_pam": False,
            "has_ir_plan": False,
            "security_budget_pct": None,
            "control_count": len(self._domain_facts),
        }

        for fact in self._domain_facts:
            details = fact.details or {}
            item_lower = fact.item.lower() if fact.item else ""
            category = fact.category.lower() if fact.category else ""

            if "edr" in item_lower or "edr" in category or "endpoint detection" in item_lower:
                metrics["has_edr"] = True

            if "siem" in item_lower or "siem" in category:
                metrics["has_siem"] = True

            if "mfa" in item_lower or "multi-factor" in item_lower or "2fa" in item_lower:
                metrics["has_mfa"] = True

            if "pam" in item_lower or "privileged access" in item_lower:
                metrics["has_pam"] = True

            if "incident response" in item_lower or "ir plan" in item_lower:
                metrics["has_ir_plan"] = True

            if "security_budget_pct" in details:
                metrics["security_budget_pct"] = details["security_budget_pct"]

        return metrics
