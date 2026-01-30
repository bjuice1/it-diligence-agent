"""
Schema Validator

Validates parsed tables against inventory schemas.
Reports missing fields, empty values, and data quality issues.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from tools_v2.parsers.models import ParsedTable, ValidationResult
from tools_v2.parsers.type_detector import map_headers_to_schema
from stores.inventory_schemas import (
    get_schema,
    get_required_fields,
    get_optional_fields,
    get_all_fields,
    validate_inventory_type,
)


def validate_table(
    table: ParsedTable,
    inventory_type: Optional[str] = None,
    strict: bool = False
) -> ValidationResult:
    """
    Validate a parsed table against an inventory schema.

    Args:
        table: ParsedTable to validate
        inventory_type: Type to validate against. If None, uses table.detected_type
        strict: If True, treat missing optional fields as warnings

    Returns:
        ValidationResult with validation details
    """
    # Determine type to validate against
    inv_type = inventory_type or table.detected_type
    if not inv_type or inv_type == "unknown":
        return ValidationResult(
            is_valid=False,
            inventory_type="unknown",
            errors=["Cannot validate: inventory type not specified or unknown"],
            total_rows=table.row_count,
        )

    if not validate_inventory_type(inv_type):
        return ValidationResult(
            is_valid=False,
            inventory_type=inv_type,
            errors=[f"Unknown inventory type: {inv_type}"],
            total_rows=table.row_count,
        )

    result = ValidationResult(
        inventory_type=inv_type,
        total_rows=table.row_count,
    )

    # Get schema
    required_fields = get_required_fields(inv_type)
    optional_fields = get_optional_fields(inv_type)
    all_schema_fields = set(required_fields + optional_fields)

    # Map headers to schema fields
    header_map = map_headers_to_schema(table.headers, inv_type)
    mapped_fields = set(header_map.keys())

    # Check for missing required fields
    for field in required_fields:
        if field not in mapped_fields:
            result.missing_required.append(field)
            result.errors.append(f"Missing required field: {field}")

    if result.missing_required:
        result.is_valid = False

    # Check for missing optional fields (informational)
    for field in optional_fields:
        if field not in mapped_fields:
            result.missing_optional[field] = table.row_count  # All rows missing this

    # Check for extra fields not in schema
    for header in table.headers:
        header_lower = header.lower().strip()
        # Check if this header was mapped to any schema field
        if header_lower not in [h.lower() for h in header_map.values()]:
            result.extra_fields.append(header)

    # Validate row data
    empty_counts = defaultdict(int)
    valid_rows = 0

    for row in table.rows:
        row_valid = True

        # Check required fields have values
        for field in required_fields:
            if field in header_map:
                actual_header = header_map[field].lower()
                value = row.get(actual_header)
                if _is_empty(value):
                    empty_counts[field] += 1
                    row_valid = False

        # Check optional fields for emptiness (just tracking)
        for field in optional_fields:
            if field in header_map:
                actual_header = header_map[field].lower()
                value = row.get(actual_header)
                if _is_empty(value):
                    if field not in result.missing_optional:
                        result.missing_optional[field] = 0
                    result.missing_optional[field] += 1

        if row_valid:
            valid_rows += 1

    result.valid_rows = valid_rows
    result.empty_required = dict(empty_counts)

    # Generate warnings for empty required fields
    for field, count in empty_counts.items():
        result.warnings.append(
            f"{count}/{table.row_count} rows have empty '{field}' (required)"
        )

    # Generate warnings for significantly missing optional fields
    if strict:
        for field, count in result.missing_optional.items():
            if count > table.row_count * 0.5:  # More than 50% missing
                result.warnings.append(
                    f"{count}/{table.row_count} rows missing '{field}'"
                )

    return result


def validate_row(
    row: Dict[str, Any],
    inventory_type: str,
    header_map: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Validate a single row against schema.

    Args:
        row: Row data dict
        inventory_type: Type to validate against
        header_map: Optional pre-computed header mapping

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    required_fields = get_required_fields(inventory_type)

    for field in required_fields:
        # Try to find value using header map or direct lookup
        value = None
        if header_map and field in header_map:
            actual_header = header_map[field].lower()
            value = row.get(actual_header)
        else:
            value = row.get(field) or row.get(field.lower())

        if _is_empty(value):
            errors.append(f"Missing required field: {field}")

    return errors


def normalize_row(
    row: Dict[str, Any],
    inventory_type: str,
    header_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Normalize a row to use schema field names.

    Converts actual headers to schema field names and handles
    empty value normalization.

    Args:
        row: Original row with actual headers
        inventory_type: Target inventory type
        header_map: Optional pre-computed header mapping

    Returns:
        Normalized row dict with schema field names
    """
    all_fields = get_all_fields(inventory_type)
    normalized = {}

    # Build reverse header map
    if header_map:
        reverse_map = {v.lower(): k for k, v in header_map.items()}
    else:
        reverse_map = {}

    for actual_header, value in row.items():
        header_lower = actual_header.lower()

        # Try to map to schema field
        if header_lower in reverse_map:
            field_name = reverse_map[header_lower]
        elif header_lower in all_fields:
            field_name = header_lower
        else:
            # Keep original name but lowercase
            field_name = header_lower

        # Normalize value
        normalized[field_name] = _normalize_value(value)

    return normalized


def _is_empty(value: Any) -> bool:
    """Check if a value should be considered empty."""
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip().lower()
        return stripped in ["", "n/a", "na", "-", "--", "tbd", "unknown", "none"]
    return False


def _normalize_value(value: Any) -> Any:
    """Normalize a cell value."""
    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        # Convert empty-like values to None
        if stripped.lower() in ["", "n/a", "na", "-", "--", "tbd", "none"]:
            return None
        return stripped

    return value


def summarize_validation(results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Summarize multiple validation results.

    Args:
        results: List of ValidationResults

    Returns:
        Summary dict with aggregate statistics
    """
    summary = {
        "total_tables": len(results),
        "valid_tables": sum(1 for r in results if r.is_valid),
        "invalid_tables": sum(1 for r in results if not r.is_valid),
        "total_rows": sum(r.total_rows for r in results),
        "valid_rows": sum(r.valid_rows for r in results),
        "by_type": defaultdict(lambda: {"count": 0, "rows": 0, "valid": 0}),
        "common_missing_fields": defaultdict(int),
        "all_errors": [],
        "all_warnings": [],
    }

    for result in results:
        # By type
        if result.inventory_type != "unknown":
            summary["by_type"][result.inventory_type]["count"] += 1
            summary["by_type"][result.inventory_type]["rows"] += result.total_rows
            if result.is_valid:
                summary["by_type"][result.inventory_type]["valid"] += 1

        # Missing fields
        for field in result.missing_required:
            summary["common_missing_fields"][field] += 1
        for field, count in result.missing_optional.items():
            if count > result.total_rows * 0.5:
                summary["common_missing_fields"][field] += 1

        # Collect messages
        summary["all_errors"].extend(result.errors)
        summary["all_warnings"].extend(result.warnings)

    # Convert defaultdicts
    summary["by_type"] = dict(summary["by_type"])
    summary["common_missing_fields"] = dict(summary["common_missing_fields"])

    return summary
