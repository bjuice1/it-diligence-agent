"""
Unit tests for deal type validation logic.

Tests validation at multiple layers:
- Database constraints
- Flask form validation
- API schema validation

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from web.database import Deal, db


class TestDatabaseConstraints:
    """Test database-level deal type constraints."""

    def test_deal_type_not_null(self):
        """Test that deal_type cannot be NULL."""
        with pytest.raises(Exception) as exc:
            deal = Deal(name="Test", target_name="Target", deal_type=None)
            db.session.add(deal)
            db.session.commit()

        # Check for NOT NULL constraint violation
        error_msg = str(exc.value).lower()
        assert "not null" in error_msg or "violates not-null" in error_msg or "null value" in error_msg

    def test_deal_type_invalid_value(self):
        """Test that invalid deal_type values are rejected."""
        with pytest.raises(Exception) as exc:
            deal = Deal(name="Test", target_name="Target", deal_type="merger")
            db.session.add(deal)
            db.session.commit()

        # Check for CHECK constraint violation
        error_msg = str(exc.value).lower()
        assert "check constraint" in error_msg or "valid_deal_type" in error_msg or "constraint" in error_msg

    def test_deal_type_valid_acquisition(self):
        """Test that 'acquisition' is accepted."""
        deal = Deal(
            name="Test Acquisition",
            target_name="Target Co",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        assert deal.id is not None
        assert deal.deal_type == "acquisition"

        # Cleanup
        db.session.delete(deal)
        db.session.commit()

    def test_deal_type_valid_carveout(self):
        """Test that 'carveout' is accepted."""
        deal = Deal(
            name="Test Carveout",
            target_name="Target Co",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        assert deal.id is not None
        assert deal.deal_type == "carveout"

        # Cleanup
        db.session.delete(deal)
        db.session.commit()

    def test_deal_type_valid_divestiture(self):
        """Test that 'divestiture' is accepted."""
        deal = Deal(
            name="Test Divestiture",
            target_name="Target Co",
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()

        assert deal.id is not None
        assert deal.deal_type == "divestiture"

        # Cleanup
        db.session.delete(deal)
        db.session.commit()


class TestDealModelDefaults:
    """Test deal model default behavior."""

    def test_default_deal_type_is_acquisition(self):
        """Test that deal_type defaults to 'acquisition' when not specified."""
        deal = Deal(
            name="Test Default",
            target_name="Target Co"
        )
        db.session.add(deal)
        db.session.commit()

        assert deal.deal_type == "acquisition"

        # Cleanup
        db.session.delete(deal)
        db.session.commit()

    def test_to_dict_includes_deal_type(self):
        """Test that to_dict() includes deal_type."""
        deal = Deal(
            name="Test Dict",
            target_name="Target Co",
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        deal_dict = deal.to_dict()
        assert "deal_type" in deal_dict
        assert deal_dict["deal_type"] == "carveout"

        # Cleanup
        db.session.delete(deal)
        db.session.commit()


class TestDealTypeEdgeCases:
    """Test edge cases for deal type validation."""

    def test_deal_type_case_sensitive(self):
        """Test that deal_type is case-sensitive (lowercase required)."""
        with pytest.raises(Exception):
            deal = Deal(
                name="Test Case",
                target_name="Target Co",
                deal_type="ACQUISITION"  # Uppercase should fail
            )
            db.session.add(deal)
            db.session.commit()

    def test_deal_type_empty_string(self):
        """Test that empty string is rejected."""
        with pytest.raises(Exception):
            deal = Deal(
                name="Test Empty",
                target_name="Target Co",
                deal_type=""
            )
            db.session.add(deal)
            db.session.commit()

    def test_deal_type_whitespace(self):
        """Test that whitespace is rejected."""
        with pytest.raises(Exception):
            deal = Deal(
                name="Test Whitespace",
                target_name="Target Co",
                deal_type="  acquisition  "
            )
            db.session.add(deal)
            db.session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
