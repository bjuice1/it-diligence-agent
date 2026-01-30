"""
Tests for Phase 3: LLM-based Inventory Enrichment

Tests:
1. ItemReview and ReviewResult models
2. Batch review formatting
3. Flag handling
4. Integration with InventoryStore
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from tools_v2.enrichment.inventory_reviewer import (
    review_inventory,
    review_item,
    ReviewResult,
    ItemReview,
    get_flagged_items,
    clear_flag,
    _review_batch,
)
from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem


# =============================================================================
# Model Tests
# =============================================================================

class TestItemReview:
    """Tests for ItemReview dataclass."""

    def test_create_confident_review(self):
        """Confident review should have description and no flag."""
        review = ItemReview(
            item_id="I-APP-abc123",
            name="Salesforce",
            description="Customer relationship management platform",
            category="CRM",
            is_confident=True,
            needs_investigation=False,
        )

        assert review.name == "Salesforce"
        assert review.is_confident
        assert not review.needs_investigation
        assert review.description is not None

    def test_create_flagged_review(self):
        """Uncertain review should be flagged."""
        review = ItemReview(
            item_id="I-APP-xyz789",
            name="ACME Claims Tool",
            is_confident=False,
            needs_investigation=True,
            flag_reason="LLM could not identify this item",
        )

        assert review.needs_investigation
        assert review.flag_reason is not None


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_empty_result(self):
        """Empty result should have zero counts."""
        result = ReviewResult()

        assert result.items_reviewed == 0
        assert result.items_enriched == 0
        assert result.items_flagged == 0

    def test_summary_with_flagged(self):
        """Summary should list flagged items."""
        result = ReviewResult(
            items_reviewed=5,
            items_enriched=3,
            items_flagged=2,
            reviews=[
                ItemReview(
                    item_id="I-APP-001",
                    name="Custom Tool",
                    needs_investigation=True,
                    flag_reason="Unknown application",
                ),
                ItemReview(
                    item_id="I-APP-002",
                    name="Salesforce",
                    description="CRM platform",
                    is_confident=True,
                ),
            ],
        )

        summary = result.summary()

        assert "Reviewed: 5 items" in summary
        assert "Enriched: 3 items" in summary
        assert "Flagged: 2 items" in summary
        assert "Custom Tool" in summary


# =============================================================================
# Store Integration Tests
# =============================================================================

class TestInventoryIntegration:
    """Tests for integration with InventoryStore."""

    def test_get_flagged_items(self):
        """Should retrieve items marked for investigation."""
        store = InventoryStore()

        # Add some items
        store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
            source_file="test.xlsx",
        )
        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Custom Tool"},
            entity="target",
            source_file="test.xlsx",
        )
        # Flag the item using proper enrichment
        item = store.get_item(item_id)
        item.set_enrichment(
            category="unknown",
            note="Unknown application",
            confidence="low",
            flag="investigate",
        )

        flagged = get_flagged_items(store)

        assert len(flagged) == 1
        assert flagged[0].data["name"] == "Custom Tool"

    def test_clear_flag(self):
        """Should remove flag from item."""
        item = InventoryItem(
            item_id="I-APP-test",
            inventory_type="application",
            entity="target",
            data={"name": "Custom Tool"},
            source_file="test.xlsx",
        )
        item.set_enrichment(
            category="unknown",
            note="Unknown application",
            confidence="low",
            flag="investigate",
        )

        clear_flag(item)

        assert item.enrichment.get("flag") is None


# =============================================================================
# Mock LLM Tests
# =============================================================================

class TestReviewWithMockLLM:
    """Tests using mocked LLM responses."""

    @patch('tools_v2.enrichment.inventory_reviewer.Anthropic')
    def test_review_batch_confident(self, mock_anthropic):
        """Confident LLM response should enrich item."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "reviews": [{
                "name": "Salesforce",
                "description": "Cloud-based CRM platform",
                "category": "CRM",
                "vendor_info": "Salesforce Inc.",
                "confidence": "confident"
            }]
        })
        mock_client.messages.create.return_value = mock_response

        # Create test item
        item = InventoryItem(
            item_id="I-APP-test",
            inventory_type="application",
            entity="target",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            source_file="test.xlsx",
        )

        # Run review
        reviews = _review_batch([item], mock_client, "claude-sonnet-4-20250514", "application")

        assert len(reviews) == 1
        assert reviews[0].description == "Cloud-based CRM platform"
        assert reviews[0].is_confident
        assert not reviews[0].needs_investigation

    @patch('tools_v2.enrichment.inventory_reviewer.Anthropic')
    def test_review_batch_unknown(self, mock_anthropic):
        """Unknown LLM response should flag item."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "reviews": [{
                "name": "ACME Internal Tool",
                "description": None,
                "category": None,
                "vendor_info": None,
                "confidence": "unknown"
            }]
        })
        mock_client.messages.create.return_value = mock_response

        item = InventoryItem(
            item_id="I-APP-test",
            inventory_type="application",
            entity="target",
            data={"name": "ACME Internal Tool"},
            source_file="test.xlsx",
        )

        reviews = _review_batch([item], mock_client, "claude-sonnet-4-20250514", "application")

        assert len(reviews) == 1
        assert reviews[0].needs_investigation
        assert reviews[0].flag_reason is not None

    @patch('tools_v2.enrichment.inventory_reviewer.Anthropic')
    def test_review_inventory_updates_store(self, mock_anthropic):
        """Review should update inventory store with enrichment."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "reviews": [
                {
                    "name": "SAP ERP",
                    "description": "Enterprise resource planning system",
                    "category": "ERP",
                    "vendor_info": "SAP SE",
                    "confidence": "confident"
                },
                {
                    "name": "Custom Portal",
                    "description": None,
                    "category": None,
                    "vendor_info": None,
                    "confidence": "unknown"
                }
            ]
        })
        mock_client.messages.create.return_value = mock_response

        # Setup store
        store = InventoryStore()
        store.add_item(
            inventory_type="application",
            data={"name": "SAP ERP", "vendor": "SAP"},
            entity="target",
            source_file="test.xlsx",
        )
        store.add_item(
            inventory_type="application",
            data={"name": "Custom Portal"},
            entity="target",
            source_file="test.xlsx",
        )

        # Run review
        result = review_inventory(
            inventory_store=store,
            api_key="test-key",
            inventory_type="application",
            entity="target",
        )

        assert result.items_reviewed == 2
        assert result.items_enriched >= 1
        assert result.items_flagged >= 1

        # Check that SAP was enriched
        items = store.get_items(inventory_type="application")
        sap_item = next((i for i in items if i.data.get("name") == "SAP ERP"), None)
        assert sap_item is not None
        assert sap_item.is_enriched

        # Check that Custom Portal was flagged
        custom_item = next((i for i in items if i.data.get("name") == "Custom Portal"), None)
        assert custom_item is not None
        assert custom_item.needs_investigation


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in review process."""

    @patch('tools_v2.enrichment.inventory_reviewer.Anthropic')
    def test_json_parse_error_flags_items(self, mock_anthropic):
        """JSON parse errors should flag items for investigation."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "This is not valid JSON"
        mock_client.messages.create.return_value = mock_response

        item = InventoryItem(
            item_id="I-APP-test",
            inventory_type="application",
            entity="target",
            data={"name": "Test App"},
            source_file="test.xlsx",
        )

        reviews = _review_batch([item], mock_client, "claude-sonnet-4-20250514", "application")

        assert len(reviews) == 1
        assert reviews[0].needs_investigation
        assert "parse error" in reviews[0].flag_reason.lower()

    @patch('tools_v2.enrichment.inventory_reviewer.Anthropic')
    def test_api_error_flags_items(self, mock_anthropic):
        """API errors should flag items for investigation."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        item = InventoryItem(
            item_id="I-APP-test",
            inventory_type="application",
            entity="target",
            data={"name": "Test App"},
            source_file="test.xlsx",
        )

        reviews = _review_batch([item], mock_client, "claude-sonnet-4-20250514", "application")

        assert len(reviews) == 1
        assert reviews[0].needs_investigation
        assert "error" in reviews[0].flag_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
