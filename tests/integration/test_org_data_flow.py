#!/usr/bin/env python3
"""
Test Script: Organization Data Flow Verification

This script verifies the complete data flow from:
  Facts File → FactStore → Organization Bridge → UI Data

Run this after an analysis to diagnose organization data issues.

Usage:
    python test_org_data_flow.py
    python test_org_data_flow.py --facts-file /path/to/facts_*.json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config_v2 import OUTPUT_DIR, DATA_DIR


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    """Print a subsection header."""
    print(f"\n--- {title} ---")


def find_latest_facts_file() -> Path:
    """Find the most recent non-empty facts file."""
    facts_files = sorted(
        OUTPUT_DIR.glob("facts_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    for f in facts_files:
        size = f.stat().st_size
        if size > 500:  # Skip empty/minimal files
            return f

    return None


def test_facts_file(facts_file: Path) -> dict:
    """Test loading and parsing a facts file."""
    print_header("STEP 1: Facts File Analysis")

    result = {
        "file_path": str(facts_file),
        "file_exists": facts_file.exists(),
        "file_size": 0,
        "total_facts": 0,
        "org_facts": 0,
        "domains": {},
        "org_categories": {},
        "gaps": 0,
    }

    if not facts_file.exists():
        print(f"ERROR: Facts file not found: {facts_file}")
        return result

    result["file_size"] = facts_file.stat().st_size
    print(f"File: {facts_file}")
    print(f"Size: {result['file_size']:,} bytes")
    print(f"Modified: {datetime.fromtimestamp(facts_file.stat().st_mtime)}")

    try:
        with open(facts_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return result

    facts = data.get("facts", [])
    gaps = data.get("gaps", [])

    result["total_facts"] = len(facts)
    result["gaps"] = len(gaps)

    print(f"\nTotal Facts: {len(facts)}")
    print(f"Total Gaps: {len(gaps)}")

    # Analyze by domain
    print_section("Facts by Domain")
    for fact in facts:
        domain = fact.get("domain", "unknown")
        result["domains"][domain] = result["domains"].get(domain, 0) + 1

    for domain, count in sorted(result["domains"].items(), key=lambda x: -x[1]):
        print(f"  {domain}: {count}")

    # Analyze organization facts specifically
    org_facts = [f for f in facts if f.get("domain") == "organization"]
    result["org_facts"] = len(org_facts)

    if org_facts:
        print_section("Organization Facts by Category")
        for fact in org_facts:
            cat = fact.get("category", "unknown")
            result["org_categories"][cat] = result["org_categories"].get(cat, 0) + 1

        for cat, count in sorted(result["org_categories"].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

        print_section("Sample Organization Facts")
        for fact in org_facts[:5]:
            item = fact.get("item", "N/A")[:60]
            details = fact.get("details", {})
            print(f"  - [{fact.get('category')}] {item}")
            if details:
                for key in ["headcount", "total_personnel_cost", "vendor_name", "services_provided"]:
                    if key in details:
                        print(f"      {key}: {details[key]}")
    else:
        print("\nWARNING: No organization facts found!")

    return result


def test_fact_store(facts_file: Path) -> tuple:
    """Test loading facts into FactStore."""
    print_header("STEP 2: FactStore Loading")

    result = {
        "loaded": False,
        "fact_count": 0,
        "gap_count": 0,
        "org_fact_count": 0,
    }

    try:
        from tools_v2.fact_store import FactStore

        # Use the class method to load from file
        store = FactStore.load(str(facts_file))

        result["loaded"] = True
        result["fact_count"] = len(store.facts)
        result["gap_count"] = len(store.gaps)

        org_facts = [f for f in store.facts if f.domain == "organization"]
        result["org_fact_count"] = len(org_facts)

        print(f"FactStore loaded successfully")
        print(f"  Facts: {result['fact_count']}")
        print(f"  Gaps: {result['gap_count']}")
        print(f"  Organization Facts: {result['org_fact_count']}")

        return result, store

    except Exception as e:
        print(f"ERROR loading FactStore: {e}")
        import traceback
        traceback.print_exc()
        return result, None


def test_organization_bridge(fact_store) -> tuple:
    """Test building organization data from facts."""
    print_header("STEP 3: Organization Bridge")

    result = {
        "built": False,
        "status": None,
        "staff_count": 0,
        "msp_count": 0,
        "total_headcount": 0,
        "total_compensation": 0,
        "categories": [],
    }

    if fact_store is None:
        print("ERROR: No FactStore available")
        return result, None

    try:
        from services.organization_bridge import build_organization_result

        org_result, status = build_organization_result(fact_store, None, "Test Target")

        result["built"] = True
        result["status"] = status

        if org_result and org_result.data_store:
            store = org_result.data_store
            result["staff_count"] = len(store.staff_members)
            result["msp_count"] = len(store.msp_relationships)
            result["total_headcount"] = org_result.total_it_headcount
            result["total_compensation"] = org_result.total_it_cost

            # Get categories
            cats = {}
            for member in store.staff_members:
                cat = member.role_category.value if hasattr(member.role_category, 'value') else str(member.role_category)
                cats[cat] = cats.get(cat, 0) + 1
            result["categories"] = list(cats.items())

        print(f"Build Status: {status}")
        print(f"Staff Members: {result['staff_count']}")
        print(f"MSP Relationships: {result['msp_count']}")
        print(f"Total Headcount: {result['total_headcount']}")
        print(f"Total Compensation: ${result['total_compensation']:,.0f}")

        if result["categories"]:
            print_section("Staff by Category")
            for cat, count in sorted(result["categories"], key=lambda x: -x[1]):
                print(f"  {cat}: {count}")

        if org_result and org_result.data_store:
            msp_list = org_result.data_store.msp_relationships
            if msp_list:
                print_section("MSP/Vendor Relationships")
                for msp in msp_list[:5]:
                    print(f"  - {msp.vendor_name}: {msp.total_fte_equivalent} FTE eq.")
                    for svc in msp.services[:2]:
                        print(f"      Service: {svc.service_name}")

        return result, org_result

    except Exception as e:
        print(f"ERROR in organization bridge: {e}")
        import traceback
        traceback.print_exc()
        return result, None


def test_web_session() -> dict:
    """Test the web session data loading."""
    print_header("STEP 4: Web Session Check")

    result = {
        "session_available": False,
        "has_fact_store": False,
        "fact_count": 0,
        "org_analysis_available": False,
        "data_source": None,
    }

    try:
        # Import web app components
        from web.app import get_session, get_organization_analysis, get_org_data_source
        from flask import Flask

        # Create a test app context
        app = Flask(__name__)
        app.secret_key = 'test-key'

        with app.test_request_context():
            # This won't work perfectly without a real session, but we can try
            print("Note: Web session test requires running Flask app")
            print("Run the Flask app and check /organization to verify")

            # Try to get data source
            try:
                # Force a fresh analysis
                from web.app import clear_organization_cache
                clear_organization_cache()

                org_result = get_organization_analysis()
                data_source = get_org_data_source()

                result["org_analysis_available"] = org_result is not None
                result["data_source"] = data_source

                print(f"Organization Analysis: {'Available' if org_result else 'Not Available'}")
                print(f"Data Source: {data_source}")

                if org_result:
                    print(f"Total Headcount: {org_result.total_it_headcount}")

            except Exception as e:
                print(f"Note: {e}")

        return result

    except Exception as e:
        print(f"Web session check skipped: {e}")
        return result


def print_summary(results: dict):
    """Print overall summary and recommendations."""
    print_header("SUMMARY & RECOMMENDATIONS")

    facts_ok = results.get("facts", {}).get("org_facts", 0) > 0
    store_ok = results.get("store", {}).get("org_fact_count", 0) > 0
    bridge_ok = results.get("bridge", {}).get("status") == "success"

    print("\nData Flow Status:")
    print(f"  1. Facts File:        {'OK' if facts_ok else 'ISSUE'} ({results.get('facts', {}).get('org_facts', 0)} org facts)")
    print(f"  2. FactStore:         {'OK' if store_ok else 'ISSUE'} ({results.get('store', {}).get('org_fact_count', 0)} org facts loaded)")
    print(f"  3. Organization Bridge: {'OK' if bridge_ok else 'ISSUE'} (status: {results.get('bridge', {}).get('status', 'N/A')})")
    print(f"  4. Web UI Data Source: {results.get('web', {}).get('data_source', 'Not tested')}")

    print("\nRecommendations:")

    if not facts_ok:
        print("  - Run analysis with documents containing organization/staffing information")
        print("  - Check that documents include IT headcount, team structure, or vendor info")

    if facts_ok and not store_ok:
        print("  - Check FactStore.load_from_file() for parsing errors")
        print("  - Verify facts file JSON structure is valid")

    if store_ok and not bridge_ok:
        print("  - Check organization_bridge.py for category mapping issues")
        print("  - Verify fact details contain expected fields (headcount, cost, etc.)")

    if bridge_ok:
        staff = results.get("bridge", {}).get("staff_count", 0)
        if staff > 0:
            print(f"  - Organization data is flowing correctly ({staff} staff members)")
            print("  - Refresh the Organization page in the web UI")
        else:
            print("  - Bridge ran but produced no staff - check fact details format")

    data_source = results.get("web", {}).get("data_source")
    if data_source == "demo":
        print("  - Web UI is showing DEMO data - refresh or clear cache")
    elif data_source == "analysis":
        print("  - Web UI is showing ANALYSIS data - working correctly!")


def main():
    parser = argparse.ArgumentParser(description="Test organization data flow")
    parser.add_argument("--facts-file", type=Path, help="Path to facts file (default: latest)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  IT DD Agent - Organization Data Flow Test")
    print("=" * 60)
    print(f"  Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output Dir: {OUTPUT_DIR}")

    results = {}

    # Step 1: Find and analyze facts file
    if args.facts_file:
        facts_file = args.facts_file
    else:
        facts_file = find_latest_facts_file()

    if facts_file is None:
        print("\nERROR: No facts files found in output directory")
        print(f"  Checked: {OUTPUT_DIR}")
        print("  Run an analysis first to generate facts.")
        return 1

    results["facts"] = test_facts_file(facts_file)

    # Step 2: Test FactStore loading
    store_result, fact_store = test_fact_store(facts_file)
    results["store"] = store_result

    # Step 3: Test organization bridge
    bridge_result, org_result = test_organization_bridge(fact_store)
    results["bridge"] = bridge_result

    # Step 4: Test web session (optional)
    results["web"] = test_web_session()

    # Summary
    print_summary(results)

    # Return success if bridge built successfully
    if results["bridge"].get("status") == "success":
        print("\n" + "=" * 60)
        print("  TEST PASSED: Organization data flow is working")
        print("=" * 60 + "\n")
        return 0
    else:
        print("\n" + "=" * 60)
        print("  TEST INCOMPLETE: See recommendations above")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
