"""
Delta Comparator Service

Compares Target vs Buyer dossiers to identify integration considerations.
Phase 8 - Entity Separation Fix Plan

Key features:
- Match items by canonical key or name
- Compute attribute differences
- Flag vendor/platform mismatches
- Generate integration notes
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set

logger = logging.getLogger(__name__)


@dataclass
class DeltaResult:
    """Result of comparing target vs buyer item."""
    target_item: Optional[Any]  # ItemDossier or None
    buyer_item: Optional[Any]   # ItemDossier or None
    match_type: str             # "matched", "target_only", "buyer_only"
    attribute_diffs: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)  # field -> (target_val, buyer_val)
    is_vendor_mismatch: bool = False
    is_version_mismatch: bool = False
    is_platform_mismatch: bool = False
    integration_notes: List[str] = field(default_factory=list)
    integration_complexity: str = "low"  # "low", "medium", "high"

    @property
    def item_name(self) -> str:
        """Get the item name from whichever side exists."""
        if self.target_item:
            return self.target_item.name
        elif self.buyer_item:
            return self.buyer_item.name
        return "Unknown"


class DeltaComparator:
    """
    Real diff engine for Target vs Buyer comparison.

    Matches items and computes meaningful differences for integration planning.
    """

    # Attributes where mismatch indicates integration complexity
    MEANINGFUL_DIFF_FIELDS = {'vendor', 'version', 'platform', 'hosting', 'region', 'database', 'technology'}

    # Attributes where mismatch is just scale/size difference
    SCALE_DIFF_FIELDS = {'user_count', 'cost', 'annual_cost', 'headcount', 'capacity', 'license_count'}

    # Fields that indicate high complexity if mismatched
    HIGH_COMPLEXITY_FIELDS = {'vendor', 'platform', 'database'}

    def __init__(self):
        self.match_stats = {
            'matched': 0,
            'target_only': 0,
            'buyer_only': 0,
            'vendor_mismatches': 0,
        }

    def match_items(
        self,
        target_dossiers: List[Any],
        buyer_dossiers: List[Any]
    ) -> List[DeltaResult]:
        """
        Match target items to buyer items and compute deltas.

        Args:
            target_dossiers: List of ItemDossier from target entity
            buyer_dossiers: List of ItemDossier from buyer entity

        Returns:
            List of DeltaResult with match info and diffs
        """
        results = []

        # Reset stats
        self.match_stats = {
            'matched': 0,
            'target_only': 0,
            'buyer_only': 0,
            'vendor_mismatches': 0,
        }

        # Index buyer items by canonical key and name for matching
        buyer_by_key = {}
        buyer_by_name = {}

        for d in buyer_dossiers:
            # Index by canonical key if available
            canonical = getattr(d, 'canonical_key', '')
            if canonical:
                # Extract item portion from canonical key (entity:domain:item:...)
                parts = canonical.split(':')
                if len(parts) >= 3:
                    # Create a buyer-agnostic key for matching
                    item_key = ':'.join(parts[1:])  # Skip entity
                    buyer_by_key[item_key] = d

            # Also index by normalized name
            name_key = d.name.lower().strip()
            buyer_by_name[name_key] = d

        matched_buyer_items: Set[str] = set()

        # Process target items
        for target in target_dossiers:
            buyer = None

            # Try canonical key match first (most accurate)
            canonical = getattr(target, 'canonical_key', '')
            if canonical:
                parts = canonical.split(':')
                if len(parts) >= 3:
                    item_key = ':'.join(parts[1:])
                    buyer = buyer_by_key.get(item_key)

            # Fall back to name match
            if not buyer:
                name_key = target.name.lower().strip()
                buyer = buyer_by_name.get(name_key)

            if buyer:
                # Matched!
                buyer_id = id(buyer)
                matched_buyer_items.add(buyer_id)
                delta = self._compute_delta(target, buyer)
                results.append(delta)
                self.match_stats['matched'] += 1
                if delta.is_vendor_mismatch:
                    self.match_stats['vendor_mismatches'] += 1
            else:
                # Target only
                results.append(DeltaResult(
                    target_item=target,
                    buyer_item=None,
                    match_type="target_only",
                    attribute_diffs={},
                    is_vendor_mismatch=False,
                    is_version_mismatch=False,
                    integration_notes=["No matching buyer system found - new for integration"],
                    integration_complexity="low"
                ))
                self.match_stats['target_only'] += 1

        # Add buyer-only items
        for buyer in buyer_dossiers:
            if id(buyer) not in matched_buyer_items:
                results.append(DeltaResult(
                    target_item=None,
                    buyer_item=buyer,
                    match_type="buyer_only",
                    attribute_diffs={},
                    is_vendor_mismatch=False,
                    is_version_mismatch=False,
                    integration_notes=["Buyer system with no target equivalent - potential consolidation target"],
                    integration_complexity="low"
                ))
                self.match_stats['buyer_only'] += 1

        # Sort by complexity (high first), then by match type, then by name
        complexity_order = {'high': 0, 'medium': 1, 'low': 2}
        type_order = {'matched': 0, 'target_only': 1, 'buyer_only': 2}
        results.sort(key=lambda r: (
            complexity_order.get(r.integration_complexity, 3),
            type_order.get(r.match_type, 3),
            r.item_name.lower()
        ))

        return results

    def _compute_delta(self, target: Any, buyer: Any) -> DeltaResult:
        """
        Compute attribute differences between matched items.

        Args:
            target: Target ItemDossier
            buyer: Buyer ItemDossier

        Returns:
            DeltaResult with differences and integration notes
        """
        diffs: Dict[str, Tuple[Any, Any]] = {}
        notes: List[str] = []

        target_attrs = getattr(target, 'attributes', {}) or {}
        buyer_attrs = getattr(buyer, 'attributes', {}) or {}

        all_keys = set(target_attrs.keys()) | set(buyer_attrs.keys())

        for key in all_keys:
            t_val = target_attrs.get(key)
            b_val = buyer_attrs.get(key)

            # Skip if both are empty/None
            if not t_val and not b_val:
                continue

            # Normalize for comparison
            t_norm = str(t_val).lower().strip() if t_val else ''
            b_norm = str(b_val).lower().strip() if b_val else ''

            if t_norm != b_norm:
                diffs[key] = (t_val, b_val)

                if key in self.MEANINGFUL_DIFF_FIELDS:
                    notes.append(f"{key.replace('_', ' ').title()}: Target={t_val or 'N/A'} vs Buyer={b_val or 'N/A'}")

        # Determine specific mismatch types
        is_vendor_mismatch = 'vendor' in diffs
        is_version_mismatch = 'version' in diffs
        is_platform_mismatch = 'platform' in diffs or 'hosting' in diffs

        # Calculate integration complexity
        complexity = "low"
        high_complexity_count = sum(1 for k in diffs if k in self.HIGH_COMPLEXITY_FIELDS)

        if is_vendor_mismatch or high_complexity_count >= 2:
            complexity = "high"
            notes.insert(0, "⚠️ HIGH COMPLEXITY - Vendor/platform mismatch requires significant integration effort")
        elif len(diffs) >= 3 or is_platform_mismatch:
            complexity = "medium"
            notes.insert(0, "⚡ MEDIUM COMPLEXITY - Multiple differences require planning")

        # Add consolidation opportunity note
        if not is_vendor_mismatch and len(diffs) <= 2:
            notes.append("✓ Good consolidation candidate - same vendor/platform")

        return DeltaResult(
            target_item=target,
            buyer_item=buyer,
            match_type="matched",
            attribute_diffs=diffs,
            is_vendor_mismatch=is_vendor_mismatch,
            is_version_mismatch=is_version_mismatch,
            is_platform_mismatch=is_platform_mismatch,
            integration_notes=notes,
            integration_complexity=complexity
        )

    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics from last comparison."""
        return self.match_stats.copy()


def render_delta_html(
    deltas: List[DeltaResult],
    domain: str,
    target_name: str = "Target",
    buyer_name: str = "Buyer"
) -> str:
    """
    Render delta comparison results to HTML.

    Args:
        deltas: List of DeltaResult from comparison
        domain: Domain name
        target_name: Target company name
        buyer_name: Buyer company name

    Returns:
        HTML string
    """
    # Count by type
    matched_count = len([d for d in deltas if d.match_type == "matched"])
    target_only_count = len([d for d in deltas if d.match_type == "target_only"])
    buyer_only_count = len([d for d in deltas if d.match_type == "buyer_only"])
    vendor_mismatch_count = len([d for d in deltas if d.is_vendor_mismatch])
    high_complexity_count = len([d for d in deltas if d.integration_complexity == "high"])

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{domain.replace('_', ' ').title()} - Integration Delta</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #6f42c1; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }}
        .stat {{ background: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; min-width: 120px; }}
        .stat .count {{ font-size: 1.8em; font-weight: bold; }}
        .stat.matched .count {{ color: #28a745; }}
        .stat.target-only .count {{ color: #007bff; }}
        .stat.buyer-only .count {{ color: #6f42c1; }}
        .stat.mismatch .count {{ color: #dc3545; }}

        .delta-item {{ background: white; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
        .delta-header {{ padding: 15px 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .delta-header.matched {{ border-left: 5px solid #28a745; background: #f8fff8; }}
        .delta-header.target-only {{ border-left: 5px solid #007bff; background: #f8f9ff; }}
        .delta-header.buyer-only {{ border-left: 5px solid #6f42c1; background: #f9f8ff; }}
        .delta-header.high {{ border-left: 5px solid #dc3545; background: #fff8f8; }}

        .complexity-badge {{ padding: 4px 10px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}
        .complexity-badge.high {{ background: #dc3545; color: white; }}
        .complexity-badge.medium {{ background: #ffc107; color: black; }}
        .complexity-badge.low {{ background: #28a745; color: white; }}

        .delta-content {{ display: none; padding: 15px 20px; border-top: 1px solid #eee; }}
        .delta-item.open .delta-content {{ display: block; }}

        .diff-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .diff-table th, .diff-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .diff-table th {{ background: #f8f9fa; font-weight: 600; }}
        .diff-value {{ padding: 4px 8px; border-radius: 4px; }}
        .diff-value.target {{ background: #e7f3ff; }}
        .diff-value.buyer {{ background: #f3e8ff; }}

        .notes {{ margin-top: 15px; padding: 10px 15px; background: #f8f9fa; border-radius: 4px; }}
        .notes li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>⚡ {domain.replace('_', ' ').title()} - Integration Delta</h1>
    <p style="color: #666;">Comparing {target_name} vs {buyer_name}</p>

    <div class="summary">
        <div class="stat matched">
            <div class="count">{matched_count}</div>
            <div>Matched</div>
        </div>
        <div class="stat target-only">
            <div class="count">{target_only_count}</div>
            <div>Target Only</div>
        </div>
        <div class="stat buyer-only">
            <div class="count">{buyer_only_count}</div>
            <div>Buyer Only</div>
        </div>
        <div class="stat mismatch">
            <div class="count">{vendor_mismatch_count}</div>
            <div>Vendor Mismatches</div>
        </div>
        <div class="stat mismatch">
            <div class="count">{high_complexity_count}</div>
            <div>High Complexity</div>
        </div>
    </div>
"""

    # Render each delta item
    for delta in deltas:
        header_class = delta.match_type
        if delta.integration_complexity == "high":
            header_class = "high"

        # Item name and badges
        name = delta.item_name
        complexity_badge = f'<span class="complexity-badge {delta.integration_complexity}">{delta.integration_complexity.upper()}</span>'

        # Type indicator
        type_indicator = ""
        if delta.match_type == "matched":
            type_indicator = "✓ Matched"
        elif delta.match_type == "target_only":
            type_indicator = "→ Target Only"
        elif delta.match_type == "buyer_only":
            type_indicator = "← Buyer Only"

        html += f"""
    <div class="delta-item" onclick="this.classList.toggle('open')">
        <div class="delta-header {header_class}">
            <div>
                <strong>{name}</strong>
                <span style="color: #666; margin-left: 10px;">{type_indicator}</span>
            </div>
            <div>
                {complexity_badge}
                {'<span style="color: #dc3545; margin-left: 10px;">⚠️ Vendor Mismatch</span>' if delta.is_vendor_mismatch else ''}
            </div>
        </div>
        <div class="delta-content">
"""

        # Attribute differences table
        if delta.attribute_diffs:
            html += """
            <table class="diff-table">
                <tr><th>Attribute</th><th>Target</th><th>Buyer</th></tr>
"""
            for attr, (t_val, b_val) in delta.attribute_diffs.items():
                html += f"""
                <tr>
                    <td><strong>{attr.replace('_', ' ').title()}</strong></td>
                    <td><span class="diff-value target">{t_val or 'N/A'}</span></td>
                    <td><span class="diff-value buyer">{b_val or 'N/A'}</span></td>
                </tr>
"""
            html += "</table>"
        else:
            if delta.match_type == "matched":
                html += "<p>✓ No significant differences found</p>"

        # Integration notes
        if delta.integration_notes:
            html += """
            <div class="notes">
                <strong>Integration Notes:</strong>
                <ul>
"""
            for note in delta.integration_notes:
                html += f"<li>{note}</li>"
            html += """
                </ul>
            </div>
"""

        html += """
        </div>
    </div>
"""

    html += """
    <script>
        // Auto-expand high complexity items
        document.querySelectorAll('.delta-header.high').forEach(h => {
            h.parentElement.classList.add('open');
        });
    </script>
</body>
</html>"""

    return html
