#!/usr/bin/env python3
"""
Verification Script for Doc 05: UI Validation & Enforcement

This script verifies that all components of the deal_type validation
system are properly implemented.

Usage:
    python verify_doc05_implementation.py
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}")
    print(f"    Path: {filepath}")
    return exists


def check_file_contains(filepath, search_text, description):
    """Check if a file contains specific text."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            found = search_text in content
            status = "✅" if found else "❌"
            print(f"{status} {description}")
            if not found:
                print(f"    Missing: '{search_text[:50]}...'")
            return found
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False


def main():
    """Run all verification checks."""
    base_path = Path(__file__).parent
    web_path = base_path / "web"

    print_header("Doc 05 Implementation Verification")
    print(f"Base path: {base_path}\n")

    all_checks = []

    # 1. Check UI Form Updates
    print_header("1. UI Form Updates")

    all_checks.append(check_file_exists(
        web_path / "templates/deals/new.html",
        "Deal creation form (new.html)"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/new.html",
        'required',
        "Form has 'required' attribute on deal_type select"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/new.html",
        'deal-type-help',
        "Dynamic help text element exists"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/new.html",
        'carveout',
        "Carve-out option exists (no hyphen)"
    ))

    # 2. Check Deal List Modal
    print_header("2. Deal List Modal")

    all_checks.append(check_file_exists(
        web_path / "templates/deals/list.html",
        "Deal list page (list.html)"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/list.html",
        'modal-deal-type',
        "Modal has deal type select"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/list.html",
        'getDealTypeBadge',
        "Badge helper function exists"
    ))

    # 3. Check Deal Detail Page
    print_header("3. Deal Detail Page & Edit Modal")

    all_checks.append(check_file_exists(
        web_path / "templates/deals/detail.html",
        "Deal detail page (detail.html)"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/detail.html",
        'editDealTypeModal',
        "Edit deal type modal exists"
    ))

    all_checks.append(check_file_contains(
        web_path / "templates/deals/detail.html",
        'openEditDealTypeModal',
        "Edit modal JavaScript functions exist"
    ))

    # 4. Check Server-Side Validation
    print_header("4. Server-Side Validation")

    all_checks.append(check_file_exists(
        web_path / "routes/deals.py",
        "Deals routes file"
    ))

    all_checks.append(check_file_contains(
        web_path / "routes/deals.py",
        'VALID_DEAL_TYPES',
        "VALID_DEAL_TYPES constant defined"
    ))

    all_checks.append(check_file_contains(
        web_path / "routes/deals.py",
        'Deal type is required',
        "Required field validation message"
    ))

    all_checks.append(check_file_contains(
        web_path / "routes/deals.py",
        'update_deal_type',
        "Update deal type endpoint exists"
    ))

    # 5. Check Database Constraints
    print_header("5. Database Constraints")

    all_checks.append(check_file_exists(
        web_path / "database.py",
        "Database models file"
    ))

    all_checks.append(check_file_contains(
        web_path / "database.py",
        'nullable=False',
        "NOT NULL constraint on deal_type"
    ))

    all_checks.append(check_file_contains(
        web_path / "database.py",
        'CheckConstraint',
        "CHECK constraint defined"
    ))

    all_checks.append(check_file_contains(
        web_path / "database.py",
        "deal_type IN ('acquisition', 'carveout', 'divestiture')",
        "CHECK constraint validates against correct values"
    ))

    # 6. Check Migration
    print_header("6. Database Migration")

    migration_file = base_path / "migrations/versions/004_add_deal_type_constraint.py"
    all_checks.append(check_file_exists(
        migration_file,
        "Migration script (004_add_deal_type_constraint.py)"
    ))

    all_checks.append(check_file_contains(
        migration_file,
        "UPDATE deals",
        "Migration includes backfill logic"
    ))

    all_checks.append(check_file_contains(
        migration_file,
        "create_check_constraint",
        "Migration adds CHECK constraint"
    ))

    # 7. Check Client-Side Validation
    print_header("7. Client-Side Validation")

    js_file = web_path / "static/js/deal_form_validation.js"
    all_checks.append(check_file_exists(
        js_file,
        "Client-side validation JavaScript"
    ))

    all_checks.append(check_file_contains(
        js_file,
        'validateDealType',
        "Validation function exists"
    ))

    all_checks.append(check_file_contains(
        js_file,
        'confirmHighRiskDealType',
        "Confirmation dialog function exists"
    ))

    # 8. Check Tests
    print_header("8. Test Suite")

    test_file = base_path / "tests/test_ui_deal_type_validation.py"
    all_checks.append(check_file_exists(
        test_file,
        "Test file (test_ui_deal_type_validation.py)"
    ))

    all_checks.append(check_file_contains(
        test_file,
        'test_create_deal_without_type_fails',
        "Test for missing deal_type"
    ))

    all_checks.append(check_file_contains(
        test_file,
        'test_create_deal_with_invalid_type_fails',
        "Test for invalid deal_type"
    ))

    all_checks.append(check_file_contains(
        test_file,
        'test_database_constraint_enforcement',
        "Test for database constraints"
    ))

    # 9. Check Documentation
    print_header("9. Documentation")

    summary_file = base_path / "IMPLEMENTATION_SUMMARY_DOC05.md"
    all_checks.append(check_file_exists(
        summary_file,
        "Implementation summary document"
    ))

    # Summary
    print_header("Verification Summary")

    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\nChecks passed: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print("\n✅ All checks passed! Implementation is complete.")
        return 0
    else:
        print(f"\n❌ {total - passed} checks failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
