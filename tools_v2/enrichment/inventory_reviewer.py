"""
Inventory Reviewer

LLM-based review of inventory items.
- Looks up each application/system
- Adds description if LLM knows about it
- Flags items when LLM is uncertain (needs_investigation)

Philosophy: Don't N/A things that Claude/GPT can answer.
Only flag when the LLM itself doesn't know.
"""

import logging
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem
from stores.app_category_mappings import (
    lookup_app,
    categorize_app_simple,
    CATEGORY_DEFINITIONS,
    get_category_description,
)

logger = logging.getLogger(__name__)

# Batch size for LLM calls (process multiple items per call for efficiency)
BATCH_SIZE = 10


@dataclass
class ItemReview:
    """Result of reviewing a single inventory item."""
    item_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # e.g., "CRM", "ERP", "Insurance"
    vendor_info: Optional[str] = None
    is_confident: bool = True
    needs_investigation: bool = False
    flag_reason: Optional[str] = None


@dataclass
class ReviewResult:
    """Result of reviewing inventory items."""
    items_reviewed: int = 0
    items_enriched: int = 0
    items_flagged: int = 0
    reviews: List[ItemReview] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Reviewed: {self.items_reviewed} items",
            f"Enriched: {self.items_enriched} items (LLM provided description)",
            f"Flagged: {self.items_flagged} items (needs investigation)",
        ]
        if self.items_flagged > 0:
            lines.append("\nFlagged items:")
            for review in self.reviews:
                if review.needs_investigation:
                    lines.append(f"  - {review.name}: {review.flag_reason}")
        return "\n".join(lines)


def review_inventory(
    inventory_store: InventoryStore,
    api_key: str,
    inventory_type: str = "application",
    entity: str = "target",
    model: str = "claude-sonnet-4-20250514",
    skip_enriched: bool = True,
    use_local_mappings: bool = True,
) -> ReviewResult:
    """
    Review all items of a given type in the inventory.

    First attempts to enrich using local app mappings (no LLM cost),
    then sends remaining unknown items to LLM for review.

    Args:
        inventory_store: The inventory store to review
        api_key: Anthropic API key
        inventory_type: Type to review (default: "application")
        entity: Entity filter ("target" or "buyer")
        model: Claude model to use
        skip_enriched: Skip items that already have enrichment
        use_local_mappings: Try local app mappings before LLM (default: True)

    Returns:
        ReviewResult with statistics and individual reviews
    """
    result = ReviewResult()

    # Get items to review
    items = inventory_store.get_items(
        inventory_type=inventory_type,
        entity=entity,
        status="active"
    )

    if skip_enriched:
        items = [i for i in items if not i.enrichment.get("llm_description")]

    if not items:
        logger.info("No items to review")
        return result

    # Phase 1: Try local app mappings first (no LLM cost)
    items_for_llm = []
    local_enriched = 0

    if use_local_mappings and inventory_type == "application":
        for item in items:
            review = _try_local_lookup(item)
            if review and review.description:
                # Successfully enriched from local mappings
                result.reviews.append(review)
                result.items_reviewed += 1

                # Update the inventory item
                item.set_enrichment(
                    category="industry_standard",
                    note=review.description,
                    confidence="high",
                    flag=None,
                )
                item.enrichment["app_category"] = review.category
                item.enrichment["enrichment_source"] = "local_mappings"
                if review.vendor_info:
                    item.enrichment["vendor_info"] = review.vendor_info

                result.items_enriched += 1
                local_enriched += 1
            else:
                # Not found in local mappings - queue for LLM
                items_for_llm.append(item)

        logger.info(f"Local mappings enriched {local_enriched}/{len(items)} items")
    else:
        items_for_llm = items

    # Phase 2: Send remaining items to LLM
    if items_for_llm and api_key:
        client = Anthropic(api_key=api_key)

        for i in range(0, len(items_for_llm), BATCH_SIZE):
            batch = items_for_llm[i:i + BATCH_SIZE]
            batch_reviews = _review_batch(batch, client, model, inventory_type)

            for review in batch_reviews:
                result.reviews.append(review)
                result.items_reviewed += 1

                # Update the inventory item
                item = inventory_store.get_item(review.item_id)
                if item and review.description:
                    # Determine category based on LLM response
                    if review.is_confident:
                        category = "industry_standard"
                    else:
                        category = "unknown"

                    item.set_enrichment(
                        category=category,
                        note=review.description,
                        confidence="high" if review.is_confident else "low",
                        flag=None,
                    )
                    item.enrichment["app_category"] = review.category
                    item.enrichment["enrichment_source"] = "llm"
                    if review.vendor_info:
                        item.enrichment["vendor_info"] = review.vendor_info

                    result.items_enriched += 1

                if review.needs_investigation:
                    if item:
                        item.set_enrichment(
                            category="unknown",
                            note=review.flag_reason or "LLM could not identify this item",
                            confidence="low",
                            flag="investigate",
                        )
                    result.items_flagged += 1
    elif items_for_llm:
        # No API key but have items - flag them
        for item in items_for_llm:
            review = ItemReview(
                item_id=item.item_id,
                name=item.data.get("name", "Unknown"),
                needs_investigation=True,
                flag_reason="Not in local mappings; no API key for LLM lookup",
            )
            result.reviews.append(review)
            result.items_reviewed += 1
            result.items_flagged += 1

    return result


def _try_local_lookup(item: InventoryItem) -> Optional[ItemReview]:
    """
    Try to enrich an item using local app category mappings.

    Args:
        item: The inventory item to look up

    Returns:
        ItemReview if found in mappings, None otherwise
    """
    name = item.data.get("name", "")
    if not name:
        return None

    mapping = lookup_app(name)
    if not mapping:
        return None

    return ItemReview(
        item_id=item.item_id,
        name=name,
        description=mapping.description,
        category=mapping.category,
        vendor_info=mapping.vendor,
        is_confident=True,
        needs_investigation=False,
    )


def review_item(
    item: InventoryItem,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> ItemReview:
    """
    Review a single inventory item.

    Args:
        item: The inventory item to review
        api_key: Anthropic API key
        model: Claude model to use

    Returns:
        ItemReview with description or flag
    """
    client = Anthropic(api_key=api_key)
    reviews = _review_batch([item], client, model, item.inventory_type)
    return reviews[0] if reviews else ItemReview(
        item_id=item.item_id,
        name=item.data.get("name", "Unknown"),
        needs_investigation=True,
        flag_reason="Review failed"
    )


def _review_batch(
    items: List[InventoryItem],
    client: Anthropic,
    model: str,
    inventory_type: str,
) -> List[ItemReview]:
    """Review a batch of items with a single LLM call."""

    # Build the prompt
    item_list = []
    for item in items:
        name = item.data.get("name", "Unknown")
        vendor = item.data.get("vendor", "")
        version = item.data.get("version", "")

        entry = f"- {name}"
        if vendor:
            entry += f" (Vendor: {vendor})"
        if version:
            entry += f" [Version: {version}]"
        item_list.append(entry)

    items_text = "\n".join(item_list)

    if inventory_type == "application":
        type_context = "software applications/systems"
    elif inventory_type == "infrastructure":
        type_context = "infrastructure components (servers, VMs, network devices)"
    elif inventory_type == "vendor":
        type_context = "vendor/supplier relationships"
    else:
        type_context = inventory_type

    prompt = f"""You are reviewing {type_context} from an IT inventory for a due diligence engagement.

For each item below, provide:
1. A brief description of what it is/does (1-2 sentences)
2. A category (e.g., CRM, ERP, Database, Insurance Platform, etc.)
3. Any relevant vendor information you know
4. Your confidence: "confident" if you know this product, "uncertain" if you're not sure

If you genuinely cannot identify an item (it appears to be a custom/internal system or you have no information), mark confidence as "unknown" and we'll flag it for investigation.

Items to review:
{items_text}

Respond in JSON format:
{{
  "reviews": [
    {{
      "name": "Item Name",
      "description": "What it is and does",
      "category": "Category",
      "vendor_info": "Any vendor details",
      "confidence": "confident|uncertain|unknown"
    }}
  ]
}}

Be honest about uncertainty. It's better to flag something for human review than guess."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())
        reviews_data = data.get("reviews", [])

        # Map reviews back to items
        reviews = []
        for i, item in enumerate(items):
            item_name = item.data.get("name", "Unknown")

            # Find matching review (by name, fuzzy match)
            review_data = None
            for rd in reviews_data:
                if rd.get("name", "").lower().strip() == item_name.lower().strip():
                    review_data = rd
                    break

            # Fallback to index if no name match
            if review_data is None and i < len(reviews_data):
                review_data = reviews_data[i]

            if review_data:
                confidence = review_data.get("confidence", "confident").lower()
                is_confident = confidence == "confident"
                needs_investigation = confidence == "unknown"

                review = ItemReview(
                    item_id=item.item_id,
                    name=item_name,
                    description=review_data.get("description"),
                    category=review_data.get("category"),
                    vendor_info=review_data.get("vendor_info"),
                    is_confident=is_confident,
                    needs_investigation=needs_investigation,
                    flag_reason="LLM could not identify this item" if needs_investigation else None,
                )
            else:
                # No review data for this item
                review = ItemReview(
                    item_id=item.item_id,
                    name=item_name,
                    needs_investigation=True,
                    flag_reason="No LLM review returned",
                )

            reviews.append(review)

        return reviews

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        # Return flagged reviews for all items
        return [
            ItemReview(
                item_id=item.item_id,
                name=item.data.get("name", "Unknown"),
                needs_investigation=True,
                flag_reason="LLM response parse error",
            )
            for item in items
        ]
    except Exception as e:
        logger.error(f"LLM review failed: {e}")
        return [
            ItemReview(
                item_id=item.item_id,
                name=item.data.get("name", "Unknown"),
                needs_investigation=True,
                flag_reason=f"LLM error: {str(e)}",
            )
            for item in items
        ]


def get_flagged_items(inventory_store: InventoryStore) -> List[InventoryItem]:
    """Get all items flagged as needing investigation."""
    all_items = inventory_store.get_items()
    return [item for item in all_items if item.needs_investigation]


def clear_flag(item: InventoryItem) -> None:
    """Clear the investigation flag from an item."""
    if item.enrichment:
        item.enrichment["flag"] = None


def validate_category(category: str) -> bool:
    """
    Validate that a category is in the defined list.

    Args:
        category: Category string to validate

    Returns:
        True if valid, False otherwise
    """
    if not category:
        return False
    return category.lower() in CATEGORY_DEFINITIONS


def normalize_category(category: str) -> str:
    """
    Normalize a category to match defined categories.

    Handles common aliases and variations.

    Args:
        category: Category string (possibly with variations)

    Returns:
        Normalized category or "unknown" if not recognized
    """
    if not category:
        return "unknown"

    cat_lower = category.lower().strip()

    # Direct match
    if cat_lower in CATEGORY_DEFINITIONS:
        return cat_lower

    # Common aliases
    aliases = {
        "erp": ["enterprise resource planning", "erp system"],
        "crm": ["customer relationship management", "sales"],
        "hcm": ["hr", "human resources", "hrms", "hris", "payroll"],
        "finance": ["accounting", "financial", "ap", "ar", "accounts payable", "accounts receivable"],
        "collaboration": ["communication", "chat", "messaging", "video conferencing"],
        "productivity": ["office", "documents", "file storage", "content management"],
        "security": ["identity", "iam", "sso", "mfa", "endpoint", "edr", "siem"],
        "infrastructure": ["cloud", "virtualization", "platform", "iaas", "paas"],
        "database": ["data platform", "data warehouse", "rdbms", "nosql"],
        "devops": ["development", "ci/cd", "itsm", "monitoring", "apm"],
        "bi_analytics": ["bi", "business intelligence", "analytics", "reporting", "visualization"],
        "industry_vertical": ["vertical", "healthcare", "insurance", "manufacturing", "retail"],
        "custom": ["in-house", "internal", "proprietary", "homegrown"],
    }

    for std_cat, alias_list in aliases.items():
        if cat_lower in alias_list or any(alias in cat_lower for alias in alias_list):
            return std_cat

    return "unknown"


def suggest_category(app_name: str) -> Optional[str]:
    """
    Suggest a category for an application based on its name.

    Uses local app mappings to determine category.

    Args:
        app_name: Application name

    Returns:
        Suggested category or None if unknown
    """
    category, mapping = categorize_app_simple(app_name)
    if category != "unknown":
        return category
    return None


def validate_inventory_categories(
    inventory_store: InventoryStore,
    inventory_type: str = "application",
) -> Dict[str, Any]:
    """
    Validate categories for all items in the inventory.

    Returns summary of valid, invalid, and unknown categories.

    Args:
        inventory_store: The inventory store to validate
        inventory_type: Type to validate

    Returns:
        Dict with validation summary
    """
    items = inventory_store.get_items(inventory_type=inventory_type)

    valid = []
    invalid = []
    unknown = []
    missing = []

    for item in items:
        category = item.data.get("category", "")
        app_category = item.enrichment.get("app_category", "")

        # Use enrichment category if data category is empty
        effective_category = category or app_category

        if not effective_category:
            missing.append({
                "item_id": item.item_id,
                "name": item.data.get("name", "Unknown"),
            })
        elif validate_category(effective_category):
            valid.append({
                "item_id": item.item_id,
                "name": item.data.get("name", "Unknown"),
                "category": effective_category,
            })
        elif normalize_category(effective_category) != "unknown":
            # Can be normalized
            normalized = normalize_category(effective_category)
            invalid.append({
                "item_id": item.item_id,
                "name": item.data.get("name", "Unknown"),
                "category": effective_category,
                "suggested": normalized,
            })
        else:
            unknown.append({
                "item_id": item.item_id,
                "name": item.data.get("name", "Unknown"),
                "category": effective_category,
            })

    return {
        "total": len(items),
        "valid": len(valid),
        "invalid": len(invalid),
        "unknown": len(unknown),
        "missing": len(missing),
        "valid_items": valid,
        "invalid_items": invalid,
        "unknown_items": unknown,
        "missing_items": missing,
    }
