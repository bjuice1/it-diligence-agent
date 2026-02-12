#!/usr/bin/env python3
"""
Verification script for Doc 07: Migration & Rollout Strategy implementation.

Checks:
- All required files created
- Feature flag implemented
- Scripts are executable
- Migration file exists
- Documentation complete
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists and report."""
    if os.path.exists(path):
        print(f"{GREEN}✓{RESET} {description}: {path}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {path} (NOT FOUND)")
        return False

def check_file_executable(path: str, description: str) -> bool:
    """Check if a file is executable."""
    if os.path.exists(path) and os.access(path, os.X_OK):
        print(f"{GREEN}✓{RESET} {description} is executable: {path}")
        return True
    else:
        print(f"{YELLOW}⚠{RESET} {description} not executable: {path}")
        return False

def check_file_contains(path: str, text: str, description: str) -> bool:
    """Check if a file contains specific text."""
    try:
        with open(path, 'r') as f:
            content = f.read()
            if text in content:
                print(f"{GREEN}✓{RESET} {description}: Found in {path}")
                return True
            else:
                print(f"{RED}✗{RESET} {description}: NOT found in {path}")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} Error reading {path}: {e}")
        return False

def main():
    """Run verification checks."""
    print("\n" + "="*60)
    print("DOC 07 IMPLEMENTATION VERIFICATION")
    print("="*60)
    print()

    base_dir = Path(__file__).parent
    checks_passed = 0
    checks_total = 0

    # Check 1: Pre-flight validation scripts
    print("1. PRE-FLIGHT VALIDATION SCRIPTS")
    print("-" * 60)

    scripts = [
        ("scripts/snapshot_existing_deals.py", "Snapshot script"),
        ("scripts/audit_deal_types.py", "Audit script"),
        ("scripts/compare_snapshots.py", "Comparison script"),
    ]

    for script_path, description in scripts:
        full_path = base_dir / script_path
        checks_total += 1
        if check_file_exists(str(full_path), description):
            checks_passed += 1
            # Check if executable
            checks_total += 1
            if check_file_executable(str(full_path), description):
                checks_passed += 1

    print()

    # Check 2: Feature flag implementation
    print("2. FEATURE FLAG IMPLEMENTATION")
    print("-" * 60)

    config_path = base_dir / "config_v2.py"
    checks_total += 1
    if check_file_contains(
        str(config_path),
        "DEAL_TYPE_AWARENESS_ENABLED",
        "Feature flag constant"
    ):
        checks_passed += 1

    checks_total += 1
    if check_file_contains(
        str(config_path),
        "os.getenv('DEAL_TYPE_AWARENESS'",
        "Environment variable check"
    ):
        checks_passed += 1

    print()

    # Check 3: Migration file
    print("3. DATABASE MIGRATION")
    print("-" * 60)

    migration_path = base_dir / "migrations/versions/004_add_deal_type_constraint.py"
    checks_total += 1
    if check_file_exists(str(migration_path), "Migration file"):
        checks_passed += 1

        # Check migration content
        checks_total += 1
        if check_file_contains(
            str(migration_path),
            "valid_deal_type",
            "CHECK constraint"
        ):
            checks_passed += 1

    print()

    # Check 4: Deployment runbook
    print("4. DEPLOYMENT RUNBOOK")
    print("-" * 60)

    runbook_path = base_dir / "docs/deployment/deal_type_rollout_runbook.md"
    checks_total += 1
    if check_file_exists(str(runbook_path), "Deployment runbook"):
        checks_passed += 1

        # Check runbook sections
        runbook_sections = [
            ("Phase 0: Pre-Flight Validation", "Phase 0 section"),
            ("Phase 1: Database Migration", "Phase 1 section"),
            ("Phase 2: Code Deployment", "Phase 2 section"),
            ("Phase 3: UI Rollout", "Phase 3 section"),
            ("Phase 4: Validation & Cleanup", "Phase 4 section"),
            ("Rollback Decision Tree", "Rollback procedures"),
        ]

        for section_text, description in runbook_sections:
            checks_total += 1
            if check_file_contains(str(runbook_path), section_text, description):
                checks_passed += 1

    print()

    # Check 5: User communication
    print("5. USER COMMUNICATION")
    print("-" * 60)

    email_path = base_dir / "docs/user_communication/deal_type_announcement_email.md"
    checks_total += 1
    if check_file_exists(str(email_path), "Email template"):
        checks_passed += 1

        # Check email content
        email_sections = [
            ("Subject:", "Email subject"),
            ("What's New?", "Feature description"),
            ("Action Required", "User action section"),
            ("In-App Notification", "In-app message"),
        ]

        for section_text, description in email_sections:
            checks_total += 1
            if check_file_contains(str(email_path), section_text, description):
                checks_passed += 1

    print()

    # Check 6: Developer guide
    print("6. DEVELOPER GUIDE")
    print("-" * 60)

    dev_guide_path = base_dir / "docs/developer/deal_type_system.md"
    checks_total += 1
    if check_file_exists(str(dev_guide_path), "Developer guide"):
        checks_passed += 1

        # Check developer guide sections
        dev_sections = [
            ("When to Check deal_type", "Decision points section"),
            ("How to Use deal_type", "Usage section"),
            ("Common Pitfalls", "Pitfalls section"),
            ("Testing Checklist", "Testing section"),
            ("Quick Reference Card", "Quick reference"),
        ]

        for section_text, description in dev_sections:
            checks_total += 1
            if check_file_contains(str(dev_guide_path), section_text, description):
                checks_passed += 1

    print()

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Checks passed: {checks_passed}/{checks_total}")

    percentage = (checks_passed / checks_total * 100) if checks_total > 0 else 0

    if percentage == 100:
        print(f"{GREEN}✓ ALL CHECKS PASSED{RESET}")
        print()
        print("Doc 07 implementation is COMPLETE.")
        print()
        print("Next steps:")
        print("1. Run pre-flight validation: python scripts/audit_deal_types.py")
        print("2. Review deployment runbook: docs/deployment/deal_type_rollout_runbook.md")
        print("3. Test scripts in staging environment")
        print("4. Schedule deployment according to runbook phases")
        return 0
    elif percentage >= 80:
        print(f"{YELLOW}⚠ MOSTLY COMPLETE ({percentage:.0f}%){RESET}")
        print()
        print("A few items need attention. Review failed checks above.")
        return 1
    else:
        print(f"{RED}✗ INCOMPLETE ({percentage:.0f}%){RESET}")
        print()
        print("Several items missing. Review failed checks above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
