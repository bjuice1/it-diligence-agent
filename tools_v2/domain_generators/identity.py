"""
Identity & Access Domain Generator

Generates DomainReportData for Identity & Access domain.

Focus areas:
- IAM platform
- MFA coverage
- PAM implementation
- Access governance maturity
"""

import logging
from typing import Optional, TYPE_CHECKING

from tools_v2.domain_generators.base import BaseDomainGenerator
from tools_v2.pe_report_schemas import InventorySummary

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


class IdentityDomainGenerator(BaseDomainGenerator):
    """Generator for Identity & Access domain reports."""

    domain = "identity_access"
    domain_display_name = "Identity & Access"

    def _build_inventory(self) -> tuple:
        """
        Build identity inventory section.

        Returns:
            Tuple of (InventorySummary, inventory_html)
        """
        inventory_html = self._build_identity_html()
        summary = self._build_summary()
        return summary, inventory_html

    def _build_summary(self) -> InventorySummary:
        """Build identity inventory summary."""
        category_counts = self._count_facts_by_category()

        # Extract key metrics
        identity_items = []
        auth_items = []
        pam_items = []
        governance_items = []

        for fact in self._domain_facts:
            category = fact.category.lower() if fact.category else ""
            item_lower = fact.item.lower() if fact.item else ""

            if "identity" in category or "idp" in category or "directory" in category:
                identity_items.append(fact.item)
            elif "auth" in category or "mfa" in category or "sso" in category:
                auth_items.append(fact.item)
            elif "pam" in category or "privileged" in category:
                pam_items.append(fact.item)
            elif "governance" in category or "access review" in item_lower:
                governance_items.append(fact.item)

        # Build summary text
        summary_parts = []
        if identity_items:
            summary_parts.append(f"{len(identity_items)} identity platforms")
        if auth_items:
            summary_parts.append(f"{len(auth_items)} authentication methods")
        if pam_items:
            summary_parts.append(f"{len(pam_items)} PAM tools")

        summary_text = ", ".join(summary_parts) if summary_parts else f"{len(self._domain_facts)} identity items"

        # Key items
        key_items = identity_items[:2] + auth_items[:2] + pam_items[:1]

        return InventorySummary(
            total_count=len(self._domain_facts),
            by_category=category_counts,
            by_criticality={},
            key_items=key_items[:5],
            summary_text=summary_text,
        )

    def _build_identity_html(self) -> str:
        """Build identity inventory HTML."""
        if not self._domain_facts:
            return "<p>No identity & access inventory documented</p>"

        # Group by category
        categories = {}
        for fact in self._domain_facts:
            cat = fact.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(fact)

        html_parts = []

        # IAM capability overview
        iam_categories = [
            ("identity", "Identity Management"),
            ("authentication", "Authentication"),
            ("authorization", "Authorization"),
            ("pam", "Privileged Access"),
            ("governance", "Access Governance"),
            ("lifecycle", "Identity Lifecycle"),
        ]

        iam_rows = []
        for cat_key, cat_label in iam_categories:
            matching = [f for f in self._domain_facts
                       if cat_key in (f.category or "").lower() or cat_key in (f.item or "").lower()]
            if matching:
                items = [f.item for f in matching[:3]]
                items_str = ", ".join(items)
                if len(matching) > 3:
                    items_str += "..."

                iam_rows.append(f"""
                <tr>
                    <td><strong>{cat_label}</strong></td>
                    <td class="count">{len(matching)}</td>
                    <td>{items_str}</td>
                </tr>
                """)

        # Add remaining categories
        covered = [c[0] for c in iam_categories]
        for cat, facts in categories.items():
            cat_lower = cat.lower()
            if not any(c in cat_lower for c in covered) and cat != "other":
                items_str = ", ".join([f.item for f in facts[:3]])
                if len(facts) > 3:
                    items_str += "..."

                iam_rows.append(f"""
                <tr>
                    <td><strong>{cat.replace('_', ' ').title()}</strong></td>
                    <td class="count">{len(facts)}</td>
                    <td>{items_str}</td>
                </tr>
                """)

        if iam_rows:
            html_parts.append(f"""
            <div class="identity-section">
                <h4>IAM Capability Overview</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>Capability</th>
                            <th>Count</th>
                            <th>Tools/Systems</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(iam_rows)}
                    </tbody>
                </table>
            </div>
            """)

        # Detailed identity systems
        key_facts = self._domain_facts[:10]
        if key_facts:
            detail_rows = []
            for fact in key_facts:
                details = fact.details or {}
                vendor = details.get("vendor", details.get("provider", "-"))
                users = details.get("user_count", details.get("users", "-"))
                deployment = details.get("deployment", details.get("type", "-"))

                detail_rows.append(f"""
                <tr>
                    <td><strong>{fact.item}</strong></td>
                    <td>{fact.category.replace('_', ' ').title() if fact.category else '-'}</td>
                    <td>{vendor}</td>
                    <td>{users}</td>
                    <td><span class="status-{fact.status}">{fact.status}</span></td>
                </tr>
                """)

            html_parts.append(f"""
            <div class="identity-section" style="margin-top: 20px;">
                <h4>Identity Systems & Tools</h4>
                <table class="inventory-table">
                    <thead>
                        <tr>
                            <th>System</th>
                            <th>Category</th>
                            <th>Vendor</th>
                            <th>Users</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(detail_rows)}
                    </tbody>
                </table>
            </div>
            """)

        return f'<div class="identity-inventory">{"".join(html_parts)}</div>'

    def get_identity_metrics(self) -> dict:
        """Extract identity-specific metrics for benchmarking."""
        metrics = {
            "primary_idp": None,
            "has_sso": False,
            "has_mfa": False,
            "mfa_coverage_pct": None,
            "has_pam": False,
            "has_access_reviews": False,
            "identity_provider_count": 0,
        }

        for fact in self._domain_facts:
            details = fact.details or {}
            item_lower = fact.item.lower() if fact.item else ""
            category = fact.category.lower() if fact.category else ""

            if "identity" in category or "idp" in category or "directory" in category:
                metrics["identity_provider_count"] += 1
                if metrics["primary_idp"] is None:
                    metrics["primary_idp"] = fact.item

            if "sso" in item_lower or "single sign" in item_lower:
                metrics["has_sso"] = True

            if "mfa" in item_lower or "multi-factor" in item_lower or "2fa" in item_lower:
                metrics["has_mfa"] = True
                if "mfa_coverage" in details:
                    metrics["mfa_coverage_pct"] = details["mfa_coverage"]

            if "pam" in item_lower or "privileged access" in item_lower:
                metrics["has_pam"] = True

            if "access review" in item_lower or "certification" in item_lower:
                metrics["has_access_reviews"] = True

        return metrics
