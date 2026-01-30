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
) -> ReviewResult:
    """
    Review all items of a given type in the inventory.

    Args:
        inventory_store: The inventory store to review
        api_key: Anthropic API key
        inventory_type: Type to review (default: "application")
        entity: Entity filter ("target" or "buyer")
        model: Claude model to use
        skip_enriched: Skip items that already have enrichment

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

    # Process in batches
    client = Anthropic(api_key=api_key)

    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        batch_reviews = _review_batch(batch, client, model, inventory_type)

        for review in batch_reviews:
            result.reviews.append(review)
            result.items_reviewed += 1

            # Update the inventory item
            item = inventory_store.get_item(review.item_id)
            if item and review.description:
                # Determine category based on LLM response
                if review.is_confident:
                    category = "industry_standard"  # Known software
                else:
                    category = "unknown"

                # Use the set_enrichment method with proper signature
                item.set_enrichment(
                    category=category,
                    note=review.description,
                    confidence="high" if review.is_confident else "low",
                    flag=None,
                )
                # Store additional LLM data in enrichment dict
                item.enrichment["llm_category"] = review.category
                if review.vendor_info:
                    item.enrichment["llm_vendor_info"] = review.vendor_info

                result.items_enriched += 1

            if review.needs_investigation:
                # Flag the item for investigation
                if item:
                    item.set_enrichment(
                        category="unknown",
                        note=review.flag_reason or "LLM could not identify this item",
                        confidence="low",
                        flag="investigate",
                    )
                result.items_flagged += 1

    return result


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
