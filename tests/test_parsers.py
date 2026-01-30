"""
Tests for Phase 2: Parsers & Router

Tests:
1. Type detection from headers
2. Schema validation
3. Markdown parsing
4. File router integration
5. Header mapping
"""

import pytest
import tempfile
from pathlib import Path

from tools_v2.parsers.models import ParsedTable, ParseResult, ValidationResult, IngestResult
from tools_v2.parsers.type_detector import (
    detect_inventory_type,
    detect_with_details,
    suggest_inventory_type,
    map_headers_to_schema,
)
from tools_v2.parsers.schema_validator import (
    validate_table,
    validate_row,
    normalize_row,
)
from tools_v2.parsers.markdown_parser import (
    parse_markdown,
    extract_markdown_tables,
    parse_markdown_table,
)
from tools_v2.file_router import ingest_file, analyze_file

from stores.inventory_store import InventoryStore


# =============================================================================
# Type Detector Tests
# =============================================================================

class TestTypeDetector:
    """Tests for inventory type detection from headers."""

    def test_detect_application_type(self):
        """Application headers should be detected."""
        headers = ["Application", "Vendor", "Version", "Hosting", "Annual Cost"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "application"
        assert confidence > 0.5

    def test_detect_application_with_app_name(self):
        """App Name header should indicate application."""
        headers = ["App Name", "Publisher", "Users", "License Type"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "application"

    def test_detect_infrastructure_type(self):
        """Infrastructure headers should be detected."""
        headers = ["Hostname", "IP Address", "OS", "Environment", "CPU", "Memory"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "infrastructure"
        assert confidence > 0.5

    def test_detect_infrastructure_servers(self):
        """Server-related headers should indicate infrastructure."""
        headers = ["Server Name", "Operating System", "Location", "Role"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "infrastructure"

    def test_detect_organization_type(self):
        """Organization headers should be detected."""
        headers = ["Role", "Team", "Department", "Headcount", "Location"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "organization"
        assert confidence > 0.5

    def test_detect_organization_with_fte(self):
        """FTE header should indicate organization."""
        headers = ["Title", "FTE", "Reports To", "Responsibilities"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "organization"

    def test_detect_vendor_type(self):
        """Vendor/contract headers should be detected."""
        headers = ["Vendor Name", "Contract Type", "Start Date", "End Date", "ACV"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "vendor"
        assert confidence > 0.5

    def test_detect_unknown_for_non_inventory(self):
        """Non-inventory tables should return unknown."""
        headers = ["Notes", "Comments", "Date", "Status"]
        inv_type, confidence = detect_inventory_type(headers)

        assert inv_type == "unknown"

    def test_detect_with_details(self):
        """Test detailed detection output."""
        headers = ["Application", "Vendor", "Version"]
        details = detect_with_details(headers)

        assert details["type"] == "application"
        assert "confidence" in details
        assert "scores" in details
        assert "matched_headers" in details

    def test_suggest_inventory_type(self):
        """Test getting ranked suggestions."""
        headers = ["Application", "Vendor", "Version", "Hostname"]
        suggestions = suggest_inventory_type(headers)

        assert len(suggestions) == 4
        assert suggestions[0][0] == "application"  # Should be top
        assert suggestions[0][1] > suggestions[1][1]  # Higher score

    def test_map_headers_to_schema(self):
        """Test header to schema field mapping."""
        headers = ["Application Name", "Vendor", "Ver", "Annual Cost"]
        mapping = map_headers_to_schema(headers, "application")

        assert "name" in mapping or "application" in mapping
        assert "vendor" in mapping
        assert "cost" in mapping


# =============================================================================
# Schema Validator Tests
# =============================================================================

class TestSchemaValidator:
    """Tests for schema validation."""

    def test_validate_valid_table(self):
        """Valid table should pass validation."""
        table = ParsedTable(
            headers=["name", "vendor", "version"],
            rows=[
                {"name": "Salesforce", "vendor": "Salesforce", "version": "Enterprise"},
                {"name": "SAP", "vendor": "SAP", "version": "S/4HANA"},
            ],
            detected_type="application",
        )

        result = validate_table(table, "application")

        assert result.is_valid
        assert result.total_rows == 2

    def test_validate_missing_required(self):
        """Missing required field should fail validation."""
        table = ParsedTable(
            headers=["vendor", "version"],  # Missing 'name'
            rows=[
                {"vendor": "Salesforce", "version": "Enterprise"},
            ],
            detected_type="application",
        )

        result = validate_table(table, "application")

        assert not result.is_valid
        assert "name" in result.missing_required

    def test_validate_empty_required_values(self):
        """Empty required values should be flagged."""
        table = ParsedTable(
            headers=["name", "vendor"],
            rows=[
                {"name": "Salesforce", "vendor": "Salesforce"},
                {"name": "", "vendor": "SAP"},  # Empty name
                {"name": "N/A", "vendor": "Oracle"},  # N/A name
            ],
            detected_type="application",
        )

        result = validate_table(table, "application")

        assert len(result.warnings) > 0
        assert "name" in result.empty_required

    def test_validate_tracks_missing_optional(self):
        """Missing optional fields should be tracked."""
        table = ParsedTable(
            headers=["name"],  # Only required field
            rows=[
                {"name": "App1"},
                {"name": "App2"},
            ],
            detected_type="application",
        )

        result = validate_table(table, "application")

        assert result.is_valid  # Still valid
        assert "vendor" in result.missing_optional
        assert "cost" in result.missing_optional

    def test_normalize_row(self):
        """Test row normalization to schema fields."""
        row = {"application name": "Salesforce", "vendor": "Salesforce", "annual cost": "$50,000"}
        header_map = {"name": "application name", "vendor": "vendor", "cost": "annual cost"}

        normalized = normalize_row(row, "application", header_map)

        assert "name" in normalized or "application name" in normalized
        assert normalized.get("vendor") == "Salesforce"


# =============================================================================
# Markdown Parser Tests
# =============================================================================

class TestMarkdownParser:
    """Tests for Markdown parsing."""

    def test_extract_single_table(self):
        """Extract single table from markdown."""
        md = """
# Application Inventory

| Application | Vendor | Version |
|-------------|--------|---------|
| Salesforce | Salesforce | Enterprise |
| SAP | SAP | S/4HANA |

Some notes here.
"""
        tables = extract_markdown_tables(md)
        assert len(tables) == 1

    def test_extract_multiple_tables(self):
        """Extract multiple tables from markdown."""
        md = """
## Apps

| Application | Vendor |
|-------------|--------|
| App1 | Vendor1 |

## Servers

| Hostname | OS |
|----------|-----|
| server1 | Linux |
"""
        tables = extract_markdown_tables(md)
        assert len(tables) == 2

    def test_parse_markdown_table(self):
        """Parse markdown table into ParsedTable."""
        table_text = """| Application | Vendor | Version |
|-------------|--------|---------|
| Salesforce | Salesforce | Enterprise |
| SAP | SAP | S/4HANA |"""

        table = parse_markdown_table(table_text)

        assert table is not None
        assert table.row_count == 2
        assert "application" in table.headers
        assert table.rows[0]["application"] == "Salesforce"

    def test_parse_markdown_full(self):
        """Test full markdown parsing with prose extraction."""
        md = """
# IT Overview

This is the application inventory for Acme Corp.

| Application | Vendor |
|-------------|--------|
| App1 | Vendor1 |
| App2 | Vendor2 |

Additional notes about the environment.
"""
        result = parse_markdown(md, "test.md")

        assert result.table_count == 1
        assert result.tables[0].row_count == 2
        assert result.has_prose
        assert "Acme Corp" in result.prose

    def test_parse_markdown_detects_type(self):
        """Parsed tables should have detected type."""
        md = """
| Application | Vendor | Version | Cost |
|-------------|--------|---------|------|
| Salesforce | Salesforce | Ent | $50000 |
"""
        result = parse_markdown(md)

        assert result.tables[0].detected_type == "application"
        assert result.tables[0].detection_confidence > 0.4


# =============================================================================
# File Router Tests
# =============================================================================

class TestFileRouter:
    """Tests for file routing and ingestion."""

    def test_ingest_markdown_file(self):
        """Test ingesting a markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
# Application Inventory

| Application | Vendor | Version | Annual Cost |
|-------------|--------|---------|-------------|
| Salesforce | Salesforce | Enterprise | $50,000 |
| SAP ERP | SAP | S/4HANA | $200,000 |
| Duck Creek | Duck Creek | 12 | $546,257 |
""")
            f.flush()
            file_path = Path(f.name)

        store = InventoryStore()
        result = ingest_file(file_path, store, entity="target")

        # Cleanup
        file_path.unlink()

        assert result.success
        assert result.inventory_items_added == 3
        assert "application" in result.by_type
        assert len(store) == 3

    def test_ingest_updates_inventory_store(self):
        """Ingested items should be in inventory store."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
| Hostname | OS | Environment |
|----------|-----|-------------|
| web-01 | Ubuntu | production |
| db-01 | RHEL | production |
""")
            f.flush()
            file_path = Path(f.name)

        store = InventoryStore()
        result = ingest_file(file_path, store, entity="target")

        file_path.unlink()

        assert result.success
        assert "infrastructure" in result.by_type

        # Check items in store
        items = store.get_items(inventory_type="infrastructure")
        assert len(items) == 2

    def test_analyze_file(self):
        """Test file analysis without importing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
# Application Inventory Report

This document contains the application inventory for Acme Corporation.
The following table lists all applications currently in use by the IT department.

| Application | Vendor |
|-------------|--------|
| App1 | V1 |
| App2 | V2 |

Additional notes: These applications are critical to business operations.
Please review and confirm the accuracy of this inventory.
""")
            f.flush()
            file_path = Path(f.name)

        analysis = analyze_file(file_path)

        file_path.unlink()

        assert analysis["file_type"] == "md"
        assert len(analysis["tables"]) == 1
        assert analysis["total_rows"] == 2
        assert analysis["has_prose"]

    def test_unsupported_file_type(self):
        """Unsupported file types should error."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            file_path = Path(f.name)

        store = InventoryStore()
        result = ingest_file(file_path, store)

        file_path.unlink()

        assert not result.success
        assert len(result.errors) > 0

    def test_unknown_table_type_tracked(self):
        """Unknown table types should be tracked."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""
| Notes | Comments | Date |
|-------|----------|------|
| Note 1 | Comment 1 | 2024-01-01 |
""")
            f.flush()
            file_path = Path(f.name)

        store = InventoryStore()
        result = ingest_file(file_path, store)

        file_path.unlink()

        assert len(result.unknown_tables) == 1
        assert result.inventory_items_added == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestParsersIntegration:
    """Integration tests combining parsers with inventory store."""

    def test_full_workflow_markdown(self):
        """Test complete workflow: parse -> validate -> ingest."""
        md_content = """
# Acme Corp IT Inventory

## Applications

| Application | Vendor | Version | Hosting | Annual Cost | Criticality |
|-------------|--------|---------|---------|-------------|-------------|
| Salesforce CRM | Salesforce | Enterprise | SaaS | $50,000 | high |
| SAP ERP | SAP | S/4HANA | On-Prem | $200,000 | critical |
| Custom Portal | Internal | 2.0 | Cloud | $0 | medium |

## Infrastructure

| Hostname | OS | Environment | CPU | Memory |
|----------|-----|-------------|-----|--------|
| web-01 | Ubuntu 22.04 | production | 4 | 16GB |
| db-01 | RHEL 8 | production | 8 | 32GB |

These systems support the core business operations.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            f.flush()
            file_path = Path(f.name)

        store = InventoryStore()
        result = ingest_file(file_path, store, entity="target")

        file_path.unlink()

        # Check results
        assert result.success
        assert result.by_type.get("application", 0) == 3
        assert result.by_type.get("infrastructure", 0) == 2

        # Check store
        apps = store.get_items(inventory_type="application")
        assert len(apps) == 3

        infra = store.get_items(inventory_type="infrastructure")
        assert len(infra) == 2

        # Check prose was captured
        assert result.prose_length > 0

    def test_reimport_deduplication(self):
        """Re-importing same data should not create duplicates."""
        md = """
| Application | Vendor |
|-------------|--------|
| App1 | Vendor1 |
| App2 | Vendor2 |
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md)
            f.flush()
            file_path = Path(f.name)

        store = InventoryStore()

        # First import
        result1 = ingest_file(file_path, store, entity="target")
        assert result1.inventory_items_added == 2

        # Second import (same data)
        result2 = ingest_file(file_path, store, entity="target")
        # Should not add duplicates
        assert len(store) == 2

        file_path.unlink()


class TestIngestResultFormatting:
    """Tests for IngestResult summary formatting."""

    def test_format_summary(self):
        """Test human-readable summary output."""
        result = IngestResult(
            source_file="test.xlsx",
            file_type="excel",
            inventory_items_added=10,
            by_type={"application": 7, "infrastructure": 3},
            validation_warnings=["5 items missing 'cost' field"],
        )

        summary = result.format_summary()

        assert "test.xlsx" in summary
        assert "Application: 7 items" in summary
        assert "Infrastructure: 3 items" in summary
        assert "missing 'cost'" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
